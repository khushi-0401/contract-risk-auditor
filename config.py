"""
Configuration settings for the Legal Contract AI Auditor
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================
# API CONFIGURATION
# ============================================

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not found in environment variables!")

# ============================================
# MODEL CONFIGURATION
# ============================================

GEMINI_MODELS = {
    'chat': 'models/gemini-2.5-flash',
    'audit': 'models/gemini-2.5-flash',
    'compare': 'models/gemini-2.5-flash',
}

MAX_CONTRACT_LENGTH = int(os.getenv('MAX_CONTRACT_LENGTH', 50000))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
RETRY_DELAY = int(os.getenv('RETRY_DELAY', 2))

# ============================================
# APP CONFIGURATION
# ============================================

APP_NAME = "Legal Contract AI Auditor"
APP_VERSION = "3.0.0"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB