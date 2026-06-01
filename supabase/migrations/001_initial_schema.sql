-- Getsustho HMS initial Supabase schema.
-- Run in Supabase SQL editor or via Supabase CLI.

create extension if not exists pgcrypto;

create type public.user_role as enum ('PATIENT','DOCTOR','HOSPITAL','STAFF');
create type public.review_status as enum ('PENDING','APPROVED','REJECTED');
create type public.membership_status as enum ('ACTIVE','LEAVE_REQUESTED','REMOVE_REQUESTED','LEFT');
create type public.appointment_status as enum ('PENDING','CONFIRMED','COMPLETED','INCOMPLETE','CANCELLED');
create type public.bed_status as enum ('AVAILABLE','BOOKED','OCCUPIED','MAINTENANCE');
create type public.bed_type as enum ('GENERAL','PRIVATE','ICU','VIP','CABIN');
create type public.ot_status as enum ('SCHEDULED','IN_PROGRESS','COMPLETED','POSTPONED','CANCELLED');
create type public.ot_referral_status as enum ('PENDING','APPROVED','REJECTED','BOOKED');
create type public.weekday_code as enum ('SAT','SUN','MON','TUE','WED','THU','FRI');

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  username text unique not null,
  email text unique,
  full_name text not null default '',
  phone text not null default '',
  role public.user_role not null default 'PATIENT',
  is_super_admin boolean not null default false,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.hospitals (
  id bigserial primary key,
  admin_user_id uuid unique not null references public.profiles(id) on delete cascade,
  name text not null,
  location text not null,
  phone text not null default '',
  email text not null default '',
  description text not null default '',
  services text not null default '',
  website text not null default '',
  created_at timestamptz not null default now()
);

create table public.hospital_branding (
  id bigserial primary key,
  hospital_id bigint unique not null references public.hospitals(id) on delete cascade,
  logo_url text,
  cover_photo_url text,
  updated_at timestamptz not null default now()
);

create table public.doctors (
  id bigserial primary key,
  user_id uuid unique not null references public.profiles(id) on delete cascade,
  doctor_id text unique,
  specialist text not null,
  appointment_fee integer not null default 0 check (appointment_fee >= 0),
  bio text not null default '',
  is_available boolean not null default true,
  profile_picture_url text,
  workplace text not null default '',
  primary_hospital_id bigint references public.hospitals(id) on delete set null,
  is_verified boolean not null default false,
  registered_by text not null default 'ADMIN',
  created_at timestamptz not null default now()
);

create table public.doctor_qualifications (
  id bigserial primary key,
  doctor_id bigint not null references public.doctors(id) on delete cascade,
  degree text not null,
  institution text not null,
  year integer,
  sort_order integer not null default 0
);

create table public.doctor_verifications (
  id bigserial primary key,
  doctor_id bigint unique not null references public.doctors(id) on delete cascade,
  license_number text not null,
  degree_certificate_url text not null,
  national_id_photo_url text not null,
  workplace_address text not null,
  status public.review_status not null default 'PENDING',
  rejection_reason text not null default '',
  submitted_at timestamptz not null default now(),
  reviewed_at timestamptz,
  reviewed_by uuid references public.profiles(id) on delete set null
);

create table public.doctor_hospitals (
  id bigserial primary key,
  doctor_id bigint not null references public.doctors(id) on delete cascade,
  hospital_id bigint not null references public.hospitals(id) on delete cascade,
  status public.membership_status not null default 'ACTIVE',
  joined_at timestamptz not null default now(),
  left_at timestamptz,
  reason text not null default '',
  unique (doctor_id, hospital_id)
);

create table public.doctor_join_requests (
  id bigserial primary key,
  doctor_id bigint not null references public.doctors(id) on delete cascade,
  hospital_id bigint not null references public.hospitals(id) on delete cascade,
  status public.review_status not null default 'PENDING',
  message text not null default '',
  requested_at timestamptz not null default now(),
  unique (doctor_id, hospital_id)
);

create table public.doctor_schedules (
  id bigserial primary key,
  doctor_id bigint not null references public.doctors(id) on delete cascade,
  hospital_id bigint not null references public.hospitals(id) on delete cascade,
  day_code public.weekday_code not null,
  start_time time not null,
  end_time time not null,
  max_patients integer not null default 10 check (max_patients > 0),
  is_active boolean not null default true,
  unique (doctor_id, hospital_id, day_code)
);

create table public.patients (
  id bigserial primary key,
  user_id uuid unique not null references public.profiles(id) on delete cascade,
  patient_id text unique,
  age integer check (age is null or age >= 0),
  blood_group text not null default '',
  address text not null default '',
  medical_notes text not null default '',
  profile_picture_url text,
  created_at timestamptz not null default now()
);

create table public.appointments (
  id bigserial primary key,
  patient_id bigint not null references public.patients(id) on delete cascade,
  doctor_id bigint not null references public.doctors(id) on delete cascade,
  hospital_id bigint not null references public.hospitals(id) on delete cascade,
  schedule_id bigint references public.doctor_schedules(id) on delete set null,
  appointment_date date not null,
  appointment_time time not null,
  serial_number integer not null check (serial_number > 0),
  symptoms text not null default '',
  notes text not null default '',
  status public.appointment_status not null default 'PENDING',
  is_extra boolean not null default false,
  booked_by text not null default 'SELF',
  is_paid boolean not null default false,
  created_at timestamptz not null default now(),
  unique (doctor_id, appointment_date, serial_number)
);

create table public.referrals (
  id bigserial primary key,
  appointment_id bigint unique not null references public.appointments(id) on delete cascade,
  ref_name text not null,
  original_fee integer not null default 0,
  discounted_fee integer not null default 0,
  created_by uuid references public.profiles(id) on delete set null,
  created_at timestamptz not null default now()
);

create table public.wards (
  id bigserial primary key,
  hospital_id bigint not null references public.hospitals(id) on delete cascade,
  name text not null,
  description text not null default ''
);

create table public.beds (
  id bigserial primary key,
  hospital_id bigint not null references public.hospitals(id) on delete cascade,
  ward_id bigint references public.wards(id) on delete set null,
  bed_number text not null,
  bed_type public.bed_type not null default 'GENERAL',
  status public.bed_status not null default 'AVAILABLE',
  daily_cost integer not null default 0,
  unique (hospital_id, bed_number)
);

create table public.bed_bookings (
  id bigserial primary key,
  bed_id bigint not null references public.beds(id) on delete cascade,
  patient_id bigint not null references public.patients(id) on delete cascade,
  admitted_by uuid references public.profiles(id) on delete set null,
  check_in_date date not null,
  check_out_date date,
  status text not null default 'BOOKED',
  notes text not null default '',
  booked_at timestamptz not null default now()
);

create table public.operation_theatres (
  id bigserial primary key,
  hospital_id bigint not null references public.hospitals(id) on delete cascade,
  name text not null,
  description text not null default '',
  is_available boolean not null default true
);

create table public.ot_bookings (
  id bigserial primary key,
  ot_id bigint not null references public.operation_theatres(id) on delete cascade,
  patient_id bigint not null references public.patients(id) on delete cascade,
  referred_by bigint references public.doctors(id) on delete set null,
  surgeon_id bigint references public.doctors(id) on delete set null,
  operation_date date not null,
  operation_time time not null,
  duration_minutes integer not null default 60,
  operation_type text not null,
  notes text not null default '',
  status public.ot_status not null default 'SCHEDULED',
  next_date date,
  postpone_reason text not null default '',
  created_at timestamptz not null default now()
);

create table public.ot_referrals (
  id bigserial primary key,
  appointment_id bigint unique not null references public.appointments(id) on delete cascade,
  referring_doctor_id bigint not null references public.doctors(id) on delete cascade,
  patient_id bigint not null references public.patients(id) on delete cascade,
  hospital_id bigint not null references public.hospitals(id) on delete cascade,
  reason text not null,
  status public.ot_referral_status not null default 'PENDING',
  referred_at timestamptz not null default now()
);

create table public.doctor_favourite_medicines (
  id bigserial primary key,
  doctor_id bigint not null references public.doctors(id) on delete cascade,
  medicine_name text not null,
  default_dosage text not null default '',
  default_frequency text not null default '',
  default_duration text not null default '',
  sort_order integer not null default 0
);

create table public.prescriptions (
  id bigserial primary key,
  appointment_id bigint unique not null references public.appointments(id) on delete cascade,
  doctor_id bigint not null references public.doctors(id) on delete cascade,
  patient_id bigint not null references public.patients(id) on delete cascade,
  diagnosis text not null default '',
  general_instructions text not null default '',
  next_visit_date date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.prescription_items (
  id bigserial primary key,
  prescription_id bigint not null references public.prescriptions(id) on delete cascade,
  medicine_name text not null,
  dosage text not null default '',
  frequency text not null default '',
  duration text not null default '',
  instructions text not null default '',
  sort_order integer not null default 0
);

create table public.blog_posts (
  id bigserial primary key,
  title text not null,
  slug text unique not null,
  content text not null,
  image_url text,
  author_id uuid references public.profiles(id) on delete set null,
  is_published boolean not null default false,
  published_at timestamptz,
  created_at timestamptz not null default now()
);

create table public.contact_messages (
  id bigserial primary key,
  name text not null,
  email text not null,
  phone text not null default '',
  message text not null,
  created_at timestamptz not null default now(),
  is_read boolean not null default false
);

create table public.password_reset_otps (
  id bigserial primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  otp text not null,
  is_used boolean not null default false,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null
);

create or replace function public.touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger profiles_touch_updated_at before update on public.profiles
for each row execute function public.touch_updated_at();

create trigger prescriptions_touch_updated_at before update on public.prescriptions
for each row execute function public.touch_updated_at();

create or replace function public.assign_patient_id()
returns trigger
language plpgsql
as $$
begin
  if new.patient_id is null then
    new.patient_id = 'PAT-' || lpad(new.id::text, 4, '0');
  end if;
  return new;
end;
$$;

create trigger patients_assign_patient_id before insert or update on public.patients
for each row execute function public.assign_patient_id();

create or replace function public.assign_doctor_id()
returns trigger
language plpgsql
as $$
begin
  if new.doctor_id is null then
    new.doctor_id = 'DOC-' || lpad(new.id::text, 4, '0');
  end if;
  return new;
end;
$$;

create trigger doctors_assign_doctor_id before insert or update on public.doctors
for each row execute function public.assign_doctor_id();

create view public.doctors_public
with (security_invoker = true)
as
select d.*, p.full_name, p.email, p.phone
from public.doctors d
join public.profiles p on p.id = d.user_id
where d.is_verified = true and p.is_active = true;

create view public.hospitals_public
with (security_invoker = true)
as
select h.*, hb.logo_url, hb.cover_photo_url
from public.hospitals h
left join public.hospital_branding hb on hb.hospital_id = h.id;

create view public.patient_appointments
with (security_invoker = true)
as
select a.*, p.user_id, d.doctor_id, dp.full_name as doctor_name, h.name as hospital_name
from public.appointments a
join public.patients p on p.id = a.patient_id
join public.doctors d on d.id = a.doctor_id
join public.profiles dp on dp.id = d.user_id
join public.hospitals h on h.id = a.hospital_id;

create view public.doctor_appointments
with (security_invoker = true)
as
select a.*, d.user_id as doctor_user_id, pp.full_name as patient_name, h.name as hospital_name
from public.appointments a
join public.doctors d on d.id = a.doctor_id
join public.patients p on p.id = a.patient_id
join public.profiles pp on pp.id = p.user_id
join public.hospitals h on h.id = a.hospital_id;

create view public.hospital_dashboard
with (security_invoker = true)
as
select h.id, h.admin_user_id, h.name,
  (select count(*) from public.doctor_hospitals dh where dh.hospital_id = h.id and dh.status = 'ACTIVE') as active_doctors,
  (select count(*) from public.appointments a where a.hospital_id = h.id) as appointments,
  (select count(*) from public.beds b where b.hospital_id = h.id and b.status = 'AVAILABLE') as available_beds
from public.hospitals h;

alter table public.profiles enable row level security;
alter table public.hospitals enable row level security;
alter table public.hospital_branding enable row level security;
alter table public.doctors enable row level security;
alter table public.doctor_qualifications enable row level security;
alter table public.doctor_verifications enable row level security;
alter table public.doctor_hospitals enable row level security;
alter table public.doctor_join_requests enable row level security;
alter table public.doctor_schedules enable row level security;
alter table public.patients enable row level security;
alter table public.appointments enable row level security;
alter table public.referrals enable row level security;
alter table public.wards enable row level security;
alter table public.beds enable row level security;
alter table public.bed_bookings enable row level security;
alter table public.operation_theatres enable row level security;
alter table public.ot_bookings enable row level security;
alter table public.ot_referrals enable row level security;
alter table public.doctor_favourite_medicines enable row level security;
alter table public.prescriptions enable row level security;
alter table public.prescription_items enable row level security;
alter table public.blog_posts enable row level security;
alter table public.contact_messages enable row level security;
alter table public.password_reset_otps enable row level security;

create policy "public can read verified doctors" on public.doctors for select using (is_verified = true);
create policy "public can read hospitals" on public.hospitals for select using (true);
create policy "public can read branding" on public.hospital_branding for select using (true);
create policy "public can read qualifications" on public.doctor_qualifications for select using (true);
create policy "public can read schedules" on public.doctor_schedules for select using (is_active = true);
create policy "public can read published posts" on public.blog_posts for select using (is_published = true);
create policy "public can create contact messages" on public.contact_messages for insert with check (true);

create policy "users can read own profile" on public.profiles for select using (id = auth.uid() or is_active = true);
create policy "users can update own profile" on public.profiles for update using (id = auth.uid()) with check (id = auth.uid());
create policy "patients own records" on public.patients for all using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "doctors own records" on public.doctors for all using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "hospital admins own hospital" on public.hospitals for all using (admin_user_id = auth.uid()) with check (admin_user_id = auth.uid());

create policy "patient appointment access" on public.appointments for select using (
  exists (select 1 from public.patients p where p.id = patient_id and p.user_id = auth.uid())
  or exists (select 1 from public.doctors d where d.id = doctor_id and d.user_id = auth.uid())
  or exists (select 1 from public.hospitals h where h.id = hospital_id and h.admin_user_id = auth.uid())
);

create policy "patient appointment create" on public.appointments for insert with check (
  exists (select 1 from public.patients p where p.id = patient_id and p.user_id = auth.uid())
  or exists (select 1 from public.hospitals h where h.id = hospital_id and h.admin_user_id = auth.uid())
);

create policy "authenticated can read prescriptions they own" on public.prescriptions for select using (
  exists (select 1 from public.patients p where p.id = patient_id and p.user_id = auth.uid())
  or exists (select 1 from public.doctors d where d.id = doctor_id and d.user_id = auth.uid())
);

create policy "authenticated can read prescription items they own" on public.prescription_items for select using (
  exists (
    select 1 from public.prescriptions pr
    join public.patients p on p.id = pr.patient_id
    left join public.doctors d on d.id = pr.doctor_id
    where pr.id = prescription_id and (p.user_id = auth.uid() or d.user_id = auth.uid())
  )
);

create index appointments_patient_idx on public.appointments(patient_id, appointment_date);
create index appointments_doctor_idx on public.appointments(doctor_id, appointment_date);
create index doctor_schedules_lookup_idx on public.doctor_schedules(doctor_id, hospital_id, is_active);
create index blog_posts_slug_idx on public.blog_posts(slug);
