import os
import sys
from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import requests
from pyairtable import Api
from datetime import datetime

app = Flask(__name__)

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')
HUGGINGFACE_API_KEY = os.environ.get('HUGGINGFACE_API_KEY', '')
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY', '')
AIRTABLE_BASE_ID = os.environ.get('AIRTABLE_BASE_ID', '')
AIRTABLE_TABLE_NAME = os.environ.get('AIRTABLE_TABLE_NAME', '')

required_env_vars = {
    'TWILIO_ACCOUNT_SID': TWILIO_ACCOUNT_SID,
    'TWILIO_AUTH_TOKEN': TWILIO_AUTH_TOKEN,
    'TWILIO_PHONE_NUMBER': TWILIO_PHONE_NUMBER,
    'HUGGINGFACE_API_KEY': HUGGINGFACE_API_KEY,
    'AIRTABLE_API_KEY': AIRTABLE_API_KEY,
    'AIRTABLE_BASE_ID': AIRTABLE_BASE_ID,
    'AIRTABLE_TABLE_NAME': AIRTABLE_TABLE_NAME
}

missing_vars = [k for k, v in required_env_vars.items() if not v]
if missing_vars:
    error_msg = f"WARNING: Missing environment variables: {', '.join(missing_vars)}"
    print(error_msg, file=sys.stderr)

airtable_api = None
airtable_table = None
if AIRTABLE_API_KEY and AIRTABLE_BASE_ID and AIRTABLE_TABLE_NAME:
    airtable_api = Api(AIRTABLE_API_KEY)
    airtable_table = airtable_api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/v1/chat/completions"

print("=== mybrain@work SMS Service Starting ===")
print(f"Twilio phone number: {TWILIO_PHONE_NUMBER}")
print(f"Airtable base: {AIRTABLE_BASE_ID}")
print(f"Airtable table: {AIRTABLE_TABLE_NAME}")
print("All environment variables validated successfully")

def query_huggingface(prompt):
    """Query Hugging Face LLM for a response using OpenAI-compatible API"""
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "meta-llama/Llama-3.2-3B-Instruct",
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant responding to text messages. Keep your responses brief, friendly, and conversational."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 150,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(HUGGINGFACE_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content'].strip()
        return "I'm sorry, I couldn't generate a response at this time."
    except Exception as e:
        print(f"Error querying Hugging Face: {str(e)}")
        if 'response' in locals():
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text[:500]}")
        return "I'm having trouble thinking right now. Please try again later."

def save_to_airtable(from_number, to_number, message, response, timestamp):
    """Save conversation to Airtable"""
    if not airtable_table:
        print("Airtable not configured - skipping save")
        return
    try:
        record = {
            "From": from_number,
            "To": to_number,
            "Incoming Message": message,
            "AI Response": response,
            "Timestamp": timestamp
        }
        airtable_table.create(record)
        print(f"Saved to Airtable: {from_number} -> {message[:50]}...")
    except Exception as e:
        print(f"Error saving to Airtable: {str(e)}")

@app.route('/sms', methods=['POST'])
def sms_reply():
    """Handle incoming SMS messages from Twilio"""
    if missing_vars:
        return jsonify({"error": "Service not configured", "missing": missing_vars}), 500
    
    try:
        incoming_msg = request.form.get('Body', '').strip()
        from_number = request.form.get('From', '')
        to_number = request.form.get('To', '')
        timestamp = datetime.now().isoformat()
        
        print(f"Received SMS from {from_number}: {incoming_msg}")
        
        prompt = f"You are a helpful AI assistant. A user sent you this message: '{incoming_msg}'. Provide a brief, friendly, and helpful response."
        
        ai_response = query_huggingface(prompt)
        
        save_to_airtable(from_number, to_number, incoming_msg, ai_response, timestamp)
        
        resp = MessagingResponse()
        resp.message(ai_response)
        
        return str(resp), 200, {'Content-Type': 'text/xml'}
    
    except Exception as e:
        print(f"Error processing SMS: {str(e)}")
        resp = MessagingResponse()
        resp.message("Sorry, I encountered an error processing your message.")
        return str(resp), 200, {'Content-Type': 'text/xml'}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "mybrain@work SMS service"
    }), 200

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        "message": "mybrain@work SMS service is running",
        "webhook_endpoint": "/sms"
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
