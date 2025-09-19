# config.py - Configuration and constants for the Beaconport Data App

import os

# Database configuration
DB_PATH = os.path.join(os.path.dirname(__file__), "beaconport_db.json")
EXCEL_FILE = "Beaconport Capture.xlsx"

# Chart configuration
CHART_SIZE = (8, 4)
MAP_SIZE = (10, 6)
CHART_DPI = 150

# Field name constants
class Fields:
    VICTIM_AGE = "Victim Age at Time of Offence"
    VICTIM_ETHNICITY = "Victim Ethnicity" 
    VICTIM_POSTCODE = "Victim Home Postcode at Time of Offence"
    DIGITAL_OPPORTUNITIES = "Digital Opportunities Present"
    CRIME_FINALISATION = "Crime Finalisation Code"

# Chart styling
CHART_STYLE = {
    'title_size': 12,
    'title_weight': 'bold',
    'label_size': 10,
    'tick_size': 8,
    'alpha': 0.7,
    'edge_color': 'black',
    'grid_alpha': 0.3
}

# Colors for different chart types
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72', 
    'accent': '#F18F01',
    'success': '#C73E1D',
    'map_points': '#FF4444',
    'histogram': '#4A90E2'
}

# Geographic settings
GEO_CONFIG = {
    'user_agent': 'beaconport_app',
    'timeout': 10,
    'rate_limit_delay': 0.1,
    'uk_bounds': [-8, 2, 49.5, 59]  # [west, east, south, north]
}