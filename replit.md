# mybrain@work SMS Service

## Overview
A Python Flask application that receives SMS messages via Twilio webhooks, processes them using Google Gemini AI with a multi-step conversation flow for career coaching support, and stores interaction history in Supabase.

## Project Architecture

### Technology Stack
- **Backend Framework**: Flask
- **SMS Service**: Twilio
- **AI/LLM**: Google Gemini 2.0 Flash
- **Database**: Supabase (PostgreSQL)
- **Production Server**: Gunicorn
- **State Management**: In-memory session storage with Supabase for persistence

### Key Components

1. **Flow-Based Conversation Engine**
   - **Flows Table**: Defines conversation flows with triggers
   - **Steps Table**: Ordered steps within each flow (response, collect, action, branch, validate)
   - **Symptoms Table**: Knowledge base for stress pattern matching
   - **Slots Table**: Variable definitions for data collection

2. **SMS Webhook Endpoint** (`/sms`)
   - Receives incoming SMS messages from Twilio
   - Detects flow triggers (e.g., "OUCH")
   - Executes conversation steps in order
   - Uses Gemini for analysis and response generation
   - Saves all interactions to Supabase

3. **Google Gemini Integration**
   - Uses Gemini 2.0 Flash model
   - Analyzes user messages for stress patterns
   - Generates personalized coaching responses
   - Detects emergency situations

4. **Supabase Database Tables**

   **flows** - Conversation flow definitions:
   - `id` (SERIAL PRIMARY KEY)
   - `flow_id` (VARCHAR UNIQUE) - Flow identifier
   - `flow_name` (VARCHAR) - Display name
   - `triggers` (TEXT) - Comma-separated trigger words
   - `is_locked` (BOOLEAN) - Prevents context switching
   - `description` (TEXT)
   - `created_at` (TIMESTAMPTZ)

   **steps** - Ordered steps within flows:
   - `id` (SERIAL PRIMARY KEY)
   - `flow_id` (VARCHAR) - References flows
   - `step_order` (INTEGER) - Execution order
   - `step_type` (VARCHAR) - response/collect/action/branch/validate
   - `content` (TEXT) - Step content or action name
   - `variable` (VARCHAR) - Variable name for collect steps
   - `guard` (TEXT) - Condition for branch/validate
   - `created_at` (TIMESTAMPTZ)

   **symptoms** - Knowledge base:
   - `id` (SERIAL PRIMARY KEY)
   - `symptom_name` (VARCHAR)
   - `keywords` (TEXT)
   - `description` (TEXT)
   - `created_at` (TIMESTAMPTZ)

   **slots** - Variable definitions:
   - `id` (SERIAL PRIMARY KEY)
   - `slot_name` (VARCHAR UNIQUE)
   - `slot_type` (VARCHAR)
   - `prompt_text` (TEXT)
   - `created_at` (TIMESTAMPTZ)

   **conversations** - Interaction logs:
   - `id` (SERIAL PRIMARY KEY)
   - `phone` (VARCHAR) - User phone number
   - `user_message` (TEXT)
   - `gemini_response` (TEXT)
   - `win` (TEXT) - User's reported wins
   - `flow` (VARCHAR) - Current flow
   - `step` (INTEGER) - Current step
   - `conversation_type` (VARCHAR)
   - `conversation_id` (UUID)
   - `created_at` (TIMESTAMPTZ)

### API Endpoints
- `GET /` - Home endpoint with service info
- `GET /health` - Health check endpoint
- `GET /refresh` - Reload logic from Supabase
- `POST /sms` - Twilio webhook endpoint for incoming SMS

## Configuration

### Required Environment Variables
- `TWILIO_ACCOUNT_SID` - Twilio account identifier
- `TWILIO_AUTH_TOKEN` - Twilio authentication token
- `TWILIO_PHONE_NUMBER` - Twilio phone number (format: +1234567890)
- `GEMINI_API_KEY` - Google Gemini API key
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `SESSION_SECRET` - Flask session secret (optional, auto-generated in dev)

## Setup Instructions

### Twilio Configuration
1. Log into your Twilio account
2. Go to your phone number settings
3. Under "Messaging", set the webhook URL to: `https://your-replit-url.repl.co/sms`
4. Set the HTTP method to `POST`

### Supabase Setup
Run the SQL in `supabase_schema.sql` in your Supabase SQL Editor to create all required tables.

## Running the Application
The application runs on port 8000 using Gunicorn with the command:
```
gunicorn --bind=0.0.0.0:8000 --reuse-port --workers=1 app:app
```

## Recent Changes
- 2026-01-12: **Added persistent sessions and scheduled flows**
  - Sessions now persist in Supabase `sessions` table - users can resume flows after app restarts
  - Added `scheduled_events` table for discontinuous/timed flows
  - New "schedule" step type with delay_hours, delay_days, resume_time, resume_weekday options
  - Background scheduler worker checks for due events every 60 seconds
  - Proper timezone handling using pytz for scheduled delivery times
  - Added followup_flow definition for check-in messages

- 2026-01-12: **Moved flows/steps/slots to static YAML file**
  - Conversation flow definitions now stored in `flows.yaml` for easy version control
  - Supabase still used for conversation logging only
  - Added PyYAML dependency
  - Use `/refresh` endpoint to reload YAML without restarting

- 2026-01-12: **Migrated from Airtable to Supabase**
  - Replaced pyairtable with supabase-py client
  - Created PostgreSQL tables: conversations (for logging only)
  - Removed Airtable environment variables
  - Added Supabase environment variables (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

## Supabase Tables

**sessions** - User session persistence:
- `phone` (VARCHAR PRIMARY KEY)
- `current_flow` (VARCHAR)
- `step_order` (INTEGER)
- `slots` (JSONB)
- `pending_slot` (VARCHAR)
- `status` (VARCHAR)
- `updated_at` (TIMESTAMPTZ)

**scheduled_events** - Timed flow continuations:
- `id` (SERIAL PRIMARY KEY)
- `phone` (VARCHAR)
- `flow_id` (VARCHAR)
- `resume_step` (INTEGER)
- `slots` (JSONB)
- `run_at` (TIMESTAMPTZ)
- `timezone` (VARCHAR)
- `status` (VARCHAR)
- `message_template` (TEXT)
- `processed_at` (TIMESTAMPTZ)
