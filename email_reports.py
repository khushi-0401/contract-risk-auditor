"""
Email Reports Module for Legal Contract AI Auditor
Users can send reports using their own email credentials
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import io
import json

# We'll use a simpler HTML to PDF approach without WeasyPrint
# For PDF we'll just send HTML as text and attach as HTML file
PDF_SUPPORT = False

# ============================================
# SEND EMAIL WITH USER CREDENTIALS
# ============================================

def send_email_with_user_credentials(
    sender_email: str,
    sender_password: str,
    recipient_email: str,
    contract_name: str,
    results: dict,
    risk_score: int,
    risk_level: str,
    stats: dict,
    include_pdf: bool = False,  # Changed to False by default
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 587,
    notes: str = ""
):
    """
    Send email using user-provided credentials.
    This allows any user to send reports using their own email.
    """
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"📊 Contract Audit Report - {contract_name}"
        
        # Create HTML email content
        html_content = create_email_html(contract_name, results, risk_score, risk_level, stats, notes)
        part = MIMEText(html_content, 'html')
        msg.attach(part)
        
        # Attach report as HTML file instead of PDF
        if include_pdf:
            # Attach HTML report as .html file
            html_attachment = MIMEBase('text', 'html')
            html_attachment.set_payload(html_content.encode('utf-8'))
            encoders.encode_base64(html_attachment)
            html_attachment.add_header(
                'Content-Disposition',
                f'attachment; filename=audit_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
            )
            msg.attach(html_attachment)
            
            # Also attach JSON data
            json_attachment = MIMEBase('application', 'json')
            json_attachment.set_payload(json.dumps(results, indent=2).encode('utf-8'))
            encoders.encode_base64(json_attachment)
            json_attachment.add_header(
                'Content-Disposition',
                f'attachment; filename=audit_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            )
            msg.attach(json_attachment)
        
        # Send email using user's credentials
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return {"success": True, "message": f"Email sent from {sender_email} to {recipient_email}"}
        
    except Exception as e:
        error_msg = str(e).lower()
        
        if "authentication failed" in error_msg or "credentials" in error_msg:
            return {"success": False, "error": "Authentication failed. Check your email and app password."}
        elif "smtp" in error_msg:
            return {"success": False, "error": f"SMTP error: {str(e)}"}
        elif "timeout" in error_msg:
            return {"success": False, "error": "Connection timeout. Check your internet."}
        else:
            return {"success": False, "error": str(e)}

# ============================================
# EMAIL HTML TEMPLATE
# ============================================

def create_email_html(contract_name, results, risk_score, risk_level, stats, notes=""):
    """Create HTML email content"""
    
    risk_color = "#28a745" if risk_score <= 33 else "#ffc107" if risk_score <= 66 else "#dc3545"
    risk_emoji = "🟢" if risk_score <= 33 else "🟡" if risk_score <= 66 else "🔴"
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contract Audit Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
            line-height: 1.6;
        }}
        .header {{
            text-align: center;
            padding: 30px 20px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            color: #1a1a2e;
        }}
        .header p {{
            margin: 5px 0;
            color: #6c757d;
        }}
        .risk-score-container {{
            text-align: center;
            padding: 30px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin: 20px 0;
        }}
        .risk-score {{
            font-size: 60px;
            font-weight: bold;
            color: {risk_color};
        }}
        .risk-label {{
            font-size: 24px;
            color: {risk_color};
            font-weight: 600;
        }}
        .section {{
            margin: 25px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }}
        .section h2 {{
            margin-top: 0;
            color: #1a1a2e;
            font-size: 20px;
        }}
        .pass {{ color: #28a745; font-weight: bold; }}
        .fail {{ color: #dc3545; font-weight: bold; }}
        .high {{ color: #dc3545; font-weight: bold; }}
        .medium {{ color: #ffc107; font-weight: bold; }}
        .low {{ color: #28a745; font-weight: bold; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
            font-size: 14px;
        }}
        th, td {{
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        th {{
            background-color: #e9ecef;
            font-weight: 600;
            color: #495057;
        }}
        tr:hover {{
            background-color: #f1f3f5;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }}
        .stat-card {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .stat-number {{
            font-size: 28px;
            font-weight: bold;
            color: #1a1a2e;
        }}
        .stat-label {{
            font-size: 12px;
            color: #6c757d;
            margin-top: 5px;
        }}
        .priority-item {{
            background: white;
            padding: 12px 15px;
            margin: 8px 0;
            border-radius: 6px;
            border-left: 4px solid #ffc107;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .priority-high {{
            border-left-color: #dc3545;
        }}
        .priority-medium {{
            border-left-color: #ffc107;
        }}
        .priority-low {{
            border-left-color: #28a745;
        }}
        .notes {{
            background: #fff3cd;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #ffc107;
            margin: 15px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            border-top: 1px solid #dee2e6;
            color: #6c757d;
            font-size: 12px;
        }}
        @media print {{
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⚖️ Legal Contract Audit Report</h1>
        <p><strong>Contract:</strong> {contract_name}</p>
        <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
    </div>
    
    <div class="risk-score-container">
        <div class="risk-score">{risk_score}%</div>
        <div class="risk-label">{risk_emoji} {risk_level}</div>
    </div>
    
    <div class="section">
        <h2>📊 Summary</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{stats['total']}</div>
                <div class="stat-label">Total Rules</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color:#28a745;">{stats['passed']}</div>
                <div class="stat-label">✅ Passed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color:#dc3545;">{stats['failed']}</div>
                <div class="stat-label">❌ Failed</div>
            </div>
        </div>
        
        <div style="margin-top: 15px;">
            <span class="high">🔴 High Risk: {stats['high_risk']}</span> &nbsp;|&nbsp;
            <span class="medium">🟡 Medium Risk: {stats['medium_risk']}</span> &nbsp;|&nbsp;
            <span class="low">🟢 Low Risk: {stats['low_risk']}</span>
        </div>
    </div>
    
    <div class="section">
        <h2>📋 Detailed Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Rule</th>
                    <th>Status</th>
                    <th>Risk Level</th>
                    <th>Reason</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for item in results.get('results', []):
        status_class = "pass" if item['status'] == 'PASS' else "fail"
        risk_class = item.get('risk_level', 'low').lower()
        reason = item['reason'][:150] + "..." if len(item['reason']) > 150 else item['reason']
        html += f"""
                <tr>
                    <td><strong>{item['rule_id']}</strong></td>
                    <td class="{status_class}">{item['status']}</td>
                    <td class="{risk_class}">{item.get('risk_level', 'N/A')}</td>
                    <td>{reason}</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
    </div>
    """
    
    # Priority Actions
    failed_items = [r for r in results.get('results', []) if r['status'] == 'FAIL']
    priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
    failed_items.sort(key=lambda x: priority_order.get(x.get('risk_level', 'Low'), 3))
    
    if failed_items:
        html += """
    <div class="section">
        <h2>💡 Priority Actions</h2>
        """
        for item in failed_items[:5]:
            priority_class = "priority-high" if item.get('risk_level') == 'High' else "priority-medium" if item.get('risk_level') == 'Medium' else "priority-low"
            emoji = "🔴" if item.get('risk_level') == 'High' else "🟡" if item.get('risk_level') == 'Medium' else "🟢"
            html += f"""
        <div class="priority-item {priority_class}">
            <strong>{emoji} {item['rule_id']}</strong>: {item.get('suggestion', 'Review this clause')}
            <br><small style="color:#6c757d;">Impact: {item.get('impact', 'Potential legal risk')}</small>
        </div>
            """
        html += """
    </div>
        """
    
    # Notes
    if notes:
        html += f"""
    <div class="notes">
        <strong>📝 Additional Notes</strong>
        <p>{notes}</p>
    </div>
        """
    
    html += """
    <div class="footer">
        <p>Generated by <strong>Legal Contract AI Auditor</strong></p>
        <p>⚠️ This is an automated report for informational purposes only. Always consult a qualified attorney for legal advice.</p>
        <p style="font-size: 11px; color: #adb5bd;">Report ID: """ + datetime.now().strftime("%Y%m%d%H%M%S") + """</p>
    </div>
</body>
</html>
    """
    
    return html

# ============================================
# GENERATE HTML REPORT (As separate file)
# ============================================

def generate_html_report(contract_name, results, risk_score, risk_level, stats, notes=""):
    """
    Generate an HTML report string that can be saved or attached.
    """
    return create_email_html(contract_name, results, risk_score, risk_level, stats, notes)

# ============================================
# SEND SIMPLE TEXT EMAIL (Fallback)
# ============================================

def send_text_email(sender_email, sender_password, recipient_email, subject, body):
    """
    Simple text email fallback if HTML fails.
    """
    try:
        msg = MIMEText(body)
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return {"success": True, "message": "Email sent successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}