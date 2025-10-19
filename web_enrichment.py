import requests
import pandas as pd
import time
import json
from bs4 import BeautifulSoup
import logging
from urllib.parse import quote
import random

logger = logging.getLogger(__name__)

class WebEnrichment:
    """
    Class to enrich company data using publicly available web sources
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.enriched_data = []
        
    def enrich_from_zauba(self, cin, company_name):
        """
        Enrich company data from ZaubaCorp (simulated)
        """
        try:
            # Simulate API call with delay
            time.sleep(random.uniform(1, 2))
            
            # Mock enrichment data (in real implementation, this would be actual API calls)
            enrichment_data = {
                'CIN': cin,
                'COMPANY_NAME': company_name,
                'STATE': 'Maharashtra',  # This would be extracted from the original data
                'STATUS': 'Active',
                'SOURCE': 'ZaubaCorp',
                'FIELD': 'Director_Names',
                'SOURCE_URL': f'https://www.zaubacorp.com/company/{cin}',
                'ENRICHED_DATA': {
                    'directors': ['John Doe', 'Jane Smith'],
                    'sector': 'Technology',
                    'website': f'https://www.{company_name.lower().replace(" ", "")}.com',
                    'email': f'info@{company_name.lower().replace(" ", "")}.com'
                }
            }
            
            return enrichment_data
            
        except Exception as e:
            logger.error(f"Error enriching from ZaubaCorp for {cin}: {str(e)}")
            return None
    
    def enrich_from_mca_api(self, cin):
        """
        Enrich company data from MCA API Setu (simulated)
        """
        try:
            time.sleep(random.uniform(0.5, 1))
            
            # Mock MCA API response
            enrichment_data = {
                'CIN': cin,
                'COMPANY_NAME': 'Sample Company Name',
                'STATE': 'Gujarat',
                'STATUS': 'Active',
                'SOURCE': 'MCA_API_Setu',
                'FIELD': 'Company_Details',
                'SOURCE_URL': f'https://api.mca.gov.in/api/v1/company/{cin}',
                'ENRICHED_DATA': {
                    'registration_number': cin,
                    'company_type': 'Private Limited',
                    'business_activity': 'Software Development',
                    'authorized_capital': '1000000',
                    'paid_up_capital': '500000'
                }
            }
            
            return enrichment_data
            
        except Exception as e:
            logger.error(f"Error enriching from MCA API for {cin}: {str(e)}")
            return None
    
    def enrich_from_gst_portal(self, cin, company_name):
        """
        Enrich company data from GST Portal (simulated)
        """
        try:
            time.sleep(random.uniform(1, 1.5))
            
            # Mock GST Portal data
            enrichment_data = {
                'CIN': cin,
                'COMPANY_NAME': company_name,
                'STATE': 'Karnataka',
                'STATUS': 'Active',
                'SOURCE': 'GST_Portal',
                'FIELD': 'GST_Details',
                'SOURCE_URL': f'https://www.gst.gov.in/search-taxpayer',
                'ENRICHED_DATA': {
                    'gst_number': f'29{cin[-6:]}1Z1',
                    'pan_number': f'ABCDE{cin[-4:]}F',
                    'registration_date': '2020-01-15',
                    'business_nature': 'Manufacturing'
                }
            }
            
            return enrichment_data
            
        except Exception as e:
            logger.error(f"Error enriching from GST Portal for {cin}: {str(e)}")
            return None
    
    def enrich_company(self, cin, company_name, sources=['zauba', 'mca_api', 'gst']):
        """
        Enrich a single company using multiple sources
        """
        enriched_records = []
        
        for source in sources:
            try:
                if source == 'zauba':
                    data = self.enrich_from_zauba(cin, company_name)
                elif source == 'mca_api':
                    data = self.enrich_from_mca_api(cin)
                elif source == 'gst':
                    data = self.enrich_from_gst_portal(cin, company_name)
                else:
                    continue
                
                if data:
                    enriched_records.append(data)
                    
            except Exception as e:
                logger.error(f"Error enriching {cin} from {source}: {str(e)}")
                continue
        
        return enriched_records
    
    def enrich_sample_companies(self, companies_df, sample_size=50):
        """
        Enrich a sample of companies showing recent changes
        """
        logger.info(f"Starting enrichment for {sample_size} companies")
        
        # Get sample of companies (prioritize recent changes)
        sample_companies = companies_df.head(sample_size)
        
        all_enriched_data = []
        
        for idx, company in sample_companies.iterrows():
            cin = company['CIN']
            company_name = company['Company_Name']
            
            logger.info(f"Enriching company {idx+1}/{sample_size}: {company_name}")
            
            # Enrich from multiple sources
            enriched_records = self.enrich_company(cin, company_name)
            all_enriched_data.extend(enriched_records)
            
            # Add delay to avoid overwhelming external APIs
            time.sleep(random.uniform(0.5, 1))
        
        self.enriched_data = all_enriched_data
        logger.info(f"Enrichment completed. Total enriched records: {len(all_enriched_data)}")
        
        return all_enriched_data
    
    def save_enriched_data(self, filename='enriched_company_data.csv'):
        """
        Save enriched data to CSV file
        """
        if not self.enriched_data:
            logger.warning("No enriched data to save")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(self.enriched_data)
        
        # Flatten enriched_data column
        enriched_df = pd.json_normalize(df['ENRICHED_DATA'])
        df = pd.concat([df.drop('ENRICHED_DATA', axis=1), enriched_df], axis=1)
        
        # Save to CSV
        df.to_csv(filename, index=False)
        logger.info(f"Enriched data saved to {filename}")
        
        return df
    
    def get_enrichment_summary(self):
        """
        Get summary of enrichment process
        """
        if not self.enriched_data:
            return None
        
        df = pd.DataFrame(self.enriched_data)
        
        summary = {
            'total_enriched_records': len(df),
            'sources_used': df['SOURCE'].value_counts().to_dict(),
            'fields_enriched': df['FIELD'].value_counts().to_dict(),
            'states_covered': df['STATE'].value_counts().to_dict(),
            'unique_companies': df['CIN'].nunique()
        }
        
        return summary

if __name__ == "__main__":
    # Initialize web enrichment
    enricher = WebEnrichment()
    
    # Load sample companies (this would typically come from change detection)
    # For demo purposes, create a sample DataFrame
    sample_companies = pd.DataFrame({
        'CIN': ['U24299PN2019PTC181506', 'U24299PN2019PTC187808', 'U24299PN2020PTC192446'],
        'Company_Name': ['ANURIUSWELL PHARMACEUTICALS PRIVATE LIMITED', 
                        'SKYI FKUR BIOPOLYMERS PRIVATE LIMITED',
                        'CHEMENGG RESEARCH PRIVATE LIMITED'],
        'State': ['Maharashtra', 'Maharashtra', 'Maharashtra'],
        'Status': ['Active', 'Active', 'Active']
    })
    
    # Enrich sample companies
    enriched_data = enricher.enrich_sample_companies(sample_companies, sample_size=3)
    
    if enriched_data:
        # Save enriched data
        enricher.save_enriched_data()
        
        # Print summary
        summary = enricher.get_enrichment_summary()
        print("\n=== Web Enrichment Summary ===")
        print(f"Total Enriched Records: {summary['total_enriched_records']}")
        print(f"Sources Used: {summary['sources_used']}")
        print(f"Fields Enriched: {summary['fields_enriched']}")
        print(f"States Covered: {summary['states_covered']}")
        print(f"Unique Companies: {summary['unique_companies']}")
    else:
        print("No enrichment data generated")
