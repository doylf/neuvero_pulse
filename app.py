import os
import sys
import uuid
from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from pyairtable import Api
from datetime import datetime
import google.generativeai as genai

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')

# Environment Variables
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

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN else None
airtable_api = Api(AIRTABLE_API_KEY) if AIRTABLE_API_KEY and AIRTABLE_BASE_ID else None
confessions_table = airtable_api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME) if airtable_api else None
state_transitions_table = airtable_api.table(AIRTABLE_BASE_ID, 'StateTransitions') if airtable_api else None
responses_table = airtable_api.table(AIRTABLE_BASE_ID, 'Responses') if airtable_api else None

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
else:
    gemini_model = None

print("=== mybrain@work SMS Service Starting ===")
print(f"Twilio phone number: {TWILIO_PHONE_NUMBER}")
print(f"Airtable base: {AIRTABLE_BASE_ID}")
print(f"Airtable tables: {AIRTABLE_TABLE_NAME}, StateTransitions, Responses")
print(f"AI Model: Google Gemini 2.0 Flash")
print("All environment variables validated successfully")

def query_gemini(prompt):
    if not gemini_model:
        return "AI service not configured. Please add GEMINI_API_KEY."
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error querying Gemini AI: {str(e)}")
        return "I'm having trouble. Try again later."

def get_response_from_table(trigger):
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

def get_state_transition(current_state, input_trigger, classification=None):
    """Query StateTransitions table to determine next state"""
    if not state_transitions_table:
        return None, None
    try:
        # Priority 1: Exact match with classification condition (if classification provided)
        if classification:
            formula = f"AND({{CurrentState}}='{current_state}', {{InputTrigger}}='{input_trigger}', {{Condition}}='classification={classification}')"
            records = state_transitions_table.all(formula=formula, sort=["-Weight"])
            if records:
                fields = records[0].get('fields', {})
                return fields.get('NextState', current_state), fields.get('ActionTrigger', 'DEFAULT')
        
        # Priority 2: Exact match without classification condition (standard transitions)
        formula = f"AND({{CurrentState}}='{current_state}', {{InputTrigger}}='{input_trigger}')"
        records = state_transitions_table.all(formula=formula, sort=["-Weight"])
        if records:
            fields = records[0].get('fields', {})
            return fields.get('NextState', current_state), fields.get('ActionTrigger', 'DEFAULT')
        
        # Priority 3: Wildcard with classification (if classification provided)
        if classification:
            formula = f"AND({{CurrentState}}='{current_state}', {{InputTrigger}}='*', {{Condition}}='classification={classification}')"
            records = state_transitions_table.all(formula=formula, sort=["-Weight"])
            if records:
                fields = records[0].get('fields', {})
                return fields.get('NextState', current_state), fields.get('ActionTrigger', 'DEFAULT')
        
        # Priority 4: Wildcard without classification (final fallback)
        formula = f"AND({{CurrentState}}='{current_state}', {{InputTrigger}}='*')"
        records = state_transitions_table.all(formula=formula, sort=["-Weight"])
        if records:
            fields = records[0].get('fields', {})
            return fields.get('NextState', current_state), fields.get('ActionTrigger', 'DEFAULT')
        
        return current_state, 'DEFAULT'
    except Exception as e:
        print(f"Error fetching state transition: {str(e)}")
        return current_state, 'DEFAULT'

def get_past_wins(phone_number, conversation_id):
    """Fetch ALL past wins for a phone number from Airtable (not conversation-scoped)"""
    if not confessions_table:
        return []
    try:
        formula = f"AND({{phone}}='{phone_number}', {{win}}!='')"
        records = confessions_table.all(formula=formula, sort=["timestamp"])
        wins = [record['fields'].get('win', '').strip() for record in records if record['fields'].get('win', '').strip()]
        return wins
    except Exception as e:
        print(f"Error fetching past wins: {str(e)}")
        return []

def get_user_state(phone_number):
    if not confessions_table:
        return "start", None, None, None, None, True
    try:
        records = confessions_table.all(formula=f"{{phone}}='{phone_number}'", sort=["-timestamp"])
        if records:
            fields = records[0].get('fields', {})
            step = fields.get('step', 'start')
            last_confession = fields.get('confession', '')
            last_win = fields.get('win', '')
            conversation_id = fields.get('conversation_id', None)
            conversation_type = fields.get('conversation_type', None)
            
            # Legacy: Map old win_prompt state to start for backward compatibility
            if step == 'win_prompt':
                step = 'start'
            
            return step, last_confession, last_win, conversation_id, conversation_type, False
        return "start", None, None, None, None, True
    except Exception as e:
        print(f"Error getting user state: {str(e)}")
        return "start", None, None, None, None, True

def delete_user_data(phone_number):
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
        return False

def save_to_airtable(phone, confession, win, step, conversation_id, conversation_type, gemini_prompt=None, gemini_response=None):
    if not confessions_table:
        print("ERROR: Airtable Confessions table not configured - skipping save")
        return False
    try:
        record = {
            "phone": phone,
            "confession": confession,
            "win": win,
            "step": step,
            "conversation_id": conversation_id,
            "conversation_type": conversation_type
        }
        if gemini_prompt:
            record["gemini_prompt"] = gemini_prompt
        if gemini_response:
            record["gemini_response"] = gemini_response
        print(f"Attempting to save to Airtable: {record}")
        result = confessions_table.create(record)
        print(f"SUCCESS: Saved to Airtable with record ID: {result.get('id', 'unknown')}")
        return True
    except Exception as e:
        print(f"ERROR saving to Airtable: {str(e)}")
        return False

@app.route('/sms', methods=['POST'])
def sms_reply():
    if missing_vars:
        return jsonify({"error": "Service not configured", "missing": missing_vars}), 500
    try:
        incoming_msg = request.form.get('Body', '').strip().upper()
        incoming_msg_original = request.form.get('Body', '').strip()
        from_number = request.form.get('From', '')
        to_number = request.form.get('To', '')
        print(f"Received SMS from {from_number}: {incoming_msg}")

        current_step, last_confession, last_win, conversation_id, conversation_type, is_first_time = get_user_state(from_number)
        print(f"Current state: step={current_step}, conversation_id={conversation_id}, conversation_type={conversation_type}")

        response_text = ""
        new_step = current_step
        confession_to_save = incoming_msg_original
        win_to_save = ""
        new_conversation_id = conversation_id or str(uuid.uuid4())
        new_conversation_type = conversation_type
        gemini_prompt_to_save = None
        gemini_response_to_save = None
        skip_save = False

        # SPECIAL COMMANDS: Handle special keywords first (before classification)
        if incoming_msg == "STOP":
            response_text = get_response_from_table("STOP")
            delete_user_data(from_number)
            resp = MessagingResponse()
            resp.message(response_text)
            return str(resp)
        
        if incoming_msg == "HELP":
            response_text = get_response_from_table("HELP")
            save_to_airtable(from_number, incoming_msg_original, "", current_step, new_conversation_id, conversation_type)
            resp = MessagingResponse()
            resp.message(response_text)
            return str(resp)
        
        if incoming_msg == "OUCH":
            new_conversation_id = str(uuid.uuid4())
            new_conversation_type = None
            new_step = "opt_in"
            
            if is_first_time:
                response_text = get_response_from_table("SUBSCRIBE")
            else:
                response_text = "Welcome back! Reply:\n1. Co-worker\n2. Boss\n3. Self-doubt\n\nOr HELP/STOP"
            
            save_to_airtable(from_number, "OUCH", "", new_step, new_conversation_id, new_conversation_type)
            resp = MessagingResponse()
            resp.message(response_text)
            return str(resp)
        
        # SAFETY: Classify ALL other messages for emergency/coaching detection (state-independent)
        classification = classify_message(incoming_msg_original)
        print(f"Message classified as: {classification}")
        
        # EMERGENCY: Immediate response regardless of state
        if classification == "EMERGENCY":
            response_text = get_response_from_table("EMERGENCY")
            save_to_airtable(from_number, incoming_msg_original, "", "start", new_conversation_id, conversation_type)
            resp = MessagingResponse()
            resp.message(response_text)
            return str(resp)
        
        # COACHING: Offer coaching support regardless of state
        if classification == "COACHING":
            response_text = get_response_from_table("COACHING_CONFIRM_PROMPT")
            new_step = "coaching_confirm"
            save_to_airtable(from_number, incoming_msg_original, "", new_step, new_conversation_id, conversation_type)
            resp = MessagingResponse()
            resp.message(response_text)
            return str(resp)
        
        # Normal state machine flow
        else:
            
            next_state, action_trigger = get_state_transition(current_step, incoming_msg, classification)
            
            # Strip whitespace from action_trigger to handle Airtable data issues
            if action_trigger:
                action_trigger = action_trigger.strip()
            
            print(f"Transition: {current_step} + '{incoming_msg}' -> {next_state} (Action: {action_trigger})")
            
            # Update state
            new_step = next_state if next_state else current_step
            
            # SPECIAL HANDLING: confess state with NORMAL classification needs AI response
            if current_step == "confess" and classification == "NORMAL":
                past_wins = get_past_wins(from_number, new_conversation_id)
                
                trigger_context = new_conversation_type.lower() if new_conversation_type else "workplace"
                
                # Select appropriate AI prompt template based on whether past wins exist
                if past_wins:
                    past_wins_text = ", ".join(past_wins)
                    prompt_template = get_response_from_table("AI_PROMPT_TEMPLATE")
                else:
                    past_wins_text = "none"
                    prompt_template = get_response_from_table("AI_PROMPT_TEMPLATE_NO_WINS")
                
                # Replace placeholders with actual values
                prompt = prompt_template.replace("{user_message}", incoming_msg_original)
                prompt = prompt.replace("{trigger_context}", trigger_context)
                prompt = prompt.replace("{past_win}", past_wins_text)
                
                ai_response = query_gemini(prompt)
                response_text = ai_response
                
                # Capture Gemini prompt and response for Airtable
                gemini_prompt_to_save = prompt
                gemini_response_to_save = ai_response
            
            # Handle actions based on ActionTrigger from StateTransitions
            elif action_trigger == "HELP":
                response_text = get_response_from_table("HELP")
            
            elif action_trigger == "DEFAULT":
                response_text = get_response_from_table("DEFAULT")
            
            elif action_trigger in ["Co-worker", "Boss", "Self-doubt"]:
                # User selected trigger in opt_in state
                new_conversation_type = action_trigger
                response_text = get_response_from_table(action_trigger)
                confession_to_save = action_trigger
            
            elif action_trigger == "EMERGENCY":
                response_text = get_response_from_table("EMERGENCY")
            
            elif action_trigger == "COACHING_CONFIRM_PROMPT":
                response_text = get_response_from_table("COACHING_CONFIRM_PROMPT")
            
            elif action_trigger == "COACHING_CONFIRM_YES":
                response_text = get_response_from_table("COACHING_CONFIRM_YES")
            
            elif action_trigger == "COACHING_CONFIRM_NO":
                response_text = get_response_from_table("COACHING_CONFIRM_NO")
            
            elif action_trigger in ["WIN_PROMPT", "AWAITING_WIN"]:
                # User is in awaiting_win state - save their response as a win
                win_to_save = incoming_msg_original
                confession_to_save = ""
                response_text = get_response_from_table("WIN_PROMPT")

        # Save to Airtable unless skipped
        if not skip_save:
            save_to_airtable(from_number, confession_to_save, win_to_save, new_step, new_conversation_id, new_conversation_type, gemini_prompt_to_save, gemini_response_to_save)

        # Defensive: ensure response_text is not empty
        if not response_text or not response_text.strip():
            response_text = "Sorry, I didn't understand that. Text HELP for support or OUCH to start over."
            print(f"WARNING: Empty response_text, using default")

        # Send response
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
    return jsonify({"status": "healthy", "service": "mybrain@work SMS service"}), 200

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "mybrain@work SMS service is running", "webhook_endpoint": "/sms"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)