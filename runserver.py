"""
This script runs the python_webapp_flask application using a development server.
"""

from os import environ
from webapp import app

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    #app.run(host='127.0.0.1' debug=True) # localhost
    app.run(host='0.0.0.0', debug=True)
