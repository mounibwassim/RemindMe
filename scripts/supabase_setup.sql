-- 1. Create Profiles Table (if not exists)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users NOT NULL PRIMARY KEY,
    username TEXT UNIQUE,
    full_name TEXT,
    avatar_url TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on Profiles
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Recreate Profiles Policies
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- 2. Create Tasks Table (if not exists)

CREATE TABLE IF NOT EXISTS public.tasks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    due_iso TEXT,
    priority INTEGER DEFAULT 2,
    category TEXT DEFAULT 'General',
    is_completed BOOLEAN DEFAULT FALSE,
    encrypted_data TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on Tasks
ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;

-- Recreate Tasks Policies
DROP POLICY IF EXISTS "Users can view own tasks" ON public.tasks;
CREATE POLICY "Users can view own tasks" ON public.tasks
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own tasks" ON public.tasks;
CREATE POLICY "Users can insert own tasks" ON public.tasks
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own tasks" ON public.tasks;
CREATE POLICY "Users can update own tasks" ON public.tasks
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own tasks" ON public.tasks;
CREATE POLICY "Users can delete own tasks" ON public.tasks
    FOR DELETE USING (auth.uid() = user_id);

-- 3. Create Audit Logs Table (if not exists)
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    notification_scheduled_at TIMESTAMP WITH TIME ZONE,
    notification_sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on Audit Logs
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- Recreate Audit Logs Policies
DROP POLICY IF EXISTS "Users can view own audit logs" ON public.audit_logs;
CREATE POLICY "Users can view own audit logs" ON public.audit_logs
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own audit logs" ON public.audit_logs;
CREATE POLICY "Users can insert own audit logs" ON public.audit_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- 4. Create Analytics Table (if not exists)
CREATE TABLE IF NOT EXISTS public.analytics (
    user_id UUID REFERENCES auth.users NOT NULL PRIMARY KEY,
    stats_json JSONB,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on Analytics
ALTER TABLE public.analytics ENABLE ROW LEVEL SECURITY;

-- Recreate Analytics Policies
DROP POLICY IF EXISTS "Users can view own analytics" ON public.analytics;
CREATE POLICY "Users can view own analytics" ON public.analytics
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can upsert own analytics" ON public.analytics;
CREATE POLICY "Users can upsert own analytics" ON public.analytics
    FOR ALL USING (auth.uid() = user_id);

-- Trigger for updated_at on tasks
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_tasks_updated_at ON public.tasks;
CREATE TRIGGER set_tasks_updated_at
    BEFORE UPDATE ON public.tasks
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();
