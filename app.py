import io
from flask import Flask, json, render_template, request, redirect, send_file, url_for, flash
from tinydb import TinyDB
import matplotlib.pyplot as plt
import subprocess
import sys
import os

app = Flask(__name__)
app.secret_key = "beaconport-secret"

def get_case_count():
    """Get the count of unique cases in the database"""
    try:
        db = TinyDB("beaconport_db.json")
        cases_table = db.table("cases")
        all_cases = cases_table.all()
        
        # Count unique case references from the main data
        unique_refs = set()
        for case in all_cases:
            # Get the case reference from the main section
            if 'main' in case:
                main_data = case['main']
                # Find the reference field (could be any column name containing the ref)
                for key, value in main_data.items():
                    if value and str(value).strip():  # Skip empty values
                        # Assume the first non-empty field in main is the reference
                        # This matches how import_excel.py uses the first column as ref
                        unique_refs.add(str(value).strip())
                        break
        
        return len(unique_refs)
    except Exception:
        return 0

@app.route("/", methods=["GET", "POST"])
def index():
    case_count = get_case_count()
    
    if request.method == "POST":
        try:
            # Run the import_excel.py script
            excel_file = "Beaconport Capture.xlsx"  # Default filename
            
            # Check if file exists
            if not os.path.exists(excel_file):
                flash(f"Error: {excel_file} not found in the current directory")
                return redirect(url_for("index"))
            
            # Run the import script
            result = subprocess.run([sys.executable, "import_excel.py", excel_file], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                flash("Excel data successfully imported! ✅")
            else:
                flash(f"Error running import: {result.stderr}")
                
        except Exception as e:
            flash(f"Error: {e}")
        
        return redirect(url_for("index"))
    
    return render_template("index.html", case_count=case_count)


@app.route("/victim_ages")
def victim_ages():
    db_path = os.path.join(os.path.dirname(__file__), "beaconport_db.json")
    with open(db_path, "r") as f:
        data = json.load(f)
    ages = []
    for case in data["cases"].values():
        for victim in case.get("victim_details", []):
            age = victim.get("Victim Age at Time of Offence")
            if age is not None:
                ages.append(age)
    return render_template("victim_ages.html")

@app.route("/victim_ages_chart.png")
def victim_ages_chart():
    db_path = os.path.join(os.path.dirname(__file__), "beaconport_db.json")
    with open(db_path, "r") as f:
        data = json.load(f)
    ages = []
    for case in data["cases"].values():
        for victim in case.get("victim_details", []):
            age = victim.get("Victim Age at Time of Offence")
            if age is not None:
                ages.append(age)
    plt.figure(figsize=(8, 4))
    plt.hist(ages, bins=range(min(ages), max(ages)+2), edgecolor='black')
    plt.title("Victim Ages Across All Cases")
    plt.xlabel("Age")
    plt.ylabel("Number of Victims")
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == "__main__":
    app.run(debug=True)