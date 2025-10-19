from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import pandas as pd
import json
from datetime import datetime
import logging
from ai_features import ConversationalQueryEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

class MCAAPI:
    """
    REST API class for MCA Insights Engine
    """
    
    def __init__(self, db_path='mca_insights.db'):
        self.db_path = db_path
        self.query_engine = ConversationalQueryEngine(db_path)
    
    def get_db_connection(self):
        """
        Get database connection
        """
        return sqlite3.connect(self.db_path)
    
    def search_company(self, search_term, search_type='name'):
        """
        Search for companies by CIN or name
        """
        try:
            conn = self.get_db_connection()
            
            if search_type.lower() == 'cin':
                query = "SELECT * FROM companies WHERE CIN LIKE ?"
                params = (f'%{search_term}%',)
            else:
                query = "SELECT * FROM companies WHERE CompanyName LIKE ?"
                params = (f'%{search_term}%',)
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error searching company: {str(e)}")
            return []
    
    def get_company_details(self, cin):
        """
        Get detailed information for a specific company
        """
        try:
            conn = self.get_db_connection()
            
            # Get company details
            company_query = "SELECT * FROM companies WHERE CIN = ?"
            company_df = pd.read_sql_query(company_query, conn, params=(cin,))
            
            # Get change history
            changes_query = "SELECT * FROM company_changes WHERE CIN = ? ORDER BY Date DESC"
            changes_df = pd.read_sql_query(changes_query, conn, params=(cin,))
            
            conn.close()
            
            result = {
                'company': company_df.to_dict('records')[0] if not company_df.empty else None,
                'changes': changes_df.to_dict('records')
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting company details: {str(e)}")
            return {'company': None, 'changes': []}
    
    def get_dashboard_stats(self):
        """
        Get dashboard statistics
        """
        try:
            conn = self.get_db_connection()
            
            # Company statistics
            company_stats = pd.read_sql_query("""
                SELECT 
                    COUNT(*) as total_companies,
                    COUNT(CASE WHEN Status = 'Active' THEN 1 END) as active_companies,
                    AVG(AuthorizedCapital) as avg_authorized_capital,
                    MAX(AuthorizedCapital) as max_authorized_capital
                FROM companies
            """, conn)
            
            # State distribution
            state_dist = pd.read_sql_query("""
                SELECT State, COUNT(*) as count 
                FROM companies 
                GROUP BY State 
                ORDER BY count DESC
            """, conn)
            
            # Status distribution
            status_dist = pd.read_sql_query("""
                SELECT Status, COUNT(*) as count 
                FROM companies 
                GROUP BY Status 
                ORDER BY count DESC
            """, conn)
            
            # Recent changes
            recent_changes = pd.read_sql_query("""
                SELECT * FROM company_changes 
                ORDER BY Date DESC 
                LIMIT 10
            """, conn)
            
            conn.close()
            
            stats = {
                'company_stats': company_stats.to_dict('records')[0],
                'state_distribution': state_dist.to_dict('records'),
                'status_distribution': status_dist.to_dict('records'),
                'recent_changes': recent_changes.to_dict('records')
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {str(e)}")
            return {}
    
    def get_changes_analysis(self, days=30):
        """
        Get changes analysis for specified number of days
        """
        try:
            conn = self.get_db_connection()
            
            # Changes by type
            changes_by_type = pd.read_sql_query("""
                SELECT Change_Type, COUNT(*) as count 
                FROM company_changes 
                GROUP BY Change_Type
            """, conn)
            
            # Changes by state
            changes_by_state = pd.read_sql_query("""
                SELECT State, COUNT(*) as count 
                FROM company_changes 
                GROUP BY State 
                ORDER BY count DESC
            """, conn)
            
            # Daily changes trend
            daily_changes = pd.read_sql_query("""
                SELECT DATE(Date) as date, COUNT(*) as count 
                FROM company_changes 
                GROUP BY DATE(Date) 
                ORDER BY date DESC 
                LIMIT ?
            """, conn, params=(days,))
            
            conn.close()
            
            analysis = {
                'changes_by_type': changes_by_type.to_dict('records'),
                'changes_by_state': changes_by_state.to_dict('records'),
                'daily_trend': daily_changes.to_dict('records')
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting changes analysis: {str(e)}")
            return {}
    
    def process_chat_query(self, query):
        """
        Process chat query using AI engine
        """
        try:
            conn = self.get_db_connection()
            response = self.query_engine.process_query(query, conn)
            conn.close()
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing chat query: {str(e)}")
            return f"Sorry, I encountered an error: {str(e)}"

# Initialize API
api = MCAAPI()

# API Routes

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'MCA Insights Engine API'
    })

@app.route('/api/search_company', methods=['GET'])
def search_company():
    """
    Search for companies by CIN or name
    """
    try:
        search_term = request.args.get('q', '')
        search_type = request.args.get('type', 'name')  # 'name' or 'cin'
        
        if not search_term:
            return jsonify({'error': 'Search term is required'}), 400
        
        results = api.search_company(search_term, search_type)
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results),
            'search_term': search_term,
            'search_type': search_type
        })
        
    except Exception as e:
        logger.error(f"Error in search_company endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/company/<cin>', methods=['GET'])
def get_company(cin):
    """
    Get detailed information for a specific company
    """
    try:
        details = api.get_company_details(cin)
        
        if details['company'] is None:
            return jsonify({'error': 'Company not found'}), 404
        
        return jsonify({
            'success': True,
            'data': details
        })
        
    except Exception as e:
        logger.error(f"Error in get_company endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """
    Get dashboard statistics
    """
    try:
        stats = api.get_dashboard_stats()
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Error in get_dashboard_stats endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/changes/analysis', methods=['GET'])
def get_changes_analysis():
    """
    Get changes analysis
    """
    try:
        days = request.args.get('days', 30, type=int)
        analysis = api.get_changes_analysis(days)
        
        return jsonify({
            'success': True,
            'data': analysis,
            'days': days
        })
        
    except Exception as e:
        logger.error(f"Error in get_changes_analysis endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Process chat query
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        query = data['query']
        response = api.process_chat_query(query)
        
        return jsonify({
            'success': True,
            'query': query,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/companies', methods=['GET'])
def get_companies():
    """
    Get companies with pagination and filters
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        state = request.args.get('state', '')
        status = request.args.get('status', '')
        
        offset = (page - 1) * per_page
        
        conn = api.get_db_connection()
        
        # Build query with filters
        where_conditions = []
        params = []
        
        if state:
            where_conditions.append("State = ?")
            params.append(state)
        
        if status:
            where_conditions.append("Status = ?")
            params.append(status)
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM companies {where_clause}"
        total_count = pd.read_sql_query(count_query, conn, params=params).iloc[0]['total']
        
        # Get paginated results
        query = f"""
            SELECT * FROM companies 
            {where_clause}
            ORDER BY CompanyName 
            LIMIT ? OFFSET ?
        """
        params.extend([per_page, offset])
        
        companies_df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return jsonify({
            'success': True,
            'data': companies_df.to_dict('records'),
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': (total_count + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"Error in get_companies endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(404)
def not_found(error):
    """
    Handle 404 errors
    """
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """
    Handle 500 errors
    """
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("Starting MCA Insights Engine API...")
    print("Available endpoints:")
    print("- GET /api/health - Health check")
    print("- GET /api/search_company?q=<term>&type=<name|cin> - Search companies")
    print("- GET /api/company/<cin> - Get company details")
    print("- GET /api/dashboard/stats - Get dashboard statistics")
    print("- GET /api/changes/analysis?days=<days> - Get changes analysis")
    print("- POST /api/chat - Process chat query")
    print("- GET /api/companies?page=<page>&per_page=<per_page>&state=<state>&status=<status> - Get companies")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
