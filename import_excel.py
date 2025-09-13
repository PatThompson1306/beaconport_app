#!/usr/bin/env python3
"""
Dynamic Excel -> TinyDB importer that preserves all sheet headers.

Usage:
    python import_excel.py [path/to/Beaconport Capture.xlsx]

Requirements:
    pip install pandas tinydb openpyxl
"""
import sys
import os
import json
import pandas as pd
import numpy as np
from tinydb import TinyDB

def clean_value(val):
    """Return a JSON-serializable Python value for a pandas/numpy value."""
    # None
    if val is None:
        return None

    # pandas NA (handles numpy.nan etc.)
    try:
        if pd.isna(val):
            return None
    except Exception:
        pass

    # pandas Timestamp -> ISO string (date or datetime)
    if hasattr(val, "to_pydatetime"):
        try:
            dt = val.to_pydatetime()
            # If time component is 00:00:00, return just the date string
            if dt.time() == pd.Timestamp(0).to_pydatetime().time():
                return dt.date().isoformat()
            return dt.isoformat()
        except Exception:
            pass

    # numpy / pandas scalar -> Python native
    if hasattr(val, "item"):
        try:
            return val.item()
        except Exception:
            pass

    # numpy primitive types
    if isinstance(val, (np.integer, np.floating, np.bool_)):
        return val.item()

    # common Python primitives
    if isinstance(val, (str, int, float, bool)):
        return val

    # fallback to str
    return str(val)

def find_ref_col(df):
    """
    Try to find the appropriate 'case reference' column in the dataframe.
    Priority:
      1) column containing both 'beaconport' and 'ref'
      2) column containing 'ref'
      3) fallback to first column
    """
    cols = list(df.columns)
    # Normalize and search
    for col in cols:
        key = str(col).strip().lower()
        if "beaconport" in key and "ref" in key:
            return col
    for col in cols:
        key = str(col).strip().lower()
        if "ref" in key:
            return col
    # fallback
    return cols[0] if cols else None

def clean_row(row):
    """Clean all values in a row dict and strip header names."""
    return {str(k).strip(): clean_value(v) for k, v in row.items()}

def normalize_sheet_key(sheet_name):
    """Create a safe key name from sheet name to store in the record."""
    return sheet_name.strip().lower().replace(" ", "_")

def import_excel_to_db(filepath, db_path="beaconport_db.json", truncate=True):
    """
    Read an Excel workbook and import all sheets into TinyDB, joined by case ref.

    Result schema for each case (example):
    {
      "main": { ... main-sheet-row... },
      "offence_details": [ { ... }, { ... } ],
      "victim_details": [ { ... } ],
      "case_data": [ { ... } ],
      ...
    }
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Excel file not found: {filepath}")

    # open workbook
    xls = pd.ExcelFile(filepath)

    # Read every sheet into a DataFrame
    sheets = {}
    for sheet_name in xls.sheet_names:
        # read with dtype=object to avoid unneeded conversions
        df = pd.read_excel(filepath, sheet_name=sheet_name, dtype=object)
        sheets[sheet_name] = df

    # Initialize TinyDB
    db = TinyDB(db_path)
    table = db.table("cases")
    if truncate:
        table.truncate()

    # Build lookups per sheet keyed by case ref
    lookups = {}
    for sheet_name, df in sheets.items():
        ref_col = find_ref_col(df)
        records = df.to_dict(orient="records")
        lookup = {}
        for r in records:
            ref_val = clean_value(r.get(ref_col))
            if ref_val is None:
                # skip rows without a reference
                continue
            lookup.setdefault(ref_val, []).append(clean_row(r))
        lookups[sheet_name] = {"ref_col": ref_col, "lookup": lookup, "original_count": len(records)}

    # Determine main sheet: prefer "Beaconport Main" if present, else use first sheet
    main_sheet_name = "Beaconport Main" if "Beaconport Main" in sheets else list(sheets.keys())[0]
    main_ref_col = find_ref_col(sheets[main_sheet_name])

    inserted = 0
    # Iterate main sheet rows and assemble combined records
    for r in sheets[main_sheet_name].to_dict(orient="records"):
        ref = clean_value(r.get(main_ref_col))
        if ref is None:
            continue
        combined = {}
        combined["main"] = clean_row(r)

        # attach all other sheet matches
        for sheet_name, info in lookups.items():
            if sheet_name == main_sheet_name:
                continue
            matched = info["lookup"].get(ref, [])
            combined_key = normalize_sheet_key(sheet_name)
            combined[combined_key] = matched

        table.insert(combined)
        inserted += 1

    # Summary
    summary = {
        "file": filepath,
        "db": db_path,
        "sheets_read": {name: {"ref_col": info["ref_col"], "rows": info["original_count"]} for name, info in lookups.items()},
        "cases_inserted": inserted
    }
    print(json.dumps(summary, indent=2))
    return summary

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "Beaconport Capture.xlsx"
    import_excel_to_db(path)
