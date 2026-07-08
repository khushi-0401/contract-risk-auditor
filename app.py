import streamlit as st
import json
import pandas as pd
import plotly.express as px
from datetime import datetime
import re
import sys

# Import your modules
from contract_parser import extract_text_from_file
from auditor_agent import audit_contract, calculate_risk_score
from utils import create_risk_chart, format_risk_badge, generate_summary_stats, get_priority_actions
from file_validator import validate_file, get_file_info, check_file_safety
from email_reports import send_email_with_user_credentials
from contract_comparator import compare_contracts
from chatbot import ContractChatbot

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Legal Contract AI Auditor",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# LOAD RISK RULES
# ============================================
@st.cache_data
def load_rules():
    try:
        with open('risk_rules.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['rules']
    except FileNotFoundError:
        st.error("❌ risk_rules.json not found! Please create this file.")
        return []
    except json.JSONDecodeError:
        st.error("❌ risk_rules.json is corrupted! Please check the JSON format.")
        return []

RULES = load_rules()

# ============================================
# FILE TYPE SUPPORT
# ============================================
SUPPORTED_TYPES = {
    'Text': ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv', '.log'],
    'Word': ['.docx'],
    'PDF': ['.pdf'],
    'Rich Text': ['.rtf'],
    'OpenDocument': ['.odt'],
    'Email': ['.eml', '.msg'],
    'Web': ['.htm', '.html'],
    'Excel': ['.xlsx', '.xls'],
    'PowerPoint': ['.pptx'],
    'Images': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
}

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
if 'audit_done' not in st.session_state:
    st.session_state.audit_done = False
if 'results' not in st.session_state:
    st.session_state.results = None
if 'risk_score' not in st.session_state:
    st.session_state.risk_score = None
if 'risk_level' not in st.session_state:
    st.session_state.risk_level = None
if 'contract_text' not in st.session_state:
    st.session_state.contract_text = None
if 'executive_summary' not in st.session_state:
    st.session_state.executive_summary = None
if 'full_audit_data' not in st.session_state:
    st.session_state.full_audit_data = None
if 'file_name' not in st.session_state:
    st.session_state.file_name = None
if 'file_size' not in st.session_state:
    st.session_state.file_size = None
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'chatbot' not in st.session_state:
    st.session_state.chatbot = None
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'risk_history' not in st.session_state:
    st.session_state.risk_history = []

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("# ⚖️ Contract Auditor")
    st.markdown("AI-Powered Legal Analysis")
    st.markdown("---")
    
    st.markdown("### How It Works")
    st.markdown("""
    1. Upload any contract document
    2. AI analyzes against risk rules
    3. Get detailed risk assessment
    4. Download comprehensive report
    """)
    
    st.markdown("---")
    
    st.markdown("### Risk Categories")
    st.markdown("""
    - 🔴 **High Risk** - Critical issues needing immediate attention
    - 🟡 **Medium Risk** - Requires review and possible action
    - 🟢 **Low Risk** - Minor concerns or compliant
    """)
    
    st.markdown("---")
    
    st.markdown("### System Status")
    st.markdown(f"**Rules Loaded:** {len(RULES)}")
    st.markdown(f"**File Types:** {len(SUPPORTED_TYPES)} categories")
    st.markdown(f"**Python Version:** {sys.version.split()[0]}")
    
    if st.session_state.audit_done:
        st.markdown(f"**Last Audit:** {datetime.now().strftime('%H:%M:%S')}")
    
    st.markdown("---")
    st.caption("⚠️ **Disclaimer:** This tool is for educational purposes only. Always consult a qualified attorney for legal advice.")

# ============================================
# MAIN CONTENT WITH TABS
# ============================================
st.markdown("# 📄 Legal Contract AI Auditor")
st.markdown("Upload your contract and get a **comprehensive risk assessment** with actionable insights.")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Audit Contract",
    "📧 Email Report",
    "🔄 Compare Contracts",
    "💬 Chat with Contract"
])

# ============================================
# TAB 1: AUDIT CONTRACT
# ============================================
with tab1:
    st.markdown("### 📂 Upload Document")
    
    all_extensions = []
    for category, exts in SUPPORTED_TYPES.items():
        all_extensions.extend(exts)
    
    st.caption(f"Supported formats: {', '.join(all_extensions)}")
    st.markdown("---")
    
    uploaded_file = st.file_uploader(
        "Choose a document",
        type=all_extensions,
        help="Supported formats: " + ", ".join(all_extensions[:10]) + "..."
    )
    
    if uploaded_file is not None:
        # Validate the file
        is_valid, error_msg = validate_file(uploaded_file)
        if not is_valid:
            st.error(f"❌ {error_msg}")
            st.stop()
        
        warnings = check_file_safety(uploaded_file)
        for warning in warnings:
            st.warning(f"⚠️ {warning}")
        
        file_info = get_file_info(uploaded_file)
        
        st.session_state.file_name = uploaded_file.name
        st.session_state.file_size = uploaded_file.size
        st.session_state.uploaded_file = uploaded_file
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📄 File Name", uploaded_file.name)
        with col2:
            size_kb = uploaded_file.size / 1024
            size_mb = size_kb / 1024
            display_size = f"{size_mb:.2f} MB" if size_mb > 1 else f"{size_kb:.2f} KB"
            st.metric("📊 File Size", display_size)
        with col3:
            if '.' in uploaded_file.name:
                file_ext = '.' + uploaded_file.name.split('.')[-1]
            else:
                file_ext = 'Unknown'
            st.metric("📌 File Type", file_ext.upper())
        
        st.markdown("---")
        
        with st.spinner("📖 Reading document..."):
            try:
                contract_text = extract_text_from_file(uploaded_file)
                st.session_state.contract_text = contract_text
                st.success(f"✅ Successfully read {uploaded_file.name} ({len(contract_text)} characters)")
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")
                st.stop()
        
        with st.expander("📝 Contract Preview (First 1000 characters)"):
            preview = contract_text[:1000]
            if len(contract_text) > 1000:
                preview = preview + "..."
            st.text_area("Preview", preview, height=200, disabled=True)
            st.caption(f"Total characters: {len(contract_text)}")
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🚀 Run Risk Audit", type="primary", use_container_width=True):
                if not RULES:
                    st.error("❌ No risk rules loaded! Check risk_rules.json")
                    st.stop()
                
                with st.spinner("🧠 AI is analyzing contract clauses... This may take 15-30 seconds."):
                    try:
                        audit_response = audit_contract(contract_text, RULES)
                        
                        if 'results' in audit_response and len(audit_response['results']) > 0:
                            st.session_state.full_audit_data = audit_response
                            st.session_state.results = audit_response['results']
                            st.session_state.executive_summary = audit_response.get('executive_summary', 'Analysis complete.')
                            
                            score, level, summary = calculate_risk_score(audit_response['results'])
                            st.session_state.risk_score = score
                            st.session_state.risk_level = level
                            st.session_state.audit_done = True
                            st.rerun()
                        else:
                            st.error("❌ No results returned. Please check your API key or try again.")
                            st.info("💡 Make sure you've set your Google API key in .env file")
                    except Exception as e:
                        st.error(f"❌ Audit failed: {e}")
                        st.info("💡 Tip: Try with a shorter document or check your API key")
        
        with col2:
            if st.button("🔄 Reset", use_container_width=True):
                reset_keys = ['audit_done', 'results', 'risk_score', 'risk_level', 'executive_summary', 'full_audit_data']
                for key in reset_keys:
                    if key in st.session_state:
                        st.session_state[key] = None
                st.rerun()
        
        # ============================================
        # RESULTS DISPLAY
        # ============================================
        if st.session_state.audit_done and st.session_state.results:
            st.markdown("---")
            st.markdown("## 📊 Audit Results")
            
            # Executive Summary
            st.markdown("### 📋 Executive Summary")
            summary_text = st.session_state.executive_summary or "Analysis complete."
            
            if st.session_state.risk_score <= 33:
                st.success(f"✅ {summary_text}")
            elif st.session_state.risk_score <= 66:
                st.warning(f"⚠️ {summary_text}")
            else:
                st.error(f"🔴 {summary_text}")
            
            st.markdown("---")
            
            # Risk Dashboard
            st.markdown("### 📈 Risk Dashboard")
            stats = generate_summary_stats(st.session_state.results)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.session_state.risk_score <= 33:
                    st.metric("Risk Score", f"{st.session_state.risk_score}%", "🟢 Low Risk")
                elif st.session_state.risk_score <= 66:
                    st.metric("Risk Score", f"{st.session_state.risk_score}%", "🟡 Medium Risk")
                else:
                    st.metric("Risk Score", f"{st.session_state.risk_score}%", "🔴 High Risk")
            
            with col2:
                st.metric("✅ Passed", stats['passed'])
            with col3:
                st.metric("❌ Failed", stats['failed'])
            with col4:
                st.metric("📋 Total Rules", stats['total'])
            
            st.markdown("---")
            
            # Risk Breakdown
            st.markdown("### 🎯 Risk Breakdown")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🔴 High Risk", stats['high_risk'])
            with col2:
                st.metric("🟡 Medium Risk", stats['medium_risk'])
            with col3:
                st.metric("🟢 Low Risk", stats['low_risk'])
            
            st.markdown("---")
            
            # Risk Chart
            chart = create_risk_chart(st.session_state.results)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
            
            st.markdown("---")
            
            # ============================================
            # RISK TREND CHART
            # ============================================
            st.markdown("### 📈 Risk Trend Analysis")
            
            if st.session_state.audit_done and st.session_state.results:
                current_entry = {
                    'date': datetime.now(),
                    'risk_score': st.session_state.risk_score,
                    'passed': stats['passed'],
                    'failed': stats['failed'],
                    'high_risk': stats['high_risk'],
                    'medium_risk': stats['medium_risk'],
                    'low_risk': stats['low_risk']
                }
                
                if not st.session_state.risk_history or st.session_state.risk_history[-1]['risk_score'] != st.session_state.risk_score:
                    st.session_state.risk_history.append(current_entry)
                    if len(st.session_state.risk_history) > 10:
                        st.session_state.risk_history = st.session_state.risk_history[-10:]

            if len(st.session_state.risk_history) > 0:
                trend_data = []
                for entry in st.session_state.risk_history:
                    trend_data.append({
                        'Date': entry['date'].strftime('%H:%M'),
                        'Risk Score': entry['risk_score'],
                        'Passed': entry['passed'],
                        'Failed': entry['failed']
                    })
                
                trend_df = pd.DataFrame(trend_data)
                
                fig = px.line(
                    trend_df,
                    x='Date',
                    y='Risk Score',
                    title='Risk Score Trend (Last 10 Audits)',
                    markers=True,
                    line_shape='linear',
                    color_discrete_sequence=['#ff6b6b']
                )
                fig.update_layout(
                    xaxis_title='Time',
                    yaxis_title='Risk Score (%)',
                    height=300,
                    showlegend=False,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                fig.update_traces(
                    marker=dict(size=10),
                    hovertemplate='<b>Time:</b> %{x}<br><b>Risk Score:</b> %{y}%'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    avg_score = sum(entry['risk_score'] for entry in st.session_state.risk_history) / len(st.session_state.risk_history)
                    st.metric("📊 Average Risk Score", f"{avg_score:.1f}%")
                with col2:
                    latest_score = st.session_state.risk_history[-1]['risk_score']
                    first_score = st.session_state.risk_history[0]['risk_score']
                    change = latest_score - first_score
                    st.metric("📈 Trend", f"{'+' if change > 0 else ''}{change:.0f}%", 
                             delta="Increasing" if change > 0 else "Decreasing" if change < 0 else "Stable")
                with col3:
                    total_audits = len(st.session_state.risk_history)
                    st.metric("📋 Total Audits", total_audits)
                
                if st.button("🗑️ Clear History"):
                    st.session_state.risk_history = []
                    st.rerun()
            else:
                st.info("📊 Audit a contract to start building your risk trend history.")
            
            st.markdown("---")
            
            # ============================================
            # PRIORITY ACTIONS
            # ============================================
            st.markdown("### 🎯 Priority Actions")
            priority_actions = get_priority_actions(st.session_state.results)
            
            if priority_actions:
                st.warning("⚠️ **Top priorities to address:**")
                for idx, action in enumerate(priority_actions, 1):
                    emoji = "🔴" if action['risk_level'] == 'High' else "🟡" if action['risk_level'] == 'Medium' else "🟢"
                    with st.expander(f"{emoji} {idx}. {action['rule_id']} - {action['risk_level']} Risk", expanded=True):
                        st.markdown("**💡 Suggestion:**")
                        st.write(action['suggestion'])
                        st.markdown("**⚠️ Impact:**")
                        st.write(action['impact'])
            else:
                st.success("✅ All rules passed! No priority actions needed.")
            
            st.markdown("---")
            
            # ============================================
            # DETAILED RULE ANALYSIS - FIXED
            # ============================================
            st.markdown("### 📋 Detailed Rule-by-Rule Analysis")
            
            table_data = []
            for item in st.session_state.results:
                reason_text = item['reason'][:150] + "..." if len(item['reason']) > 150 else item['reason']
                suggestion_text = item.get('suggestion', 'N/A')[:100] + "..." if item.get('suggestion') and len(item.get('suggestion', '')) > 100 else item.get('suggestion', 'N/A')
                impact_text = item.get('impact', 'N/A')[:100] + "..." if item.get('impact') and len(item.get('impact', '')) > 100 else item.get('impact', 'N/A')
                
                table_data.append({
                    'Rule ID': item['rule_id'],
                    'Status': item['status'],
                    'Risk Level': item.get('risk_level', 'N/A'),
                    'Reason': reason_text,
                    'Suggestion': suggestion_text,
                    'Impact': impact_text
                })
            
            df = pd.DataFrame(table_data)
            
            def color_status(val):
                if val == 'PASS':
                    return 'background-color: #d4edda; color: #155724; font-weight: bold;'
                elif val == 'FAIL':
                    return 'background-color: #f8d7da; color: #721c24; font-weight: bold;'
                return ''
            
            def color_risk_level(val):
                if val == 'High':
                    return 'background-color: #f8d7da; color: #721c24;'
                elif val == 'Medium':
                    return 'background-color: #fff3cd; color: #856404;'
                elif val == 'Low':
                    return 'background-color: #d4edda; color: #155724;'
                return ''
            
            # FIXED: Changed applymap to map
            styled_df = df.style.map(color_status, subset=['Status'])
            styled_df = styled_df.map(color_risk_level, subset=['Risk Level'])
            
            st.dataframe(styled_df, use_container_width=True, height=400, hide_index=True)
            
            st.markdown("---")
            
            # ============================================
            # DEEP DIVE
            # ============================================
            st.markdown("### 🔍 Deep Dive: Full Analysis")
            
            for item in st.session_state.results:
                status_emoji = "✅" if item['status'] == 'PASS' else "❌"
                risk_badge = format_risk_badge(item.get('risk_level', 'Low'))
                reason_preview = item['reason'][:100] + "..." if len(item['reason']) > 100 else item['reason']
                
                with st.expander(f"{status_emoji} {item['rule_id']}: {reason_preview}", expanded=item['status'] == 'FAIL'):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(f"**📌 Rule:** `{item['rule_id']}`")
                        st.markdown(f"**Status:** {status_emoji} **{item['status']}**")
                        st.markdown(f"**Risk Level:** {risk_badge}", unsafe_allow_html=True)
                        st.markdown("**📝 Reason:**")
                        st.write(item['reason'])
                    
                    with col2:
                        if item['status'] == 'FAIL':
                            st.error("**⚠️ Impact:**")
                            st.write(item.get('impact', 'Potential legal risk'))
                            st.warning("**💡 Suggestion:**")
                            st.write(item.get('suggestion', 'Review this clause'))
                        else:
                            st.success("✅ This clause is compliant")
            
            st.markdown("---")
            
            # ============================================
            # EXPORT SECTION WITH COPY BUTTON
            # ============================================
            st.markdown("### 📥 Export Report")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                json_str = json.dumps(st.session_state.full_audit_data, indent=2)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                st.download_button(
                    label="📄 Download JSON",
                    data=json_str,
                    file_name=f"audit_report_{timestamp}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col2:
                csv = df.to_csv(index=False)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                st.download_button(
                    label="📊 Download CSV",
                    data=csv,
                    file_name=f"audit_summary_{timestamp}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col3:
                md_report = f"""# Legal Contract Audit Report

**File:** {st.session_state.file_name}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Risk Score:** {st.session_state.risk_score}%

## Executive Summary
{st.session_state.executive_summary}

## Results Summary
- Total Rules: {stats['total']}
- Passed: {stats['passed']}
- Failed: {stats['failed']}
- High Risk: {stats['high_risk']}
- Medium Risk: {stats['medium_risk']}
- Low Risk: {stats['low_risk']}

## Detailed Results
"""
                for item in st.session_state.results:
                    md_report += f"""
### {item['rule_id']} - {item['status']}
- **Risk Level:** {item.get('risk_level', 'N/A')}
- **Reason:** {item['reason']}
- **Suggestion:** {item.get('suggestion', 'N/A')}
- **Impact:** {item.get('impact', 'N/A')}
"""
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                st.download_button(
                    label="📝 Download Markdown",
                    data=md_report,
                    file_name=f"audit_report_{timestamp}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            with col4:
                if st.button("📋 Copy Summary", use_container_width=True):
                    summary = f"""⚖️ CONTRACT AUDIT REPORT
{'='*50}
Contract: {st.session_state.file_name}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}
Risk Score: {st.session_state.risk_score}%
Status: {st.session_state.risk_level}
{'='*50}
Results Summary:
✅ Passed: {stats['passed']}
❌ Failed: {stats['failed']}
🔴 High Risk: {stats['high_risk']}
🟡 Medium Risk: {stats['medium_risk']}
🟢 Low Risk: {stats['low_risk']}
{'='*50}
FAILED RULES:
"""
                    for item in st.session_state.results:
                        if item['status'] == 'FAIL':
                            summary += f"""
❌ {item['rule_id']}: {item['reason']}
   💡 Suggestion: {item.get('suggestion', 'Review this clause')}
   ⚠️ Impact: {item.get('impact', 'Potential legal risk')}
"""
                    
                    summary += f"""
{'='*50}
Executive Summary:
{st.session_state.executive_summary}
{'='*50}
Generated by Legal Contract AI Auditor
⚠️ This is an automated report. Always consult a qualified attorney.
"""
                    
                    st.code(summary, language='text')
                    st.success("✅ Summary generated! Select and copy the text above.")

# ============================================
# TAB 2: EMAIL REPORTS
# ============================================
with tab2:
    st.markdown("### 📧 Send Audit Report via Email")
    
    if st.session_state.audit_done and st.session_state.results:
        st.info("📊 Your contract has been audited. You can send the report via email.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Risk Score", f"{st.session_state.risk_score}%")
        with col2:
            stats = generate_summary_stats(st.session_state.results)
            st.metric("Failed Rules", stats['failed'])
        with col3:
            st.metric("Passed Rules", stats['passed'])
        
        st.markdown("---")
        
        with st.expander("📖 How to get Gmail App Password", expanded=False):
            st.markdown("""
            1. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
            2. Turn ON **2-Step Verification** for your Google account
            3. Select **Mail** as the app
            4. Select **Windows Computer** as the device
            5. Click **Generate** and copy the 16-character password
            6. Paste it below as "Your App Password"
            """)
        
        with st.form("email_form"):
            st.markdown("### 📧 Your Email Details")
            st.caption("Enter your email details to send the report")
            
            col1, col2 = st.columns(2)
            with col1:
                sender_email = st.text_input(
                    "Your Email Address",
                    placeholder="your_email@gmail.com",
                    help="Your Gmail/Outlook/other email address"
                )
            with col2:
                sender_password = st.text_input(
                    "Your App Password",
                    type="password",
                    placeholder="16-character app password",
                    help="For Gmail: Generate App Password from Google Account"
                )
            
            st.markdown("### 📧 Recipient Details")
            recipient_email = st.text_input(
                "Recipient Email",
                placeholder="client@company.com",
                help="Who should receive this report?"
            )
            
            st.markdown("### 📎 Report Options")
            include_attachments = st.checkbox("📎 Attach HTML Report and Data", value=True)
            include_notes = st.text_area(
                "📝 Additional Notes (Optional)",
                placeholder="Any additional comments for the recipient..."
            )
            
            with st.expander("⚙️ Advanced SMTP Settings (Optional)"):
                smtp_server = st.text_input("SMTP Server", value="smtp.gmail.com")
                smtp_port = st.number_input("SMTP Port", value=587)
            
            submitted = st.form_submit_button("📧 Send Report", type="primary")
            
            if submitted:
                if not sender_email:
                    st.error("❌ Please enter your email address.")
                elif not sender_password:
                    st.error("❌ Please enter your app password.")
                elif not recipient_email:
                    st.error("❌ Please enter recipient email address.")
                else:
                    with st.spinner("📧 Sending email..."):
                        stats = generate_summary_stats(st.session_state.results)
                        
                        result = send_email_with_user_credentials(
                            sender_email=sender_email,
                            sender_password=sender_password,
                            recipient_email=recipient_email,
                            contract_name=st.session_state.file_name or "Contract",
                            results=st.session_state.full_audit_data,
                            risk_score=st.session_state.risk_score,
                            risk_level=st.session_state.risk_level,
                            stats=stats,
                            include_pdf=include_attachments,
                            smtp_server=smtp_server,
                            smtp_port=smtp_port,
                            notes=include_notes
                        )
                        
                        if result['success']:
                            st.success(f"✅ {result['message']}")
                            if include_attachments:
                                st.info("📎 HTML report and JSON data attached to email.")
                        else:
                            st.error(f"❌ {result['error']}")
                            st.info("💡 For Gmail: Use an App Password, not your regular password.")
    else:
        st.warning("⚠️ Please audit a contract first before sending email reports.")
        st.info("Go to the 'Audit Contract' tab, upload a document, and run the audit.")

# ============================================
# TAB 3: COMPARE CONTRACTS
# ============================================
with tab3:
    st.markdown("### 🔄 Compare Two Contracts")
    st.caption("Upload two contracts to compare them side by side")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📄 Contract 1**")
        file1 = st.file_uploader(
            "Choose first contract",
            type=all_extensions,
            key="compare1",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("**📄 Contract 2**")
        file2 = st.file_uploader(
            "Choose second contract",
            type=all_extensions,
            key="compare2",
            label_visibility="collapsed"
        )
    
    if file1 and file2:
        with st.spinner("📖 Reading documents..."):
            try:
                text1 = extract_text_from_file(file1)
                text2 = extract_text_from_file(file2)
                st.success(f"✅ Read {file1.name} ({len(text1)} chars) and {file2.name} ({len(text2)} chars)")
            except Exception as e:
                st.error(f"❌ Error reading files: {e}")
                st.stop()
        
        if st.button("🔍 Compare Contracts", type="primary"):
            with st.spinner("🧠 AI is comparing contracts..."):
                result = compare_contracts(text1, text2)
                
                if 'error' in result:
                    st.error(f"❌ {result['error']}")
                else:
                    st.markdown("---")
                    st.markdown("## 📊 Comparison Results")
                    
                    st.info(f"**📋 Assessment:** {result.get('overall_assessment', 'N/A')}")
                    st.success(f"**💡 Recommendation:** {result.get('recommendation', 'N/A')}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        missing1 = result.get('missing_in_contract1', [])
                        if missing1:
                            st.error(f"**❌ Missing in Contract 1:**\n- " + "\n- ".join(missing1))
                        else:
                            st.success("✅ Contract 1 has all key clauses")
                    
                    with col2:
                        missing2 = result.get('missing_in_contract2', [])
                        if missing2:
                            st.error(f"**❌ Missing in Contract 2:**\n- " + "\n- ".join(missing2))
                        else:
                            st.success("✅ Contract 2 has all key clauses")
                    
                    if result.get('differences'):
                        st.markdown("### 📋 Key Differences")
                        
                        diff_data = []
                        for diff in result['differences']:
                            diff_data.append({
                                'Clause': diff.get('clause', 'Unknown'),
                                'Contract 1': diff.get('contract1', 'N/A')[:200],
                                'Contract 2': diff.get('contract2', 'N/A')[:200],
                                'Risk Impact': diff.get('risk_impact', 'N/A')[:200],
                                'Recommendation': diff.get('recommendation', 'Review')
                            })
                        
                        df = pd.DataFrame(diff_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)
    
    else:
        st.info("👆 Upload two contracts to compare them")

# ============================================
# TAB 4: CHAT WITH CONTRACT
# ============================================
with tab4:
    st.markdown("### 💬 Chat with Your Contract")
    st.caption("Ask questions about your contract and get AI-powered answers")
    
    if st.session_state.contract_text:
        st.success(f"📄 Contract loaded: {st.session_state.file_name}")
        
        if st.session_state.chatbot is None or st.session_state.chatbot.contract_text != st.session_state.contract_text:
            st.session_state.chatbot = ContractChatbot(st.session_state.contract_text)
            st.session_state.chat_messages = []
        
        for msg in st.session_state.chat_messages:
            if msg['role'] == 'user':
                st.chat_message("user").write(msg['content'])
            else:
                st.chat_message("assistant").write(msg['content'])
        
        question = st.chat_input("Ask a question about your contract...")
        
        if question:
            st.chat_message("user").write(question)
            st.session_state.chat_messages.append({'role': 'user', 'content': question})
            
            with st.spinner("🧠 Thinking..."):
                response = st.session_state.chatbot.ask(question)
            
            st.chat_message("assistant").write(response)
            st.session_state.chat_messages.append({'role': 'assistant', 'content': response})
        
        st.markdown("### 🔍 Quick Questions")
        col1, col2, col3 = st.columns(3)
        
        quick_questions = [
            "What are the key risks in this contract?",
            "Summarize this contract",
            "What is the termination notice period?",
            "Is there a confidentiality clause?",
            "What is the governing law?",
            "Are there any missing clauses?"
        ]
        
        for i, q in enumerate(quick_questions):
            col = [col1, col2, col3][i % 3]
            with col:
                if st.button(q, key=f"quick_{i}", use_container_width=True):
                    st.chat_message("user").write(q)
                    st.session_state.chat_messages.append({'role': 'user', 'content': q})
                    
                    with st.spinner("🧠 Thinking..."):
                        response = st.session_state.chatbot.ask(q)
                    
                    st.chat_message("assistant").write(response)
                    st.session_state.chat_messages.append({'role': 'assistant', 'content': response})
                    st.rerun()
        
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_messages = []
            st.session_state.chatbot = ContractChatbot(st.session_state.contract_text)
            st.rerun()
    
    else:
        st.warning("⚠️ Please audit a contract first before chatting.")
        st.info("Go to the 'Audit Contract' tab, upload a document, and run the audit.")

# ============================================
# WELCOME MESSAGE
# ============================================
if 'uploaded_file' not in st.session_state or st.session_state.uploaded_file is None:
    if not st.session_state.audit_done:
        with tab1:
            st.info("👆 **Upload a document** to start the audit")
            
            with st.expander("📖 Need a sample document to test?"):
                st.markdown("**Copy this sample contract, save as a .txt file, and upload:**")
                
                sample_text = """Sample Service Agreement

This Agreement is made on January 1, 2024, between TechCorp Inc. and Client Solutions LLC.

1. SERVICES: TechCorp Inc. shall provide software development services.

2. INDEMNIFICATION: TechCorp Inc. agrees to indemnify and hold harmless Client Solutions LLC from any claims arising from the services provided.

3. GOVERNING LAW: This contract shall be governed by the laws of Texas.

4. TERMINATION: Either party may terminate this agreement upon fifteen (15) days written notice.

5. CONFIDENTIALITY: Client Solutions LLC agrees to keep all proprietary information confidential.

6. PAYMENT TERMS: Client Solutions LLC shall pay TechCorp Inc. as per the agreed schedule.

7. DISPUTE RESOLUTION: Any dispute arising out of this agreement shall be resolved through arbitration."""
                
                st.code(sample_text, language='text')
                st.caption("Copy this text, save as a .txt file, and upload to test!")

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown("⚖️ **Legal Contract AI Auditor** | Built with Streamlit & Google Gemini")
st.markdown("⚠️ **Disclaimer:** This tool is for educational and informational purposes only. It does not constitute legal advice. Always consult a qualified attorney for legal matters.")
st.caption(f"Version 3.0 | 2024 | Python {sys.version.split()[0]}")
