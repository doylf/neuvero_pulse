-- Run this SQL in your Supabase SQL Editor to create the required tables

-- Create flows table
CREATE TABLE IF NOT EXISTS flows (
    id SERIAL PRIMARY KEY,
    flow_id VARCHAR(100) UNIQUE NOT NULL,
    flow_name VARCHAR(255),
    triggers TEXT,
    is_locked BOOLEAN DEFAULT FALSE,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create steps table
CREATE TABLE IF NOT EXISTS steps (
    id SERIAL PRIMARY KEY,
    flow_id VARCHAR(100) NOT NULL,
    step_order INTEGER NOT NULL,
    step_type VARCHAR(50) NOT NULL,
    content TEXT,
    variable VARCHAR(100),
    guard TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create symptoms table (knowledge base)
CREATE TABLE IF NOT EXISTS symptoms (
    id SERIAL PRIMARY KEY,
    symptom_name VARCHAR(255),
    keywords TEXT,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create slots table
CREATE TABLE IF NOT EXISTS slots (
    id SERIAL PRIMARY KEY,
    slot_name VARCHAR(100) UNIQUE NOT NULL,
    slot_type VARCHAR(50),
    prompt_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create conversations table (logs)
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(50) NOT NULL,
    user_message TEXT,
    gemini_response TEXT,
    win TEXT,
    flow VARCHAR(100),
    step INTEGER,
    conversation_type VARCHAR(50),
    conversation_id UUID DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversations_phone ON conversations(phone);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_steps_flow_id ON steps(flow_id);
CREATE INDEX IF NOT EXISTS idx_steps_order ON steps(flow_id, step_order);

-- Insert sample OUCH flow for testing
INSERT INTO flows (flow_id, flow_name, triggers, is_locked, description) VALUES
('ouch_flow', 'OUCH Career Coaching', 'OUCH,ouch', false, 'Main career coaching conversation flow')
ON CONFLICT (flow_id) DO NOTHING;

-- Insert sample steps for OUCH flow
INSERT INTO steps (flow_id, step_order, step_type, content, variable, guard) VALUES
('ouch_flow', 1, 'response', 'Welcome! I hear you. What is bothering you at work? (Co-worker, Boss, or Self-doubt?)', NULL, NULL),
('ouch_flow', 2, 'collect', NULL, 'stress_trigger', NULL),
('ouch_flow', 3, 'response', 'Tell me more about what happened with your {stress_trigger}.', NULL, NULL),
('ouch_flow', 4, 'collect', NULL, 'user_message', NULL),
('ouch_flow', 5, 'action', 'analyze_stress_gemini', NULL, NULL),
('ouch_flow', 6, 'branch', 'emergency_flow', NULL, 'ai_analysis.category == EMERGENCY'),
('ouch_flow', 7, 'action', 'generate_final_advice', NULL, NULL),
('ouch_flow', 8, 'response', '{final_advice}', NULL, NULL)
ON CONFLICT DO NOTHING;
