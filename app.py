import os
import sys
from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import requests
from pyairtable import Api
from datetime import datetime

app = Flask(__name__)

required_env_vars = [
    'TWILIO_ACCOUNT_SID',
    'TWILIO_AUTH_TOKEN',
    'TWILIO_PHONE_NUMBER',
    'HUGGINGFACE_API_KEY',
    'AIRTABLE_API_KEY',
    'AIRTABLE_BASE_ID',
    'AIRTABLE_TABLE_NAME'
]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    error_msg = f"ERROR: Missing required environment variables: {', '.join(missing_vars)}"
    print(error_msg, file=sys.stderr)
    sys.exit(1)

TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
TWILIO_PHONE_NUMBER = os.environ['TWILIO_PHONE_NUMBER']
HUGGINGFACE_API_KEY = os.environ['HUGGINGFACE_API_KEY']
AIRTABLE_API_KEY = os.environ['AIRTABLE_API_KEY']
AIRTABLE_BASE_ID = os.environ['AIRTABLE_BASE_ID']
AIRTABLE_TABLE_NAME = os.environ['AIRTABLE_TABLE_NAME']

airtable_api = Api(AIRTABLE_API_KEY)
airtable_table = airtable_api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

print("=== FMC: Fraud Meets Clarity SMS Service Starting ===")
print(f"Twilio phone number: {TWILIO_PHONE_NUMBER}")
print(f"Airtable base: {AIRTABLE_BASE_ID}")
print(f"Airtable table: {AIRTABLE_TABLE_NAME}")
print("All environment variables validated successfully")

def query_huggingface(prompt):
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 250, "temperature": 0.7, "top_p": 0.9, "return_full_text": False}
    }
    try:
        response = requests.post(HUGGINGFACE_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result[0].get('generated_text', '').strip() if isinstance(result, list) and len(result) > 0 else "Error generating response."
    except Exception as e:
        print(f"Error querying Hugging Face: {str(e)}")
        return "I'm having trouble. Try again later."

def save_to_airtable(from_number, to_number, message, response, timestamp):
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
    try:
        incoming_msg = request.form.get('Body', '').strip().upper()
        from_number = request.form.get('From', '')
        to_number = request.form.get('To', '')
        timestamp = datetime.now().isoformat()
        print(f"Received SMS from {from_number}: {incoming_msg}")

        resp = MessagingResponse()
        msg = resp.message()

        user_state = {k: eval(v) for k, v in request.cookies.items()} if request.cookies else {}
        user_state = user_state.get(from_number, {"step": "start", "last_confession": "", "last_win": ""})

        if user_state["step"] == "start" and incoming_msg == "OUCH":
            msg.body("Welcome to Neuvero.ai - you’re opted into career tips via text. Text HELP for support or STOP to unsubscribe. What made you say OUCH - Co-worker, Boss or self-doubt? Text 1, 2 or 3")
            user_state["step"] = "opt_in"

        elif user_state["step"] == "opt_in":
            if incoming_msg in ["1", "2", "3"]:
                options = {"1": "Co-worker", "2": "Boss", "3": "Self-doubt"}
                msg.body(f"{options[incoming_msg]} sting? What’s the exact lie? Two words max.")
                user_state["step"] = "confess"
            elif incoming_msg == "HELP":
                msg.body("Text OUCH for confidence boosts or STOP to end.")
                user_state["step"] = "start"
            elif incoming_msg == "STOP":
                msg.body("You’re unsubscribed. Text OUCH to restart.")
                user_state["step"] = "start"
            else:
                msg.body("Text 1, 2, or 3 for Co-worker, Boss, or self-doubt, or HELP/STOP")

        elif user_state["step"] == "confess":
            classify_prompt = f"Classify in ONE word: EMERGENCY, NORMAL, or COACHING.\nEMERGENCY: suicide, self-harm.\nCOACHING: advice, 'what do I do'.\nNORMAL: venting, doubt.\nText: {incoming_msg}"
            category = query_huggingface(classify_prompt).strip().upper()

            if category == "EMERGENCY":
                msg.body("That sounds urgent. Text 988 for free crisis support now.")
            elif category == "COACHING":
                msg.body("Need real talk? Text YES for a 10-min call: [go.neuvero.ai/book-floyd]")
            else:  # NORMAL
                records = airtable_table.all(formula=f"{{From}}='{from_number}'")
                last_win = next((r['fields'].get('Win') for r in records if r['fields'].get('Win')), "")
                prompt = f"User said: {incoming_msg}. Past win: {last_win or 'none'}. Reply in 10 calm words, counter doubt with evidence."
                ai_response = query_huggingface(prompt)
                msg.body(ai_response + " Text a win?")
                user_state["last_confession"] = incoming_msg

            save_to_airtable(from_number, to_number, incoming_msg, msg.body[0].text if msg.body else "", timestamp)
            if "win" in msg.body[0].text.lower():
                user_state["step"] = "win_prompt"
            else:
                user_state["step"] = "start"

        resp.set_cookie(from_number, str(user_state), max_age=3600)  # 1-hour session
        return str(resp), 200, {'Content-Type': 'text/xml'}

    except Exception as e:
        print(f"Error processing SMS: {str(e)}")
        resp = MessagingResponse()
        resp.message("Sorry, I encountered an error.")
        return str(resp), 200, {'Content-Type': 'text/xml'}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "FMC SMS Service"}), 200

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "FMC SMS Service is running", "webhook_endpoint": "/sms"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)