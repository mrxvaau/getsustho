import { createSupabaseAdminClient, createSupabaseClient, supabase } from '../config/supabase.js';
import { env } from '../config/env.js';
import { generateUsername } from '../utils/ids.js';

function requireAuthConfig() {
  const client = createSupabaseClient();
  if (!client) throw new Error('Supabase is not configured. Copy .env.example to .env and add your project keys.');
  return client;
}

export async function getProfileByUserId(userId) {
  if (!userId || !supabase) return null;
  const { data, error } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', userId)
    .maybeSingle();
  if (error) throw error;
  return data;
}

export async function ensureProfile(user, defaults = {}) {
  const admin = createSupabaseAdminClient();
  if (!admin) throw new Error('Supabase service role key is required to create profiles.');

  const existing = await getProfileByUserId(user.id);
  if (existing) return existing;

  const fullName = defaults.full_name || user.user_metadata?.full_name || user.email?.split('@')[0] || 'Patient';
  const profile = {
    id: user.id,
    email: user.email,
    username: defaults.username || generateUsername('pat', fullName),
    full_name: fullName,
    phone: defaults.phone || '',
    role: defaults.role || 'PATIENT',
    is_super_admin: defaults.is_super_admin || false
  };

  const { data, error } = await admin.from('profiles').insert(profile).select('*').single();
  if (error) throw error;

  if (profile.role === 'PATIENT') {
    await admin.from('patients').insert({
      user_id: user.id,
      age: defaults.age || null,
      blood_group: defaults.blood_group || '',
      address: defaults.address || ''
    });
  }

  return data;
}

export async function signUpWithPassword({ email, password, fullName, phone, role = 'PATIENT' }) {
  const client = requireAuthConfig();
  const { data, error } = await client.auth.signUp({
    email,
    password,
    options: { data: { full_name: fullName, phone, role } }
  });
  if (error) throw error;
  if (data.user) await ensureProfile(data.user, { full_name: fullName, phone, role });
  return data;
}

export async function signInWithPassword({ email, password }) {
  const client = requireAuthConfig();
  const { data, error } = await client.auth.signInWithPassword({ email, password });
  if (error) throw error;
  if (data.user) await ensureProfile(data.user);
  return data;
}

export async function startOAuth(provider) {
  const client = requireAuthConfig();
  const { data, error } = await client.auth.signInWithOAuth({
    provider,
    options: {
      redirectTo: `${env.APP_URL}/auth/callback`,
      scopes: provider === 'facebook' ? 'email,public_profile' : 'email profile'
    }
  });
  if (error) throw error;
  return data.url;
}

export async function finishOAuth(code) {
  const client = requireAuthConfig();
  const { data, error } = await client.auth.exchangeCodeForSession(code);
  if (error) throw error;
  if (data.user) await ensureProfile(data.user);
  return data.session;
}

export async function signOut(accessToken) {
  const client = createSupabaseClient(accessToken);
  if (!client) return;
  await client.auth.signOut();
}
