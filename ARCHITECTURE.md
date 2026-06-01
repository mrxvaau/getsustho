# Architecture

## Layers

`routes` accept HTTP input and choose views.

`services` contain application behavior and Supabase queries.

`middleware` loads the current Supabase user, profile, and role.

`views` are EJS templates. They do not contain database logic.

`supabase/migrations` owns schema, RLS, views, indexes, and triggers.

## Auth Model

Supabase Auth is the source of identity. Application-specific fields live in `public.profiles`.

```text
auth.users.id -> public.profiles.id
public.profiles.role -> PATIENT | DOCTOR | HOSPITAL | STAFF
public.profiles.is_super_admin -> platform admin flag
```

OAuth flow:

```text
/auth/oauth/google -> Supabase OAuth -> /auth/callback -> exchange code -> session -> /go
```

## Database Model

The schema mirrors the Django domain:

- hospitals and hospital branding
- doctors, qualifications, verification, memberships, schedules
- patients
- appointments and referrals
- beds and wards
- operation theatres and OT workflows
- prescriptions and prescription items
- blog posts
- contact messages

## Security Model

- Public can read published doctors, hospitals, schedules, qualifications, and blog posts.
- Public can create contact messages.
- Patients can access their own patient rows and appointments.
- Doctors can access their own doctor rows and appointments.
- Hospital admins can access their own hospital row.
- Server-side admin actions can use the service-role client, never from the browser.
