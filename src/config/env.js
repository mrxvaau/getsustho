import dotenv from 'dotenv';
import { z } from 'zod';

dotenv.config();

const schema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  PORT: z.coerce.number().int().positive().default(4000),
  APP_URL: z.string().url().default('http://127.0.0.1:4000'),
  SESSION_SECRET: z.string().min(16).default('development-session-secret-change-me'),
  SUPABASE_URL: z.string().url().optional().or(z.literal('')),
  SUPABASE_ANON_KEY: z.string().optional().or(z.literal('')),
  SUPABASE_SERVICE_ROLE_KEY: z.string().optional().or(z.literal('')),
  GOOGLE_ENABLED: z.coerce.boolean().default(true),
  FACEBOOK_ENABLED: z.coerce.boolean().default(true)
});

export const env = schema.parse(process.env);

export function hasSupabaseConfig() {
  return Boolean(env.SUPABASE_URL && env.SUPABASE_ANON_KEY);
}

export function hasAdminSupabaseConfig() {
  return Boolean(env.SUPABASE_URL && env.SUPABASE_SERVICE_ROLE_KEY);
}
