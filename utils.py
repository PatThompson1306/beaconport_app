# utils.py - Utility functions and decorators

import functools
import os
import sys
import subprocess
from flask import send_file
from chart_service import ChartService
from config import EXCEL_FILE


def safe_chart_route(chart_function):
    """Decorator to handle errors in chart generation routes"""
    @functools.wraps(chart_function)
    def wrapper(*args, **kwargs):
        try:
            return chart_function(*args, **kwargs)
        except Exception as e:
            print(f"Chart generation error in {chart_function.__name__}: {e}")
            error_chart = ChartService.create_error_chart(str(e))
            return send_file(error_chart, mimetype='image/png')
    return wrapper


def validate_excel_file(filename: str = EXCEL_FILE) -> tuple[bool, str]:
    """Validate that the Excel file exists and is readable"""
    if not os.path.exists(filename):
        return False, f"Excel file '{filename}' not found in current directory"
    
    if not filename.lower().endswith(('.xlsx', '.xls')):
        return False, f"File '{filename}' is not a valid Excel file"
    
    try:
        # Check if file is readable
        with open(filename, 'rb') as f:
            f.read(1)
        return True, "File validation successful"
    except PermissionError:
        return False, f"Permission denied reading '{filename}'"
    except Exception as e:
        return False, f"Error validating file: {str(e)}"


def run_excel_import(excel_file: str = EXCEL_FILE) -> tuple[bool, str]:
    """Run the Excel import script with proper error handling"""
    # Validate file first
    is_valid, validation_msg = validate_excel_file(excel_file)
    if not is_valid:
        return False, validation_msg
    
    try:
        # Check if import script exists
        import_script = "import_excel.py"
        if not os.path.exists(import_script):
            return False, f"Import script '{import_script}' not found"
        
        # Run the import
        result = subprocess.run(
            [sys.executable, import_script, excel_file],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            return True, "Excel data successfully imported!"
        else:
            error_msg = result.stderr if result.stderr else "Unknown error occurred"
            return False, f"Import failed: {error_msg}"
            
    except subprocess.TimeoutExpired:
        return False, "Import timed out after 5 minutes"
    except Exception as e:
        return False, f"Error running import: {str(e)}"


def format_flash_message(success: bool, message: str) -> str:
    """Format flash messages with appropriate icons"""
    if success:
        return f"✅ {message}"
    else:
        return f"❌ {message}"


def safe_int_conversion(value, default: int = 0) -> int:
    """Safely convert value to integer with fallback"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def clean_string(value) -> str:
    """Clean and validate string values"""
    if value is None:
        return ""
    return str(value).strip()


def get_app_stats(db_service) -> dict:
    """Get application statistics for display"""
    try:
        case_count = db_service.get_case_count()
        victim_count = len(db_service.get_all_victims())
        
        return {
            'case_count': case_count,
            'victim_count': victim_count,
            'has_data': case_count > 0
        }
    except Exception as e:
        print(f"Error getting app stats: {e}")
        return {
            'case_count': 0,
            'victim_count': 0,
            'has_data': False
        }