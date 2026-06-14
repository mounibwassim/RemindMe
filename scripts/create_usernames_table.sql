-- Create Usernames Table in Supabase
-- Copy and run this script in your Supabase SQL Editor:
-- https://supabase.com/dashboard/project/nwfyvcfxktggybufsggi/sql/new

CREATE TABLE IF NOT EXISTS public.usernames (
    username TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    uid TEXT NOT NULL,
    avatar_emoji TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security (RLS)
ALTER TABLE public.usernames ENABLE ROW LEVEL SECURITY;

-- Create policies for service_role access (service_role bypasses RLS, but we add these for completeness)
DROP POLICY IF EXISTS "Enable read access for all" ON public.usernames;
CREATE POLICY "Enable read access for all" ON public.usernames
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Enable insert/update for service role only" ON public.usernames;
-- Note: Service role automatically bypasses RLS, so no special write policy is required.
