import pandas as pd
from tinydb import TinyDB

# paths
excel_path = "C:\\Users\\UserPC\\Desktop\\my_folder\\Beaconport POC\\beaconport_app\\Beaconport Capture.xlsx"
db = TinyDB("beaconport_db.json")
cases_table = db.table("cases")

# load sheets from core Beaconport workbook
main_df = pd.read_excel(excel_path, sheet_name="Beaconport Main")
offence_df = pd.read_excel(excel_path, sheet_name="Offence Details")
case_df = pd.read_excel(excel_path, sheet_name="Case Data")
victim_df = pd.read_excel(excel_path, sheet_name="Victim Details")
suspect_df = pd.read_excel(excel_path, sheet_name="Suspect Details")

# clear old data before import
cases_table.truncate()

# loop through cases in main sheet
for _, row in main_df.iterrows():
    case_id = row["Unnamed: 1"]

    # case details
    case_data = {
        "case_id": case_id,
        "allocated_to": row.get("Unnamed: 2", ""),
        "force": {
            "code": row.get("Unnamed: 3", ""),
            "reference": row.get("Unnamed: 4", "")
        },
        "notes": row.get("Unnamed: 6", "")
    }

    # match offence
    offence_match = offence_df[offence_df["Unnamed: 1"] == case_id]
    offence_data = {}
    if not offence_match.empty:
        o = offence_match.iloc[0]
        offence_data = {
            "offence_type": o.get("Unnamed: 4", ""),
            "offence_date": str(o.get("Unnamed: 2", "")),
            "reported_date": str(o.get("Unnamed: 3", "")),
            "location": {
                "postcode": o.get("Unnamed: 7", ""),
                "type": o.get("Unnamed: 8", "")
            },
            "court_outcome": o.get("Unnamed: 15", "")
        }

    # match victim
    victim_match = victim_df[victim_df["Unnamed: 1"] == case_id]
    victim_data = {}
    if not victim_match.empty:
        v = victim_match.iloc[0]
        victim_data = {
            "first_name": v.get("Unnamed: 2", ""),
            "last_name": v.get("Unnamed: 4", ""),
            "dob": str(v.get("Unnamed: 5", "")),
            "ethnicity": v.get("Unnamed: 9", ""),
            "home_postcode": v.get("Unnamed: 12", "")
        }

    # match suspect
    suspect_match = suspect_df[suspect_df["Unnamed: 1"] == case_id]
    suspect_data = {}
    if not suspect_match.empty:
        s = suspect_match.iloc[0]
        suspect_data = {
            "first_name": s.get("Unnamed: 2", ""),
            "last_name": s.get("Unnamed: 4", ""),
            "dob": str(s.get("Unnamed: 5", "")),
            "ethnicity": s.get("Unnamed: 9", ""),
            "home_postcode": s.get("Unnamed: 13", "")
        }

    # final record
    case_record = {
        "case": case_data,
        "offence": offence_data,
        "victim": victim_data,
        "suspect": suspect_data
    }

    cases_table.insert(case_record)

print("✅ Excel data imported into TinyDB")
