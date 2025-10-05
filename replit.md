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

1. **Multi-Step Conversation Flow** (managed via StateTransitions table)
   - **START**: User texts "OUCH" to begin → transitions to opt_in
   - **OPT_IN**: User selects trigger (1=Co-worker, 2=Boss, 3=Self-doubt) or HELP/STOP → transitions to confess
   - **CONFESS**: Gemini classifies message (EMERGENCY/NORMAL/COACHING):
     - EMERGENCY: Provides 988 crisis hotline
     - COACHING: Offers 10-min booking link
     - NORMAL: Fetches ALL past wins, generates empathetic response (AI asks for wins naturally) → transitions to awaiting_win
   - **AWAITING_WIN**: Stores user's reported win → transitions back to start

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
   - **Confessions Table Fields**: id, phone, confession, win, timestamp, step, conversation_id, conversation_type, gemini_prompt, gemini_response
   - **StateTransitions Table**: Manages state machine logic (CurrentState, InputTrigger, Condition, NextState, ActionTrigger, Weight)
   - **Responses Table**: Stores all text responses indexed by Trigger field (includes AI_PROMPT_TEMPLATE)
   - Tracks complete interaction history per user
   - **Conversation Tracking**: Each conversation gets unique UUID (conversation_id) generated on "OUCH"
   - **Win Tracking**: ALL past wins for a phone number are included in {past_win} placeholder (not conversation-scoped)
   - **Conversation Type**: Tracks selected trigger (Co-worker/Boss/Self-doubt) throughout conversation
   - **AI Transparency**: Stores both the prompt sent to Gemini and the AI-generated response for analysis
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

**Confessions Table** should have these fields:
- `id` (Auto Number) - Primary key
- `phone` (Single line text) - User's phone number
- `confession` (Single line text) - User's message/input
- `win` (Single line text) - User's reported win
- `timestamp` (Date/Time) - When the message was received (auto-computed)
- `step` (Single Select: opt_in, confess, awaiting_win, start, coaching_confirm) - Current conversation state
- `conversation_id` (Single line text) - UUID for tracking conversation sessions
- `conversation_type` (Single line text) - Selected trigger (Co-worker/Boss/Self-doubt)
- `gemini_prompt` (Long text) - The prompt sent to Gemini AI for response generation
- `gemini_response` (Long text) - The response received from Gemini AI (sent to customer)

**StateTransitions Table** for managing state machine:
- `CurrentState` (Single line text) - The current state
- `InputTrigger` (Single line text) - The input that triggers transition (* for wildcard)
- `Condition` (Single line text) - Optional condition (e.g., classification=EMERGENCY)
- `NextState` (Single line text) - The next state to transition to
- `ActionTrigger` (Single line text) - The action to perform
- `Weight` (Number) - Priority for matching (higher = higher priority)

**Responses Table** for storing all text responses:
- `Trigger` (Single line text) - The trigger key (e.g., SUBSCRIBE, HELP, STOP, AI_PROMPT_TEMPLATE)
- `Prompt` (Long text) - The response text or prompt template

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
- 2025-10-04: First-time user detection:
  - Opt-in message (SUBSCRIBE) now only shown once per phone number
  - Added `is_first_time` flag to track new vs returning users
  - Returning users get "Welcome back" message and skip to trigger selection
  - Enhanced AI prompt to include trigger context (co-worker/boss/self-doubt) for personalized responses
- 2025-10-05: Conversation tracking implementation:
  - Added conversation_id (UUID) to track individual conversation sessions
  - Added conversation_type to persist user's selected trigger throughout conversation
  - UUID generated on "OUCH" and maintained throughout conversation lifecycle
  - Past wins now scoped to current conversation_id (not all user history)
  - Fixed win tracking: wins saved with step="win_prompt" for proper retrieval
  - Removed session/cookie dependencies (fully stateless webhook design)
  - Updated Airtable schema: added conversation_id and conversation_type fields
- 2025-10-05: STOP command and AI transparency:
  - STOP command now deletes all Confessions records for the phone number
  - Added gemini_prompt and gemini_response fields to Confessions table
  - Captures and stores both the prompt sent to Gemini and AI-generated response for analysis
  - AI data only saved during NORMAL message handling in CONFESS state
- 2025-10-05: StateTransitions table and win tracking refactor:
  - Added StateTransitions table for generalized state machine logic
  - Changed win tracking: ALL past wins for phone number included in {past_win} placeholder (not conversation-scoped)
  - Removed separate "Text a win?" prompt - AI asks naturally via prompt template
  - New state flow: CONFESS → awaiting_win → START
  - Win saved when user responds after AI message
  - AI_PROMPT_TEMPLATE editable in Responses table with {user_message}, {trigger_context}, {past_win} placeholders
- 2025-10-05: StateTransitions integration complete:
  - Refactored SMS handler to use get_state_transition() for all routing (replaces hardcoded if/elif logic)
  - Conversation flow now fully data-driven through Airtable StateTransitions table
  - Action-based response routing using ActionTrigger field
  - STOP command returns early to prevent stale state issues
  - Added defensive default for empty response_text to prevent silent failures
  - ActionTrigger whitespace normalized via strip() to handle Airtable data formatting
  - Win capture flow verified: user response after AI → saved as win, state resets to start
  - All state transitions and responses now editable in Airtable without code changes
