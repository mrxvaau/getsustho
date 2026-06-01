import { supabase, supabaseAdmin } from '../config/supabase.js';
import { nextAvailableDate } from '../utils/dates.js';

function requireDb() {
  if (!supabase) throw new Error('Supabase is not configured. Copy .env.example to .env and add your project keys.');
}

export async function getLandingData() {
  requireDb();
  const [doctors, hospitals, posts] = await Promise.all([
    supabase.from('doctors_public').select('*').limit(6),
    supabase.from('hospitals_public').select('*').limit(6),
    supabase.from('blog_posts').select('id,title,slug,content,image_url,published_at').eq('is_published', true).order('published_at', { ascending: false }).limit(3)
  ]);
  for (const result of [doctors, hospitals, posts]) if (result.error) throw result.error;
  return { doctors: doctors.data || [], hospitals: hospitals.data || [], posts: posts.data || [] };
}

export async function saveContactMessage(payload) {
  requireDb();
  const { error } = await supabase.from('contact_messages').insert(payload);
  if (error) throw error;
}

export async function getDoctorProfile(doctorId) {
  requireDb();
  const { data, error } = await supabase
    .from('doctors_public')
    .select('*, doctor_qualifications(*), doctor_schedules(*)')
    .eq('doctor_id', doctorId)
    .maybeSingle();
  if (error) throw error;
  return data;
}

export async function getHospitalProfile(id) {
  requireDb();
  const { data, error } = await supabase
    .from('hospitals_public')
    .select('*, doctors_public(*)')
    .eq('id', id)
    .maybeSingle();
  if (error) throw error;
  return data;
}

export async function getBlogPosts() {
  requireDb();
  const { data, error } = await supabase
    .from('blog_posts')
    .select('id,title,slug,content,image_url,published_at')
    .eq('is_published', true)
    .order('published_at', { ascending: false });
  if (error) throw error;
  return data || [];
}

export async function getBlogPost(slug) {
  requireDb();
  const { data, error } = await supabase
    .from('blog_posts')
    .select('*')
    .eq('slug', slug)
    .eq('is_published', true)
    .maybeSingle();
  if (error) throw error;
  return data;
}

export async function getDashboard(profile) {
  requireDb();
  if (!profile) return {};

  if (profile.is_super_admin) {
    const [hospitals, doctors, patients, appointments, verifications, messages] = await Promise.all([
      supabase.from('hospitals').select('id', { count: 'exact', head: true }),
      supabase.from('doctors').select('id', { count: 'exact', head: true }),
      supabase.from('patients').select('id', { count: 'exact', head: true }),
      supabase.from('appointments').select('id', { count: 'exact', head: true }),
      supabase.from('doctor_verifications').select('*, doctors(*, profiles(*))').eq('status', 'PENDING').order('submitted_at'),
      supabase.from('contact_messages').select('*').order('created_at', { ascending: false }).limit(10)
    ]);
    for (const result of [hospitals, doctors, patients, appointments, verifications, messages]) if (result.error) throw result.error;
    return {
      totals: { hospitals: hospitals.count, doctors: doctors.count, patients: patients.count, appointments: appointments.count },
      verifications: verifications.data || [],
      messages: messages.data || []
    };
  }

  if (profile.role === 'PATIENT') {
    const { data, error } = await supabase
      .from('patient_appointments')
      .select('*')
      .eq('user_id', profile.id)
      .order('appointment_date', { ascending: true });
    if (error) throw error;
    return { appointments: data || [] };
  }

  if (profile.role === 'DOCTOR') {
    const { data, error } = await supabase
      .from('doctor_appointments')
      .select('*')
      .eq('doctor_user_id', profile.id)
      .order('appointment_date', { ascending: true });
    if (error) throw error;
    return { appointments: data || [] };
  }

  if (profile.role === 'HOSPITAL') {
    const { data, error } = await supabase
      .from('hospital_dashboard')
      .select('*')
      .eq('admin_user_id', profile.id)
      .maybeSingle();
    if (error) throw error;
    return data || {};
  }

  return {};
}

export async function bookAppointment({ patientId, doctorId, hospitalId, scheduleId, symptoms, bookedBy = 'SELF' }) {
  requireDb();
  const client = supabaseAdmin || supabase;
  const { data: schedule, error: scheduleError } = await client
    .from('doctor_schedules')
    .select('*')
    .eq('id', scheduleId)
    .single();
  if (scheduleError) throw scheduleError;

  const appointmentDate = nextAvailableDate(schedule);
  if (!appointmentDate) throw new Error('No available appointment slot found.');

  const { data: lastSerial, error: serialError } = await client
    .from('appointments')
    .select('serial_number')
    .eq('doctor_id', doctorId)
    .eq('appointment_date', appointmentDate)
    .in('status', ['PENDING', 'CONFIRMED', 'COMPLETED'])
    .order('serial_number', { ascending: false })
    .limit(1);
  if (serialError) throw serialError;

  const serial = lastSerial?.[0]?.serial_number ? lastSerial[0].serial_number + 1 : 1;
  const { data, error } = await client.from('appointments').insert({
    patient_id: patientId,
    doctor_id: doctorId,
    hospital_id: hospitalId,
    schedule_id: scheduleId,
    appointment_date: appointmentDate,
    appointment_time: schedule.start_time,
    serial_number: serial,
    symptoms,
    status: 'PENDING',
    booked_by: bookedBy
  }).select('*').single();
  if (error) throw error;
  return data;
}
