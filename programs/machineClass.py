"""
super class of machines to inherit general attributes and functions
"""

import pandas as pd

class Machine(object):

    def __init__(self):

        self.df = pd.DataFrame()
        self.name = ""
        self.path = ""
