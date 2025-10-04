import requests
import time
import json

# Webhook URL (replace with your Replit URL)
WEBHOOK_URL = "https://fmc-webhook.yourusername.replit.app/sms"
TWILIO_NUMBER = "+1555xxx xxxx"  # Your Twilio campaign number
TEST_NUMBER = "+15551234567"    # Any test number

def send_webhook_request(payload):
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(WEBHOOK_URL, data=payload, headers=headers)
    print(f"Request: {payload['Body']} - Status: {response.status_code}")
    print(f"Response: {response.text}")
    time.sleep(1)  # Buffer for processing
    return response.text

# Test cases to cover all state paths
test_cases = [
    {"Body": "OUCH", "From": TEST_NUMBER, "To": TWILIO_NUMBER},  # Start → opt_in
    {"Body": "1", "From": TEST_NUMBER, "To": TWILIO_NUMBER},     # opt_in → confess
    {"Body": "TERRIBLE PRESENTATION", "From": TEST_NUMBER, "To": TWILIO_NUMBER},  # confess → win_prompt (NORMAL)
    {"Body": "LED MEETING", "From": TEST_NUMBER, "To": TWILIO_NUMBER},  # win_prompt → start
    {"Body": "I NEED A COACH", "From": TEST_NUMBER, "To": TWILIO_NUMBER},  # confess → coaching_confirm
    {"Body": "YES", "From": TEST_NUMBER, "To": TWILIO_NUMBER},    # coaching_confirm → start
    {"Body": "HELP", "From": TEST_NUMBER, "To": TWILIO_NUMBER},   # HELP → start
    {"Body": "STOP", "From": TEST_NUMBER, "To": TWILIO_NUMBER},   # STOP → start
    {"Body": "I CAN'T GO ON", "From": TEST_NUMBER, "To": TWILIO_NUMBER}  # confess → start (EMERGENCY)
]

# Execute tests
for case in test_cases:
    payload = {k: v for k, v in case.items()}
    response = send_webhook_request(payload)

print("Webhook test sequence complete!")