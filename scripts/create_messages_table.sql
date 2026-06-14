-- Create messages table in Supabase for storing AI Assistant chat history
-- Run this script in the Supabase SQL Editor:
-- https://supabase.com/dashboard/project/nwfyvcfxktggybufsggi/sql/new

CREATE TABLE IF NOT EXISTS public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexing for fast search by user
CREATE INDEX IF NOT EXISTS idx_messages_user_created ON public.messages(user_id, created_at);

-- Enable Row Level Security (RLS)
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- Drop old policies if they exist
DROP POLICY IF EXISTS "Users can view their own messages" ON public.messages;
DROP POLICY IF EXISTS "Users can insert their own messages" ON public.messages;

-- RLS policy: Users can only select their own messages
CREATE POLICY "Users can view their own messages"
    ON public.messages
    FOR SELECT
    USING (auth.uid() = user_id);

-- RLS policy: Users can only insert their own messages
CREATE POLICY "Users can insert their own messages"
    ON public.messages
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);
