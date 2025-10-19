import pandas as pd
import numpy as np
import sqlite3
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MCADataIntegrator:
    """
    Class to handle data integration and consolidation of MCA state-wise CSV files
    """
    
    def __init__(self, data_dir="."):
        self.data_dir = data_dir
        self.state_files = {
            'maharashtra': 'maharashtra.csv',
            'gujarat': 'gujarat.csv', 
            'delhi': 'delhi.csv',
            'tamil_nadu': 'tamil_nadu.csv',
            'karnataka': 'karnataka.csv'
        }
        self.master_data = None
        self.db_path = 'mca_insights.db'
        
    def load_state_data(self, state_name, file_path):
        """
        Load and clean data from a single state CSV file
        """
        try:
            logger.info(f"Loading data for {state_name}")
            df = pd.read_csv(file_path)
            
            # Standardize column names
            df.columns = df.columns.str.strip()
            
            # Add state information
            df['State'] = state_name.title()
            df['State_Code'] = state_name.lower()
            
            # Clean and standardize data types
            df = self._clean_dataframe(df)
            
            logger.info(f"Loaded {len(df)} records for {state_name}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading {state_name} data: {str(e)}")
            return None
    
    def _clean_dataframe(self, df):
        """
        Clean and standardize dataframe columns
        """
        # Handle missing values
        df = df.fillna('')
        
        # Standardize numeric columns
        numeric_columns = ['AuthorizedCapital', 'PaidupCapital']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Standardize date columns
        date_columns = ['CompanyRegistrationdate_date']
        for col in date_columns:
            if col in df.columns:
                df['Registration_Date'] = pd.to_datetime(df[col], errors='coerce')
        
        # Clean text columns
        text_columns = ['CompanyName', 'CompanyCategory', 'CompanyClass', 'CompanyStatus']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.upper()
        
        # Standardize Status column name
        if 'CompanyStatus' in df.columns:
            df['Status'] = df['CompanyStatus']
        
        return df
    
    def consolidate_data(self):
        """
        Consolidate all state-wise data into a master dataset
        """
        logger.info("Starting data consolidation process")
        consolidated_data = []
        
        for state_name, file_path in self.state_files.items():
            full_path = os.path.join(self.data_dir, file_path)
            if os.path.exists(full_path):
                state_data = self.load_state_data(state_name, full_path)
                if state_data is not None:
                    consolidated_data.append(state_data)
            else:
                logger.warning(f"File not found: {full_path}")
        
        if consolidated_data:
            self.master_data = pd.concat(consolidated_data, ignore_index=True)
            
            # Remove duplicates based on CIN
            initial_count = len(self.master_data)
            self.master_data = self.master_data.drop_duplicates(subset=['CIN'], keep='first')
            final_count = len(self.master_data)
            
            logger.info(f"Consolidated data: {initial_count} -> {final_count} records after deduplication")
            
            # Save consolidated data
            self.master_data.to_csv('consolidated_mca_data.csv', index=False)
            logger.info("Consolidated data saved to consolidated_mca_data.csv")
            
            return self.master_data
        else:
            logger.error("No data could be loaded")
            return None
    
    def create_database(self):
        """
        Create SQLite database and store consolidated data
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            if self.master_data is not None:
                self.master_data.to_sql('companies', conn, if_exists='replace', index=False)
                logger.info(f"Database created with {len(self.master_data)} records")
            
            # Create indexes for better query performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cin ON companies(CIN)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_state ON companies(State)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON companies(Status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_registration_date ON companies(Registration_Date)")
            
            conn.close()
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating database: {str(e)}")
    
    def get_data_summary(self):
        """
        Get summary statistics of the consolidated data
        """
        if self.master_data is None:
            return None
            
        summary = {
            'total_companies': len(self.master_data),
            'states': self.master_data['State'].value_counts().to_dict(),
            'status_distribution': self.master_data['Status'].value_counts().to_dict(),
            'date_range': {
                'earliest': self.master_data['Registration_Date'].min(),
                'latest': self.master_data['Registration_Date'].max()
            }
        }
        
        return summary

if __name__ == "__main__":
    # Initialize data integrator
    integrator = MCADataIntegrator()
    
    # Consolidate data
    master_data = integrator.consolidate_data()
    
    if master_data is not None:
        # Create database
        integrator.create_database()
        
        # Print summary
        summary = integrator.get_data_summary()
        print("\n=== Data Consolidation Summary ===")
        print(f"Total Companies: {summary['total_companies']}")
        print(f"States: {summary['states']}")
        print(f"Status Distribution: {summary['status_distribution']}")
        print(f"Date Range: {summary['date_range']['earliest']} to {summary['date_range']['latest']}")
    else:
        print("Data consolidation failed")
