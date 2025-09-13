# import necessary libraries
from flask import Flask, render_template, request, redirect, url_for, flash
import subprocess
import sys
import os

# initialise Flask app
app = Flask(__name__)
app.secret_key = "beaconport-secret"

# define routes
@app.route("/", methods=["GET", "POST"])
# main route to handle form submission and display messages
def index():
    if request.method == "POST":
        try:
            # Run the import_excel.py script
            excel_file = os.path.join(os.path.dirname(__file__), "Beaconport Capture.xlsx")  # Default filename
            import_script = os.path.join(os.path.dirname(__file__), "import_excel.py")
            
            # Check if file exists
            if not os.path.exists(excel_file):
                flash(f"Error: {excel_file} not found in the application directory")
                return redirect(url_for("index"))
            if not os.path.exists(import_script):
                flash(f"Error: import_excel.py not found in the application directory")
                return redirect(url_for("index"))
            
            # Run the import script
            result = subprocess.run([sys.executable, import_script, excel_file], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                flash("Excel data successfully imported! ✅")
            else:
                flash(f"Error running import: {result.stderr}")
                
        except Exception as e:
            flash(f"Error: {e}")
        
        return redirect(url_for("index"))
    
    return render_template("index.html")

# run the app
if __name__ == "__main__":
    app.run(debug=True)