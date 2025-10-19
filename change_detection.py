import pandas as pd
import numpy as np
import sqlite3
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ChangeDetector:
    """
    Class to detect and log company-level changes across daily snapshots
    """
    
    def __init__(self, db_path='mca_insights.db'):
        self.db_path = db_path
        self.change_logs = []
        
    def load_snapshot(self, snapshot_file):
        """
        Load a daily snapshot CSV file
        """
        try:
            df = pd.read_csv(snapshot_file)
            df['snapshot_date'] = pd.to_datetime(df['snapshot_date'])
            logger.info(f"Loaded snapshot with {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"Error loading snapshot {snapshot_file}: {str(e)}")
            return None
    
    def detect_changes(self, old_df, new_df, change_date):
        """
        Detect changes between two snapshots
        """
        changes = []
        
        # Get CINs from both snapshots
        old_cins = set(old_df['CIN']) if old_df is not None else set()
        new_cins = set(new_df['CIN'])
        
        # Detect new incorporations
        new_incorporations = new_cins - old_cins
        for cin in new_incorporations:
            company_data = new_df[new_df['CIN'] == cin].iloc[0]
            changes.append({
                'CIN': cin,
                'Change_Type': 'New Incorporation',
                'Field_Changed': 'All',
                'Old_Value': '',
                'New_Value': company_data['Company_Name'],
                'Date': change_date,
                'Company_Name': company_data['Company_Name'],
                'State': company_data['State'],
                'Status': company_data['Status']
            })
        
        # Detect deregistrations/strike offs
        deregistrations = old_cins - new_cins
        for cin in deregistrations:
            company_data = old_df[old_df['CIN'] == cin].iloc[0]
            changes.append({
                'CIN': cin,
                'Change_Type': 'Deregistration',
                'Field_Changed': 'Status',
                'Old_Value': company_data['Status'],
                'New_Value': 'Deregistered',
                'Date': change_date,
                'Company_Name': company_data['Company_Name'],
                'State': company_data['State'],
                'Status': 'Deregistered'
            })
        
        # Detect field-level changes for existing companies
        common_cins = old_cins & new_cins
        for cin in common_cins:
            old_company = old_df[old_df['CIN'] == cin].iloc[0]
            new_company = new_df[new_df['CIN'] == cin].iloc[0]
            
            # Check for changes in key fields
            fields_to_check = [
                'Status', 'Authorized_Capital', 'Paidup_Capital', 
                'Company_Name', 'Address', 'Industry_Classification'
            ]
            
            for field in fields_to_check:
                if field in old_company and field in new_company:
                    old_value = str(old_company[field]) if pd.notna(old_company[field]) else ''
                    new_value = str(new_company[field]) if pd.notna(new_company[field]) else ''
                    
                    if old_value != new_value and old_value != '' and new_value != '':
                        changes.append({
                            'CIN': cin,
                            'Change_Type': 'Field Update',
                            'Field_Changed': field,
                            'Old_Value': old_value,
                            'New_Value': new_value,
                            'Date': change_date,
                            'Company_Name': new_company['Company_Name'],
                            'State': new_company['State'],
                            'Status': new_company['Status']
                        })
        
        return changes
    
    def process_daily_changes(self, snapshot_files):
        """
        Process changes across multiple daily snapshots
        """
        logger.info("Starting daily change detection process")
        
        all_changes = []
        previous_df = None
        
        for i, snapshot_file in enumerate(snapshot_files):
            logger.info(f"Processing snapshot {i+1}: {snapshot_file}")
            current_df = self.load_snapshot(snapshot_file)
            
            if current_df is not None:
                if previous_df is not None:
                    # Detect changes between previous and current snapshot
                    change_date = current_df['snapshot_date'].iloc[0]
                    changes = self.detect_changes(previous_df, current_df, change_date)
                    all_changes.extend(changes)
                    logger.info(f"Detected {len(changes)} changes in snapshot {i+1}")
                
                previous_df = current_df
        
        self.change_logs = all_changes
        logger.info(f"Total changes detected: {len(all_changes)}")
        
        return all_changes
    
    def save_change_logs(self, output_format='csv'):
        """
        Save change logs to file
        """
        if not self.change_logs:
            logger.warning("No changes to save")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_format == 'csv':
            df = pd.DataFrame(self.change_logs)
            filename = f'change_logs_{timestamp}.csv'
            df.to_csv(filename, index=False)
            logger.info(f"Change logs saved to {filename}")
            
        elif output_format == 'json':
            filename = f'change_logs_{timestamp}.json'
            with open(filename, 'w') as f:
                json.dump(self.change_logs, f, indent=2, default=str)
            logger.info(f"Change logs saved to {filename}")
    
    def get_change_summary(self):
        """
        Get summary of detected changes
        """
        if not self.change_logs:
            return None
        
        df = pd.DataFrame(self.change_logs)
        
        summary = {
            'total_changes': len(df),
            'change_types': df['Change_Type'].value_counts().to_dict(),
            'fields_changed': df['Field_Changed'].value_counts().to_dict(),
            'states_affected': df['State'].value_counts().to_dict(),
            'date_range': {
                'earliest': df['Date'].min(),
                'latest': df['Date'].max()
            }
        }
        
        return summary
    
    def update_master_database(self):
        """
        Update the master database with latest company information
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Create changes table if it doesn't exist
            conn.execute('''
                CREATE TABLE IF NOT EXISTS company_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    CIN TEXT,
                    Change_Type TEXT,
                    Field_Changed TEXT,
                    Old_Value TEXT,
                    New_Value TEXT,
                    Date TEXT,
                    Company_Name TEXT,
                    State TEXT,
                    Status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert change logs
            if self.change_logs:
                df = pd.DataFrame(self.change_logs)
                df.to_sql('company_changes', conn, if_exists='append', index=False)
                logger.info(f"Inserted {len(self.change_logs)} change records into database")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating master database: {str(e)}")

if __name__ == "__main__":
    # Initialize change detector
    detector = ChangeDetector()
    
    # Process daily changes from snapshot files
    snapshot_files = ['snapshot_day1.csv', 'snapshot_day2.csv', 'snapshot_day3.csv']
    changes = detector.process_daily_changes(snapshot_files)
    
    if changes:
        # Save change logs
        detector.save_change_logs('csv')
        detector.save_change_logs('json')
        
        # Update database
        detector.update_master_database()
        
        # Print summary
        summary = detector.get_change_summary()
        print("\n=== Change Detection Summary ===")
        print(f"Total Changes: {summary['total_changes']}")
        print(f"Change Types: {summary['change_types']}")
        print(f"Fields Changed: {summary['fields_changed']}")
        print(f"States Affected: {summary['states_affected']}")
        print(f"Date Range: {summary['date_range']['earliest']} to {summary['date_range']['latest']}")
    else:
        print("No changes detected")
