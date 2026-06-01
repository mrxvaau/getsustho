import { createClient } from '@supabase/supabase-js';
import { env, hasAdminSupabaseConfig, hasSupabaseConfig } from './env.js';

const authOptions = {
  auth: {
    flowType: 'pkce',
    autoRefreshToken: false,
    detectSessionInUrl: false,
    persistSession: false
  }
};

export function createSupabaseClient(accessToken) {
  if (!hasSupabaseConfig()) return null;
  return createClient(env.SUPABASE_URL, env.SUPABASE_ANON_KEY, {
    ...authOptions,
    global: accessToken ? { headers: { Authorization: `Bearer ${accessToken}` } } : undefined
  });
}

export function createSupabaseAdminClient() {
  if (!hasAdminSupabaseConfig()) return null;
  return createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_ROLE_KEY, authOptions);
}

export const supabase = createSupabaseClient();
export const supabaseAdmin = createSupabaseAdminClient();
