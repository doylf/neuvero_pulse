import requests
import json
import time
import os

# Environment variables from Secrets
AIRTABLE_API_KEY = os.environ['AIRTABLE_API_KEY']
AIRTABLE_BASE_ID = os.environ['AIRTABLE_BASE_ID']

BASE_URL = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}


def create_table(table_schema):
    """Sends the schema definition to Airtable to create a new table."""
    print(f"Creating table: {table_schema['name']}...")

    try:
        response = requests.post(BASE_URL, headers=HEADERS, json=table_schema)

        if response.status_code == 200:
            print(f"✅ Success! Table '{table_schema['name']}' created.")
            return response.json()
        elif response.status_code == 422:
            print(
                f"❌ Error: Validation failed. Check field types or duplicate names."
            )
            print(response.text)
        else:
            print(f"❌ Error {response.status_code}: {response.text}")

    except Exception as e:
        print(f"❌ Exception: {str(e)}")

    # Airtable API rate limit buffer
    time.sleep(1)


# --- SCHEMA DEFINITIONS (DDL EQUIVALENT) ---

# 1. Flows
schema_flows = {
    "name":
    "Flows",
    "fields": [{
        "name": "flow_id",
        "type": "singleLineText",
        "primary": True
    }, {
        "name": "description",
        "type": "multilineText"
    }, {
        "name": "triggers",
        "type": "multilineText"
    }, {
        "name": "flow_guard",
        "type": "multilineText"
    }, {
        "name": "priority",
        "type": "number",
        "options": {
            "precision": 0
        }
    }, {
        "name": "is_active",
        "type": "checkbox"
    }, {
        "name": "persisted_slots",
        "type": "multilineText"
    }]
}

# 2. Steps
schema_steps = {
    "name":
    "Steps",
    "fields": [{
        "name": "step_id",
        "type": "singleLineText",
        "primary": True
    }, {
        "name": "flow_reference",
        "type": "singleLineText"
    }, {
        "name": "step_order",
        "type": "number",
        "options": {
            "precision": 0
        }
    }, {
        "name": "step_type",
        "type": "singleSelect",
        "options": {
            "choices": [{
                "name": "collect"
            }, {
                "name": "action"
            }, {
                "name": "set_slots"
            }, {
                "name": "branch"
            }, {
                "name": "subflow"
            }, {
                "name": "pattern"
            }, {
                "name": "validate"
            }, {
                "name": "response"
            }]
        }
    }, {
        "name": "content",
        "type": "multilineText"
    }, {
        "name": "slot_name",
        "type": "singleLineText"
    }, {
        "name": "next_step_reference",
        "type": "singleLineText"
    }, {
        "name": "branch_conditions",
        "type": "multilineText"
    }, {
        "name": "guard_condition",
        "type": "multilineText"
    }, {
        "name": "step_description",
        "type": "multilineText"
    }]
}

# 3. Slots
schema_slots = {
    "name":
    "Slots",
    "fields": [{
        "name": "slot_name",
        "type": "singleLineText",
        "primary": True
    }, {
        "name": "type",
        "type": "singleSelect",
        "options": {
            "choices": [{
                "name": "text"
            }, {
                "name": "boolean"
            }, {
                "name": "categorical"
            }, {
                "name": "number"
            }, {
                "name": "list"
            }, {
                "name": "json"
            }]
        }
    }, {
        "name": "description",
        "type": "multilineText"
    }, {
        "name": "initial_value",
        "type": "multilineText"
    }, {
        "name": "persist_across_flows",
        "type": "checkbox"
    }, {
        "name": "mapping_strategy",
        "type": "singleSelect",
        "options": {
            "choices": [{
                "name": "from_llm"
            }, {
                "name": "from_entity"
            }, {
                "name": "from_intent"
            }, {
                "name": "from_trigger"
            }, {
                "name": "custom_action"
            }]
        }
    }, {
        "name": "validation_rule",
        "type": "multilineText"
    }]
}

# 4. Users
schema_users = {
    "name":
    "Users",
    "fields": [{
        "name": "User_ID",
        "type": "singleLineText",
        "primary": True
    }, {
        "name": "Phone",
        "type": "phoneNumber"
    }, {
        "name": "Email",
        "type": "email"
    }, {
        "name": "Status",
        "type": "singleSelect",
        "options": {
            "choices": [{
                "name": "Active"
            }, {
                "name": "Paused"
            }, {
                "name": "Banned"
            }, {
                "name": "Anonymous"
            }, {
                "name": "Paid"
            }]
        }
    }, {
        "name": "organization_reference",
        "type": "singleLineText"
    }, {
        "name": "current_flow_reference",
        "type": "singleLineText"
    }, {
        "name": "Onboarding_Date",
        "type": "dateTime"
    }, {
        "name": "Last_Active",
        "type": "dateTime"
    }]
}

# 5. Conversations
schema_conversations = {
    "name":
    "Conversations",
    "fields": [{
        "name": "Log_ID",
        "type": "formula",
        "formula": "RECORD_ID()",
        "primary": True
    }, {
        "name": "user_reference",
        "type": "singleLineText"
    }, {
        "name": "Channel_ID",
        "type": "singleLineText"
    }, {
        "name": "User_Message",
        "type": "multilineText"
    }, {
        "name": "Bot_Response",
        "type": "multilineText"
    }, {
        "name": "active_flow_reference",
        "type": "singleLineText"
    }, {
        "name": "step_reference",
        "type": "singleLineText"
    }, {
        "name": "Commands",
        "type": "multilineText"
    }]
}

# 6. UserContext
schema_user_context = {
    "name":
    "UserContext",
    "fields": [{
        "name": "Record_ID",
        "type": "formula",
        "formula":
        "CONCATENATE({owner_reference}, ' - ', Subject, ' - ', Predicate)",
        "primary": True
    }, {
        "name": "owner_reference",
        "type": "singleLineText"
    }, {
        "name": "Subject",
        "type": "singleLineText"
    }, {
        "name": "Predicate",
        "type": "singleLineText"
    }, {
        "name": "Object",
        "type": "singleLineText"
    }, {
        "name": "Is_New_Entity",
        "type": "checkbox"
    }]
}

# 7. Events
schema_events = {
    "name":
    "Events",
    "fields": [{
        "name": "Event_ID",
        "type": "formula",
        "formula": "RECORD_ID()",
        "primary": True
    }, {
        "name": "user_reference",
        "type": "singleLineText"
    }, {
        "name": "Content",
        "type": "multilineText"
    }, {
        "name": "Category",
        "type": "singleSelect",
        "options": {
            "choices": [{
                "name": "Win"
            }, {
                "name": "Gratitude"
            }, {
                "name": "Crisis Alert"
            }, {
                "name": "Feedback"
            }, {
                "name": "System Flag"
            }]
        }
    }, {
        "name": "conversation_reference",
        "type": "singleLineText"
    }]
}

# 8. Organizations
schema_organizations = {
    "name":
    "Organizations",
    "fields": [{
        "name": "Org_Name",
        "type": "singleLineText",
        "primary": True
    }, {
        "name": "Plan_Type",
        "type": "singleSelect",
        "options": {
            "choices": [{
                "name": "Free"
            }, {
                "name": "Pro"
            }, {
                "name": "Enterprise"
            }]
        }
    }, {
        "name": "employees_reference",
        "type": "singleLineText"
    }]
}

# --- EXECUTION ---
if __name__ == "__main__":
    print("🚀 Starting Schema Creation...")

    # Create tables in order
    create_table(schema_flows)
    #    create_table(schema_steps)
    #    create_table(schema_slots)
    #    create_table(schema_users)
    #    create_table(schema_user_context)
    #    create_table(schema_organizations)
    #    create_table(schema_user_events)
    #    create_table(schema_conversations)

    print("\n✨ Operations complete. Check your Airtable base.")
