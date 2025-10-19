#!/usr/bin/env python3
"""
MCA Insights Engine - Test Script

This script tests the core functionality of the MCA Insights Engine
without running the full pipeline.
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_data_integration():
    """
    Test data integration functionality
    """
    print("🧪 Testing Data Integration...")
    
    try:
        from data_integration import MCADataIntegrator
        
        integrator = MCADataIntegrator()
        
        # Test loading a single state file
        maharashtra_data = integrator.load_state_data('maharashtra', 'maharashtra.csv')
        
        if maharashtra_data is not None:
            print(f"✅ Successfully loaded Maharashtra data: {len(maharashtra_data)} records")
            print(f"   Columns: {list(maharashtra_data.columns)}")
            return True
        else:
            print("❌ Failed to load Maharashtra data")
            return False
            
    except Exception as e:
        print(f"❌ Data integration test failed: {str(e)}")
        return False

def test_database():
    """
    Test database functionality
    """
    print("\n🧪 Testing Database...")
    
    try:
        if os.path.exists('mca_insights.db'):
            conn = sqlite3.connect('mca_insights.db')
            
            # Test basic queries
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM companies")
            count = cursor.fetchone()[0]
            
            cursor.execute("SELECT State, COUNT(*) FROM companies GROUP BY State LIMIT 5")
            states = cursor.fetchall()
            
            conn.close()
            
            print(f"✅ Database test successful: {count} companies")
            print(f"   Top states: {states}")
            return True
        else:
            print("❌ Database file not found")
            return False
            
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False

def test_ai_features():
    """
    Test AI features functionality
    """
    print("\n🧪 Testing AI Features...")
    
    try:
        from ai_features import AISummaryGenerator, ConversationalQueryEngine
        
        # Test AI Summary Generator
        summary_gen = AISummaryGenerator()
        
        # Create sample data
        sample_changes = pd.DataFrame({
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
        
        summary = summary_gen.generate_daily_summary(sample_changes)
        
        print(f"✅ AI Summary Generator test successful: {summary['summary_type']}")
        
        # Test Conversational Query Engine
        query_engine = ConversationalQueryEngine()
        response = query_engine.process_query("Show new incorporations")
        
        print(f"✅ Conversational Query Engine test successful")
        print(f"   Sample response: {response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ AI features test failed: {str(e)}")
        return False

def test_web_enrichment():
    """
    Test web enrichment functionality
    """
    print("\n🧪 Testing Web Enrichment...")
    
    try:
        from web_enrichment import WebEnrichment
        
        enricher = WebEnrichment()
        
        # Test with sample data
        sample_companies = pd.DataFrame({
            'CIN': ['U24299PN2019PTC181506'],
            'Company_Name': ['ANURIUSWELL PHARMACEUTICALS PRIVATE LIMITED'],
            'State': ['Maharashtra'],
            'Status': ['Active']
        })
        
        enriched_data = enricher.enrich_sample_companies(sample_companies, sample_size=1)
        
        if enriched_data:
            print(f"✅ Web enrichment test successful: {len(enriched_data)} enriched records")
            return True
        else:
            print("❌ No enriched data generated")
            return False
            
    except Exception as e:
        print(f"❌ Web enrichment test failed: {str(e)}")
        return False

def test_api_endpoints():
    """
    Test API endpoints functionality
    """
    print("\n🧪 Testing API Endpoints...")
    
    try:
        from api import MCAAPI
        
        api = MCAAPI()
        
        # Test search functionality
        results = api.search_company('ANURIUSWELL', 'name')
        
        print(f"✅ API test successful: {len(results)} search results")
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        return False

def main():
    """
    Run all tests
    """
    print("🚀 MCA Insights Engine - Test Suite")
    print("=" * 50)
    
    tests = [
        ("Data Integration", test_data_integration),
        ("Database", test_database),
        ("AI Features", test_ai_features),
        ("Web Enrichment", test_web_enrichment),
        ("API Endpoints", test_api_endpoints)
    ]
    
    results = {}
    
    for test_name, test_function in tests:
        try:
            success = test_function()
            results[test_name] = success
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The MCA Insights Engine is ready to use.")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
