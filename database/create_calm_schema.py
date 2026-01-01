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

# 1. Flows Table
# Acts as the "Menu" for the bot.
schema_flows = {
    "name":
    "Flows",
    "description":
    "High-level conversation capabilities.",
    "fields": [
        # Primary Key
        {
            "name": "flow_id",
            "type": "singleLineText",
            "description": "Unique ID for the flow (e.g., flow_stress_relief)"
        },
        # Columns
        {
            "name":
            "description",
            "type":
            "multilineText",
            "description":
            "Description for the AI to understand when to select this flow"
        },
        {
            "name": "triggers",
            "type": "singleLineText",
            "description": "Comma-separated keywords (e.g., OUCH, HELP)"
        },
        {
            "name": "is_locked",
            "type": "checkbox",
            "options": {
                "icon": "check",  # FIXED: Changed 'lock' to 'check' (standard)
                "color":
                "redBright"  # This might work, if not, remove 'options' entirely
            }
        },
        {
            "name": "guard_condition",
            "type": "singleLineText",
            "description":
            "Python-like condition string (e.g., user.is_premium)"
        }
    ]
}

# 2. Steps Table
# The linear logic script.
schema_steps = {
    "name":
    "Steps",
    "description":
    "The logic and script for every flow.",
    "fields": [
        # Primary Key
        {
            "name": "step_uid",
            "type": "singleLineText",
            "description": "Unique Step ID (e.g., flow_stress_1)"
        },
        # Foreign Key Reference (Loose Text Link for simplicity)
        {
            "name": "flow_id",
            "type": "singleLineText"
        },
        {
            "name": "step_order",
            "type": "number",
            "options": {
                "precision": 0
            }
        },
        {
            "name": "step_type",
            "type": "singleSelect",
            "options": {
                "choices": [
                    # FIXED: Used valid Airtable color enums
                    {
                        "name": "response",
                        "color": "blueLight2"
                    },
                    {
                        "name": "collect",
                        "color": "yellowLight2"
                    },
                    {
                        "name": "action",
                        "color": "redLight2"
                    },
                    {
                        "name": "branch",
                        "color": "orangeLight2"
                    },
                    {
                        "name": "validate",
                        "color": "purpleLight2"
                    }
                ]
            }
        },
        {
            "name": "content",
            "type": "multilineText",
            "description": "The text to say, or function to call"
        },
        {
            "name": "variable",
            "type": "singleLineText",
            "description": "Variable name to store result in (e.g., user_name)"
        },
        {
            "name": "guard",
            "type": "singleLineText",
            "description":
            "Condition required to proceed (e.g., input == 'YES')"
        }
    ]
}

# 3. Slots Table
# The memory definitions.
schema_slots = {
    "name":
    "Slots",
    "description":
    "Memory variables definitions.",
    "fields": [
        {
            "name": "slot_name",
            "type": "singleLineText",
            "description": "Name of the variable"
        },
        {
            "name": "type",
            "type": "singleSelect",
            "options": {
                "choices": [
                    # FIXED: Used valid Airtable color enums
                    {
                        "name": "text",
                        "color": "grayLight2"
                    },
                    {
                        "name": "boolean",
                        "color": "blueLight2"
                    },
                    {
                        "name": "categorical",
                        "color": "purpleLight2"
                    },
                    {
                        "name": "json",
                        "color": "greenLight2"
                    }
                ]
            }
        },
        {
            "name": "description",
            "type": "multilineText"
        }
    ]
}

# --- EXECUTION ---
if __name__ == "__main__":
    print("🚀 Starting Schema Creation...")

    # Create tables in order
    create_table(schema_flows)
    create_table(schema_steps)
    create_table(schema_slots)

    print("\n✨ Operations complete. Check your Airtable base.")
