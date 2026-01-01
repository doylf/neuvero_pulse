import os
import sys
import uuid
import json
from datetime import datetime
from flask import Flask, request, jsonify

# Twilio
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client

# Database & AI
from pyairtable import Api
import google.generativeai as genai

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get(
    'SESSION_SECRET', 'dev-secret-key-change-in-production')

# --- CONFIGURATION & ENV VARS ---
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY', '')
AIRTABLE_BASE_ID = os.environ.get('AIRTABLE_BASE_ID', '')
AIRTABLE_TABLE_NAME = os.environ.get('AIRTABLE_TABLE_NAME', 'Conversations')

# Safety Check
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
    error_msg = f"CRITICAL WARNING: Missing environment variables: {', '.join(missing_vars)}"
    print(error_msg, file=sys.stderr)

# --- INITIALIZE CLIENTS ---

if AIRTABLE_API_KEY and AIRTABLE_BASE_ID:
    airtable_api = Api(AIRTABLE_API_KEY)
else:
    airtable_api = None
    print("Warning: Airtable not connected.")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
else:
    gemini_model = None
    print("Warning: Gemini AI not connected.")

if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
else:
    twilio_client = None


# --- DATA MANAGER (Logic Loader) ---
class DataManager:

    def __init__(self):
        self.flows = []
        self.steps = []
        self.symptoms = []
        self.slots_def = []
        if airtable_api:
            self.refresh_data()

    def refresh_data(self):
        """Loads all logic tables from Airtable into memory."""
        print("Loading Logic from Airtable...")
        try:
            base = airtable_api.base(AIRTABLE_BASE_ID)
            self.flows = base.table('Flows').all()
            self.steps = base.table('Steps').all(sort=['step_order'])
            try:
                self.symptoms = base.table('Symptoms').all()
            except:
                print("Warning: Symptoms table not found or empty.")
                self.symptoms = []
            self.slots_def = base.table('Slots').all()
            print(f"Loaded {len(self.flows)} flows, {len(self.steps)} steps.")
        except Exception as e:
            print(f"CRITICAL ERROR loading Airtable data: {e}")

    def get_flow(self, flow_id):
        return next(
            (f['fields']
             for f in self.flows if f['fields'].get('flow_id') == flow_id),
            None)

    def get_steps_for_flow(self, flow_id):
        return [
            s['fields'] for s in self.steps
            if s['fields'].get('flow_id') == flow_id
        ]

    def find_trigger_flow(self, user_text):
        """Checks if text matches any flow triggers."""
        text = user_text.upper()
        for flow in self.flows:
            triggers = flow['fields'].get('triggers', '').upper().split(',')
            triggers = [t.strip() for t in triggers if t.strip()]
            for trigger in triggers:
                if trigger in text:
                    return flow['fields']
        return None


# Initialize Data Manager
db = DataManager()

# Session Storage (In-Memory for Dev)
user_sessions = {}


# --- ACTION ENGINE ---
class ActionEngine:

    @staticmethod
    def execute(action_name, session, user_phone):
        """Runs the python code associated with an 'action' step."""
        print(f"Executing Action: {action_name}")
        slots = session['slots']

        if action_name == 'analyze_stress_gemini':
            user_message = slots.get('user_message', '')
            trigger = slots.get('stress_trigger', 'Unknown')

            # Build Knowledge Base Context
            kb_text = "\n".join([
                f"- {s['fields'].get('symptom_name','Pattern')}: {s['fields'].get('keywords','')}"
                for s in db.symptoms
            ])

            prompt = f"""
            Act as a career coach. Analyze this user message: "{user_message}".
            Context: The user blames "{trigger}".

            Here is your knowledge base of stress patterns:
            {kb_text}

            1. Match the user_message to ONE symptom pattern from the list.
            2. Determine if this is an EMERGENCY (self-harm/danger) or NORMAL.

            Return ONLY JSON format: {{ "pattern": "Pattern Name", "category": "NORMAL" or "EMERGENCY" }}
            """

            try:
                if gemini_model:
                    response = gemini_model.generate_content(prompt)
                    cleaned_text = response.text.strip().replace(
                        '```json', '').replace('```', '')
                    analysis = json.loads(cleaned_text)
                    slots['ai_analysis'] = analysis
                else:
                    slots['ai_analysis'] = {
                        "category": "NORMAL",
                        "pattern": "Test Mode"
                    }
            except Exception as e:
                print(f"Gemini Error: {e}")
                slots['ai_analysis'] = {
                    "category": "NORMAL",
                    "pattern": "Unknown"
                }
            return None

        elif action_name == 'generate_final_advice':
            analysis = slots.get('ai_analysis', {})
            subtype = slots.get('subtype_choice', 'General')
            pattern = analysis.get('pattern', 'General Stress')

            prompt = f"""
            The user is suffering from "{pattern}".
            They identified their neuro-subtype as "{subtype}".
            Write a short (under 160 chars), empathetic text message with one specific actionable tip.
            """
            try:
                if gemini_model:
                    resp = gemini_model.generate_content(prompt)
                    slots['final_advice'] = resp.text.strip()
                else:
                    slots[
                        'final_advice'] = "Take a deep breath. (AI Test Mode)"
            except:
                slots[
                    'final_advice'] = "Take a deep breath. We will get through this."
            return None

        elif action_name == 'log_to_airtable':
            try:
                if airtable_api:
                    base = airtable_api.base(AIRTABLE_BASE_ID)
                    base.table(AIRTABLE_TABLE_NAME).create({
                        "phone":
                        user_phone,
                        "user_message":
                        slots.get('user_message'),
                        "timestamp":
                        datetime.now().isoformat(),
                        "gemini_response":
                        slots.get('final_advice')
                    })
            except Exception as e:
                print(f"Logging Error: {e}")
            return None

        elif action_name == 'alert_admin':
            print("ALERT: Admin notified of emergency.")
            return None

        elif action_name == 'complete_onboarding':
            # Logic to mark user as 'onboarded' in DB
            pass

        return None


# --- CORE LOGIC LOOP ---


def check_guard(guard_str, user_input, slots):
    """
    Evaluates the 'Guard' condition string. 
    Returns TRUE if the guard BLOCKS execution (Condition failed).
    """
    if not guard_str:
        return False  # No guard, no block

    if "input !=" in guard_str:
        target = guard_str.split("!=")[1].strip().replace("'",
                                                          "").replace('"', "")
        return user_input.upper() != target.upper()

    if "ai_analysis.category ==" in guard_str:
        target = guard_str.split("==")[1].strip().replace("'",
                                                          "").replace('"', "")
        analysis = slots.get('ai_analysis', {})
        # Note: For branching, we return the boolean directly
        return analysis.get('category') == target

    return False


def process_conversation(phone, user_input):
    """The main engine driver."""
    session = user_sessions.get(phone, {
        'current_flow': None,
        'step_order': 0,
        'slots': {},
        'pending_slot': None
    })

    # 1. ROUTER: Check for Context Switching
    new_flow_obj = db.find_trigger_flow(user_input)

    if new_flow_obj:
        # Check if current flow is Locked
        current_flow_id = session['current_flow']
        current_flow_def = db.get_flow(
            current_flow_id) if current_flow_id else None

        is_locked = current_flow_def.get(
            'is_locked') if current_flow_def else False

        # If not locked (or user is forcing start/restart), switch
        if not is_locked or new_flow_obj['flow_id'] == current_flow_id:
            print(f"Switching context to {new_flow_obj['flow_id']}")
            session = {
                'current_flow': new_flow_obj['flow_id'],
                'step_order': 0,
                'slots': {},
                'pending_slot': None
            }
            user_sessions[phone] = session

    # If no session, start default prompt
    if not session['current_flow']:
        return "I'm listening. Text OUCH to start."

    # 2. RUN STEPS LOOP
    response_buffer = []

    while True:
        # Get all steps for this flow
        steps = db.get_steps_for_flow(session['current_flow'])

        # End of Flow Check
        if session['step_order'] >= len(steps):
            session['current_flow'] = None
            break

        current_step = steps[session['step_order']]
        step_type = current_step.get('step_type')
        content = current_step.get('content')
        variable = current_step.get('variable')
        guard = current_step.get('guard')

        # --- EXECUTE STEP TYPES ---

        if step_type == 'response':
            # Replace variables {{variable}}
            out_text = content
            if '{' in out_text:
                for k, v in session['slots'].items():
                    val = str(v) if v is not None else ""
                    out_text = out_text.replace(f"{{{k}}}", val)
            response_buffer.append(out_text)
            session['step_order'] += 1

        elif step_type == 'action':
            ActionEngine.execute(content, session, phone)
            session['step_order'] += 1

        elif step_type == 'branch':
            # Logic: If Condition is Met, Jump. Else, Continue.
            condition_met = check_guard(guard, user_input, session['slots'])
            if condition_met:
                print(f"Branching to {content}")
                session['current_flow'] = content
                session['step_order'] = 0
                continue  # Restart loop with new flow
            else:
                session['step_order'] += 1

        elif step_type == 'validate':
            # Logic: If Guard Blocks (True), Return Error.
            is_blocked = check_guard(guard, user_input, session['slots'])
            if is_blocked:
                # Guard FAILED. Stop and ask again.
                response_buffer.append(f"Please reply with '{content}'.")
                user_sessions[
                    phone] = session  # Save state (stay on this step)
                return "\n".join(response_buffer)

            session['step_order'] += 1

        elif step_type == 'collect':
            # Logic: Do we have this data in slots?
            if variable in session['slots']:
                # We have it, move on.
                session['step_order'] += 1
            else:
                # We need it.
                session['pending_slot'] = variable
                # We do NOT increment step_order. We wait here.
                # Break the loop to send buffered responses (questions).
                break

    # Save session
    user_sessions[phone] = session

    if not response_buffer:
        return ""

    return "\n".join(response_buffer)


# --- ROUTES ---


@app.route('/sms', methods=['POST'])
def sms_reply():
    """Twilio Webhook"""
    if missing_vars:
        return jsonify({
            "error": "Service Config Error",
            "missing": missing_vars
        }), 500

    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')

    print(f"SMS From {from_number}: {incoming_msg}")

    # Handle Slot Filling from Previous Turn
    session = user_sessions.get(from_number)
    is_trigger = db.find_trigger_flow(incoming_msg)

    # If waiting for slot AND input is not a new trigger (like HELP), save data
    if session and session.get('pending_slot') and not is_trigger:
        slot_name = session['pending_slot']
        print(f"Filling Slot {slot_name} with '{incoming_msg}'")
        session['slots'][slot_name] = incoming_msg
        session['pending_slot'] = None  # Clear it
        user_sessions[from_number] = session

    # Run Engine
    try:
        response_text = process_conversation(from_number, incoming_msg)
    except Exception as e:
        print(f"Engine Error: {e}")
        import traceback
        traceback.print_exc()
        response_text = "System Error. Text STOP."

    # Send Response
    resp = MessagingResponse()
    resp.message(response_text)
    return str(resp)


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "mybrain@work SMS service"
    }), 200


@app.route('/refresh', methods=['GET'])
def refresh_logic():
    """Endpoint to force reload Airtable logic without restart"""
    db.refresh_data()
    return jsonify({"status": "Logic Refreshed"}), 200


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "mybrain@work SMS service is running",
        "webhook_endpoint": "/sms"
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
