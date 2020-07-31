# flask_aws
flask webapp hosted on aws

## Program description

This is a flask app hosted on aws. It allows researchers at miprobes to access a webpage anywhere that allows them to

 - upload experimental and metadatafiles to the cloud
 - convert these raw files into a standard format that is then stored in a database (sqlite during prototyping stage)
 - produce a table and a heatmap of the uploaded file
 - an analysis page that produces plots of a well-layout or a cell-layout of data in the database, filtered by barcode

### index.html, upload_page.html, analysis.html

These are html files that describe the format of the webpage that is loaded.
If there are buttons or text boxes on the page, jquery is used to trigger corresponding
functions in views.py, with optional arguments also sent to views.py depending on the user input.

### views.py

Perhaps the heart of the flask webapp. Decorators point the loaded html page or jquery request to the correct function. These functions then call other functions that initialize objects, process data, and create graphs, then finish with returning either a full template or graph(s) to the html page.

### machineA.py, assay.py

Object-oriented class for assay metadata files or experimental files that determines how the files are processed. Returns a dataframe and an optional dict of additional parameters, depending on what needs to be done with the uploaded file.

### sqlite_s3.py

Object-oriented class for sqlite that creates a connection to sqlite and describes the tables that are created for assay, assayLayout, and experiment tables. After a file is uploaded, a function within this class is called that upserts it into the correct database. As SQL is being used, special care about having exactly the correct columns in exactly the correct order must be observed (atleast until more flexible code is implemented).

### support_functions.py

any extraneous function is included in here, mainly the interactive plotly graphs.


## Running the server

### remotely

 - Access the AWS site to find the IP of the instance.
 - If the instance is not running, start it then ssh into it
   - ssh requires an ssh key that has been added to the aws instance
   - eg. ssh -i ~/.ssh/miprobes.pem ubuntu@18.195.215.190
 -Start the flask server via
   - cd awsmiprobes
   - python runserver.py
 - Once the server appears to be started, go to a web browser and type
   in that IP and port 5000
   - http://18.195.215.190:5000
   
### Locally
 - Packages are managed using Conda. Download Conda or Miniconda from the internet 
   and ensure it is loaded before proceeding
 - From github download the conda venv list of packages from flask_aws/mirage_requirements.yml 
 - Download the packages for the venv using conda (can be named something other than mirage)
   - conda env create -f mirage.yml 
 - Activate the environment
   - conda activate mirage
 - run the server
   - python runserver.py
 - Once the server appears started, go to a web browser and put in the loop-back IP and 
   designated port
   - http://0.0.0.0:5000 or http://localhost:5000
 

