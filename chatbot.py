"""
Chatbot Module for Legal Contract AI Auditor
"""

import google.generativeai as genai
from config import GOOGLE_API_KEY

genai.configure(api_key=GOOGLE_API_KEY)

class ContractChatbot:
    """AI Chatbot for interacting with contracts"""
    
    def __init__(self, contract_text=None):
        self.contract_text = contract_text
        self.chat_history = []
        self.model = genai.GenerativeModel('models/gemini-2.5-flash')
        self.conversation = None
        
        if contract_text:
            self.start_conversation(contract_text)
    
    def start_conversation(self, contract_text):
        self.contract_text = contract_text
        
        system_prompt = f"""
        You are a Legal Contract Assistant. Answer questions based on this contract.
        
        CONTRACT:
        {contract_text[:40000]}
        
        Rules:
        1. Answer based ONLY on the contract
        2. If not found, say "The contract does not mention this"
        3. Provide clear, concise answers
        """
        
        self.conversation = self.model.start_chat(history=[])
        self.conversation.send_message(system_prompt)
    
    def ask(self, question):
        if not self.conversation:
            return "Please load a contract first."
        
        try:
            response = self.conversation.send_message(question)
            self.chat_history.append({"role": "user", "content": question})
            self.chat_history.append({"role": "assistant", "content": response.text})
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_history(self):
        return self.chat_history
    
    def clear_history(self):
        self.chat_history = []
        if self.contract_text:
            self.start_conversation(self.contract_text)