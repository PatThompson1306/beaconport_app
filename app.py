# app.py - Beaconport Data Application

import time
from flask import Flask, render_template, request, redirect, send_file, url_for, flash

# Import our services and utilities
from database_service import DatabaseService
from chart_service import ChartService
from utils import safe_chart_route, run_excel_import, format_flash_message, get_app_stats

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "beaconport-secret"  # In production, use environment variable

# Initialize services
db_service = DatabaseService()


@app.route("/", methods=["GET", "POST"])
def index():
    """Main page with data import functionality"""
    if request.method == "POST":
        success, message = run_excel_import()
        flash(format_flash_message(success, message))
        return redirect(url_for("index"))
    
    # Get application statistics
    stats = get_app_stats(db_service)
    
    return render_template("index.html", **stats)


@app.route("/victim_data")
def victim_ages():
    """Page displaying victim analysis charts"""
    return render_template("victim_data.html", now=time.time())


@app.route("/digital_vs_finalisation")
def digital_vs_finalisation():
    """Page displaying digital opportunities analysis"""
    return render_template("digital_vs_finalisation.html", now=time.time())


# Chart generation routes with error handling
@app.route("/victim_ages_chart.png")
@safe_chart_route
def victim_ages_chart():
    """Generate victim ages histogram"""
    ages = db_service.get_victim_ages()
    chart_buffer = ChartService.create_histogram(
        ages,
        "Distribution of Victim Ages Across All Cases",
        "Age (Years)",
        "Number of Victims"
    )
    return send_file(chart_buffer, mimetype='image/png')


@app.route("/victim_ethnicity_chart.png")
@safe_chart_route
def victim_ethnicity_chart():
    """Generate victim ethnicity bar chart"""
    ethnicities = db_service.get_victim_ethnicities()
    chart_buffer = ChartService.create_bar_chart(
        ethnicities,
        "Victim Ethnicity Distribution",
        "Ethnicity",
        "Number of Victims"
    )
    return send_file(chart_buffer, mimetype='image/png')


@app.route("/victim_postcode_map.png")
@safe_chart_route
def victim_postcode_map():
    """Generate geographic visualization of victim postcodes"""
    postcodes = db_service.get_victim_postcodes()
    chart_buffer = ChartService.create_postcode_map(postcodes)
    return send_file(chart_buffer, mimetype='image/png')


@app.route("/digital_vs_finalisation_chart.png")
@safe_chart_route
def digital_vs_finalisation_chart():
    """Generate scatter plot of digital opportunities vs crime finalisation"""
    pairs = db_service.get_digital_vs_finalisation_pairs()
    chart_buffer = ChartService.create_scatter_plot(
        pairs,
        "Digital Opportunities vs Crime Finalisation Code",
        "Digital Opportunities Present",
        "Crime Finalisation Code"
    )
    return send_file(chart_buffer, mimetype='image/png')


# Additional analysis routes
@app.route("/api/stats")
def api_stats():
    """API endpoint for application statistics"""
    stats = get_app_stats(db_service)
    return stats


@app.route("/health")
def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}


# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template("error.html", 
                         error_code=404, 
                         error_message="Page not found"), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template("error.html", 
                         error_code=500, 
                         error_message="Internal server error"), 500


if __name__ == "__main__":
    print("Starting Beaconport Data Application...")
    print(f"Database path: {db_service.db_path}")
    
    # Check initial stats
    stats = get_app_stats(db_service)
    print(f"Initial stats: {stats['case_count']} cases, {stats['victim_count']} victims")
    
    app.run(debug=True, host='127.0.0.1', port=5000)