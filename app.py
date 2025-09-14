import io # in-memory file handling
from flask import Flask, json, render_template, request, redirect, send_file, url_for, flash # flask as the core web framework
from tinydb import TinyDB # tinydb for simple JSON database
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for web server
import matplotlib.pyplot as plt # matplotlib for charting
import subprocess # to run import script
import sys # to get the python executable
import os # for file path handling

# Initialise the Flask app
app = Flask(__name__)
app.secret_key = "beaconport-secret"

# Function to get the count of unique cases in the database
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


# Function to get victim ages from the database (consolidated version)
def get_victim_ages():
    """Extract victim ages from the database"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), "beaconport_db.json")
        
        if not os.path.exists(db_path):
            return []
            
        with open(db_path, "r") as f:
            data = json.load(f)
            
        ages = []
        for case in data.get("cases", {}).values():
            for victim in case.get("victim_details", []):
                age = victim.get("Victim Age at Time of Offence")
                if age is not None:
                    try:
                        ages.append(int(age))  # Ensure it's an integer
                    except (ValueError, TypeError):
                        continue  # Skip invalid age values
        
        return ages
    except Exception:
        return []


# Route for the main page
@app.route("/", methods=["GET", "POST"])
def index():
    """Main page to display case count and import form"""
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


# Route to page which will display victim ages chart
@app.route("/victim_ages")
def victim_ages():
    """Display the victim ages chart page"""
    return render_template("victim_ages.html")


# Route to serve the victim ages chart image
@app.route("/victim_ages_chart.png")
def victim_ages_chart():
    """Generate and serve the victim ages histogram"""
    ages = get_victim_ages()
    
    # Handle case where no ages are found
    if not ages:
        # Create a simple "No data" chart
        plt.figure(figsize=(8, 4))
        plt.text(0.5, 0.5, 'No victim age data available', 
                horizontalalignment='center', verticalalignment='center',
                transform=plt.gca().transAxes, fontsize=16)
        plt.title("Victim Ages Across All Cases")
        plt.axis('off')
    else:
        plt.figure(figsize=(8, 4))
        plt.hist(ages, bins=range(min(ages), max(ages)+2), edgecolor='black')
        plt.title("Victim Ages Across All Cases")
        plt.xlabel("Age")
        plt.ylabel("Number of Victims")
        plt.grid(True, alpha=0.3)
    
    # Save to buffer and return
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    plt.close()
    buf.seek(0)
    
    return send_file(buf, mimetype='image/png')


if __name__ == "__main__":
    app.run(debug=True)