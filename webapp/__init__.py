"""
The flask application package.
"""

from flask import Flask
from os import environ

app = Flask(__name__)

import webapp.views



