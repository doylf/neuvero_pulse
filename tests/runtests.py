import requests
import time
import json

# Webhook URL (replace with your Replit URL)
WEBHOOK_URL = "https://09ac2762-fc6d-49c5-bac4-150d51044e31-00-26pubw4g0qez.janeway.replit.dev/sms"
TWILIO_NUMBER = "+16169874525"  # Your Twilio campaign number
TEST_NUMBER = "+15551234567"  # Any test number


def send_webhook_request(payload):
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(WEBHOOK_URL, data=payload, headers=headers)
    print(f"Request: {payload['Body']} - Status: {response.status_code}")
    print(f"Response: {response.text}")
    time.sleep(1)  # Buffer for processing
    return response.text


# Test cases to cover all state paths
test_cases = [
    {
        "Body": "OUCH",
        "From": TEST_NUMBER,
        "To": TWILIO_NUMBER
    },  # Start → opt_in
    {
        "Body": "1",
        "From": TEST_NUMBER,
        "To": TWILIO_NUMBER
    },  # opt_in → confess
    {
        "Body": "TERRIBLE PRESENTATION",
        "From": TEST_NUMBER,
        "To": TWILIO_NUMBER
    },  # confess → win_prompt (NORMAL)
    {
        "Body": "Ouch",
        "From": TEST_NUMBER,
        "To": TWILIO_NUMBER
    },
    {
        "Body": "2",
        "From": TEST_NUMBER,
        "To": TWILIO_NUMBER
    },
    {
        "Body": "LED MEETING",
        "From": TEST_NUMBER,
        "To": TWILIO_NUMBER
    },  # win_prompt → start
    {
        "Body": "I NEED A COACH",
        "From": TEST_NUMBER,
        "To": TWILIO_NUMBER
    },  # confess → coaching_confirm
    {
        "Body": "YES",
        "From": TEST_NUMBER,
        "To": TWILIO_NUMBER
    },  # coaching_confirm → start
    {
        "Body": "HELP",
        "From": TEST_NUMBER,
        "To": TWILIO_NUMBER
    },  # HELP → start
    {
        "Body": "STOP",
        "From": TEST_NUMBER,
        "To": TWILIO_NUMBER
    },  # STOP → start
    {
        "Body": "I CAN'T GO ON",
        "From": TEST_NUMBER,
        "To": TWILIO_NUMBER
    }  # confess → start (EMERGENCY)
]

# Execute tests
for case in test_cases:
    payload = {k: v for k, v in case.items()}
    response = send_webhook_request(payload)

print("Webhook test sequence complete!")
