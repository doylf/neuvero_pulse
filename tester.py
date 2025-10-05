#!/usr/bin/env python3
"""
Test tool for mybrain@work SMS webhook
Simulates Twilio SMS messages without needing to publish or use actual SMS
"""

import requests
import sys
from xml.etree import ElementTree as ET

WEBHOOK_URL = "http://localhost:8000/sms"
TEST_PHONE = "+15555551234"  # Simulated phone number
TWILIO_NUMBER = "+16169874525"


def send_message(message):
    """Send a test message to the webhook"""
    data = {'Body': message, 'From': TEST_PHONE, 'To': TWILIO_NUMBER}

    try:
        response = requests.post(WEBHOOK_URL, data=data)

        if response.status_code == 200:
            # Parse the TwiML response
            root = ET.fromstring(response.text)
            message_elem = root.find('.//Message')
            if message_elem is not None:
                return message_elem.text
            return "No message found in response"
        else:
            return f"Error: HTTP {response.status_code}"
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to webhook. Make sure the Flask server is running on port 8000."
    except Exception as e:
        return f"Error: {str(e)}"


def main():
    print("=" * 60)
    print("mybrain@work SMS Webhook Test Tool")
    print("=" * 60)
    print(f"Testing webhook: {WEBHOOK_URL}")
    print(f"Simulated phone: {TEST_PHONE}")
    print()
    print("Commands:")
    print("  - Type your message and press Enter to send")
    print("  - Type 'quit' or 'exit' to stop")
    print("  - Type 'new' to simulate a new phone number")
    print()
    print("Suggested test flow:")
    print("  1. OUCH")
    print("  2. 1 (or 2, or 3)")
    print("  3. <your confession>")
    print("  4. <your win>")
    print("=" * 60)
    print()

    global TEST_PHONE

    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ['quit', 'exit']:
                print("\nGoodbye!")
                break

            if user_input.lower() == 'new':
                # Generate a new phone number
                import random
                TEST_PHONE = f"+1555555{random.randint(1000, 9999)}"
                print(f"\n📱 Simulating new phone number: {TEST_PHONE}\n")
                continue

            if not user_input:
                continue

            # Send the message and get response
            response = send_message(user_input)
            print(f"\n🤖 Bot: {response}\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}\n")


if __name__ == "__main__":
    main()
