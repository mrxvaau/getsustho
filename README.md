# Getsustho HMS

Getsustho is a clean Node.js + Supabase rebuild of the original Django hospital management system. It uses Express for server-rendered pages, Supabase Auth for email/password plus Google/Facebook login, and Supabase Postgres as the primary database.

## What Is Included

- Public landing page, doctor profiles, hospital profiles, blog pages, and contact form
- Supabase email/password login and patient registration
- Supabase Google and Facebook OAuth login
- Role-based dashboard routing for `PATIENT`, `DOCTOR`, `HOSPITAL`, `STAFF`, and super admin users
- Clean architecture:
  - `src/config` for environment and Supabase clients
  - `src/middleware` for auth and role checks
  - `src/routes` for HTTP routes
  - `src/services` for domain/database logic
  - `src/views` for EJS pages
  - `supabase/migrations` for database schema
- Full Supabase schema based on the old Django models

## Requirements

- Node.js 20+
- Supabase project
- Google OAuth app
- Facebook app

## Setup

```bash
cd getsustho
npm install
copy .env.example .env
```

Fill `.env`:

```env
APP_URL=http://127.0.0.1:4000
SESSION_SECRET=use-a-long-random-secret
SUPABASE_URL=https://YOUR-PROJECT-REF.supabase.co
SUPABASE_ANON_KEY=your-publishable-or-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

Never expose `SUPABASE_SERVICE_ROLE_KEY` in browser code. This project only uses it on the Express server.

## Supabase Database

Run this SQL in the Supabase SQL editor:

```text
supabase/migrations/001_initial_schema.sql
```

The schema uses:

- `auth.users` for identity
- `public.profiles` for app user profile, role, phone, username, and super-admin flag
- RLS enabled on every application table
- `security_invoker` views for public/dashboard read models
- triggers for `PAT-0001` and `DOC-0001` style IDs

## Supabase Auth Providers

In Supabase Dashboard, open:

```text
Authentication > Providers
```

Enable Google and Facebook.

Set the app callback URL to:

```text
http://127.0.0.1:4000/auth/callback
```

For production, use:

```text
https://your-domain.com/auth/callback
```

### Google

In Google Cloud Console, add Supabase's callback URL as the authorized redirect URI:

```text
https://YOUR-PROJECT-REF.supabase.co/auth/v1/callback
```

Then paste the Google client ID and secret into Supabase Authentication Providers.

### Facebook

In Meta Developers, add this Valid OAuth Redirect URI:

```text
https://YOUR-PROJECT-REF.supabase.co/auth/v1/callback
```

Facebook must have the `email` permission enabled for reliable profile creation.

## Run

```bash
npm run dev
```

Open:

```text
http://127.0.0.1:4000
```

## Verify

```bash
npm run check
npm start
```

Visit:

- `/`
- `/auth/login`
- `/auth/register/patient`
- `/blog`

## Creating The First Super Admin

1. Register or sign in once.
2. In Supabase SQL editor, promote the user:

```sql
update public.profiles
set is_super_admin = true
where email = 'admin@example.com';
```

3. Visit `/go`; the app redirects the account to `/superadmin`.

## Data Migration From Django

The old Django app exported data to:

```text
../backups/sqlite_data_export.json
```

Because Django uses integer user IDs and Supabase Auth uses UUID users, user migration is not a direct `loaddata` import. Recommended migration path:

1. Create users in Supabase Auth.
2. Map old Django users to Supabase UUIDs by email.
3. Insert profiles/patients/doctors/hospitals using the new UUIDs.
4. Insert operational tables after user/profile mapping is complete.

This is safer than trying to force Django auth rows into Supabase Auth.

## Project Structure

```text
getsustho/
  public/css/styles.css
  src/
    app.js
    server.js
    config/
    middleware/
    routes/
    services/
    utils/
    views/
  supabase/migrations/001_initial_schema.sql
```

## Notes

- Supabase Auth handles password reset and OAuth provider identity linking.
- The Express session stores Supabase session tokens server-side.
- RLS is intentionally conservative; expand policies only when each workflow is implemented.
- Supabase Storage should be used for doctor photos, patient photos, hospital branding, verification documents, and blog images.
