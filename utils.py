"""
Utility functions for the Legal Contract AI Auditor
"""

import streamlit as st
import pandas as pd
import plotly.express as px

def create_risk_chart(results):
    """Creates a bar chart showing risk distribution"""
    if not results:
        return None
    
    risk_counts = {"High": 0, "Medium": 0, "Low": 0}
    for item in results:
        if item['status'] == 'FAIL':
            level = item.get('risk_level', 'Low')
            risk_counts[level] = risk_counts.get(level, 0) + 1
    
    df = pd.DataFrame({
        'Risk Level': list(risk_counts.keys()),
        'Count': list(risk_counts.values())
    })
    
    color_map = {'High': '#ff4444', 'Medium': '#ffaa00', 'Low': '#44bb44'}
    
    fig = px.bar(
        df, 
        x='Risk Level', 
        y='Count',
        color='Risk Level',
        color_discrete_map=color_map,
        title='Distribution of Risks by Severity',
        text='Count'
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(showlegend=False, height=300)
    
    return fig

def format_risk_badge(risk_level):
    """Returns colored HTML badge for risk level"""
    colors = {'High': '#ff4444', 'Medium': '#ffaa00', 'Low': '#44bb44'}
    emojis = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢'}
    color = colors.get(risk_level, '#888888')
    emoji = emojis.get(risk_level, '⚪')
    return f"<span style='background-color:{color};color:white;padding:4px 12px;border-radius:12px;font-weight:bold;'>{emoji} {risk_level}</span>"

def generate_summary_stats(results):
    """Generates summary statistics from results"""
    if not results:
        return {'total': 0, 'passed': 0, 'failed': 0, 'high_risk': 0, 'medium_risk': 0, 'low_risk': 0}
    
    total = len(results)
    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = total - passed
    
    high_risk = sum(1 for r in results if r.get('risk_level') == 'High' and r['status'] == 'FAIL')
    medium_risk = sum(1 for r in results if r.get('risk_level') == 'Medium' and r['status'] == 'FAIL')
    low_risk = sum(1 for r in results if r.get('risk_level') == 'Low' and r['status'] == 'FAIL')
    
    return {'total': total, 'passed': passed, 'failed': failed, 'high_risk': high_risk, 'medium_risk': medium_risk, 'low_risk': low_risk}

def get_priority_actions(results):
    """Extracts priority actions from failed rules"""
    if not results:
        return []
    
    priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
    failed_items = [r for r in results if r['status'] == 'FAIL']
    failed_items.sort(key=lambda x: priority_order.get(x.get('risk_level', 'Low'), 3))
    
    actions = []
    for item in failed_items[:5]:
        actions.append({
            'rule_id': item['rule_id'],
            'risk_level': item.get('risk_level', 'Low'),
            'suggestion': item.get('suggestion', 'Review this clause'),
            'impact': item.get('impact', 'Potential legal risk')
        })
    
    return actions