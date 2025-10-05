import os
import sys
import uuid
from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from pyairtable import Api
from datetime import timedelta
import google.generativeai as genai

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get(
    'SESSION_SECRET', 'dev-secret-key-change-in-production')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY', '')
AIRTABLE_BASE_ID = os.environ.get('AIRTABLE_BASE_ID', '')
AIRTABLE_TABLE_NAME = os.environ.get('AIRTABLE_TABLE_NAME', 'Confessions')

required_env_vars = {
    'TWILIO_ACCOUNT_SID': TWILIO_ACCOUNT_SID,
    'TWILIO_AUTH_TOKEN': TWILIO_AUTH_TOKEN,
    'TWILIO_PHONE_NUMBER': TWILIO_PHONE_NUMBER,
    'GEMINI_API_KEY': GEMINI_API_KEY,
    'AIRTABLE_API_KEY': AIRTABLE_API_KEY,
    'AIRTABLE_BASE_ID': AIRTABLE_BASE_ID
}

missing_vars = [k for k, v in required_env_vars.items() if not v]
if missing_vars:
    error_msg = f"WARNING: Missing environment variables: {', '.join(missing_vars)}"
    print(error_msg, file=sys.stderr)

twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

airtable_api = None
confessions_table = None
responses_table = None
if AIRTABLE_API_KEY and AIRTABLE_BASE_ID:
    airtable_api = Api(AIRTABLE_API_KEY)
    confessions_table = airtable_api.table(AIRTABLE_BASE_ID,
                                           AIRTABLE_TABLE_NAME)
    responses_table = airtable_api.table(AIRTABLE_BASE_ID, 'Responses')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
else:
    gemini_model = None

print("=== mybrain@work SMS Service Starting ===")
print(f"Twilio phone number: {TWILIO_PHONE_NUMBER}")
print(f"Airtable base: {AIRTABLE_BASE_ID}")
print(f"Airtable tables: {AIRTABLE_TABLE_NAME}, Responses")
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


def get_response_from_table(trigger):
    """Fetch response text from Responses table by Trigger"""
    if not responses_table:
        return f"Response table not configured (trigger: {trigger})"

    try:
        records = responses_table.all(formula=f"{{Trigger}}='{trigger}'")
        if records:
            fields = records[0].get('fields', {})
            return fields.get('Prompt', f"No response found for {trigger}")
        return f"No response found for trigger: {trigger}"
    except Exception as e:
        print(f"Error fetching response from table: {str(e)}")
        return "System error. Please try again."


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


def get_past_wins(phone_number, conversation_id):
    """Fetch past user-reported wins from Airtable where step=win_prompt and matching conversation_id"""
    if not confessions_table:
        return []

    try:
        formula = f"AND({{phone}}='{phone_number}', {{step}}='win_prompt', {{conversation_id}}='{conversation_id}')"
        records = confessions_table.all(formula=formula)
        wins = []
        for record in records:
            fields = record.get('fields', {})
            win = fields.get('win', '').strip()
            if win and len(win) > 0:
                wins.append(win)
        return wins
    except Exception as e:
        print(f"Error fetching wins from Airtable: {str(e)}")
        return []


def get_user_state(phone_number):
    """Get the last state for a user from Airtable. Returns (step, last_confession, last_win, conversation_id, conversation_type, is_first_time)"""
    if not confessions_table:
        return "start", None, None, None, None, True

    try:
        records = confessions_table.all(formula=f"{{phone}}='{phone_number}'",
                                        sort=["-timestamp"])
        if records:
            fields = records[0].get('fields', {})
            step = fields.get('step', 'start')
            last_confession = fields.get('confession', '')
            last_win = fields.get('win', '')
            conversation_id = fields.get('conversation_id', None)
            conversation_type = fields.get('conversation_type', None)

            if step == "win_prompt" and last_win and len(last_win.strip()) > 0:
                return "start", last_confession, last_win, conversation_id, conversation_type, False

            return step, last_confession, last_win, conversation_id, conversation_type, False
        return "start", None, None, None, None, True
    except Exception as e:
        print(f"Error getting user state: {str(e)}")
        return "start", None, None, None, None, True


def delete_user_data(phone_number):
    """Delete all Confessions records for a phone number"""
    if not confessions_table:
        print("ERROR: Airtable Confessions table not configured - skipping delete")
        return False
    
    try:
        records = confessions_table.all(formula=f"{{phone}}='{phone_number}'")
        if records:
            for record in records:
                confessions_table.delete(record['id'])
            print(f"SUCCESS: Deleted {len(records)} records for {phone_number}")
            return True
        else:
            print(f"No records found for {phone_number}")
            return True
    except Exception as e:
        print(f"ERROR deleting user data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def save_to_airtable(phone, confession, win, step="start", conversation_id=None, conversation_type=None, gemini_prompt=None, gemini_response=None):
    """Save conversation to Airtable (timestamp is auto-computed by Airtable)"""
    if not confessions_table:
        print(
            "ERROR: Airtable Confessions table not configured - skipping save")
        return False
    try:
        record = {
            "phone": phone,
            "confession": confession,
            "win": win,
            "step": step
        }
        
        if conversation_id:
            record["conversation_id"] = conversation_id
        if conversation_type:
            record["conversation_type"] = conversation_type
        if gemini_prompt:
            record["gemini_prompt"] = gemini_prompt
        if gemini_response:
            record["gemini_response"] = gemini_response
            
        print(
            f"Attempting to save to Airtable: phone={phone}, step={step}, conversation_id={conversation_id}, conversation_type={conversation_type}, confession={confession[:50] if confession else 'empty'}..., win={win[:50] if win else 'empty'}, gemini_prompt={'YES' if gemini_prompt else 'NO'}, gemini_response={'YES' if gemini_response else 'NO'}"
        )
        result = confessions_table.create(record)
        print(
            f"SUCCESS: Saved to Airtable with record ID: {result.get('id', 'unknown')}"
        )
        return True
    except Exception as e:
        print(f"ERROR saving to Airtable: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


@app.route('/sms', methods=['POST'])
def sms_reply():
    """Handle incoming SMS messages from Twilio"""
    if missing_vars:
        return jsonify({
            "error": "Service not configured",
            "missing": missing_vars
        }), 500

    try:
        incoming_msg = request.form.get('Body', '').strip().upper()
        incoming_msg_original = request.form.get('Body', '').strip()
        from_number = request.form.get('From', '')
        to_number = request.form.get('To', '')

        print(f"Received SMS from {from_number}: {incoming_msg}")

        current_step, last_confession, last_win, conversation_id, conversation_type, is_first_time = get_user_state(from_number)
        print(
            f"Current state: step={current_step}, conversation_id={conversation_id}, conversation_type={conversation_type}, is_first_time={is_first_time}"
        )

        response_text = ""
        new_step = current_step
        confession_to_save = incoming_msg_original
        win_to_save = ""
        new_conversation_id = conversation_id
        new_conversation_type = conversation_type
        skip_save = False

        # GLOBAL - Check for STOP (works from any state)
        if incoming_msg == "STOP":
            response_text = get_response_from_table("STOP")
            delete_user_data(from_number)
            skip_save = True  # Don't save a new record after deletion
        
        # START STATE - Check for OUCH trigger
        elif incoming_msg == "OUCH":
            # Generate new conversation ID
            new_conversation_id = str(uuid.uuid4())
            new_conversation_type = None
            
            if is_first_time:
                # First-time user: show opt-in message
                response_text = get_response_from_table("SUBSCRIBE")
            else:
                # Returning user: skip opt-in, go straight to trigger selection
                response_text = "Welcome back! Reply:\n1. Co-worker\n2. Boss\n3. Self-doubt\n\nOr HELP/STOP"
            
            new_step = "opt_in"

        # OPT-IN STATE
        elif current_step == "opt_in":
            if incoming_msg == "HELP":
                response_text = get_response_from_table("HELP")
                new_step = "start"
            elif incoming_msg in ["1", "2", "3"]:
                trigger_map = {"1": "Co-worker", "2": "Boss", "3": "Self-doubt"}
                trigger = trigger_map[incoming_msg]
                new_conversation_type = trigger
                response_text = get_response_from_table(trigger)
                new_step = "confess"
                confession_to_save = trigger
            else:
                response_text = "Please text 1, 2, or 3 for Co-worker, Boss, or self-doubt, or HELP/STOP"

        # CONFESS STATE
        elif current_step == "confess":
            classification = classify_message(incoming_msg_original)

            if classification == "EMERGENCY":
                response_text = get_response_from_table("EMERGENCY")
                new_step = "start"
            elif classification == "COACHING":
                response_text = get_response_from_table(
                    "COACHING_CONFIRM_PROMPT")
                new_step = "coaching_confirm"
            else:  # NORMAL
                past_wins = get_past_wins(from_number, new_conversation_id)
                last_win_text = past_wins[-1] if past_wins else "none"

                trigger_context = new_conversation_type.lower(
                ) if new_conversation_type else "workplace"
                prompt = f"User said: {incoming_msg_original}. Context: {trigger_context} issue. Past win: {last_win_text}. Reply in 10 calm words, address workplace frustration with evidence."
                ai_response = query_gemini(prompt)
                response_text = f"{ai_response}\n\nText a win?"
                win_to_save = ""
                new_step = "win_prompt"

        # COACHING_CONFIRM STATE - Handle YES response
        elif current_step == "coaching_confirm":
            if incoming_msg == "YES":
                response_text = get_response_from_table("COACHING_CONFIRM_YES")
            else:
                response_text = get_response_from_table("COACHING_CONFIRM_NO")
            new_step = "start"

        # WIN_PROMPT STATE
        elif current_step == "win_prompt":
            response_text = get_response_from_table("WIN_PROMPT")
            confession_to_save = ""
            win_to_save = incoming_msg_original
            new_step = "win_prompt"

        # DEFAULT - If no state matches, prompt to start
        else:
            response_text = get_response_from_table("DEFAULT")
            new_step = "start"

        # Save to Airtable (unless skip_save is True)
        if not skip_save:
            save_to_airtable(phone=from_number,
                             confession=confession_to_save,
                             win=win_to_save,
                             step=new_step,
                             conversation_id=new_conversation_id,
                             conversation_type=new_conversation_type)

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
