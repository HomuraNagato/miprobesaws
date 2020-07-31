"""
specific program to digest machine data from machine_A into a csv
"""

import numpy as np
import pandas as pd
import re
import string

from .machineClass import Machine

class Assay(Machine):
    
    def __init__(self, columns):

        Machine.__init__(self)
        self.name = ''
        self.barcode = ''
        self.columns = [ re.sub("\'", "", tup[0]) for tup in columns ]
        
    def processDOC(self, doc, barcode='0'):

        # ignore this barcode, will collect if within the file itself,
        # retained to allow calling same function as experimental files

        print("*** processing doc: *** \n")
        # get barcode and some parameters to update in metadata
        ret = {}

        # create dataframe of parameters using a cut point as the position
        # pf the bottom of the parameters section
        pos_params_bot = doc.loc[doc['parameter'] == 'VP'].index[0] + 1
        docParams = doc.iloc[0:pos_params_bot, 0:2]

        # create dataframe of post-experiment 
        pos_post_top = doc.loc[doc['parameter'] == 'post-experiment'].index[0] + 1
        pos_post_bot = doc.loc[doc['parameter'] == 'time'].index[0] + 1
        docPost = doc.iloc[pos_post_top:pos_post_bot, 0:2]

        # create dataframe of wells
        pos_well_top = doc.loc[doc['parameter'] == 'well_layout'].index[0] + 2
        docLayout = doc.iloc[pos_well_top:pos_well_top+8, 1:13]
        docLayout = docLayout.values.reshape(1,96)[0]

        # create wells for joining
        wells_num = np.arange(1,13)
        wells_char = np.array(list(string.ascii_lowercase[0:8]))
        wells = [ char + str(num).zfill(2) for char in wells_char for num in wells_num ]
        #print(wells)

        # determine barcode
        #df.loc[0, 'barcode'] = df.loc[:,'inducer'][0] + '-' + str(df.loc[:,'inducer concentration'][0])
        self.barcode = docParams[docParams['parameter'] == 'inducer'].iloc[0,1] + '-' + str(docParams[docParams['parameter'] == 'inducer concentration'].iloc[0,1])
        print("barcode! {}".format(self.barcode))

        # get layout of wells and store for processing later
        docLayout = pd.DataFrame({ 'layout': docLayout, 'wells': wells, 'barcode': self.barcode })
        ret['assayLayout'] = docLayout
        #print("docLayout: \n{}".format(docLayout))

        # put the two sections of assay into a dataframe
        df = pd.concat([docParams, docPost], axis=0)

        # pivot orders, must re-order as desired
        df['barcode'] = self.barcode

        #print("self columns:", self.columns)
        df = df.pivot(index='barcode', columns='parameter', values='value')
        
        # flatten to get barcode as an index
        df = df.reset_index()
        
        # create unique index
        df = df.reset_index()

        df.loc[0, 'barcode'] = self.barcode

        # reorder columns based off sql assay order
        df = df[self.columns]
        
        #print("*** DOC ***", df.head(), "\n")

        return df, ret
        
