# Neuvero Pulse SMS Service

## Overview
A Python Flask application that receives SMS messages via Twilio webhooks, processes them using Google Gemini AI with a multi-step conversation flow for career coaching support, and stores interaction history in Supabase.

## Project Architecture

### Technology Stack
- **Backend Framework**: Flask
- **SMS Service**: Twilio (+16169874525)
- **AI/LLM**: Google Gemini 2.0 Flash
- **Database**: Supabase (PostgreSQL with vector extension)
- **Production Server**: Gunicorn
- **State Management**: Users table stores flow state + slots (JSONB)

### File Structure (Modular Architecture)
```
/neuvero-pulse
  ├── app.py                 # Flask Application & Webhook Listener
  ├── flow_schema.json       # JSON schema for YAML validation
  ├── requirements.txt       # Dependencies
  │
  ├── templates/
  │    ├── assessment.html        # Legacy static assessment quiz
  │    └── assessment_engine.html # Generic survey renderer (data-driven)
  │
  ├── data/
  │    └── config.yaml       # Global settings, system prompts, slots, symptoms
  │
  └── flows/                 # Modular Flow "Cartridges"
       ├── router.yaml           # Main menu & command routing
       ├── module_ouch.yaml      # OUCH / Crisis coaching
       ├── module_emergency.yaml # Emergency response flow
       ├── module_followup.yaml  # Scheduled check-ins
       ├── module_assessment.yaml # Assessment verification flow
       └── marketing_hooks.yaml  # Data-driven web surveys
```

### Key Components

1. **Modular DataManager (The Kernel)**
   - Loads `data/config.yaml` as base configuration
   - Scans `flows/*.yaml` and merges all flow modules
   - Validates each module against step type schema
   - Detects duplicate flow IDs with warnings

2. **Flow-Based Conversation Engine**
   - Step types: response, collect, action, branch, validate, schedule
   - Infinite loop guard (max 50 iterations)
   - Symptoms knowledge base for stress pattern matching

3. **SMS Webhook Endpoint** (`/sms`)
   - Receives incoming SMS messages from Twilio
   - Auto-creates users by phone number
   - Detects flow triggers (e.g., "OUCH", "MENU")
   - Executes conversation steps in order
   - Uses Gemini for analysis and response generation

4. **Session Persistence**
   - Flow state stored in users table (current_flow, current_step_id)
   - Slots persisted in users.slots JSONB column
   - Sessions survive server restarts

5. **Scheduled Tasks**
   - Background scheduler worker runs every 60 seconds
   - Processes due scheduled_tasks and sends SMS via Twilio
   - Proper timezone handling (user local time → UTC storage)

### Supabase Database Schema

**users** - Identity and session state:
- `id` (UUID PRIMARY KEY)
- `phone` (UNIQUE), `email` (UNIQUE)
- `status` (Active/Paused/Banned)
- `org_id` (references organizations)
- `current_flow`, `current_step_id` - Flow state persistence
- `slots` (JSONB) - Conversation context persistence
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

**scheduled_tasks** - Timed flow continuations:
- `id` (BIGINT IDENTITY)
- `user_id`, `flow_id`, `step_id`
- `execute_at`, `status` (Pending/Completed/Cancelled)

### API Endpoints
- `GET /` - Home endpoint with service info
- `GET /health` - Health check endpoint
- `GET /refresh` - Reload all YAML modules without restarting
- `GET /assessment/<slug>` - Data-driven survey pages (e.g., `/assessment/style`, `/assessment/burnout`)
- `GET /assessment` - Legacy static assessment page
- `POST /sms` - Twilio webhook for incoming SMS
- `POST /hooks/typeform` - Webhook for assessment form submissions
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

## Adding New Flow Modules

1. Create a new YAML file in `flows/` directory (e.g., `module_win.yaml`)
2. Define flows with proper structure:
```yaml
flows:
  win_flow:
    description: "Log a success"
    triggers: ["WIN", "win"]
    steps:
      - id: step_1
        type: response
        content: "What was your win today?"
      - id: step_2
        type: collect
        variable: win_text
```
3. Call `/refresh` endpoint or restart to load

## Recent Changes
- 2026-01-13: **Data-Driven Web Surveys**
  - Surveys defined in YAML with web_survey block (slug, title, questions, results)
  - Dynamic route /assessment/<slug> renders surveys from YAML
  - flows/marketing_hooks.yaml contains style and burnout surveys
  - templates/assessment_engine.html is the generic survey renderer
  - Add new surveys by editing YAML - no code changes needed

- 2026-01-13: **Web Assessment Survey Integration**
  - Added /hooks/typeform webhook for form submissions
  - New generate_profile_insights action for personalized coaching
  - flows/module_assessment.yaml for SMS verification flow
  - Fixed slot preservation when switching flows

- 2026-01-13: **Modular Architecture Refactoring**
  - Split single flows.yaml into data/config.yaml + flows/*.yaml cartridges
  - DataManager now merges all flow modules at startup
  - Added per-module validation with step type checking
  - Added router flow for main menu navigation

- 2026-01-13: **Session Persistence to Database**
  - Slots now stored in users.slots JSONB column
  - Removed in-memory slot storage
  - Sessions survive server restarts

- 2026-01-13: **Infinite Loop Guard**
  - Added max 50 iteration limit in flow processing
  - Prevents runaway loops in malformed YAML

- 2026-01-12: **Updated to full production schema**
  - Users table now stores flow state (current_flow, current_step_id)
  - Events table for categorized journal entries
  - Scheduled_tasks for timed flow continuations
