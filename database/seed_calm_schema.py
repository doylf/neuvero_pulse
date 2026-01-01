import os
import time
from pyairtable import Api

# --- CONFIG ---
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.environ.get('AIRTABLE_BASE_ID')

if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
    print("❌ Error: Missing Environment Variables.")
    exit()

api = Api(AIRTABLE_API_KEY)
base = api.base(AIRTABLE_BASE_ID)

# --- DATA TO UPLOAD ---

flows_data = [{
    "flow_id": "flow_onboarding",
    "description": "First time user setup",
    "triggers": "START",
    "is_locked": True,
    "guard_condition": "user.is_new == True"
}, {
    "flow_id": "flow_stress_relief",
    "description": "User is stressed (OUCH loop)",
    "triggers": "OUCH, TIPS",
    "is_locked": False,
    "guard_condition": None
}, {
    "flow_id": "flow_emergency",
    "description": "Crisis support",
    "triggers": "suicide, kill, hurt, emergency",
    "is_locked": False,
    "guard_condition": None
}, {
    "flow_id": "flow_admin",
    "description": "Help/Stop commands",
    "triggers": "STOP, HELP",
    "is_locked": False,
    "guard_condition": None
}]

steps_data = [
    # Onboarding
    {
        "flow_id": "flow_onboarding",
        "step_order": 1,
        "step_type": "response",
        "content":
        "Welcome to Neuvero.ai! To customize your career tips, what is your first name?",
        "variable": None,
        "guard": None
    },
    {
        "flow_id": "flow_onboarding",
        "step_order": 2,
        "step_type": "collect",
        "content": None,
        "variable": "user_name",
        "guard": None
    },
    {
        "flow_id": "flow_onboarding",
        "step_order": 3,
        "step_type": "response",
        "content":
        "Thanks {user_name}. Reply YES to accept our terms and start.",
        "variable": None,
        "guard": None
    },
    {
        "flow_id": "flow_onboarding",
        "step_order": 4,
        "step_type": "collect",
        "content": None,
        "variable": "terms_accepted",
        "guard": None
    },
    {
        "flow_id": "flow_onboarding",
        "step_order": 5,
        "step_type": "validate",
        "content": "YES",
        "variable": "terms_accepted",
        "guard": "input != 'YES'"
    },
    {
        "flow_id": "flow_onboarding",
        "step_order": 6,
        "step_type": "action",
        "content": "complete_onboarding",
        "variable": None,
        "guard": None
    },
    {
        "flow_id": "flow_onboarding",
        "step_order": 7,
        "step_type": "response",
        "content": "You are all set. Text OUCH anytime you feel work stress.",
        "variable": None,
        "guard": None
    },

    # Stress Relief
    {
        "flow_id": "flow_stress_relief",
        "step_order": 1,
        "step_type": "response",
        "content":
        "I'm here to help. What triggered this? 1) Co-worker 2) Boss 3) Self-doubt. Reply with the number.",
        "variable": None,
        "guard": None
    },
    {
        "flow_id": "flow_stress_relief",
        "step_order": 2,
        "step_type": "collect",
        "content": None,
        "variable": "stress_trigger",
        "guard": None
    },
    {
        "flow_id": "flow_stress_relief",
        "step_order": 3,
        "step_type": "response",
        "content": "Understood. In one sentence, tell me what happened.",
        "variable": None,
        "guard": None
    },
    {
        "flow_id": "flow_stress_relief",
        "step_order": 4,
        "step_type": "collect",
        "content": None,
        "variable": "confession_text",
        "guard": None
    },
    {
        "flow_id": "flow_stress_relief",
        "step_order": 5,
        "step_type": "action",
        "content": "analyze_stress_gemini",
        "variable": "ai_analysis",
        "guard": None
    },
    {
        "flow_id": "flow_stress_relief",
        "step_order": 6,
        "step_type": "branch",
        "content": "flow_emergency",
        "variable": None,
        "guard": "ai_analysis.category == 'EMERGENCY'"
    },
    {
        "flow_id": "flow_stress_relief",
        "step_order": 7,
        "step_type": "response",
        "content":
        "Thanks for sharing. To recommend a tool, does this feel like: 1) Threat/Fear 2) Spinning Thoughts 3) Brain Fog?",
        "variable": None,
        "guard": None
    },
    {
        "flow_id": "flow_stress_relief",
        "step_order": 8,
        "step_type": "collect",
        "content": None,
        "variable": "subtype_choice",
        "guard": None
    },
    {
        "flow_id": "flow_stress_relief",
        "step_order": 9,
        "step_type": "action",
        "content": "generate_final_advice",
        "variable": "final_advice",
        "guard": None
    },
    {
        "flow_id": "flow_stress_relief",
        "step_order": 10,
        "step_type": "response",
        "content": "{final_advice}",
        "variable": None,
        "guard": None
    },
    {
        "flow_id": "flow_stress_relief",
        "step_order": 11,
        "step_type": "action",
        "content": "log_to_airtable",
        "variable": None,
        "guard": None
    },
    {
        "flow_id": "flow_stress_relief",
        "step_order": 12,
        "step_type": "response",
        "content": "Text OUCH to start again.",
        "variable": None,
        "guard": None
    },

    # Emergency
    {
        "flow_id": "flow_emergency",
        "step_order": 1,
        "step_type": "response",
        "content":
        "It sounds like you are in a crisis. Please text 988 immediately for free, 24/7 support.",
        "variable": None,
        "guard": None
    },

    # Admin
    {
        "flow_id": "flow_admin",
        "step_order": 1,
        "step_type": "action",
        "content": "handle_system_command",
        "variable": "admin_response",
        "guard": None
    },
    {
        "flow_id": "flow_admin",
        "step_order": 2,
        "step_type": "response",
        "content": "{admin_response}",
        "variable": None,
        "guard": None
    }
]

slots_data = [{
    "slot_name": "user_name",
    "type": "text",
    "description": "User's first name"
}, {
    "slot_name": "terms_accepted",
    "type": "boolean",
    "description": "Did user say YES to terms"
}, {
    "slot_name": "stress_trigger",
    "type": "categorical",
    "description": "1=Coworker, 2=Boss, 3=Self"
}, {
    "slot_name": "confession_text",
    "type": "text",
    "description": "Raw input of the stress event"
}, {
    "slot_name": "ai_analysis",
    "type": "json",
    "description": "Output object from Gemini analysis"
}, {
    "slot_name": "subtype_choice",
    "type": "categorical",
    "description": "1=Amygdala, 2=DMN, 3=PFC"
}, {
    "slot_name": "final_advice",
    "type": "text",
    "description": "The generated advice string"
}, {
    "slot_name": "admin_response",
    "type": "text",
    "description": "Dynamic response for admin commands"
}]

# --- UPLOAD FUNCTION ---


def upload_data(table_name, data):
    print(f"Uploading {len(data)} rows to '{table_name}'...")
    try:
        table = base.table(table_name)
        # Batch create (Airtable handles chunks automatically in newer pyairtable versions,
        # but manual chunking is safer for older versions. pyairtable .batch_create is robust.)
        table.batch_create(data)
        print(f"✅ {table_name} populated.")
    except Exception as e:
        print(f"❌ Error uploading to {table_name}: {e}")


if __name__ == "__main__":
    print("🚀 Seeding Database...")
    upload_data("Flows", flows_data)
    upload_data("Steps", steps_data)
    upload_data("Slots", slots_data)
    print("✨ Database Seeded!")
