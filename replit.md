# mybrain@work SMS Service

## Overview
A Python Flask application that receives SMS messages via Twilio webhooks, processes them using Google Gemini AI with a multi-step conversation flow for career coaching support, and stores interaction history in Supabase.

## Project Architecture

### Technology Stack
- **Backend Framework**: Flask
- **SMS Service**: Twilio (+16169874525)
- **AI/LLM**: Google Gemini 2.0 Flash
- **Database**: Supabase (PostgreSQL with vector extension)
- **Production Server**: Gunicorn
- **State Management**: User table for flow state, in-memory for slot values

### Key Components

1. **Flow-Based Conversation Engine**
   - Flow definitions stored in `flows.yaml` (version controlled)
   - Supports step types: response, collect, action, branch, validate, schedule
   - Symptoms knowledge base for stress pattern matching

2. **SMS Webhook Endpoint** (`/sms`)
   - Receives incoming SMS messages from Twilio
   - Auto-creates users by phone number
   - Detects flow triggers (e.g., "OUCH")
   - Executes conversation steps in order
   - Uses Gemini for analysis and response generation

3. **Scheduled Tasks**
   - Background scheduler worker runs every 60 seconds
   - Processes due scheduled_tasks and sends SMS via Twilio
   - Proper timezone handling (user local time → UTC storage)

4. **Events Logging**
   - Wins, Gratitude, Crisis events stored separately
   - Linked back to conversation logs

### Supabase Database Schema

**organizations** - B2B layer:
- `id` (UUID PRIMARY KEY)
- `name`, `plan_type` (Free/Pro/Enterprise)

**users** - Identity and session state:
- `id` (UUID PRIMARY KEY)
- `phone` (UNIQUE), `email` (UNIQUE)
- `status` (Active/Paused/Banned)
- `org_id` (references organizations)
- `current_flow`, `current_step_id` - Flow state persistence
- `last_active`, `created_at`

**conversations** - Chat logs:
- `id` (BIGINT IDENTITY)
- `user_id` (references users)
- `channel_id`, `flow_context`, `step_context`
- `user_message`, `gemini_response`

**events** - High-value journal:
- `id` (BIGINT IDENTITY)
- `user_id` (references users)
- `category` (Win/Gratitude/Crisis/Feedback/System)
- `content`, `conversation_ref`, `occurred_at`

**knowledge_graph** - AI memory with vectors:
- `id` (BIGINT IDENTITY)
- `user_id`, `subject`, `predicate`, `object`
- `embedding` (vector 1536 dims)

**scheduled_tasks** - Timed flow continuations:
- `id` (BIGINT IDENTITY)
- `user_id`, `flow_id`, `step_id`
- `execute_at`, `status` (Pending/Completed/Cancelled)

### API Endpoints
- `GET /` - Home endpoint with service info
- `GET /health` - Health check endpoint
- `GET /refresh` - Reload flows from YAML
- `POST /sms` - Twilio webhook for incoming SMS
- `POST /process-scheduled` - Manual trigger for scheduled tasks

## Configuration

### Required Environment Variables
- `TWILIO_ACCOUNT_SID` - Twilio account identifier
- `TWILIO_AUTH_TOKEN` - Twilio authentication token
- `TWILIO_PHONE_NUMBER` - Twilio phone number (+16169874525)
- `GEMINI_API_KEY` - Google Gemini API key
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key

### Twilio Configuration
1. Log into your Twilio account
2. Go to your phone number settings
3. Under "Messaging", set webhook URL to: `https://your-replit-url.repl.co/sms`
4. Set HTTP method to `POST`

## Running the Application
```
gunicorn --bind=0.0.0.0:8000 --reuse-port --workers=1 app:app
```

## Recent Changes
- 2026-01-12: **Updated to full production schema**
  - Users table now stores flow state (current_flow, current_step_id)
  - Conversations linked to user_id instead of raw phone
  - Events table for categorized journal entries (Win, Gratitude, Crisis)
  - Knowledge_graph table ready for AI memory with vector embeddings
  - Scheduled_tasks for timed flow continuations

- 2026-01-12: **Added persistent sessions and scheduled flows**
  - Background scheduler worker checks for due tasks every 60 seconds
  - Proper timezone handling using pytz
  - Added followup_flow definition for check-in messages

- 2026-01-12: **Moved flows/steps/slots to static YAML file**
  - Conversation flow definitions in `flows.yaml` for version control
  - Use `/refresh` endpoint to reload YAML without restarting
