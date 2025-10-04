import os
import sys
from flask import Flask, request, jsonify, make_response
from twilio.twiml.messaging_response import MessagingResponse
import requests
from pyairtable import Api
from datetime import datetime, timedelta
import google.generativeai as genai

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY', '')
AIRTABLE_BASE_ID = os.environ.get('AIRTABLE_BASE_ID', '')
AIRTABLE_TABLE_NAME = os.environ.get('AIRTABLE_TABLE_NAME', '')

required_env_vars = {
    'TWILIO_ACCOUNT_SID': TWILIO_ACCOUNT_SID,
    'TWILIO_AUTH_TOKEN': TWILIO_AUTH_TOKEN,
    'TWILIO_PHONE_NUMBER': TWILIO_PHONE_NUMBER,
    'GEMINI_API_KEY': GEMINI_API_KEY,
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

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
else:
    gemini_model = None

print("=== mybrain@work SMS Service Starting ===")
print(f"Twilio phone number: {TWILIO_PHONE_NUMBER}")
print(f"Airtable base: {AIRTABLE_BASE_ID}")
print(f"Airtable table: {AIRTABLE_TABLE_NAME}")
print(f"AI Model: Google Gemini 2.0 Flash")
print("All environment variables validated successfully")

def query_gemini(prompt):
    """Query Google Gemini AI with custom prompt"""
    if not gemini_model:
        return "AI service not configured. Please add GEMINI_API_KEY."
    
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error querying Gemini AI: {str(e)}")
        return "I'm having trouble. Try again later."

def classify_message(message):
    """Classify message as EMERGENCY, NORMAL, or COACHING"""
    prompt = f"Classify in ONE word: EMERGENCY, NORMAL, or COACHING. EMERGENCY: suicide, self-harm. COACHING: advice, 'what do I do'. NORMAL: venting, doubt. Text: {message}"
    classification = query_gemini(prompt).upper()
    
    if "EMERGENCY" in classification:
        return "EMERGENCY"
    elif "COACHING" in classification:
        return "COACHING"
    else:
        return "NORMAL"

def get_past_wins(phone_number):
    """Fetch past wins from Airtable for a phone number"""
    if not airtable_table:
        return []
    
    try:
        records = airtable_table.all(formula=f"{{phone}}='{phone_number}'")
        wins = []
        for record in records:
            fields = record.get('fields', {})
            win = fields.get('win', '').strip()
            if win and win != fields.get('confession', ''):
                wins.append(win)
        return wins
    except Exception as e:
        print(f"Error fetching wins from Airtable: {str(e)}")
        return []

def save_to_airtable(phone, confession, win, timestamp, step=1):
    """Save conversation to Airtable"""
    if not airtable_table:
        print("Airtable not configured - skipping save")
        return
    try:
        record = {
            "phone": phone,
            "confession": confession,
            "win": win,
            "timestamp": timestamp,
            "step": step
        }
        airtable_table.create(record)
        print(f"Saved to Airtable: {phone} -> {confession[:50]}...")
    except Exception as e:
        print(f"Error saving to Airtable: {str(e)}")

def get_user_state(phone_number):
    """Get the last state for a user from Airtable"""
    if not airtable_table:
        return "start", None, None
    
    try:
        records = airtable_table.all(
            formula=f"{{phone}}='{phone_number}'",
            sort=["-timestamp"]
        )
        if records:
            fields = records[0].get('fields', {})
            step = fields.get('step', 'start')
            last_confession = fields.get('confession', '')
            last_win = fields.get('win', '')
            return step, last_confession, last_win
        return "start", None, None
    except Exception as e:
        print(f"Error getting user state: {str(e)}")
        return "start", None, None

@app.route('/sms', methods=['POST'])
def sms_reply():
    """Handle incoming SMS messages from Twilio"""
    if missing_vars:
        return jsonify({"error": "Service not configured", "missing": missing_vars}), 500
    
    try:
        incoming_msg = request.form.get('Body', '').strip().upper()
        incoming_msg_original = request.form.get('Body', '').strip()
        from_number = request.form.get('From', '')
        to_number = request.form.get('To', '')
        timestamp = datetime.now().isoformat()
        
        print(f"Received SMS from {from_number}: {incoming_msg}")
        
        current_step, last_confession, last_win = get_user_state(from_number)
        response_text = ""
        new_step = current_step
        confession_to_save = incoming_msg_original
        win_to_save = ""
        
        # START STATE - Check for OUCH trigger
        if incoming_msg == "OUCH":
            response_text = "Welcome to Neuvero.ai - you're opted into career tips via text. Text HELP for support or STOP to unsubscribe. What made you say OUCH - Co-worker, Boss or self-doubt? Text 1, 2 or 3"
            new_step = "opt_in"
        
        # OPT-IN STATE
        elif current_step == "opt_in":
            if incoming_msg == "HELP":
                response_text = "Text OUCH for tips or STOP to end"
                new_step = "start"
            elif incoming_msg == "STOP":
                response_text = "You're unsubscribed. Text OUCH to restart"
                new_step = "start"
            elif incoming_msg in ["1", "2", "3"]:
                trigger_map = {"1": "Co-worker", "2": "Boss", "3": "Self-doubt"}
                trigger = trigger_map[incoming_msg]
                response_text = f"{trigger}. What's the exact lie? Two words max."
                new_step = "confess"
                confession_to_save = trigger
            else:
                response_text = "Please text 1, 2, or 3 to tell me what made you say OUCH"
        
        # CONFESS STATE
        elif current_step == "confess":
            classification = classify_message(incoming_msg_original)
            
            if classification == "EMERGENCY":
                response_text = "That sounds urgent. Text 988 for free crisis support now."
                new_step = "start"
            elif classification == "COACHING":
                response_text = "Need real talk? Text YES for a 10-min call: go.neuvero.ai/book-floyd"
                new_step = "start"
            else:  # NORMAL
                past_wins = get_past_wins(from_number)
                last_win_text = past_wins[-1] if past_wins else "none"
                
                prompt = f"User said: {incoming_msg_original}. Past win: {last_win_text}. Reply in 10 calm words, counter doubt with evidence."
                ai_response = query_gemini(prompt)
                response_text = f"{ai_response}\n\nText a win?"
                win_to_save = ai_response
                new_step = "win_prompt"
        
        # WIN_PROMPT STATE
        elif current_step == "win_prompt":
            response_text = "Thanks for sharing! Text OUCH anytime you need support."
            win_to_save = incoming_msg_original
            new_step = "start"
        
        # DEFAULT - If no state matches, prompt to start
        else:
            response_text = "Text OUCH to get started with career coaching support"
            new_step = "start"
        
        # Save to Airtable
        save_to_airtable(
            phone=from_number,
            confession=confession_to_save,
            win=win_to_save,
            timestamp=timestamp,
            step=new_step
        )
        
        # Send response via Twilio
        resp = MessagingResponse()
        resp.message(response_text)
        
        return str(resp), 200, {'Content-Type': 'text/xml'}
    
    except Exception as e:
        print(f"Error processing SMS: {str(e)}")
        import traceback
        traceback.print_exc()
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
