import pandas as pd
import json
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class AISummaryGenerator:
    """
    Class to generate AI-powered summaries of daily changes
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            logger.warning("Gemini API key not found. Using mock summaries.")
            self.model = None
    
    def generate_daily_summary(self, changes_df):
        """
        Generate AI-powered daily summary of company changes
        """
        if changes_df.empty:
            return self._generate_empty_summary()
        
        # Prepare data for AI analysis
        summary_data = self._prepare_summary_data(changes_df)
        
        if self.model:
            return self._generate_ai_summary(summary_data)
        else:
            return self._generate_mock_summary(summary_data)
    
    def _prepare_summary_data(self, changes_df):
        """
        Prepare structured data for AI analysis
        """
        summary_data = {
            'total_changes': len(changes_df),
            'new_incorporations': len(changes_df[changes_df['Change_Type'] == 'New Incorporation']),
            'deregistrations': len(changes_df[changes_df['Change_Type'] == 'Deregistration']),
            'field_updates': len(changes_df[changes_df['Change_Type'] == 'Field Update']),
            'states_affected': changes_df['State'].value_counts().to_dict(),
            'top_fields_changed': changes_df['Field_Changed'].value_counts().head(5).to_dict(),
            'date_range': {
                'start': changes_df['Date'].min(),
                'end': changes_df['Date'].max()
            }
        }
        
        return summary_data
    
    def _generate_ai_summary(self, summary_data):
        """
        Generate summary using Gemini API
        """
        try:
            prompt = f"""
            Based on the following MCA company data changes, generate a concise daily summary report:
            
            Data: {json.dumps(summary_data, default=str)}
            
            Please provide:
            1. A brief overview of the day's activity
            2. Key highlights and trends
            3. Notable changes by state
            4. Any significant patterns or insights
            
            Keep the summary professional and informative, suitable for business stakeholders.
            """
            
            response = self.model.generate_content(prompt)
            summary = response.text
            
            return {
                'generated_at': datetime.now().isoformat(),
                'summary_type': 'AI Generated (Gemini)',
                'content': summary,
                'metadata': summary_data
            }
            
        except Exception as e:
            logger.error(f"Error generating AI summary: {str(e)}")
            return self._generate_mock_summary(summary_data)
    
    def _generate_mock_summary(self, summary_data):
        """
        Generate mock summary when AI is not available
        """
        summary_content = f"""
        MCA Daily Change Summary - {datetime.now().strftime('%Y-%m-%d')}
        
        OVERVIEW:
        Today's MCA data update shows {summary_data['total_changes']} total changes across company records.
        
        KEY METRICS:
        • New Incorporations: {summary_data['new_incorporations']}
        • Deregistrations: {summary_data['deregistrations']}
        • Field Updates: {summary_data['field_updates']}
        
        STATE-WISE BREAKDOWN:
        """
        
        for state, count in list(summary_data['states_affected'].items())[:5]:
            summary_content += f"• {state}: {count} changes\n"
        
        summary_content += f"""
        TOP FIELDS MODIFIED:
        """
        
        for field, count in list(summary_data['top_fields_changed'].items())[:3]:
            summary_content += f"• {field}: {count} updates\n"
        
        summary_content += f"""
        INSIGHTS:
        The data shows active corporate activity with a focus on {list(summary_data['top_fields_changed'].keys())[0] if summary_data['top_fields_changed'] else 'various'} modifications.
        """
        
        return {
            'generated_at': datetime.now().isoformat(),
            'summary_type': 'Mock Generated',
            'content': summary_content,
            'metadata': summary_data
        }
    
    def _generate_empty_summary(self):
        """
        Generate summary for days with no changes
        """
        return {
            'generated_at': datetime.now().isoformat(),
            'summary_type': 'No Changes',
            'content': f"No company changes detected for {datetime.now().strftime('%Y-%m-%d')}",
            'metadata': {'total_changes': 0}
        }
    
    def save_summary(self, summary, filename=None):
        """
        Save summary to file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"daily_summary_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"Summary saved to {filename}")
        return filename

class ConversationalQueryEngine:
    """
    Class to handle conversational queries about MCA data
    """
    
    def __init__(self, db_path='mca_insights.db', api_key=None):
        self.db_path = db_path
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            logger.warning("Gemini API key not found. Using rule-based queries.")
            self.model = None
    
    def process_query(self, query: str, db_connection=None):
        """
        Process natural language query about MCA data
        """
        query_lower = query.lower()
        
        # Rule-based query processing
        if 'new incorporation' in query_lower or 'newly incorporated' in query_lower:
            return self._handle_new_incorporations_query(query, db_connection)
        elif 'struck off' in query_lower or 'deregistered' in query_lower:
            return self._handle_deregistration_query(query, db_connection)
        elif 'manufacturing' in query_lower or 'sector' in query_lower:
            return self._handle_sector_query(query, db_connection)
        elif 'capital' in query_lower:
            return self._handle_capital_query(query, db_connection)
        elif 'maharashtra' in query_lower or 'gujarat' in query_lower or 'state' in query_lower:
            return self._handle_state_query(query, db_connection)
        else:
            return self._handle_general_query(query, db_connection)
    
    def _handle_new_incorporations_query(self, query, db_connection):
        """
        Handle queries about new incorporations
        """
        try:
            if db_connection:
                cursor = db_connection.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as count, State 
                    FROM company_changes 
                    WHERE Change_Type = 'New Incorporation' 
                    GROUP BY State
                """)
                results = cursor.fetchall()
                
                response = "New Incorporations by State:\n"
                for count, state in results:
                    response += f"• {state}: {count} companies\n"
                
                return response
            else:
                return "New incorporations data not available. Please ensure database is connected."
                
        except Exception as e:
            logger.error(f"Error handling new incorporations query: {str(e)}")
            return "Sorry, I couldn't retrieve new incorporation data."
    
    def _handle_deregistration_query(self, query, db_connection):
        """
        Handle queries about deregistrations
        """
        try:
            if db_connection:
                cursor = db_connection.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as count, State 
                    FROM company_changes 
                    WHERE Change_Type = 'Deregistration' 
                    GROUP BY State
                """)
                results = cursor.fetchall()
                
                response = "Deregistrations by State:\n"
                for count, state in results:
                    response += f"• {state}: {count} companies\n"
                
                return response
            else:
                return "Deregistration data not available. Please ensure database is connected."
                
        except Exception as e:
            logger.error(f"Error handling deregistration query: {str(e)}")
            return "Sorry, I couldn't retrieve deregistration data."
    
    def _handle_sector_query(self, query, db_connection):
        """
        Handle queries about sectors/industries
        """
        try:
            if db_connection:
                cursor = db_connection.cursor()
                cursor.execute("""
                    SELECT Industry_Classification, COUNT(*) as count 
                    FROM companies 
                    WHERE Industry_Classification IS NOT NULL 
                    GROUP BY Industry_Classification 
                    ORDER BY count DESC 
                    LIMIT 10
                """)
                results = cursor.fetchall()
                
                response = "Top Industries by Company Count:\n"
                for industry, count in results:
                    response += f"• {industry}: {count} companies\n"
                
                return response
            else:
                return "Industry data not available. Please ensure database is connected."
                
        except Exception as e:
            logger.error(f"Error handling sector query: {str(e)}")
            return "Sorry, I couldn't retrieve industry data."
    
    def _handle_capital_query(self, query, db_connection):
        """
        Handle queries about capital
        """
        try:
            if db_connection:
                cursor = db_connection.cursor()
                cursor.execute("""
                    SELECT AVG(AuthorizedCapital) as avg_capital, 
                           MAX(AuthorizedCapital) as max_capital,
                           COUNT(*) as total_companies
                    FROM companies 
                    WHERE AuthorizedCapital > 0
                """)
                result = cursor.fetchone()
                
                if result:
                    avg_capital, max_capital, total_companies = result
                    response = f"Capital Statistics:\n"
                    response += f"• Average Authorized Capital: ₹{avg_capital:,.2f}\n"
                    response += f"• Maximum Authorized Capital: ₹{max_capital:,.2f}\n"
                    response += f"• Total Companies: {total_companies:,}\n"
                    
                    return response
            else:
                return "Capital data not available. Please ensure database is connected."
                
        except Exception as e:
            logger.error(f"Error handling capital query: {str(e)}")
            return "Sorry, I couldn't retrieve capital data."
    
    def _handle_state_query(self, query, db_connection):
        """
        Handle queries about specific states
        """
        try:
            if db_connection:
                # Extract state name from query
                states = ['maharashtra', 'gujarat', 'delhi', 'tamil nadu', 'karnataka']
                mentioned_state = None
                
                for state in states:
                    if state in query.lower():
                        mentioned_state = state.title()
                        break
                
                if mentioned_state:
                    cursor = db_connection.cursor()
                    cursor.execute("""
                        SELECT COUNT(*) as count, Status 
                        FROM companies 
                        WHERE State = ? 
                        GROUP BY Status
                    """, (mentioned_state,))
                    results = cursor.fetchall()
                    
                    response = f"Company Status in {mentioned_state}:\n"
                    for count, status in results:
                        response += f"• {status}: {count} companies\n"
                    
                    return response
                else:
                    return "Please specify a state name (Maharashtra, Gujarat, Delhi, Tamil Nadu, or Karnataka)."
            else:
                return "State data not available. Please ensure database is connected."
                
        except Exception as e:
            logger.error(f"Error handling state query: {str(e)}")
            return "Sorry, I couldn't retrieve state data."
    
    def _handle_general_query(self, query, db_connection):
        """
        Handle general queries
        """
        return "I can help you with queries about:\n• New incorporations\n• Deregistrations\n• Industry sectors\n• Capital information\n• State-wise data\n\nPlease ask a specific question about MCA data."

if __name__ == "__main__":
    # Test AI Summary Generator
    print("Testing AI Summary Generator...")
    
    # Create sample changes data
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
    
    # Generate summary
    summary_gen = AISummaryGenerator()
    summary = summary_gen.generate_daily_summary(sample_changes)
    print(f"Generated Summary: {summary['summary_type']}")
    print(summary['content'])
    
    # Test Conversational Query Engine
    print("\nTesting Conversational Query Engine...")
    query_engine = ConversationalQueryEngine()
    
    test_queries = [
        "Show new incorporations in Maharashtra",
        "How many companies were struck off?",
        "What are the top manufacturing sectors?"
    ]
    
    for query in test_queries:
        response = query_engine.process_query(query)
        print(f"Query: {query}")
        print(f"Response: {response}\n")
