from typing import Self
from pyairtable import Api
import os

# Environment variables from Secrets
AIRTABLE_API_KEY = os.environ['AIRTABLE_API_KEY']
AIRTABLE_BASE_ID = os.environ['AIRTABLE_BASE_ID']
AIRTABLE_TABLE_NAME = "Responses"  # Target the Responses table

# Airtable API setup
airtable_api = Api(AIRTABLE_API_KEY)
airtable_table = airtable_api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

# Data to populate
responses_data = [
    {"Trigger": "SUBSCRIBE", "Prompt": "Welcome to Neuvero.ai - you’re opted into career tips via text. Text HELP for support or STOP to unsubscribe. What made you say OUCH - Co-worker, Boss or self-doubt? Text 1, 2 or 3", "ResponseType": "NORMAL", "Weight": 5},
    {"Trigger": "EMERGENCY", "Prompt": "That sounds urgent. Text 988 for free crisis support now.", "ResponseType": "EMERGENCY", "Weight": 5},
    {"Trigger": "HELP", "Prompt": "Text OUCH for tips or STOP to end", "ResponseType": "HELP", "Weight": 1},
    {"Trigger": "STOP", "Prompt": "You’re unsubscribed. Text OUCH to restart", "ResponseType": "STOP", "Weight": 1},
    {"Trigger": "COACHING_CONFIRM_PROMPT", "Prompt": "Need real talk? Text YES for a 10-min call: [go.neuvero.ai/book-floyd]", "ResponseType": "COACHING", "Weight": 1},
    {"Trigger": "COACHING_CONFIRM_YES", "Prompt": "Great! Book here: [go.neuvero.ai/book-floyd]. Text OUCH anytime.", "ResponseType": "COACHING", "Weight": 1},
    {"Trigger": "COACHING_CONFIRM_NO", "Prompt": "No problem. Text OUCH anytime.", "ResponseType": "COACHING", "Weight": 1},
    {"Trigger": "WIN_PROMPT", "Prompt": "Thanks! Text OUCH anytime.", "ResponseType": "NORMAL", "Weight": 1},
    {"Trigger": "DEFAULT", "Prompt": "Text OUCH to start career tips.", "ResponseType": "NORMAL", "Weight": 1}


    {"Trigger": "CO-WORKER", "Prompt": "User said: {{confession}}. Context: co-worker issue. Past win: {{win or 'none'}}. Reply in 10 calm words, address workplace frustration with evidence.", "ResponseType": "NORMAL", "Weight": 1}
    {"Trigger": "BOSS", "Prompt": "User said: {{confession}}. Context: boss issue. Past win: {{win or 'none'}}. Reply in 10 calm words, counter doubt with evidence.", "ResponseType": "NORMAL", "Weight": 1}
    {"Trigger": "SELF", "Prompt": "User said: {{confession}}. Context: self-doubt. Past win: {{win or 'none'}}. Reply in 10 calm words, boost confidence with evidence.", "ResponseType": "NORMAL", "Weight": 1}
    
]

# Populate the table
for response in responses_data:
    try:
        airtable_table.create(response)
        print(f"Added: {response['Trigger']}")
    except Exception as e:
        print(f"Error adding {response['Trigger']}: {str(e)}")

print("Population complete!")