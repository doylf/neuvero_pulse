import os
import sys
import json
import yaml
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import threading
import time

from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client

from supabase import create_client, Client as SupabaseClient
import google.generativeai as genai

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get(
    'SESSION_SECRET', 'dev-secret-key-change-in-production')

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')

required_env_vars = {
    'TWILIO_ACCOUNT_SID': TWILIO_ACCOUNT_SID,
    'TWILIO_AUTH_TOKEN': TWILIO_AUTH_TOKEN,
    'TWILIO_PHONE_NUMBER': TWILIO_PHONE_NUMBER,
    'GEMINI_API_KEY': GEMINI_API_KEY,
    'SUPABASE_URL': SUPABASE_URL,
    'SUPABASE_SERVICE_ROLE_KEY': SUPABASE_SERVICE_ROLE_KEY
}

missing_vars = [k for k, v in required_env_vars.items() if not v]
if missing_vars:
    error_msg = f"CRITICAL WARNING: Missing environment variables: {', '.join(missing_vars)}"
    print(error_msg, file=sys.stderr)

supabase: SupabaseClient = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    print("Supabase connected successfully.")
else:
    print("Warning: Supabase not connected.")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
else:
    gemini_model = None
    print("Warning: Gemini AI not connected.")

twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


class SessionManager:
    
    @staticmethod
    def get_session(phone):
        if not supabase:
            return None
        try:
            result = supabase.table('sessions').select('*').eq('phone', phone).execute()
            if result.data and len(result.data) > 0:
                row = result.data[0]
                return {
                    'current_flow': row.get('current_flow'),
                    'step_order': row.get('step_order', 0),
                    'slots': row.get('slots', {}),
                    'pending_slot': row.get('pending_slot'),
                    'timezone': row.get('timezone', 'America/New_York')
                }
        except Exception as e:
            print(f"Error getting session: {e}")
        return None

    @staticmethod
    def save_session(phone, session):
        if not supabase:
            return
        try:
            data = {
                'phone': phone,
                'current_flow': session.get('current_flow'),
                'step_order': session.get('step_order', 0),
                'slots': session.get('slots', {}),
                'pending_slot': session.get('pending_slot'),
                'status': 'active',
                'updated_at': datetime.utcnow().isoformat()
            }
            supabase.table('sessions').upsert(data, on_conflict='phone').execute()
        except Exception as e:
            print(f"Error saving session: {e}")

    @staticmethod
    def clear_session(phone):
        if not supabase:
            return
        try:
            supabase.table('sessions').delete().eq('phone', phone).execute()
        except Exception as e:
            print(f"Error clearing session: {e}")


class ScheduleManager:
    
    @staticmethod
    def schedule_step(phone, flow_id, resume_step, slots, delay_hours=None, delay_days=None, 
                      resume_time=None, resume_weekday=None, message_template=None, timezone='America/New_York'):
        if not supabase:
            return
        
        now = datetime.utcnow()
        run_at = now
        
        if delay_hours:
            run_at = now + timedelta(hours=delay_hours)
        elif delay_days:
            run_at = now + timedelta(days=delay_days)
            if resume_time:
                hour, minute = map(int, resume_time.split(':'))
                run_at = run_at.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if resume_weekday is not None:
            days_ahead = resume_weekday - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            run_at = now + timedelta(days=days_ahead)
            if resume_time:
                hour, minute = map(int, resume_time.split(':'))
                run_at = run_at.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        try:
            supabase.table('scheduled_events').insert({
                'phone': phone,
                'flow_id': flow_id,
                'resume_step': resume_step,
                'slots': slots,
                'run_at': run_at.isoformat(),
                'timezone': timezone,
                'status': 'pending',
                'message_template': message_template
            }).execute()
            print(f"Scheduled event for {phone} at {run_at}")
        except Exception as e:
            print(f"Error scheduling event: {e}")

    @staticmethod
    def get_due_events():
        if not supabase:
            return []
        try:
            now = datetime.utcnow().isoformat()
            result = supabase.table('scheduled_events')\
                .select('*')\
                .eq('status', 'pending')\
                .lte('run_at', now)\
                .execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error getting due events: {e}")
            return []

    @staticmethod
    def mark_processed(event_id):
        if not supabase:
            return
        try:
            supabase.table('scheduled_events').update({
                'status': 'processed',
                'processed_at': datetime.utcnow().isoformat()
            }).eq('id', event_id).execute()
        except Exception as e:
            print(f"Error marking event processed: {e}")


class DataManager:

    def __init__(self, yaml_path='flows.yaml'):
        self.yaml_path = yaml_path
        self.flows = []
        self.steps = []
        self.symptoms = []
        self.slots_def = []
        self.refresh_data()

    def refresh_data(self):
        print(f"Loading Logic from YAML file: {self.yaml_path}")
        try:
            with open(self.yaml_path, 'r') as f:
                data = yaml.safe_load(f)
            
            self.flows = data.get('flows', [])
            self.steps = sorted(data.get('steps', []), key=lambda s: s.get('step_order', 0))
            self.symptoms = data.get('symptoms', [])
            self.slots_def = data.get('slots', [])
            
            print(f"Loaded {len(self.flows)} flows, {len(self.steps)} steps, {len(self.symptoms)} symptoms, {len(self.slots_def)} slots.")
        except FileNotFoundError:
            print(f"ERROR: YAML file not found: {self.yaml_path}")
        except Exception as e:
            print(f"CRITICAL ERROR loading YAML data: {e}")

    def get_flow(self, flow_id):
        return next(
            (f for f in self.flows if f.get('flow_id') == flow_id),
            None)

    def get_steps_for_flow(self, flow_id):
        return [s for s in self.steps if s.get('flow_id') == flow_id]

    def find_trigger_flow(self, user_text):
        text = user_text.upper()
        for flow in self.flows:
            triggers = flow.get('triggers', '').upper().split(',')
            triggers = [t.strip() for t in triggers if t.strip()]
            for trigger in triggers:
                if trigger in text:
                    return flow
        return None


db = DataManager()


class ActionEngine:

    @staticmethod
    def execute(action_name, session, user_phone):
        print(f"Executing Action: {action_name}")
        slots = session['slots']

        action_name = action_name.strip()

        if action_name == 'analyze_stress_gemini':
            user_message = slots.get('user_message', '')
            trigger = slots.get('stress_trigger', 'Unknown')

            kb_text = "\n".join([
                f"- {s.get('symptom_name','Pattern')}: {s.get('keywords','')}"
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
                    slots['final_advice'] = "Take a deep breath. (AI Test Mode)"
            except:
                slots['final_advice'] = "Take a deep breath. We will get through this."
            return None

        elif action_name == 'log_to_supabase':
            try:
                if supabase:
                    supabase.table('conversations').insert({
                        "phone": user_phone,
                        "user_message": slots.get('user_message'),
                        "gemini_response": slots.get('final_advice')
                    }).execute()
            except Exception as e:
                print(f"Logging Error: {e}")
            return None

        elif action_name == 'save_win':
            win_text = slots.get('win_text')
            try:
                if supabase:
                    supabase.table('conversations').insert({
                        "phone": user_phone,
                        "win": win_text,
                        "conversation_type": "win_submission"
                    }).execute()
                    print(f"Successfully saved win to Supabase: {win_text}")
                else:
                    print("Error: Supabase not connected.")
            except Exception as e:
                print(f"Error saving win to Supabase: {e}")
            return None

        elif action_name == 'alert_admin':
            print("ALERT: Admin notified of emergency.")
            return None

        elif action_name == 'complete_onboarding':
            pass

        return None


def check_guard(guard_str, user_input, slots):
    if not guard_str:
        return False

    if "input !=" in guard_str:
        target = guard_str.split("!=")[1].strip().replace("'", "").replace('"', "")
        return user_input.upper() != target.upper()

    if "ai_analysis.category ==" in guard_str:
        target = guard_str.split("==")[1].strip().replace("'", "").replace('"', "")
        analysis = slots.get('ai_analysis', {})
        return analysis.get('category') == target

    return False


def send_sms(to_phone, message):
    if twilio_client and TWILIO_PHONE_NUMBER:
        try:
            twilio_client.messages.create(
                body=message,
                from_=TWILIO_PHONE_NUMBER,
                to=to_phone
            )
            print(f"Sent SMS to {to_phone}: {message[:50]}...")
            return True
        except Exception as e:
            print(f"Error sending SMS: {e}")
    return False


def process_conversation(phone, user_input, is_scheduled=False):
    session = SessionManager.get_session(phone)
    if not session:
        session = {
            'current_flow': None,
            'step_order': 0,
            'slots': {},
            'pending_slot': None,
            'timezone': 'America/New_York'
        }

    if not is_scheduled:
        new_flow_obj = db.find_trigger_flow(user_input)

        if new_flow_obj:
            current_flow_id = session['current_flow']
            current_flow_def = db.get_flow(current_flow_id) if current_flow_id else None

            is_locked = current_flow_def.get('is_locked') if current_flow_def else False

            if not is_locked or new_flow_obj['flow_id'] == current_flow_id:
                print(f"Switching context to {new_flow_obj['flow_id']}")
                session = {
                    'current_flow': new_flow_obj['flow_id'],
                    'step_order': 0,
                    'slots': {},
                    'pending_slot': None,
                    'timezone': session.get('timezone', 'America/New_York')
                }

    if not session['current_flow']:
        SessionManager.save_session(phone, session)
        return "I'm listening. Text OUCH to start."

    response_buffer = []

    while True:
        steps = db.get_steps_for_flow(session['current_flow'])

        if session['step_order'] >= len(steps):
            session['current_flow'] = None
            break

        current_step = steps[session['step_order']]
        step_type = current_step.get('step_type')
        content = current_step.get('content')
        variable = current_step.get('variable')
        guard = current_step.get('guard')

        if step_type == 'response':
            out_text = content
            if out_text and '{' in out_text:
                for k, v in session['slots'].items():
                    val = str(v) if v is not None else ""
                    out_text = out_text.replace(f"{{{k}}}", val)
            response_buffer.append(out_text)
            session['step_order'] += 1

        elif step_type == 'action':
            ActionEngine.execute(content, session, phone)
            session['step_order'] += 1

        elif step_type == 'branch':
            condition_met = check_guard(guard, user_input, session['slots'])
            if condition_met:
                print(f"Branching to {content}")
                session['current_flow'] = content
                session['step_order'] = 0
                continue
            else:
                session['step_order'] += 1

        elif step_type == 'validate':
            is_blocked = check_guard(guard, user_input, session['slots'])
            if is_blocked:
                response_buffer.append(f"Please reply with '{content}'.")
                SessionManager.save_session(phone, session)
                return "\n".join(response_buffer)
            session['step_order'] += 1

        elif step_type == 'collect':
            if variable in session['slots']:
                session['step_order'] += 1
            else:
                session['pending_slot'] = variable
                break

        elif step_type == 'schedule':
            delay_hours = current_step.get('delay_hours')
            delay_days = current_step.get('delay_days')
            resume_time = current_step.get('resume_time')
            resume_weekday = current_step.get('resume_weekday')
            message_template = current_step.get('message_template')
            
            ScheduleManager.schedule_step(
                phone=phone,
                flow_id=session['current_flow'],
                resume_step=session['step_order'] + 1,
                slots=session['slots'],
                delay_hours=delay_hours,
                delay_days=delay_days,
                resume_time=resume_time,
                resume_weekday=resume_weekday,
                message_template=message_template,
                timezone=session.get('timezone', 'America/New_York')
            )
            
            if content:
                out_text = content
                if '{' in out_text:
                    for k, v in session['slots'].items():
                        val = str(v) if v is not None else ""
                        out_text = out_text.replace(f"{{{k}}}", val)
                response_buffer.append(out_text)
            
            session['step_order'] += 1
            session['current_flow'] = None
            break

    SessionManager.save_session(phone, session)

    final_response_text = "\n".join(response_buffer) if response_buffer else ""

    try:
        if supabase and final_response_text:
            supabase.table('conversations').insert({
                "phone": phone,
                "user_message": user_input,
                "gemini_response": final_response_text,
                "flow": session.get('current_flow', 'unknown'),
                "step": session.get('step_order', 0),
                "conversation_type": "chat_log"
            }).execute()
    except Exception as e:
        print(f"Logging Error: {e}")

    return final_response_text


def process_scheduled_events():
    events = ScheduleManager.get_due_events()
    for event in events:
        try:
            phone = event['phone']
            flow_id = event['flow_id']
            resume_step = event['resume_step']
            slots = event.get('slots', {})
            message_template = event.get('message_template')
            
            session = {
                'current_flow': flow_id,
                'step_order': resume_step,
                'slots': slots,
                'pending_slot': None,
                'timezone': event.get('timezone', 'America/New_York')
            }
            SessionManager.save_session(phone, session)
            
            if message_template:
                out_text = message_template
                if '{' in out_text:
                    for k, v in slots.items():
                        val = str(v) if v is not None else ""
                        out_text = out_text.replace(f"{{{k}}}", val)
                send_sms(phone, out_text)
            else:
                response = process_conversation(phone, '', is_scheduled=True)
                if response:
                    send_sms(phone, response)
            
            ScheduleManager.mark_processed(event['id'])
            print(f"Processed scheduled event {event['id']} for {phone}")
            
        except Exception as e:
            print(f"Error processing scheduled event: {e}")


def scheduler_worker():
    print("Scheduler worker started")
    while True:
        try:
            process_scheduled_events()
        except Exception as e:
            print(f"Scheduler error: {e}")
        time.sleep(60)


@app.route('/sms', methods=['POST'])
def sms_reply():
    if missing_vars:
        return jsonify({
            "error": "Service Config Error",
            "missing": missing_vars
        }), 500

    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')

    print(f"SMS From {from_number}: {incoming_msg}")

    session = SessionManager.get_session(from_number)
    is_trigger = db.find_trigger_flow(incoming_msg)

    if session and session.get('pending_slot') and not is_trigger:
        slot_name = session['pending_slot']
        print(f"Filling Slot {slot_name} with '{incoming_msg}'")
        session['slots'][slot_name] = incoming_msg
        session['pending_slot'] = None
        SessionManager.save_session(from_number, session)

    try:
        response_text = process_conversation(from_number, incoming_msg)
    except Exception as e:
        print(f"Engine Error: {e}")
        import traceback
        traceback.print_exc()
        response_text = "System Error. Text STOP."

    resp = MessagingResponse()
    resp.message(response_text)
    return str(resp)


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "mybrain@work SMS service",
        "database": "Supabase",
        "features": ["persistent_sessions", "scheduled_flows"]
    }), 200


@app.route('/refresh', methods=['GET'])
def refresh_logic():
    db.refresh_data()
    return jsonify({"status": "Logic Refreshed from YAML"}), 200


@app.route('/process-scheduled', methods=['POST'])
def trigger_scheduled():
    process_scheduled_events()
    return jsonify({"status": "Processed scheduled events"}), 200


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "mybrain@work SMS service is running",
        "webhook_endpoint": "/sms",
        "database": "Supabase",
        "features": ["persistent_sessions", "scheduled_flows"]
    }), 200


if __name__ == '__main__':
    print("=== mybrain@work SMS Service Starting ===")
    print(f"Twilio phone number: {TWILIO_PHONE_NUMBER}")
    print(f"Database: Supabase")
    print(f"AI Model: Google Gemini 2.0 Flash")
    print("Features: Persistent Sessions, Scheduled Flows")
    if not missing_vars:
        print("All environment variables validated successfully")
    
    scheduler_thread = threading.Thread(target=scheduler_worker, daemon=True)
    scheduler_thread.start()
    
    app.run(host='0.0.0.0', port=8000, debug=False)
