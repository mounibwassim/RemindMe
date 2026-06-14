-- Create Password Recovery OTPs Table in Supabase
-- Copy and run this script in your Supabase SQL Editor:
-- https://supabase.com/dashboard/project/nwfyvcfxktggybufsggi/sql/new

CREATE TABLE IF NOT EXISTS public.password_recovery_otps (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    otp_code VARCHAR(6) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN DEFAULT FALSE
);

-- Indexing for speed and security lookups
CREATE INDEX IF NOT EXISTS idx_otps_email_used ON public.password_recovery_otps(email, used);

-- Enable Row Level Security (RLS)
ALTER TABLE public.password_recovery_otps ENABLE ROW LEVEL SECURITY;

-- Note: Since the FastAPI backend uses the service role key, it bypasses RLS.
-- Keeping RLS enabled with no public policies ensures client anon/authenticated tokens cannot access it.
