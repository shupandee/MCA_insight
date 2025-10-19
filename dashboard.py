import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import logging
from ai_features import AISummaryGenerator, ConversationalQueryEngine
from change_detection import ChangeDetector
from web_enrichment import WebEnrichment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="MCA Insights Engine",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .bot-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
</style>
""", unsafe_allow_html=True)

class MCADashboard:
    """
    Main dashboard class for MCA Insights Engine
    """
    
    def __init__(self):
        self.db_path = 'mca_insights.db'
        self.ai_summary_gen = AISummaryGenerator()
        self.query_engine = ConversationalQueryEngine(self.db_path)
        
    def load_data(self):
        """
        Load data from database
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Load companies data
            companies_df = pd.read_sql_query("SELECT * FROM companies", conn)
            
            # Load changes data
            changes_df = pd.read_sql_query("SELECT * FROM company_changes", conn)
            
            conn.close()
            
            return companies_df, changes_df
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return None, None
    
    def render_header(self):
        """
        Render the main header
        """
        st.markdown('<h1 class="main-header">🏢 MCA Insights Engine</h1>', unsafe_allow_html=True)
        st.markdown("---")
    
    def render_sidebar(self, companies_df: pd.DataFrame):
        """
        Render the sidebar with filters and navigation
        """
        st.sidebar.title("🔍 Navigation & Filters")
        
        # Navigation
        page = st.sidebar.selectbox(
            "Select Page",
            ["📊 Dashboard Overview", "🔍 Company Search", "📈 Change Analysis", "🤖 AI Chat", "📋 Reports"]
        )
        
        # Filters
        st.sidebar.markdown("### Filters")
        
        # State filter (dynamic from data)
        try:
            state_options = sorted({str(s).strip() for s in companies_df['State'].dropna().unique()})
        except Exception:
            state_options = []
        states = ['All'] + state_options
        selected_state = st.sidebar.selectbox("State", states, index=states.index('Tamil Nadu') if 'Tamil Nadu' in states else 0)
        
        # Status filter (dynamic from data)
        try:
            status_options = sorted({str(s).strip() for s in companies_df['Status'].dropna().unique()})
        except Exception:
            status_options = []
        statuses = ['All'] + status_options
        selected_status = st.sidebar.selectbox("Company Status", statuses)
        
        # Date range filter
        st.sidebar.markdown("### Date Range")
        date_range = st.sidebar.date_input(
            "Select Date Range",
            value=(datetime.now() - timedelta(days=30), datetime.now()),
            max_value=datetime.now()
        )
        
        return page, selected_state, selected_status, date_range
    
    def render_dashboard_overview(self, companies_df, changes_df):
        """
        Render the main dashboard overview
        """
        st.header("📊 Dashboard Overview")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Companies",
                value=f"{len(companies_df):,}",
                delta=f"+{len(changes_df[changes_df['Change_Type'] == 'New Incorporation'])} new"
            )
        
        with col2:
            st.metric(
                label="Active Companies",
                value=f"{len(companies_df[companies_df['Status'] == 'Active']):,}",
                delta=f"-{len(changes_df[changes_df['Change_Type'] == 'Deregistration'])} deregistered"
            )
        
        with col3:
            st.metric(
                label="Total Changes",
                value=f"{len(changes_df):,}",
                delta=f"{len(changes_df[changes_df['Change_Type'] == 'Field Update'])} field updates"
            )
        
        with col4:
            avg_capital = companies_df['AuthorizedCapital'].mean() if not companies_df.empty else 0
            try:
                formatted_cap = f"₹{avg_capital:,.0f}" if pd.notna(avg_capital) else "₹0"
            except Exception:
                formatted_cap = "₹0"
            st.metric(
                label="Avg Authorized Capital",
                value=formatted_cap,
                delta="Capital Analysis"
            )
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Companies by State")
            state_counts = companies_df['State'].value_counts()
            if state_counts.empty:
                st.info("No companies available for the selected filters.")
            else:
                state_df = state_counts.reset_index()
                state_df.columns = ["State", "Count"]
                fig = px.pie(
                    data_frame=state_df,
                    values="Count",
                    names="State",
                    title="Company Distribution by State"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📊 Status Distribution")
            status_counts = companies_df['Status'].value_counts()
            if status_counts.empty:
                st.info("No status data available for the selected filters.")
            else:
                status_df = status_counts.reset_index()
                status_df.columns = ["Status", "Count"]
                fig = px.bar(
                    data_frame=status_df,
                    x="Status",
                    y="Count",
                    title="Company Status Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Recent changes
        st.subheader("🔄 Recent Changes")
        if not changes_df.empty:
            recent_changes = changes_df.head(10)
            st.dataframe(recent_changes, use_container_width=True)
        else:
            st.info("No recent changes found.")
    
    def render_company_search(self, companies_df):
        """
        Render the company search page
        """
        st.header("🔍 Company Search")
        
        # Search options
        search_type = st.radio("Search by:", ["CIN", "Company Name"])
        
        if search_type == "CIN":
            search_term = st.text_input("Enter CIN:", placeholder="U24299PN2019PTC181506")
        else:
            search_term = st.text_input("Enter Company Name:", placeholder="ANURIUSWELL PHARMACEUTICALS")
        
        if st.button("🔍 Search"):
            if search_term:
                if search_type == "CIN":
                    results = companies_df[companies_df['CIN'].str.contains(search_term, case=False, na=False)]
                else:
                    results = companies_df[companies_df['CompanyName'].str.contains(search_term, case=False, na=False)]
                
                if not results.empty:
                    st.success(f"Found {len(results)} companies")
                    st.dataframe(results, use_container_width=True)
                    
                    # Show detailed view for first result
                    if len(results) == 1:
                        self.render_company_details(results.iloc[0])
                else:
                    st.warning("No companies found matching your search criteria.")
    
    def render_company_details(self, company):
        """
        Render detailed company information
        """
        st.subheader("📋 Company Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**CIN:** {company['CIN']}")
            st.write(f"**Company Name:** {company['CompanyName']}")
            st.write(f"**State:** {company['State']}")
            st.write(f"**Status:** {company['Status']}")
        
        with col2:
            st.write(f"**Authorized Capital:** ₹{company['AuthorizedCapital']:,.2f}")
            st.write(f"**Paid-up Capital:** ₹{company['PaidupCapital']:,.2f}")
            st.write(f"**Registration Date:** {company['Registration_Date']}")
            st.write(f"**Industry:** {company['CompanyIndustrialClassification']}")
    
    def render_change_analysis(self, changes_df):
        """
        Render change analysis page
        """
        st.header("📈 Change Analysis")
        
        if changes_df.empty:
            st.info("No change data available.")
            return
        
        # Change type distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Change Types")
            change_counts = changes_df['Change_Type'].value_counts()
            fig = px.pie(
                values=change_counts.values,
                names=change_counts.index,
                title="Distribution of Change Types"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📅 Changes Over Time")
            changes_df['Date'] = pd.to_datetime(changes_df['Date'])
            daily_changes = changes_df.groupby(changes_df['Date'].dt.date).size().reset_index()
            daily_changes.columns = ['Date', 'Count']
            
            fig = px.line(
                daily_changes,
                x='Date',
                y='Count',
                title="Daily Changes Trend"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # State-wise changes
        st.subheader("🗺️ Changes by State")
        state_changes = changes_df['State'].value_counts()
        if state_changes.empty:
            st.info("No changes available for the selected filters.")
        else:
            state_changes_df = state_changes.reset_index()
            state_changes_df.columns = ["State", "Count"]
            fig = px.bar(
                data_frame=state_changes_df,
                x="State",
                y="Count",
                title="Changes by State"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed changes table
        st.subheader("📋 Detailed Changes")
        st.dataframe(changes_df, use_container_width=True)
    
    def render_ai_chat(self):
        """
        Render the AI chat interface
        """
        st.header("🤖 AI Chat Assistant")
        st.markdown("Ask questions about MCA data in natural language!")
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask me about MCA data..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate response
            with st.chat_message("assistant"):
                try:
                    conn = sqlite3.connect(self.db_path)
                    response = self.query_engine.process_query(prompt, conn)
                    conn.close()
                    
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.markdown(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    def render_reports(self, changes_df):
        """
        Render reports page
        """
        st.header("📋 Reports")
        
        # AI Summary Generation
        st.subheader("🤖 AI Daily Summary")
        
        if st.button("Generate AI Summary"):
            if not changes_df.empty:
                with st.spinner("Generating AI summary..."):
                    summary = self.ai_summary_gen.generate_daily_summary(changes_df)
                    
                    st.success("Summary generated successfully!")
                    st.markdown("### 📄 Daily Summary Report")
                    st.text_area("Summary Content", summary['content'], height=300)
                    
                    # Save summary
                    if st.button("Save Summary"):
                        filename = self.ai_summary_gen.save_summary(summary)
                        st.success(f"Summary saved to {filename}")
            else:
                st.warning("No change data available for summary generation.")
        
        # Export options
        st.subheader("📤 Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export Changes CSV"):
                if not changes_df.empty:
                    csv = changes_df.to_csv(index=False)
                    st.download_button(
                        label="Download Changes CSV",
                        data=csv,
                        file_name=f"mca_changes_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No change data to export.")
        
        with col2:
            if st.button("Export Summary JSON"):
                if not changes_df.empty:
                    summary = self.ai_summary_gen.generate_daily_summary(changes_df)
                    json_data = json.dumps(summary, indent=2, default=str)
                    st.download_button(
                        label="Download Summary JSON",
                        data=json_data,
                        file_name=f"mca_summary_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )
                else:
                    st.warning("No data available for summary export.")
    
    def run(self):
        """
        Main method to run the dashboard
        """
        self.render_header()
        
        # Load data
        companies_df, changes_df = self.load_data()
        
        if companies_df is None:
            st.error("Failed to load data. Please ensure the database exists and contains data.")
            return
        
        # Render sidebar and get filters
        page, selected_state, selected_status, date_range = self.render_sidebar(companies_df)
        
        # Apply filters
        def _norm(s: pd.Series) -> pd.Series:
            # Lowercase, remove all non-alphanumeric characters so variants match
            return (
                s.fillna("")
                 .astype(str)
                 .str.casefold()
                 .str.replace(r"[^a-z0-9]", "", regex=True)
            )

        def _norm_one(text: str) -> str:
            return (
                str(text)
                .casefold()
                .encode('ascii', 'ignore')
                .decode('ascii')
                .replace(" ", "")
                .replace("-", "")
                .replace("_", "")
                .replace(".", "")
            )

        if selected_state != 'All':
            sel_state_norm = _norm_one(selected_state)
            # Common aliases mapping
            aliases = {
                "tamilnadu": {"tamilnadu", "tamilnadoo", "tn"},
                "andhrapradesh": {"andhrapradesh", "ap"},
                "uttarpradesh": {"uttarpradesh", "up"},
                "madhyapradesh": {"madhyapradesh", "mp"},
            }
            alias_set = None
            for key, vals in aliases.items():
                if sel_state_norm in vals:
                    alias_set = vals
                    break
            # Exact match first
            norm_state_series = _norm(companies_df['State'])
            match_mask = norm_state_series == sel_state_norm
            # Fallback: alias set or bi-directional contains
            if not match_mask.any():
                contains_mask = norm_state_series.str.contains(sel_state_norm, na=False) | sel_state_norm.__contains__("")
                match_mask = contains_mask
            if alias_set is not None and not match_mask.any():
                alias_mask = norm_state_series.isin(list(alias_set))
                match_mask = alias_mask
            filtered_companies = companies_df[match_mask]
            # Fallback: contains match if exact yields zero
            if filtered_companies.empty:
                filtered_companies = companies_df[norm_state_series.str.contains(sel_state_norm, na=False)]
            companies_df = filtered_companies
            if not changes_df.empty and 'State' in changes_df.columns:
                norm_changes_series = _norm(changes_df['State'])
                ch_mask = norm_changes_series == sel_state_norm
                if not ch_mask.any():
                    ch_mask = norm_changes_series.str.contains(sel_state_norm, na=False)
                if alias_set is not None and not ch_mask.any():
                    ch_mask = norm_changes_series.isin(list(alias_set))
                filtered_changes = changes_df[ch_mask]
                if filtered_changes.empty:
                    filtered_changes = changes_df[norm_changes_series.str.contains(sel_state_norm, na=False)]
                changes_df = filtered_changes
        
        if selected_status != 'All':
            sel_status_norm = (
                str(selected_status)
                .casefold()
                .replace(" ", "")
                .replace("-", "")
                .replace("_", "")
                .replace(".", "")
            )
            companies_df = companies_df[_norm(companies_df['Status']) == sel_status_norm]

        # Sidebar quick debug counts (non-intrusive) to validate filters
        with st.sidebar.expander("Data Snapshot", expanded=False):
            try:
                st.caption(
                    f"Companies after filters: {len(companies_df):,} | Changes: {len(changes_df):,}"
                )
            except Exception:
                pass
        
        # If companies_df becomes empty after filters, show a friendly note
        if companies_df.empty:
            st.info("No companies match the selected filters. Try changing State/Status or the date range.")
        
        # Apply date range to changes_df if available
        try:
            if isinstance(date_range, (list, tuple)) and len(date_range) == 2 and not changes_df.empty:
                start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
                if 'Date' in changes_df.columns:
                    changes_df['Date'] = pd.to_datetime(changes_df['Date'], errors='coerce')
                    mask = (changes_df['Date'] >= start_date) & (changes_df['Date'] <= end_date)
                    changes_df = changes_df[mask]
        except Exception:
            pass
        # Render selected page
        if page == "📊 Dashboard Overview":
            self.render_dashboard_overview(companies_df, changes_df)
        elif page == "🔍 Company Search":
            self.render_company_search(companies_df)
        elif page == "📈 Change Analysis":
            self.render_change_analysis(changes_df)
        elif page == "🤖 AI Chat":
            self.render_ai_chat()
        elif page == "📋 Reports":
            self.render_reports(changes_df)

if __name__ == "__main__":
    dashboard = MCADashboard()
    dashboard.run()
