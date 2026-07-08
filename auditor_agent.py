"""
AI Auditor Agent for Legal Contract Analysis
"""

import google.generativeai as genai
import json
import re
import time
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from config import GOOGLE_API_KEY, GEMINI_MODELS, MAX_CONTRACT_LENGTH, MAX_RETRIES, RETRY_DELAY

# Configure the API
genai.configure(api_key=GOOGLE_API_KEY)

# ============================================
# MAIN AUDIT FUNCTION
# ============================================

def audit_contract(contract_text, rules):
    """Sends contract to Gemini AI for risk assessment"""
    
    if not contract_text or not contract_text.strip():
        return {"results": [], "executive_summary": "❌ No contract text provided."}
    
    if not rules:
        return {"results": [], "executive_summary": "❌ No risk rules provided."}
    
    try:
        model = _get_working_model()
        if not model:
            return {"results": [], "executive_summary": "❌ No working model found."}
        
        rules_text = _format_rules_for_prompt(rules)
        contract_preview = contract_text[:MAX_CONTRACT_LENGTH]
        prompt = _create_audit_prompt(rules_text, contract_preview)
        response = _get_ai_response_with_retry(model, prompt)
        result = _parse_ai_response(response.text)
        
        result['_metadata'] = {
            'model_used': model.model_name,
            'contract_length': len(contract_text),
            'analyzed_length': len(contract_preview),
            'rules_checked': len(rules)
        }
        
        return result
        
    except Exception as e:
        return {"results": [], "executive_summary": f"⚠️ Error: {str(e)}"}

# ============================================
# MODEL SELECTION
# ============================================

def _get_working_model():
    """Try different models until one works"""
    models_to_try = [
        'models/gemini-2.5-flash',
        'models/gemini-2.0-flash',
        'models/gemini-flash-latest',
    ]
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            test_response = model.generate_content("Test")
            if test_response and test_response.text:
                return model
        except:
            continue
    
    return None

# ============================================
# HELPER FUNCTIONS
# ============================================

def _format_rules_for_prompt(rules):
    rules_text = ""
    for rule in rules:
        rules_text += f"""
Rule {rule['id']}: {rule['description']}
  - Category: {rule.get('category', 'General')}
  - Severity: {rule.get('severity', 'Medium')}
  - What to check: {rule.get('prompt', 'Check this clause')}
  - Risk explanation: {rule.get('risk_explanation', 'Potential risk')}
  - Suggested fix: {rule.get('suggestion_template', 'Review and revise')}
\n"""
    return rules_text

def _create_audit_prompt(rules_text, contract_text):
    return f"""You are a Senior Legal Contract Auditor. Analyze the contract based on these rules.

RULES:
{rules_text}

CONTRACT:
{contract_text}

Return ONLY valid JSON in this format:
{{
  "results": [
    {{
      "rule_id": "R001",
      "status": "PASS or FAIL",
      "risk_level": "Low/Medium/High",
      "reason": "Detailed explanation (2-3 sentences)",
      "suggestion": "Actionable fix (or null if PASS)",
      "impact": "What could happen (2-3 sentences)"
    }}
  ],
  "executive_summary": "2-3 sentence overview"
}}
"""

def _get_ai_response_with_retry(model, prompt, max_retries=MAX_RETRIES):
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            if response and response.text:
                return response
            raise ValueError("Empty response")
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            raise Exception(f"All attempts failed: {str(e)}")

def _parse_ai_response(response_text):
    try:
        clean_text = response_text.strip()
        clean_text = re.sub(r'```json\s*', '', clean_text)
        clean_text = re.sub(r'```\s*', '', clean_text)
        
        json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        if json_match:
            clean_text = json_match.group()
        
        result = json.loads(clean_text)
        
        if 'results' not in result:
            result['results'] = []
        if 'executive_summary' not in result:
            result['executive_summary'] = "Analysis complete."
        
        for item in result['results']:
            if 'rule_id' not in item:
                item['rule_id'] = 'Unknown'
            if 'status' not in item:
                item['status'] = 'FAIL'
            if 'risk_level' not in item:
                item['risk_level'] = 'Medium'
            if 'reason' not in item:
                item['reason'] = 'No reason provided'
            if 'suggestion' not in item:
                item['suggestion'] = 'Review this clause'
            if 'impact' not in item:
                item['impact'] = 'Potential legal risk'
        
        return result
        
    except json.JSONDecodeError:
        return {"results": [], "executive_summary": "⚠️ Error parsing AI response."}
    except Exception as e:
        return {"results": [], "executive_summary": f"⚠️ Error: {str(e)}"}

# ============================================
# RISK SCORE CALCULATION
# ============================================

def calculate_risk_score(results):
    if not results or len(results) == 0:
        return 0, "🟢 Low Risk", "No risks identified"
    
    severity_weights = {"High": 3, "Medium": 2, "Low": 1}
    total_risk_points = 0
    max_possible_points = 0
    failed_count = 0
    high_count = 0
    medium_count = 0
    low_count = 0
    
    for item in results:
        risk_level = item.get('risk_level', 'Low')
        weight = severity_weights.get(risk_level, 1)
        max_possible_points += weight
        
        if item['status'] == 'FAIL':
            total_risk_points += weight
            failed_count += 1
            if risk_level == 'High':
                high_count += 1
            elif risk_level == 'Medium':
                medium_count += 1
            else:
                low_count += 1
    
    if max_possible_points == 0:
        return 0, "🟢 Low Risk", "No risks identified"
    
    risk_percentage = round((total_risk_points / max_possible_points) * 100)
    
    if risk_percentage == 0:
        level = "🟢 Low Risk"
        summary = "✅ All clauses are compliant."
    elif risk_percentage <= 33:
        level = "🟡 Medium Risk"
        summary = f"⚠️ {failed_count} rule(s) failed ({high_count} high, {medium_count} medium, {low_count} low)."
    else:
        level = "🔴 High Risk"
        summary = f"🔴 {failed_count} rule(s) failed ({high_count} high, {medium_count} medium, {low_count} low)."
    
    return risk_percentage, level, summary