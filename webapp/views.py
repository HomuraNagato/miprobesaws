"""
Routes and views for the flask application.
"""

import os
from datetime import datetime
import pandas as pd
import numpy as np
import json

from flask import Flask, flash, render_template, request, redirect, url_for, jsonify
from flask_uploads import UploadSet
import plotly
import plotly.graph_objs as go
import plotly.express as px
import boto3

from webapp import app

import programs.support_functions as support
from programs.sqlite_s3 import LiteConn
from programs.machine_A import MachineA
from programs.assay import Assay


@app.route('/')
@app.route('/home')
def home():
    """Renders the home page."""
    return render_template(
        'index.html',
        title='Home Page',
        year=datetime.now().year,
        message='Your home page.'
    )


@app.route('/sql_query', methods=['GET', 'POST'])
def sql_query():

    '''
    queries
    query into a dataframe based off select
    otherwise execute on table
    DELETE FROM experiments WHERE fileID == "Magellan Sheet 6.csv"
    SELECT * FROM experiments GROUP BY fileID
    '''

    connObj = LiteConn()
    
    query = request.args['query']
    print("raw query: {}".format(query))

    if query == '':
        query = "SELECT * FROM experiments;"
        

    with connObj as conn:
        if query.split()[0] == 'SELECT':
            df = connObj.query_func(query)
        else:
            connObj.execute_func(query)
            file_query = "SELECT fileID FROM experiments GROUP BY fileID;"
            df = connObj.query_func(file_query)

    print(df.shape)
    columns = df.columns

    df = support.format_table(df, columns)

    table = support.create_table(df, columns, query)

    return table


@app.route('/upload_page', methods=['GET', 'POST'])
def upload_page():
    print("accessed upload_data REFACTION  method", request.method)

    '''
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Bucket.put_object
    '''

    connObj = LiteConn(tbl_name='experiments')
    
    if request.method == 'POST':
        
        # get file
        doc = request.files['file']
        filename = doc.filename

        # upload to aws S3
        s3 = boto3.resource('s3')
        res = s3.Bucket('miprobes.s3').put_object(Key=doc.filename,
                                            Body=doc,
                                            CacheControl= 'no-cache'  )
        
        print("Posted file: {} s3 response: {}".format(request.files['file'], res))

        # rewind filestream to allow re-reading
        doc.seek(0)
        barcode = ''

        # create machine class
        if 'Magellan' in filename or 'Fluorescence' in filename:
            handler = MachineA(connObj.columns)
            if 'Magellan' in filename:
                barcode = 'lac-0.1'
            elif 'Fluorescence' in filename:
                barcode= 'fluor-0.1'
        elif 'assay' in filename:
            # reset object for assay
            connObj = LiteConn(tbl_name='assays')
            handler = Assay(connObj.columns)
            barcode = handler.barcode
            print("barcode:", barcode)
            # 'programs/temp/assay_template_values.xlsx'
            file_path = os.path.join('programs/temp/', filename)
            doc.save(file_path)
            if 'xlsx' in filename:
                doc = pd.read_excel(file_path, sheet_name=0)
            else:
                doc = pd.read_csv(file_path)
        else:
            print("Error, unknown file type uploaded. Currently supported are experimental data from Magellan machines and assay files with 'assay' in it's name")
            return ""

        # process file
        df, par_params = handler.processDOC(doc, barcode)
        # select columns to view in table, perhaps move this to a class function if desire a subset
        columns = handler.columns
        
        # upload to sqlite
        with connObj as conn:

            connObj.createDB()
            connObj.upsert(df)

            # update assay with post-experiment values
            if par_params and connObj.table_name == 'experiments':
                print("will update assays")
                connObj.update_paren('assays', par_params)
                # add assayLayout table
            elif par_params and connObj.table_name == 'assays':
                print("will update assays with layout")
                connObj.upsertAssayLayout(par_params)
                

        # format a table
        df = support.format_table(df, columns)
        print(df.shape)

        table = support.create_table(df, columns, filename)
        
        return table
    
    else:

        # generic table query
        query = "SELECT * FROM " + connObj.table_name + ";"
        print("query: {}".format(query))
        
        with connObj as conn:
            df = connObj.query_func(query)

        columns = df.columns
        
        df = support.format_table(df, columns)

        table = support.create_table(df, columns, '')

        return render_template(
            'upload_page.html',
            table=table,
            heatmaps='',
            year=datetime.now().year,
            title='Upload Page',
            message='upload experimental and metadata files to the database'
        )

@app.route('/s3_heatmap', methods=['GET', 'POST'])
def s3_heatmap():

    connObj = LiteConn()
    
    # only experimental files have a filename
    doc = request.files['file'] 
    print("doc filename:", doc.filename)
    
    query = "SELECT * FROM " + connObj.table_name + " WHERE fileID == '" + doc.filename + "';"
    print("query: {}".format(query))

    with connObj as conn:
        df = connObj.query_func(query)
        
    print("heatmap head", df.head(), "\n", df.shape)
    heatmap = support.create_heatmap(df, doc.filename)

    return heatmap


@app.route('/analysis', methods=['GET', 'POST'])
def analysis():

    #print("request.method: {}".format(request.method)) # GET
    
    # determine barcode based on either input in text cell within anlaysis page, or a default one
    if request.args and request.args['query'] != '':
        print("request.args: {}".format(request.args))
        barcode = request.args['query']
    else:
        barcode = 'lac-0.1'

    print("requesting barcode {}".format(barcode))

    # ---------------------
    # Well oriented graph
    connObj = LiteConn(tbl_name='experiments')
    query = "SELECT * FROM {} WHERE barcode == '{}'".format(connObj.table_name, barcode)
    with connObj as conn:
        df = connObj.query_func(query)

    #print("query: {}\ndf shape {}".format(query, df.shape))

    # return if no barcode in db
    if df.shape[0] == 0:
        print("barcode: {} not found in the database".format(barcode))
        return ""

    df = df.loc[:,['wells', 'barcode', 'fileID', 'values']]
    graph = support.create_scatter_graph(df, barcode)

    # ---------------------
    # layout oriented graph
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

    #print("***** df1\n", df1.head)
    #print("***** df2\n", df2.head)
    df = df1.merge(df2, on=['barcode', 'wells'], how='inner')
    print("joined head\n", df.head(), "\n", df.shape)

    normalized_graph = support.create_normalized_graph(df, barcode)

    # ---------------------
    
    if request.args and request.args['query'] != '':
        if request.args['action'] == 'wellLayout':
            return graph
        else:
            return normalized_graph
    else:
        return render_template(
            'analysis.html',
            title='analysis page',
            graph=graph,
            normalized_graph=normalized_graph,
            message='page for analysis.'
        )





