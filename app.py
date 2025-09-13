'''
# relevant libraries

import os # for interactivity with the OS 
from flask import Flask, render_template, request, redirect # for web app structure
from tinydb import TinyDB # for proof of concept (lightweight JSON based DB)

# create the flask object
app = Flask(__name__)

# creates the TinyDB object an creates a cases table
db = TinyDB("beaconport_db.json")
cases_table = db.table("cases")

# defines the route for GET and POST methods
@app.route("/", methods=["GET", "POST"])

def index():
    # Print debug info
    print("👉 Current working directory:", os.getcwd())
    print("👉 Flask template folder:", app.template_folder)

    if request.method == "POST":
        # placeholder for testing basic records into TinyDB
        record = {
            "case_id": request.form["case_id"],
            "notes": request.form["notes"]
        }
        cases_table.insert(record)
        # refreshes the page
        return redirect("/")

    # loads all cases in TinyDB to display
    all_cases = cases_table.all()
    return render_template("index.html", cases=all_cases)

if __name__ == "__main__":
    app.run(debug=True)
'''

# import relevant libraries
from flask import Flask, render_template
from tinydb import TinyDB

# create flask instance
app = Flask(__name__)

# connect to TinyDB
db = TinyDB("beaconport_db.json")
cases_table = db.table("cases")

# create route for HTML
@app.route("/")
def index():
    # load all imported cases
    all_cases = cases_table.all()
    return render_template("index.html", cases=all_cases)

if __name__ == "__main__":
    app.run(debug=True)

