"""
support functions to manipulate data before plotting
"""

import plotly
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import json
import string

def default_fig():

    fig = go.Figure()
    
    layout = go.Layout(

        width = 1200,
        height = 800,

        margin = { 'l': 20, 'r': 20, 't': 20, 'b': 20, 'pad': 10 },

    )
    fig = dict(data=[0,1,2,], layout=layout)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON
    
def create_line_chart(df, x_axis, y_axis, text_axis, group_axis):

    fig = go.Figure()

    # columns: date, close_price, symbol, simple_name

    data = []
    count = 0
    for group in df[group_axis].unique():

        df_sub = df[df[group_axis] == group]

        # cut clutter by only displaying four items at start
        if count < 4:
            visible = True
        else:
            visible = 'legendonly'

        data.append(go.Scatter(
            x = df_sub[x_axis],
            y = df_sub[y_axis],
            visible=visible,
            mode = 'lines',
            name = group,

        ))
        count += 1


    layout = go.Layout(
        title = 'Robinhood lineplot',
        showlegend = True,
        yaxis = {'title': y_axis},
        xaxis = {'title': x_axis},
        template='plotly_dark'
    )

    fig = dict(data=data, layout=layout)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON


def format_table(df, columns, row_filter_col=None, row_filter=None):
    
    if row_filter_col:
        df = df.loc[df[row_filter_col] == row_filter, columns].copy()
    else:
        df = df.loc[:, columns].copy()

    return df

def create_table(df, columns, filename):

    fig = go.Figure()

    data = [
        go.Table(
            header=dict(values= columns,
                    fill_color= 'paleturquoise',
                    align= 'left'),
            cells=dict(values= [ df[x] for x in columns ],
                    fill_color= 'lavender',
                    align= 'left'),
            )
        ]

    layout = go.Layout(
        title = filename,

        #width = 1200,

        #margin = { 'l': 20, 'r': 20, 't': 20, 'b': 20, 'pad': 10 },
        #autosize = False,

    )
    
    #fig.update_yaxes(automargin=True)

    fig = dict(data=data, layout=layout)
    
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON



def create_heatmap(df, fname):

    fig = go.Figure()

    print(" **************** heatmap **************** ", fname)
    # heatmap page https://plotly.com/python/heatmaps/

    # sort along index column axis
    df = df.loc[:,['wells', 'values']].sort_values('wells')
    print(df.head())
    wells_num = np.arange(1,13)
    wells_char = np.array(list(string.ascii_lowercase[0:8]))
    #wells = [ char + str(num) for char in wells_char for num in wells_num ]
    wells = df['wells'].to_numpy()
    #wells = wells.reshape(8,12)
    wells = wells.reshape(12, 8, order='F') # fortran ordering, converse to C ordering
    wells_values = df['values'].to_numpy().reshape(12, 8, order='F')
    print("wells num:", wells_num)
    print("wells char:", wells_char)
    print("wells_values:", wells_values)        

    data = [
        go.Heatmap(
            z = wells_values,
            x = wells_char,
            y = wells_num,
            hoverongaps = True
        )
    ]
    
    layout = go.Layout(
        title = fname,
        showlegend = True,
        template='plotly_dark',

        #width = 1200,
        #height = 800,

        #margin = { 'l': 20, 'r': 20, 't': 20, 'b': 20, 'pad': 10 },
        #autosize = False,

    )
    
    fig = dict(data=data, layout=layout)
    
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON

def create_scatter_graph(df, barcode):
    
    fig = go.Figure()

    print(" **************** analysis scatter graph **************** ")

    df = df.sort_values('wells')

    df2 = df.groupby(['wells'], as_index=False).agg( { 'values': ['mean', 'std'] } ).reset_index()
    print(df2)
    
    data= [
        go.Scatter(
            x = df2['wells'].to_numpy(),
            y = df2['values']['mean'].to_numpy(),
            error_y = dict(
                type = 'data',
                symmetric=True,
                array=df2['values']['std'].to_numpy()
            ),
            mode = 'markers'
        )
    ]

    layout = go.Layout(
        title = '[Raw] [well layout] barcode: ' + barcode,
        #showlegend = True,
        yaxis = {'title': 'values'},
        xaxis = {'title': 'wells'},
        template='plotly_dark'
        
    )
    
    fig = dict(data=data, layout=layout)
    
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON
    
def create_normalized_graph(df, barcode):

    fig = go.Figure()

    print(" **************** analysis scatter graph **************** ")

    df = df.sort_values('wells')
    df2 = df.groupby(['wells', 'layout'], as_index=False).agg( { 'values': ['mean', 'std'] } )
    df2.columns = ['wells', 'layout', 'mean', 'std']
    df2['root'] = df2['layout'].str.extract('(.*)_[unind,ind]', expand=True)
    print(df2)

    buf = np.mean(df2[df2['layout'] == 'buffer']['mean'])
    #print(buf)
    
    df_unind = df2[df2['layout'].str.match('.*_unind')]
    df_ind = df2[df2['layout'].str.match('.*_ind')]
    
    print("unindf df\n", df_unind.head())
    print("indf df\n", df_ind.head())

    df3 = df_unind.merge(df_ind, on=['root'])
    df3['normal_mean'] = (df3['mean_y'] - buf) / (df3['mean_x'] - buf)
    print("df3\n{}".format(df3.head()))

    # create graph
    data= [
        go.Scatter(
            x = df3['root'].to_numpy(),
            y = df3['normal_mean'].to_numpy(),
            mode = 'markers'
        )
    ]

    layout = go.Layout(
        title = '[normalized] [cell layout] barcode: ' + barcode,
        yaxis = {'title': 'normalized values'},
        xaxis = {'title': 'cell name'},
        template='plotly_dark'
        
    )
    
    fig = dict(data=data, layout=layout)
    
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON
