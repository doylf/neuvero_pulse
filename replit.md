# mybrain@work SMS Service

## Overview
A Python Flask application that receives SMS messages via Twilio webhooks, processes them using a Hugging Face LLM (Mistral-7B), and stores conversation history in Airtable.

## Project Architecture

### Technology Stack
- **Backend Framework**: Flask
- **SMS Service**: Twilio
- **AI/LLM**: Hugging Face Inference API (Mistral-7B-Instruct-v0.2)
- **Database**: Airtable
- **Production Server**: Gunicorn

### Key Components

1. **SMS Webhook Endpoint** (`/sms`)
   - Receives incoming SMS messages from Twilio
   - Processes messages through Hugging Face LLM
   - Sends AI-generated responses back via SMS
   - Stores conversation history in Airtable

2. **Hugging Face Integration**
   - Uses Mistral-7B-Instruct-v0.2 model
   - Configurable temperature and token limits
   - Handles API timeouts and errors gracefully

3. **Airtable Storage**
   - Stores: from number, to number, incoming message, AI response, timestamp
   - Automatic record creation for each conversation

### API Endpoints
- `GET /` - Home endpoint with service info
- `GET /health` - Health check endpoint
- `POST /sms` - Twilio webhook endpoint for incoming SMS

## Configuration

### Required Environment Variables
- `TWILIO_ACCOUNT_SID` - Twilio account identifier
- `TWILIO_AUTH_TOKEN` - Twilio authentication token
- `TWILIO_PHONE_NUMBER` - Twilio phone number (format: +1234567890)
- `HUGGINGFACE_API_KEY` - Hugging Face API token
- `AIRTABLE_API_KEY` - Airtable personal access token
- `AIRTABLE_BASE_ID` - Airtable base ID
- `AIRTABLE_TABLE_NAME` - Airtable table name

## Setup Instructions

### Twilio Configuration
1. Log into your Twilio account
2. Go to your phone number settings
3. Under "Messaging", set the webhook URL to: `https://your-replit-url.repl.co/sms`
4. Set the HTTP method to `POST`

### Airtable Setup
Your Airtable table should have these fields:
- `From` (Single line text)
- `To` (Single line text)
- `Incoming Message` (Long text)
- `AI Response` (Long text)
- `Timestamp` (Single line text or Date)

## Running the Application
The application runs on port 8000 using Gunicorn with the command:
```
gunicorn --bind=0.0.0.0:8000 --reuse-port --workers=1 app:app
```

## Recent Changes
- 2025-10-04: Initial setup with Flask, Twilio, Hugging Face, and Airtable integration
- Configured Gunicorn for production deployment
- Added health check and home endpoints
