"""
specific program to digest machine data from machine_A into a csv
"""

import numpy as np
import pandas as pd
import re

from .machineClass import Machine

class MachineA(Machine):

    def __init__(self, columns):

        Machine.__init__(self)
        self.name = ''
        self.machineid = ''
        self.machineType = 'Magellan'
        # sql columns pre-determined to increase probability the file can be upserted into the database
        self.columns = [ re.sub("\'", "", tup[0]) for tup in columns ]

    def processDOC(self, doc, barcode):
        '''
        doc      raw file uploaded and passed in through the html page and sent to python via requests
        barcode  unique ID for an experiment. If multiple files of the same class have the same barcode,
                 they are considered replicates.
        
        df       dataframe with data and metadata together in a 96 x n dataframe
        ret      dict of extra data that shouldn't go into the dataframe and need to be handled elsewhere
        '''
        
        df_dict = {}
        ret = {}
        wells = {}
        count = 0

        # template example of inserted barcode
        df_dict['barcode'] = barcode
        ret['barcode'] = barcode

        self.name = doc.filename # eg. 'Magellan Sheet 5.csv'
        # if calling from read.csv, use doc, if from html upload, use doc.stream
        for line in doc.stream:
        #for line in doc:
            # decode byte to string, split into array
            line = line.decode('latin').lower().strip().split(',')

            # assume static position of column and well data
            if count == 0:
                columns = line
                
            elif count > 0 and count <= 96:
                wells[line[0]] = line[1]
                
            # handle metadata
            else:
                line = ' '.join(line)
                #print("meta line: {}".format(line))

                if 'date' in line and 'measurement' not in line:
                    #print("regexing date:", line)
                    date_regex = re.findall('\:\s([\w\d\-\:]*)\,?', line)

                    if date_regex:
                        print("date_regex", date_regex)
                        ret['date'] = date_regex[0]
                        ret['time'] = date_regex[1]

                elif ':' in line and 'date' not in line:
                    meta_regex = re.search('(.*)\:\s([\d\w].*)', line)
                    if meta_regex:
                        #print("\tMETA regex:", meta_regex.group(1), "--", meta_regex.group(2))
                        key = meta_regex.group(1)
                        # remove text in parentheses
                        key = re.sub('\s?\([^)]*\)', '', key)
                        value = meta_regex.group(2)
                        df_dict[key] = value
                    else:
                        print("missing meta line: {}".format(line))
            
            count += 1

        #print('wells:', wells)
        df_dict['wells'] = wells
        df_dict['fileID'] = self.name

        #print("df_dict:", df_dict)
            
        df = pd.DataFrame.from_dict(df_dict)
        df = df.reset_index()

        df = df.rename(columns={ 'index': 'wells', 'wells': 'values', 'meas. temperature: raw data': 'temperature' })
        # hack to get leading zero in wells
        df['wells'] = df['wells'].apply(lambda x: x[0] + '0' + x[1] if len(x) == 2 else x)

        # default value if not included in experimental file
        for col in self.columns:
            if col not in df.columns:
                df[col] = None

        # reorder columns based off sql assay order (loaded in init)
        df = df[self.columns]
        
        #print(df.head())
        #print("returning unformatted params: {}".format(ret))
        return df, ret
        

if __name__ == '__main__':

    MACA = MachineA()
    pdir = 'sample_data/'
    fname = 'Magellan Sheet 4.csv'
    doc = MACA.process(pdir, fname)

    #print(doc)

    df = pd.DataFrame.from_dict(doc)
    df = df.reset_index()
    df.rename(columns={ 'index': 'wells', 'wells': 'values', 'meas. temperature: raw data': 'temperature' })
    
    print(df.head())
