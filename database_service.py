# database_service.py - Database service for handling data operations

import json
import os
from typing import List, Dict, Any
from tinydb import TinyDB
from config import DB_PATH, Fields


class DatabaseService:
    def get_digital_vs_finalisation_pairs(self) -> list:
        """Return a list of (digital_opportunities, crime_finalisation) pairs for all cases."""
        data = self.get_data()
        pairs = []
        for case in data.get("cases", {}).values():
            digital = None
            case_data_list = case.get("case_data", [])
            if case_data_list and isinstance(case_data_list[0], dict):
                digital = case_data_list[0].get(Fields.DIGITAL_OPPORTUNITIES)
            finalisation = None
            offence_details_list = case.get("offence_details", [])
            if offence_details_list and isinstance(offence_details_list[0], dict):
                finalisation = offence_details_list[0].get(Fields.CRIME_FINALISATION)
            # Only include pairs where both values exist and are not None
            if digital is not None and finalisation is not None:
                pairs.append((digital, finalisation))
        return pairs
    """Service class for handling database operations"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
    
    def get_data(self) -> Dict[str, Any]:
        """Load data from JSON database file"""
        try:
            if not os.path.exists(self.db_path):
                return {"cases": {}}
            with open(self.db_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading database: {e}")
            return {"cases": {}}
    
    def get_case_count(self) -> int:
        """Get count of unique cases in database"""
        try:
            db = TinyDB(self.db_path)
            cases_table = db.table("cases")
            all_cases = cases_table.all()
            unique_refs = set()
            
            for case in all_cases:
                if 'main' in case:
                    main_data = case['main']
                    # Get first non-empty value as unique identifier
                    for value in main_data.values():
                        if value and str(value).strip():
                            unique_refs.add(str(value).strip())
                            break
            
            db.close()
            return len(unique_refs)
        except Exception as e:
            print(f"Error getting case count: {e}")
            return 0
    
    def get_all_victims(self) -> List[Dict[str, Any]]:
        """Get all victim records from all cases"""
        data = self.get_data()
        victims = []
        for case in data.get("cases", {}).values():
            victims.extend(case.get("victim_details", []))
        return victims
    
    def get_field_values(self, field_name: str, data_source: str = "victim_details") -> List[Any]:
        """Extract values for a specific field from specified data source"""
        data = self.get_data()
        values = []
        
        for case in data.get("cases", {}).values():
            source_data = case.get(data_source, [])
            
            # Handle both list and single item cases
            if not isinstance(source_data, list):
                source_data = [source_data] if source_data else []
            
            for item in source_data:
                if isinstance(item, dict):
                    value = item.get(field_name)
                    if value is not None and str(value).strip():
                        values.append(value)
        
        return values
    
    def get_victim_ages(self) -> List[int]:
        """Get all victim ages, filtered and converted to integers"""
        ages = self.get_field_values(Fields.VICTIM_AGE)
        clean_ages = []
        
        for age in ages:
            try:
                age_int = int(age)
                if 0 <= age_int <= 120:  # Reasonable age range
                    clean_ages.append(age_int)
            except (ValueError, TypeError):
                continue
                
        return clean_ages
    
    def get_victim_ethnicities(self) -> List[str]:
        """Get all victim ethnicities, cleaned"""
        ethnicities = self.get_field_values(Fields.VICTIM_ETHNICITY)
        return [str(e).strip() for e in ethnicities if str(e).strip()]
    
    def get_victim_postcodes(self) -> List[str]:
        """Get all victim postcodes, cleaned"""
        postcodes = self.get_field_values(Fields.VICTIM_POSTCODE)
        clean_postcodes = []
        
        for pc in postcodes:
            pc_str = str(pc).strip().upper()
            if pc_str and len(pc_str) >= 4:  # Basic postcode validation
                clean_postcodes.append(pc_str)
        
        return clean_postcodes
    
    def get_finalisation_vs_digital_correlation(self) -> Dict[str, Dict[str, int]]:
        """
        Compute the co-occurrence counts between CRIME_FINALISATION and DIGITAL_OPPORTUNITIES.
        Includes all instances, even if one of the values is missing (None or empty).
        Returns a nested dictionary: {finalisation: {digital_opportunity: count, ...}, ...}
        """
        data = self.get_data()
        correlation = {}

        for case in data.get("cases", {}).values():
            # Get digital opportunities data
            digital = None
            case_data_list = case.get("case_data", [])
            if case_data_list and isinstance(case_data_list[0], dict):
                digital = case_data_list[0].get(Fields.DIGITAL_OPPORTUNITIES)

            # Get crime finalisation data  
            finalisation = None
            offence_details_list = case.get("offence_details", [])
            if offence_details_list and isinstance(offence_details_list[0], dict):
                finalisation = offence_details_list[0].get(Fields.CRIME_FINALISATION)

            # Use string representation, even for missing values
            finalisation_str = str(finalisation).strip() if finalisation is not None else ""
            digital_str = str(digital).strip() if digital is not None else ""

            if finalisation_str not in correlation:
                correlation[finalisation_str] = {}
            if digital_str not in correlation[finalisation_str]:
                correlation[finalisation_str][digital_str] = 0
            correlation[finalisation_str][digital_str] += 1

        return correlation
        
        return pairs