#!/usr/bin/env python3
"""
Fix Database - Create missing company_changes table
"""

import sqlite3
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database():
    """
    Create the missing company_changes table
    """
    try:
        # Connect to database
        conn = sqlite3.connect('mca_insights.db')
        cursor = conn.cursor()
        
        # Check if company_changes table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='company_changes'
        """)
        
        if cursor.fetchone() is None:
            logger.info("Creating company_changes table...")
            
            # Create company_changes table
            cursor.execute('''
                CREATE TABLE company_changes (
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
            
            # Insert some sample data
            sample_changes = [
                ('U24299PN2019PTC181506', 'New Incorporation', 'All', '', 'ANURIUSWELL PHARMACEUTICALS', '2025-10-19', 'ANURIUSWELL PHARMACEUTICALS', 'Maharashtra', 'Active'),
                ('U24299PN2019PTC187808', 'Field Update', 'Status', 'Active', 'Strike Off', '2025-10-19', 'SKYI FKUR BIOPOLYMERS', 'Maharashtra', 'Strike Off'),
                ('U24299PN2020PTC192446', 'Field Update', 'Authorized_Capital', '100000', '500000', '2025-10-19', 'CHEMENGG RESEARCH', 'Maharashtra', 'Active')
            ]
            
            cursor.executemany('''
                INSERT INTO company_changes 
                (CIN, Change_Type, Field_Changed, Old_Value, New_Value, Date, Company_Name, State, Status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', sample_changes)
            
            logger.info("Sample data inserted into company_changes table")
            
        else:
            logger.info("company_changes table already exists")
        
        # Check companies table
        cursor.execute("SELECT COUNT(*) FROM companies")
        count = cursor.fetchone()[0]
        logger.info(f"Companies table has {count} records")
        
        conn.commit()
        conn.close()
        
        logger.info("Database fix completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing database: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing MCA Insights Database...")
    success = fix_database()
    
    if success:
        print("✅ Database fixed successfully!")
        print("🔄 Please refresh your dashboard browser page")
    else:
        print("❌ Database fix failed")
