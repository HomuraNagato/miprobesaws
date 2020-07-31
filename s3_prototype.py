
import os
import sqlite3
import boto3
import numpy as np
import pandas as pd

from programs.machine_A import MachineA
from programs.sqlite_s3 import LiteConn
from programs.assay import Assay


if __name__ == '__main__':

    
    '''
    connObj = LiteConn(tbl_name='assays')
    #connObj = LiteConn(tbl_name='experiments')
    
    doc = pd.read_excel('programs/temp/assay_template_values.xlsx', sheet_name=0)
    #doc = open('programs/temp/Magellan Sheet 5.csv', 'r', encoding='latin')
    handler = Assay(connObj.columns)
    #handler = MachineA(connObj.columns)

    barcode = 'lac-0.1'
    df, par_params = handler.processDOC(doc, barcode)
    
    with connObj as conn:

        #connObj.createDB()
        #connObj.upsert(df)

        # update assay with post-experiment values
        if par_params and connObj.table_name == 'experiments':
            print("will update assays with ret {}".format(par_params))
            connObj.update_paren('assays', par_params)
        # add assayLayout table
        elif par_params and connObj.table_name == 'assays':
            print("will update assays with layout")
            connObj.upsertAssayLayout(par_params)

    '''
    barcode = 'lac-0.1'
    # need two connections for experimental data and assay data, required for
    # manipulating before creating a heatmap
    connObj = LiteConn(tbl_name='experiments')
    query = "SELECT * FROM " + connObj.table_name + " WHERE barcode == '" + barcode + "';"

    with connObj as conn:
        df1 = connObj.query_func(query)

    connObj = LiteConn(tbl_name='assayLayout')
    query = "SELECT * FROM " + connObj.table_name + " WHERE barcode == '" + barcode + "';"

    with connObj as conn:
        df2 = connObj.query_func(query)

    #print("experiment head\n", df1.head(), "\n", df1.shape)
    #print("assay head\n", df2.head(), "\n", df2.shape)

    df = df1.merge(df2, on=['barcode', 'wells'], how='inner')


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
    df3['normal_mean'] = (df3['mean_y'] - buf) / df3['mean_x']
    print("df3\n{}".format(df3.head()))
    
    #heatmap = support.create_heatmap(df, doc.filename)




