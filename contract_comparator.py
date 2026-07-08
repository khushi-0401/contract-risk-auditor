"""
Contract Comparator Module for Legal Contract AI Auditor
"""

import google.generativeai as genai
import json
import re
from config import GOOGLE_API_KEY

genai.configure(api_key=GOOGLE_API_KEY)

def compare_contracts(contract1_text, contract2_text):
    """Compare two contracts and highlight key differences"""
    
    if not contract1_text or not contract2_text:
        return {
            "error": "Both contracts are required",
            "differences": [],
            "overall_assessment": "Comparison failed"
        }
    
    try:
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        c1_preview = contract1_text[:30000]
        c2_preview = contract2_text[:30000]
        
        prompt = f"""
        Compare these two contracts and identify key differences.
        
        CONTRACT 1:
        {c1_preview}
        
        CONTRACT 2:
        {c2_preview}
        
        Return ONLY valid JSON:
        {{
            "differences": [
                {{
                    "clause": "Clause name",
                    "contract1": "What's in contract 1",
                    "contract2": "What's in contract 2",
                    "risk_impact": "Risk difference",
                    "recommendation": "What to change"
                }}
            ],
            "missing_in_contract1": ["Missing clause 1", "Missing clause 2"],
            "missing_in_contract2": ["Missing clause 1", "Missing clause 2"],
            "overall_assessment": "Overall comparison",
            "recommendation": "What to adopt"
        }}
        """
        
        response = model.generate_content(prompt)
        return parse_comparison_response(response.text)
        
    except Exception as e:
        return {"error": str(e), "differences": [], "overall_assessment": f"Error: {str(e)}"}

def parse_comparison_response(response_text):
    try:
        clean_text = response_text.strip()
        clean_text = re.sub(r'```json\s*', '', clean_text)
        clean_text = re.sub(r'```\s*', '', clean_text)
        
        json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        if json_match:
            clean_text = json_match.group()
        
        result = json.loads(clean_text)
        
        if 'differences' not in result:
            result['differences'] = []
        if 'missing_in_contract1' not in result:
            result['missing_in_contract1'] = []
        if 'missing_in_contract2' not in result:
            result['missing_in_contract2'] = []
        if 'overall_assessment' not in result:
            result['overall_assessment'] = "Comparison complete."
        if 'recommendation' not in result:
            result['recommendation'] = "Review differences."
        
        return result
        
    except json.JSONDecodeError:
        return {
            "error": "Failed to parse response",
            "differences": [],
            "overall_assessment": "Comparison failed"
        }