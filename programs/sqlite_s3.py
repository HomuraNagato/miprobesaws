

import sqlite3
import boto3
import pandas as pd

from programs.machine_A import MachineA


class LiteConn(object):

    def __init__(self, db_name = 'pensieveS3.db', tbl_name='experiments'):
        self.db_name = db_name
        self.table_name = tbl_name
        self.columns = self.defineColumns()
    
    def __enter__(self):
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
        if exc_val:
            raise

    def defineColumns(self):
        columns_dict = {
            'experiments': [
                    ("'wells'", "TEXT"), 
                    ("'barcode'", "TEXT"),
#                    ("'date'", "DATE"), 
                    ("'instrument serial number'", "INT"), 
                    ("'measurement mode'", "TEXT"),
                    ("'excitation wavelength'","TEXT"), 
                    ("'emission wavelength'", "TEXT"), 
                    ("'excitation bandwidth'", "TEXT"),
                    ("'emission bandwidth'", "TEXT"), 
                    ("'gain'", "TEXT"), 
                    ("'number of reads'", "TEXT"), 
                    ("'flashmode'", "TEXT"),
                    ("'integration time'", "TEXT"), 
                    ("'lag time'", "TEXT"), 
                    ("'plate definition file'", "TEXT"), 
                    ("'z-position'", "TEXT"),
                    ("'unit'", "TEXT"), 
                    ("'temperature'", "TEXT"), 
                    ("'values'", "INT"),
                    ("'fileID'", "TEXT")
            ],
            'assays': [
                ("'index'", "INTEGER"),
                ("'barcode'", "TEXT"),
                ("'inducer'", "TEXT"),
                ("'inducer concentration'", "TEXT"),
                ("'media'", "TEXT"),
                ("'volume in well'", "INT"),
                ("'strain'", "TEXT"),
                ("'VP'", "TEXT"),
                ("'start time'", "DATE"),
                ("'read time'", "TEXT"),
                ("'induction time'", "TEXT"),
                ("'researcher name'", "TEXT"),
                ("'culture type'", "TEXT"),
                ("'plate reader'", "TEXT"),
                ("'plate reader method'", "TEXT"),
                ("'date'", "TEXT"),
                ("'time'", "TEXT")
            ],
            'assayLayout': [
                ("'layout'", "TEXT"),
                ("'wells'", "TEXT"),
                ("'barcode'", "TEXT")
            ]
        }                             
        return columns_dict[self.table_name]


    def createDB(self, unique = 'UNIQUE(wells, fileID)'):
        #self.cursor.execute("""DROP TABLE {}""".format(self.table_name))

        

        query = """CREATE TABLE IF NOT EXISTS {} (""".format(self.table_name) + \
                    ', '.join([ '\" \"'.join(tup) for tup in self.columns ]) + ", " + unique + ")"

        self.cursor.execute(query)
        self.conn.commit()

    def upsert(self, df):
        
        # convert df to tuple
        tasks = [ tuple(row) for row in df.to_numpy() ]

        print("upserting into table {} shape: {}\n{}".format(self.table_name, df.shape, df.head()))

        sql = "REPLACE INTO {} VALUES (".format(self.table_name) + ', '.join(['?'] * len(self.columns)) + ");"

        self.conn.executemany(sql, tasks)
        self.conn.commit()


    def query_func(self, query):
        df = pd.read_sql(query, self.conn)
        return df

    def execute_func(self, query):
        self.conn.execute(query)
        self.conn.commit()

    def update_paren(self, tbl_par, params):
        '''
        get a df of parent to adjust values of
        convert values in df based off column=key in params
        upsert with temp values to allow for self.upsert in parent,
        as this is called from child most likely
        '''
        query = "SELECT * FROM {} WHERE barcode = '{}';".format(tbl_par, params['barcode'])
        par_df = self.query_func(query)

        #print("{} sql\n {}\n".format(tbl_par, par_df))

        for key, val in params.items():
            par_df[key] = val

        #print("{} updated sql\n {}\n".format(tbl_par, par_df))

        tmp_tbl_name = self.table_name
        self.table_name = tbl_par
        self.columns = self.defineColumns()
        
        self.upsert(par_df)

        self.table_name = tmp_tbl_name
        self.columns = self.defineColumns()

    def upsertAssayLayout(self, params):

        table_name = 'assayLayout'
        df = params[table_name]

        # as these internal functions use defined table_names and columns, if acting on a different
        # table, have to update the functions active table, call those functions, then restore the 
        # original table
        tmp_tbl_name = self.table_name
        self.table_name = table_name
        self.columns = self.defineColumns()
        
        self.createDB(unique='UNIQUE(wells, barcode)')
        self.upsert(df)
        
        self.table_name = tmp_tbl_name
        self.columns = self.defineColumns()
        
