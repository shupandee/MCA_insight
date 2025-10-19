# MCA Insights Engine

A comprehensive Python application for tracking and analyzing company-level changes in Ministry of Corporate Affairs (MCA) data with AI-powered insights and conversational query capabilities.

## 🎯 Overview

The MCA Insights Engine consolidates state-wise MCA data, detects daily company-level changes, enriches company information using public web sources, and provides an intelligent interface for data exploration through AI-powered summaries and conversational queries.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │  Data Pipeline  │    │   AI Features   │
│                 │    │                 │    │                 │
│ • Maharashtra   │───▶│ • Integration   │───▶│ • Summary Gen   │
│ • Gujarat       │    │ • Change Detect │    │ • Chat Engine   │
│ • Delhi         │    │ • Web Enrichment│    │                 │
│ • Tamil Nadu    │    │                 │    │                 │
│ • Karnataka     │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   User Interface│
                       │                 │
                       │ • Streamlit UI  │
                       │ • REST API      │
                       │ • Chat Interface│
                       └─────────────────┘
```

## 📋 Features

### Core Functionality
- **Data Integration**: Consolidates and normalizes state-wise MCA CSV files
- **Change Detection**: Tracks daily company-level changes (incorporations, deregistrations, field updates)
- **Web Enrichment**: Enriches company data using public APIs (ZaubaCorp, MCA API Setu, GST Portal)
- **AI-Powered Insights**: Generates automated daily summaries and conversational query interface
- **Interactive Dashboard**: Streamlit-based web interface with search, filters, and visualizations
- **REST API**: External integration endpoints for third-party applications

### AI Features
- **Daily Summary Generation**: Automated AI summaries of company changes
- **Conversational Chat**: Natural language queries about MCA data
- **Trend Analysis**: Pattern recognition and insights generation

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Required Python packages (see requirements.txt)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd MCA_Insights_Engine
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables** (optional)
   ```bash
   # Create .env file for OpenAI API key
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

### Running the Application

#### Full Pipeline
```bash
python main.py --mode full
```

#### Individual Components
```bash
# Data integration only
python main.py --mode data

# Change detection only
python main.py --mode changes

# Web enrichment only
python main.py --mode enrichment --sample-size 100

# Start dashboard
python main.py --mode dashboard

# Start API server
python main.py --mode api
```

## 📁 Project Structure

```
MCA_Insights_Engine/
├── main.py                 # Main orchestration script
├── data_integration.py     # Data consolidation and cleaning
├── change_detection.py     # Change tracking and logging
├── web_enrichment.py       # Web-based data enrichment
├── ai_features.py         # AI summary and chat functionality
├── dashboard.py           # Streamlit web interface
├── api.py                # REST API endpoints
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── .env                 # Environment variables (optional)
├── mca_insights.log     # Application logs
├── mca_insights.db      # SQLite database
└── data/               # Data files
    ├── maharashtra.csv
    ├── gujarat.csv
    ├── delhi.csv
    ├── tamil_nadu.csv
    ├── karnataka.csv
    ├── snapshot_day1.csv
    ├── snapshot_day2.csv
    └── snapshot_day3.csv
```

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: OpenAI API key for AI features (optional, uses mock data if not provided)

### Database Configuration
- Default SQLite database: `mca_insights.db`
- Tables: `companies`, `company_changes`

### API Configuration
- Default port: 5000
- CORS enabled for cross-origin requests

## 📊 Data Flow

### 1. Data Integration
- Loads state-wise CSV files
- Standardizes column structures
- Handles missing values and duplicates
- Creates consolidated master dataset
- Stores in SQLite database

### 2. Change Detection
- Compares daily snapshots
- Identifies new incorporations
- Tracks deregistrations/strike-offs
- Monitors field-level changes
- Generates structured change logs

### 3. Web Enrichment
- Samples companies with recent changes
- Enriches from multiple sources:
  - ZaubaCorp (director information)
  - MCA API Setu (company details)
  - GST Portal (tax information)
- Saves enriched data to CSV

### 4. AI Features
- Generates daily summaries using AI
- Provides conversational query interface
- Supports natural language questions
- Returns structured insights

## 🎨 User Interface

### Streamlit Dashboard
- **Dashboard Overview**: Key metrics, charts, and recent changes
- **Company Search**: Search by CIN or company name
- **Change Analysis**: Visualizations of change patterns
- **AI Chat**: Conversational interface for data queries
- **Reports**: Export options and AI-generated summaries

### REST API Endpoints

#### Health Check
```http
GET /api/health
```

#### Search Companies
```http
GET /api/search_company?q=<search_term>&type=<name|cin>
```

#### Get Company Details
```http
GET /api/company/<cin>
```

#### Dashboard Statistics
```http
GET /api/dashboard/stats
```

#### Changes Analysis
```http
GET /api/changes/analysis?days=<days>
```

#### Chat Interface
```http
POST /api/chat
Content-Type: application/json
{
  "query": "Show new incorporations in Maharashtra"
}
```

#### Get Companies (Paginated)
```http
GET /api/companies?page=<page>&per_page=<per_page>&state=<state>&status=<status>
```

## 🤖 AI Features

### Daily Summary Generation
Automatically generates concise daily reports highlighting:
- Total changes (incorporations, deregistrations, updates)
- State-wise breakdown
- Top fields modified
- Key insights and trends

### Conversational Query Engine
Supports natural language queries such as:
- "Show new incorporations in Maharashtra"
- "How many companies were struck off last month?"
- "What are the top manufacturing sectors?"
- "List companies with authorized capital above ₹10 lakh"

## 📈 Sample Queries

### Dashboard Queries
```python
# Search for a specific company
GET /api/search_company?q=ANURIUSWELL&type=name

# Get company details
GET /api/company/U24299PN2019PTC181506

# Get dashboard statistics
GET /api/dashboard/stats
```

### Chat Queries
```python
# Natural language queries
POST /api/chat
{
  "query": "Show me companies in the pharmaceutical sector"
}

POST /api/chat
{
  "query": "What's the average authorized capital in Gujarat?"
}
```

## 🔍 Data Schema

### Companies Table
- `CIN`: Corporate Identification Number
- `Company_Name`: Company name
- `State`: State of registration
- `Status`: Company status (Active, Strike Off, etc.)
- `Authorized_Capital`: Authorized capital amount
- `Paidup_Capital`: Paid-up capital amount
- `Registration_Date`: Date of incorporation
- `Industry_Classification`: NIC code classification

### Company Changes Table
- `CIN`: Corporate Identification Number
- `Change_Type`: Type of change (New Incorporation, Deregistration, Field Update)
- `Field_Changed`: Specific field that changed
- `Old_Value`: Previous value
- `New_Value`: New value
- `Date`: Date of change
- `Company_Name`: Company name
- `State`: State
- `Status`: Current status

## 🛠️ Development

### Adding New Data Sources
1. Update `web_enrichment.py` with new source methods
2. Add source configuration in `enrich_company()` method
3. Update data schema if needed

### Extending AI Features
1. Modify `ai_features.py` for new AI capabilities
2. Update prompt templates for different query types
3. Add new conversational patterns

### Customizing Dashboard
1. Modify `dashboard.py` for UI changes
2. Add new visualizations using Plotly
3. Update filters and search functionality

## 📝 Logging

The application uses Python's logging module with:
- File logging: `mca_insights.log`
- Console output
- Different log levels (INFO, ERROR, DEBUG)

## 🧪 Testing

### Manual Testing
```bash
# Test data integration
python data_integration.py

# Test change detection
python change_detection.py

# Test web enrichment
python web_enrichment.py

# Test AI features
python ai_features.py
```

### API Testing
Use tools like Postman or curl to test API endpoints:
```bash
curl -X GET "http://localhost:5000/api/health"
curl -X GET "http://localhost:5000/api/search_company?q=ANURIUSWELL&type=name"
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure SQLite database exists
   - Check file permissions

2. **Missing Dependencies**
   - Run `pip install -r requirements.txt`
   - Check Python version compatibility

3. **API Key Issues**
   - Verify OpenAI API key in `.env` file
   - Application will use mock data if key is missing

4. **Data Loading Errors**
   - Verify CSV files exist in correct location
   - Check file formats and column names

### Log Analysis
Check `mca_insights.log` for detailed error information and debugging.

## 📄 License

This project is developed as part of an assignment for MCA Insights Engine implementation.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Create an issue in the repository

---

**Note**: This is a working proxy implementation demonstrating the intended logic and integration with appropriate data sources. The system is designed to be extensible and can be enhanced with additional features as needed.
