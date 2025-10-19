#!/usr/bin/env python3
"""
MCA Insights Engine - Main Orchestration Script

This script orchestrates the entire MCA Insights Engine pipeline:
1. Data Integration
2. Change Detection
3. Web Enrichment
4. AI Features
5. Dashboard and API

Usage:
    python main.py --mode [full|data|changes|enrichment|dashboard|api]
"""

import argparse
import logging
import sys
import os
from datetime import datetime
import pandas as pd

# Import our modules
from data_integration import MCADataIntegrator
from change_detection import ChangeDetector
from web_enrichment import WebEnrichment
from ai_features import AISummaryGenerator, ConversationalQueryEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mca_insights.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MCAInsightsEngine:
    """
    Main orchestration class for MCA Insights Engine
    """
    
    def __init__(self):
        self.data_integrator = MCADataIntegrator()
        self.change_detector = ChangeDetector()
        self.web_enricher = WebEnrichment()
        self.ai_summary_gen = AISummaryGenerator()
        self.query_engine = ConversationalQueryEngine()
        
    def run_data_integration(self):
        """
        Run data integration pipeline
        """
        logger.info("Starting data integration pipeline...")
        
        try:
            # Consolidate data from all states
            master_data = self.data_integrator.consolidate_data()
            
            if master_data is not None:
                # Create database
                self.data_integrator.create_database()
                
                # Get and log summary
                summary = self.data_integrator.get_data_summary()
                logger.info(f"Data integration completed successfully")
                logger.info(f"Total companies: {summary['total_companies']}")
                logger.info(f"States processed: {list(summary['states'].keys())}")
                
                return True
            else:
                logger.error("Data integration failed")
                return False
                
        except Exception as e:
            logger.error(f"Error in data integration: {str(e)}")
            return False
    
    def run_change_detection(self):
        """
        Run change detection pipeline
        """
        logger.info("Starting change detection pipeline...")
        
        try:
            # Process daily changes from snapshots
            snapshot_files = ['snapshot_day1.csv', 'snapshot_day2.csv', 'snapshot_day3.csv']
            changes = self.change_detector.process_daily_changes(snapshot_files)
            
            if changes:
                # Save change logs
                self.change_detector.save_change_logs('csv')
                self.change_detector.save_change_logs('json')
                
                # Update master database
                self.change_detector.update_master_database()
                
                # Get and log summary
                summary = self.change_detector.get_change_summary()
                logger.info(f"Change detection completed successfully")
                logger.info(f"Total changes detected: {summary['total_changes']}")
                logger.info(f"Change types: {summary['change_types']}")
                
                return True
            else:
                logger.warning("No changes detected")
                return True
                
        except Exception as e:
            logger.error(f"Error in change detection: {str(e)}")
            return False
    
    def run_web_enrichment(self, sample_size=50):
        """
        Run web enrichment pipeline
        """
        logger.info("Starting web enrichment pipeline...")
        
        try:
            # Load sample companies from changes (if available)
            try:
                changes_df = pd.read_csv('change_logs_*.csv')
                sample_companies = changes_df[['CIN', 'Company_Name', 'State', 'Status']].drop_duplicates()
            except:
                # Fallback: create sample from master data
                logger.info("Using fallback sample companies")
                sample_companies = pd.DataFrame({
                    'CIN': ['U24299PN2019PTC181506', 'U24299PN2019PTC187808', 'U24299PN2020PTC192446'],
                    'Company_Name': ['ANURIUSWELL PHARMACEUTICALS PRIVATE LIMITED', 
                                    'SKYI FKUR BIOPOLYMERS PRIVATE LIMITED',
                                    'CHEMENGG RESEARCH PRIVATE LIMITED'],
                    'State': ['Maharashtra', 'Maharashtra', 'Maharashtra'],
                    'Status': ['Active', 'Active', 'Active']
                })
            
            # Enrich sample companies
            enriched_data = self.web_enricher.enrich_sample_companies(sample_companies, sample_size)
            
            if enriched_data:
                # Save enriched data
                self.web_enricher.save_enriched_data()
                
                # Get and log summary
                summary = self.web_enricher.get_enrichment_summary()
                logger.info(f"Web enrichment completed successfully")
                logger.info(f"Total enriched records: {summary['total_enriched_records']}")
                logger.info(f"Sources used: {summary['sources_used']}")
                
                return True
            else:
                logger.warning("No enrichment data generated")
                return True
                
        except Exception as e:
            logger.error(f"Error in web enrichment: {str(e)}")
            return False
    
    def run_ai_features(self):
        """
        Run AI features pipeline
        """
        logger.info("Starting AI features pipeline...")
        
        try:
            # Load changes data for AI summary
            try:
                changes_df = pd.read_csv('change_logs_*.csv')
            except:
                logger.info("No changes data found, creating sample data")
                changes_df = pd.DataFrame({
                    'CIN': ['U24299PN2019PTC181506', 'U24299PN2019PTC187808'],
                    'Change_Type': ['New Incorporation', 'Field Update'],
                    'Field_Changed': ['All', 'Status'],
                    'Old_Value': ['', 'Active'],
                    'New_Value': ['ANURIUSWELL PHARMACEUTICALS', 'Strike Off'],
                    'Date': [datetime.now(), datetime.now()],
                    'Company_Name': ['ANURIUSWELL PHARMACEUTICALS', 'SKYI FKUR BIOPOLYMERS'],
                    'State': ['Maharashtra', 'Maharashtra'],
                    'Status': ['Active', 'Strike Off']
                })
            
            # Generate AI summary
            summary = self.ai_summary_gen.generate_daily_summary(changes_df)
            
            # Save summary
            filename = self.ai_summary_gen.save_summary(summary)
            
            logger.info(f"AI features completed successfully")
            logger.info(f"Summary type: {summary['summary_type']}")
            logger.info(f"Summary saved to: {filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in AI features: {str(e)}")
            return False
    
    def run_dashboard(self):
        """
        Run Streamlit dashboard
        """
        logger.info("Starting Streamlit dashboard...")
        
        try:
            import subprocess
            subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard.py"])
            return True
            
        except Exception as e:
            logger.error(f"Error running dashboard: {str(e)}")
            return False
    
    def run_api(self):
        """
        Run Flask API server
        """
        logger.info("Starting Flask API server...")
        
        try:
            from api import app
            app.run(debug=False, host='0.0.0.0', port=5000)
            return True
            
        except Exception as e:
            logger.error(f"Error running API: {str(e)}")
            return False
    
    def run_full_pipeline(self):
        """
        Run the complete MCA Insights Engine pipeline
        """
        logger.info("Starting full MCA Insights Engine pipeline...")
        
        pipeline_steps = [
            ("Data Integration", self.run_data_integration),
            ("Change Detection", self.run_change_detection),
            ("Web Enrichment", lambda: self.run_web_enrichment(50)),
            ("AI Features", self.run_ai_features)
        ]
        
        results = {}
        
        for step_name, step_function in pipeline_steps:
            logger.info(f"Running {step_name}...")
            try:
                success = step_function()
                results[step_name] = success
                
                if success:
                    logger.info(f"{step_name} completed successfully")
                else:
                    logger.error(f"{step_name} failed")
                    
            except Exception as e:
                logger.error(f"Error in {step_name}: {str(e)}")
                results[step_name] = False
        
        # Summary
        logger.info("Pipeline execution summary:")
        for step_name, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            logger.info(f"  {step_name}: {status}")
        
        successful_steps = sum(results.values())
        total_steps = len(results)
        
        logger.info(f"Pipeline completed: {successful_steps}/{total_steps} steps successful")
        
        return results

def main():
    """
    Main function to handle command line arguments and run the pipeline
    """
    parser = argparse.ArgumentParser(description='MCA Insights Engine')
    parser.add_argument('--mode', choices=['full', 'data', 'changes', 'enrichment', 'dashboard', 'api'], 
                       default='full', help='Pipeline mode to run')
    parser.add_argument('--sample-size', type=int, default=50, 
                       help='Sample size for web enrichment')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize the engine
    engine = MCAInsightsEngine()
    
    logger.info(f"MCA Insights Engine started in {args.mode} mode")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    
    try:
        if args.mode == 'full':
            results = engine.run_full_pipeline()
            success = all(results.values())
        elif args.mode == 'data':
            success = engine.run_data_integration()
        elif args.mode == 'changes':
            success = engine.run_change_detection()
        elif args.mode == 'enrichment':
            success = engine.run_web_enrichment(args.sample_size)
        elif args.mode == 'dashboard':
            success = engine.run_dashboard()
        elif args.mode == 'api':
            success = engine.run_api()
        else:
            logger.error(f"Unknown mode: {args.mode}")
            success = False
        
        if success:
            logger.info("Pipeline execution completed successfully")
            sys.exit(0)
        else:
            logger.error("Pipeline execution failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Pipeline execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
