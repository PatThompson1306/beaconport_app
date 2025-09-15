# Importing necessary libraries
from collections import Counter
import io 
from flask import Flask, json, render_template, request, redirect, send_file, url_for, flash 
from tinydb import TinyDB 
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt 
import subprocess 
import sys
import os 

# Initialise the Flask app
app = Flask(__name__)
app.secret_key = "beaconport-secret"

# Helper function: Get the count of unique cases in the database - to be displayed on the main app page
def get_case_count():
    try:
        db = TinyDB("beaconport_db.json")
        cases_table = db.table("cases")
        all_cases = cases_table.all()
        unique_refs = set()
        for case in all_cases:
            if 'main' in case:
                main_data = case['main']
                for key, value in main_data.items():
                    if value and str(value).strip():
                        unique_refs.add(str(value).strip())
                        break
                for value in main_data.values():
                    if value and str(value).strip():
                        unique_refs.add(str(value).strip())
                        break
        return len(unique_refs)
    except Exception as e:
        print(f"Error in get_case_count: {e}")
        return 0


# Helper function: Victim ages across all cases for charting
def get_victim_ages():
    db_path = os.path.join(os.path.dirname(__file__), "beaconport_db.json")
    with open(db_path, "r") as f:
        data = json.load(f)
    ages = []
    for case in data["cases"].values():
        for victim in case.get("victim_details", []):
            age = victim.get("Victim Age at Time of Offence")
            if age is not None:
                ages.append(age)
    return ages


# Helper function: Victim Ethnicity Distribution
def get_victim_ethnicity():
    db_path = os.path.join(os.path.dirname(__file__), "beaconport_db.json")
    with open(db_path, "r") as f:
        data = json.load(f)
    ethnicities = []
    for case in data["cases"].values():
        for victim in case.get("victim_details", []):
            ethnicity = victim.get("Victim Ethnicity")
            if ethnicity is not None:
                ethnicities.append(ethnicity)
    return ethnicities


# Helper function: Digital Opportunities Present vs. Crime Finalisation Code pairs
def get_digital_vs_finalisation():
    db_path = os.path.join(os.path.dirname(__file__), "beaconport_db.json")
    with open(db_path, "r") as f:
        data = json.load(f)
    pairs = []
    for case in data["cases"].values():
        # Get from case_data (Digital Opportunities Present)
        digital = None
        case_data_list = case.get("case_data", [])
        if case_data_list:
            digital = case_data_list[0].get("Digital Opportunities Present")
        # Get from offence_details (Crime Finalisation Code)
        finalisation = None
        offence_details_list = case.get("offence_details", [])
        if offence_details_list:
            finalisation = offence_details_list[0].get("Crime Finalisation Code")
        # Only add if both values are present
        if digital is not None and finalisation is not None:
            pairs.append((digital, finalisation))
    return pairs


# Route for the main page
@app.route("/", methods=["GET", "POST"])
# Display the main page with update as to loading data and the number of unique cases
def index():
    case_count = get_case_count()
    if request.method == "POST":
        try:
            excel_file = "Beaconport Capture.xlsx"
            if not os.path.exists(excel_file):
                flash(f"Error: {excel_file} not found in the current directory")
                return redirect(url_for("index"))
            result = subprocess.run([sys.executable, "import_excel.py", excel_file], capture_output=True, text=True)
            if result.returncode == 0:
                flash("Excel data successfully imported! ✅")
            else:
                flash(f"Error running import: {result.stderr}")
        except Exception as e:
            flash(f"Error: {e}")
        return redirect(url_for("index"))
    return render_template("index.html", case_count=case_count)


# Route to page which will display victim ages information
@app.route("/victim_data")
def victim_ages():
    return render_template("victim_data.html")
# Route to serve the victim ages visualisation along with the relevant charting code
@app.route("/victim_ages_chart.png")
def victim_ages_chart():
    ages = get_victim_ages()
    buf = io.BytesIO()
    plt.figure(figsize=(8, 4))
    if ages:
        counts, bins, patches = plt.hist(ages, bins=range(min(ages), max(ages)+2), edgecolor='black')
        plt.title("Victim Ages Across All Cases")
        plt.xlabel("Age")
        plt.ylabel("Number of Victims")
        # Set y-axis to whole numbers only
        from matplotlib.ticker import MaxNLocator
        ax = plt.gca()
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        # Center age numbers on columns
        bin_centers = [bin_left + 0.5 for bin_left in bins[:-1]]
        ax.set_xticks(bin_centers)
        ax.set_xticklabels([str(int(center)) for center in bin_centers])
        # Add count labels to each column
        for count, bin_left, patch in zip(counts, bins, patches):
            if count > 0:
                plt.text(bin_left + 0.5, count, str(int(count)), ha='center', va='bottom', fontsize=9)
    else:
        plt.text(0.5, 0.5, 'No data available', ha='center', va='center')
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return send_file(buf, mimetype='image/png')
# Route to serve the victim ethnicity visualisation along with the relevant charting code
@app.route("/victim_ethnicity_chart.png")
def victim_ethnicity_chart():
    ethnicities = get_victim_ethnicity()
    buf = io.BytesIO()
    plt.figure(figsize=(8, 4))
    if ethnicities:
        counts = Counter(ethnicities)
        plt.bar(counts.keys(), counts.values(), color='blue')
        plt.title("Victim Ethnicity Distribution")
        plt.xlabel("Ethnicity")
        plt.ylabel("Number of Victims")
        plt.xticks(rotation=45)
    else:
        plt.text(0.5, 0.5, 'No data available', ha='center', va='center')
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


# Route to page which will display digital opportunities information
@app.route("/digital_vs_finalisation")
def digital_vs_finalisation():
    return render_template("digital_vs_finalisation.html")
# Route to serve the digital vs finalisation visualisation along with the relevant charting code
@app.route("/digital_vs_finalisation_chart.png")
def digital_vs_finalisation_chart():
    pairs = get_digital_vs_finalisation()
    x = [p[0] for p in pairs]
    y = [p[1] for p in pairs]
    buf = io.BytesIO()
    plt.figure(figsize=(8, 4))
    if x and y:
        plt.scatter(x, y, color='blue')
        plt.title("Digital Opportunities vs Crime Finalisation Code")
        plt.xlabel("Digital Opportunities Present")
        plt.ylabel("Crime Finalisation Code")
        plt.grid(True)
    else:
        plt.text(0.5, 0.5, 'No data available', ha='center', va='center')
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


# Run the app
if __name__ == "__main__":
    app.run(debug=True)