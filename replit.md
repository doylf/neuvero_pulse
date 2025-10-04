# mybrain@work SMS Service

## Overview
A Python Flask application that receives SMS messages via Twilio webhooks, processes them using Google Gemini AI with a multi-step conversation flow for career coaching support, and stores interaction history in Airtable.

## Project Architecture

### Technology Stack
- **Backend Framework**: Flask
- **SMS Service**: Twilio
- **AI/LLM**: Google Gemini 2.0 Flash
- **Database**: Airtable
- **Production Server**: Gunicorn
- **State Management**: Airtable-based state tracking (stateless webhook design)

### Key Components

1. **Multi-Step Conversation Flow**
   - **START**: User texts "OUCH" to begin → transitions to opt_in
   - **OPT_IN**: User selects trigger (1=Co-worker, 2=Boss, 3=Self-doubt) or HELP/STOP → transitions to confess
   - **CONFESS**: Gemini classifies message (EMERGENCY/NORMAL/COACHING):
     - EMERGENCY: Provides 988 crisis hotline
     - COACHING: Offers 10-min booking link
     - NORMAL: Fetches past wins, generates empathetic response, asks for wins → transitions to win_prompt
   - **WIN_PROMPT**: Stores user's reported win → transitions back to start

2. **SMS Webhook Endpoint** (`/sms`)
   - Receives incoming SMS messages from Twilio
   - Queries Airtable to determine user's current conversation step
   - Routes messages through appropriate state handler
   - Uses Gemini for message classification and response generation
   - Saves all interactions to Airtable with step tracking

3. **Google Gemini Integration**
   - Uses Gemini 2.0 Flash model
   - Two use cases:
     - Message classification (EMERGENCY/NORMAL/COACHING)
     - Empathetic response generation with evidence-based counters to self-doubt
   - Handles API errors gracefully

4. **Airtable Storage**
   - Fields: id, phone, confession, win, timestamp, step
   - Tracks complete interaction history per user
   - Enables past win retrieval for personalized responses
   - State persistence through step field

### API Endpoints
- `GET /` - Home endpoint with service info
- `GET /health` - Health check endpoint
- `POST /sms` - Twilio webhook endpoint for incoming SMS

## Configuration

### Required Environment Variables
- `TWILIO_ACCOUNT_SID` - Twilio account identifier
- `TWILIO_AUTH_TOKEN` - Twilio authentication token
- `TWILIO_PHONE_NUMBER` - Twilio phone number (format: +1234567890)
- `GEMINI_API_KEY` - Google Gemini API key
- `AIRTABLE_API_KEY` - Airtable personal access token
- `AIRTABLE_BASE_ID` - Airtable base ID
- `AIRTABLE_TABLE_NAME` - Airtable table name
- `SESSION_SECRET` - Flask session secret (optional, auto-generated in dev)

## Setup Instructions

### Twilio Configuration
1. Log into your Twilio account
2. Go to your phone number settings
3. Under "Messaging", set the webhook URL to: `https://your-replit-url.repl.co/sms`
4. Set the HTTP method to `POST`

### Airtable Setup
Your Airtable "Confessions" table should have these fields:
- `id` (Auto Number) - Primary key
- `phone` (Single line text) - User's phone number
- `confession` (Single line text) - User's message/input
- `win` (Single line text) - User's reported win or AI response
- `timestamp` (Date/Time) - When the message was received
- `step` (Single Select: opt_in, confess, win_prompt, start) - Current conversation state

## Running the Application
The application runs on port 8000 using Gunicorn with the command:
```
gunicorn --bind=0.0.0.0:8000 --reuse-port --workers=1 app:app
```

## Recent Changes
- 2025-10-04: Initial setup with Flask, Twilio, Hugging Face, and Airtable integration
- Configured Gunicorn for production deployment
- Added health check and home endpoints
- 2025-10-04: Migrated from Hugging Face to Google Gemini 2.0 Flash (later changed to 1.5 Flash)
- Implemented complete multi-step conversation flow with state management
- Added message classification (EMERGENCY/NORMAL/COACHING)
- Implemented past win retrieval for personalized responses
- Updated Airtable schema to match user requirements (phone, confession, win, timestamp, step)
- 2025-10-04: Major refactor to database-driven responses:
  - Added Airtable "Responses" table for all text responses (driven by Trigger field)
  - Switched to Gemini 1.5 Flash model
  - Replaced cookie-based state with Airtable state management (Twilio webhooks are stateless)
  - Fixed win logging: user wins saved with step="win_prompt" for proper retrieval
  - Auto-reset logic: state returns to "start" after win is saved
