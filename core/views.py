from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Sum, Count, Q
from functools import wraps
from datetime import date, timedelta
import json

from .models import User
from hospital.models import (
    Hospital, HospitalBranding, HospitalStaff,
    Doctor, DoctorQualification, DoctorVerification,
    DoctorHospital, DoctorJoinRequest, DoctorSchedule,
    Patient, Appointment, Referral,
    Ward, Bed, BedBooking,
    OperationTheatre, OTBooking, OTReferral,
    DoctorFavouriteMedicine, Prescription, PrescriptionItem,
    BlogPost, ContactMessage, PasswordResetOTP,
    generate_password, generate_username, MEDICINES,
)
from .forms import (
    PatientRegistrationForm, HospitalRegistrationForm,
    DoctorSelfRegistrationForm, AdminDoctorRegistrationForm,
    AdminPatientRegistrationForm,
    PatientProfileForm, PatientAccountForm,
    DoctorProfileForm, DoctorAccountForm,
    DoctorScheduleForm, ContactForm,
)


# ── DECORATORS ────────────────────────────────
def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in roles:
                messages.error(request, 'Access denied.')
                return redirect('login')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def superadmin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'STAFF':
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── EMAIL HELPERS ─────────────────────────────
def send_email_safe(subject, body, recipient):
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=False)
        print(f"[EMAIL SENT] To: {recipient}")
    except Exception as e:
        print(f"[EMAIL FAILED] {e}")


def send_welcome_patient(patient):
    send_email_safe(
        "Welcome to MediCare HMS!",
        f"Hello {patient.user.get_full_name() or patient.user.username},\n\n"
        f"Your patient account is ready.\n"
        f"Username: {patient.user.username}\nPatient ID: {patient.patient_id}\n\n"
        f"Login: http://127.0.0.1:8000/\n\nRegards,\nMediCare HMS",
        patient.user.email
    )

def send_welcome_hospital(hospital):
    send_email_safe(
        f"Welcome to MediCare HMS — {hospital.name}",
        f"Hello,\n\nYour hospital {hospital.name} has been registered.\n"
        f"Username: {hospital.admin.username}\n\nLogin: http://127.0.0.1:8000/\n\nRegards,\nMediCare HMS",
        hospital.admin.email
    )

def send_doctor_under_review(doctor):
    send_email_safe(
        "Your MediCare HMS Account is Under Review",
        f"Dear {doctor.user.get_full_name() or doctor.user.username},\n\n"
        f"Your account is under review. You'll be notified once approved.\n"
        f"Doctor ID: {doctor.doctor_id}\n\nRegards,\nMediCare HMS",
        doctor.user.email
    )

def send_doctor_approved(doctor):
    send_email_safe(
        "Your MediCare HMS Account is Approved!",
        f"Dear {doctor.user.get_full_name() or doctor.user.username},\n\n"
        f"Your account has been approved!\nUsername: {doctor.user.username}\n"
        f"Doctor ID: {doctor.doctor_id}\n\nLogin: http://127.0.0.1:8000/\n\nRegards,\nMediCare HMS",
        doctor.user.email
    )

def send_doctor_rejected(doctor, reason):
    send_email_safe(
        "MediCare HMS Verification Update",
        f"Dear {doctor.user.get_full_name() or doctor.user.username},\n\n"
        f"Your verification was unsuccessful.\nReason: {reason}\n\nRegards,\nMediCare HMS",
        doctor.user.email
    )

def send_doctor_credentials(doctor, hospital, raw_password):
    send_email_safe(
        f"Welcome to {hospital.name} — Your Credentials",
        f"Username: {doctor.user.username}\nPassword: {raw_password}\nDoctor ID: {doctor.doctor_id}\n"
        f"\nLogin: http://127.0.0.1:8000/\n\nRegards,\n{hospital.name}",
        doctor.user.email
    )

def send_staff_credentials(staff, raw_password):
    send_email_safe(
        f"Staff Account — {staff.hospital.name}",
        f"Your staff account has been created.\n"
        f"Username: {staff.user.username}\nPassword: {raw_password}\n"
        f"\nLogin: http://127.0.0.1:8000/\n\nRegards,\n{staff.hospital.name}",
        staff.user.email
    )

def send_patient_credentials(patient, raw_password, appointment=None):
    body = f"Username: {patient.user.username}\nPassword: {raw_password}\nPatient ID: {patient.patient_id}\n"
    if appointment:
        body += f"\nAppointment:\nDoctor: {appointment.doctor}\nDate: {appointment.appointment_date}\nSerial: #{appointment.serial_number}\n"
    body += "\nLogin: http://127.0.0.1:8000/"
    send_email_safe("Your MediCare HMS Account", body, patient.user.email)

def send_appointment_confirmation(appointment):
    send_email_safe(
        "Appointment Confirmed — MediCare HMS",
        f"Hello {appointment.patient.user.get_full_name() or appointment.patient.user.username},\n\n"
        f"Doctor: {appointment.doctor}\nHospital: {appointment.hospital}\n"
        f"Date: {appointment.appointment_date}\nSerial: #{appointment.serial_number}\n\n"
        f"Please arrive 15 minutes early.\n\nRegards,\nMediCare HMS",
        appointment.patient.user.email
    )

def send_appointment_cancelled_doctor_left(appointment, hospital):
    send_email_safe(
        "Appointment Cancelled",
        f"Hello {appointment.patient.user.get_full_name() or appointment.patient.user.username},\n\n"
        f"Your appointment with {appointment.doctor} on {appointment.appointment_date} "
        f"has been cancelled as the doctor is no longer at {hospital.name}.\n\n"
        f"Please book a new appointment.\n\nRegards,\n{hospital.name}",
        appointment.patient.user.email
    )


# ── HELPERS ───────────────────────────────────
def _next_available(schedule):
    day_map = {'MON':0,'TUE':1,'WED':2,'THU':3,'FRI':4,'SAT':5,'SUN':6}
    target  = day_map[schedule.day]
    check   = date.today()
    if check.weekday() == target and not schedule.is_full(check):
        return check
    for _ in range(60):
        check += timedelta(days=1)
        if check.weekday() == target and not schedule.is_full(check):
            return check
    return None

def _get_or_create_patient(user):
    try:
        return user.patient_profile
    except Patient.DoesNotExist:
        p = Patient(user=user)
        p.save()
        return p


# ── PUBLIC PAGES ──────────────────────────────
def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
    blogs    = BlogPost.objects.filter(is_published=True)[:3]
    doctors = Doctor.objects.filter(
    is_verified=True,
    user__is_active=True,
    is_available=True,
    show_on_landing=True
).select_related('user').order_by('landing_order', 'doctor_id')[:6]
    hospitals = Hospital.objects.all()[:6]
    contact_form = ContactForm()
    if request.method == 'POST':
        contact_form = ContactForm(request.POST)
        if contact_form.is_valid():
            d = contact_form.cleaned_data
            ContactMessage.objects.create(
                name=d['name'], email=d['email'],
                phone=d.get('phone',''), message=d['message']
            )
            messages.success(request, 'Message sent! We will get back to you soon.')
            return redirect('landing')
    return render(request, 'public/landing.html', {
        'blogs': blogs, 'doctors': doctors,
        'hospitals': hospitals, 'contact_form': contact_form,
    })


def doctor_public_profile(request, doctor_id):
    doctor         = get_object_or_404(Doctor, doctor_id=doctor_id, is_verified=True, user__is_active=True)
    qualifications = doctor.qualifications.all()
    schedules      = DoctorSchedule.objects.filter(doctor=doctor, is_active=True).select_related('hospital')
    hospitals      = doctor.get_hospitals()
    return render(request, 'public/doctor_profile.html', {
        'doctor':         doctor,
        'qualifications': qualifications,
        'schedules':      schedules,
        'hospitals':      hospitals,
    })


def hospital_public_profile(request, hospital_id):
    hospital = get_object_or_404(Hospital, pk=hospital_id)
    try:
        branding = hospital.branding
    except HospitalBranding.DoesNotExist:
        branding = None
    doctors = Doctor.objects.filter(
        hospital_memberships__hospital=hospital,
        hospital_memberships__status='ACTIVE',
        is_verified=True,
    ).distinct().select_related('user')
    return render(request, 'public/hospital_profile.html', {
        'hospital': hospital, 'branding': branding, 'doctors': doctors,
    })


def blog_list(request):
    posts = BlogPost.objects.filter(is_published=True)
    return render(request, 'public/blog_list.html', {'posts': posts})


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    return render(request, 'public/blog_detail.html', {'post': post})


# ── FORGOT PASSWORD ───────────────────────────
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email','').strip().lower()
        try:
            user = User.objects.get(email=email)
            otp_obj = PasswordResetOTP.generate(user)
            send_email_safe(
                "Your MediCare HMS Password Reset OTP",
                f"Hello {user.get_full_name() or user.username},\n\n"
                f"Your OTP for password reset is: {otp_obj.otp}\n\n"
                f"This OTP expires in 10 minutes.\n\n"
                f"If you did not request this, ignore this email.\n\nRegards,\nMediCare HMS",
                user.email
            )
            request.session['reset_email'] = email
            messages.success(request, f'OTP sent to {email}.')
            return redirect('verify_otp')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email.')
    return render(request, 'auth/forgot_password.html')


def verify_otp(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('forgot_password')
    if request.method == 'POST':
        otp = request.POST.get('otp','').strip()
        try:
            user    = User.objects.get(email=email)
            otp_obj = PasswordResetOTP.objects.filter(
                user=user, otp=otp, is_used=False
            ).order_by('-created_at').first()
            if otp_obj and otp_obj.is_valid:
                otp_obj.is_used = True
                otp_obj.save()
                request.session['reset_verified'] = True
                return redirect('reset_password')
            else:
                messages.error(request, 'Invalid or expired OTP.')
        except User.DoesNotExist:
            messages.error(request, 'Something went wrong.')
    return render(request, 'auth/verify_otp.html', {'email': email})


def reset_password(request):
    email    = request.session.get('reset_email')
    verified = request.session.get('reset_verified')
    if not email or not verified:
        return redirect('forgot_password')
    if request.method == 'POST':
        p1 = request.POST.get('password1','')
        p2 = request.POST.get('password2','')
        if p1 != p2:
            messages.error(request, 'Passwords do not match.')
        elif len(p1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            try:
                user = User.objects.get(email=email)
                user.set_password(p1)
                user.save()
                del request.session['reset_email']
                del request.session['reset_verified']
                messages.success(request, 'Password reset successful! Please log in.')
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'Something went wrong.')
    return render(request, 'auth/reset_password.html')


# ── AUTH ──────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
    if request.method == 'POST':
        user = authenticate(request,
                            username=request.POST.get('username'),
                            password=request.POST.get('password'))
        if user:
            login(request, user)
            return redirect('dashboard_redirect')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'auth/login.html')


def logout_view(request):
    logout(request)
    return redirect('landing')


@login_required
def dashboard_redirect(request):
    if request.user.is_superuser: return redirect('superadmin_dashboard')
    r = request.user.role
    if r == 'PATIENT':  return redirect('patient_portal')
    if r == 'DOCTOR':   return redirect('doctor_dashboard')
    if r == 'HOSPITAL': return redirect('hospital_dashboard')
    if r == 'STAFF':    return redirect('staff_dashboard')
    return redirect('landing')


def patient_register(request):
    form = PatientRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user    = form.save()
        patient = user.patient_profile
        send_welcome_patient(patient)
        messages.success(request, 'Account created! Check your email.')
        return redirect('login')
    return render(request, 'auth/patient_register.html', {'form': form})


def hospital_register(request):
    form = HospitalRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user     = form.save()
        hospital = user.hospital_admin
        send_welcome_hospital(hospital)
        messages.success(request, 'Hospital registered! Check your email.')
        return redirect('login')
    return render(request, 'auth/hospital_register.html', {'form': form})


def doctor_self_register(request):
    form = DoctorSelfRegistrationForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        d    = form.cleaned_data
        user = form.save(commit=True)
        doctor = Doctor(
            user=user, specialist=d['specialist'],
            appointment_fee=d.get('appointment_fee',0),
            bio=d.get('bio',''), workplace=d.get('workplace',''),
            profile_picture=d.get('profile_picture'),
            registered_by='SELF', is_verified=False,
        )
        doctor.save()
        DoctorVerification.objects.create(
            doctor=doctor,
            license_number=d['license_number'],
            degree_certificate=d['degree_certificate'],
            national_id_photo=d['national_id_photo'],
            workplace_address=d['workplace'],
            status='PENDING',
        )
        send_doctor_under_review(doctor)
        messages.success(request, 'Registration submitted! You will be notified once approved.')
        return redirect('login')
    return render(request, 'auth/doctor_register.html', {'form': form})


# ── SUPERADMIN ────────────────────────────────
@superadmin_required
def superadmin_dashboard(request):
    pending_verifications = DoctorVerification.objects.filter(
        status='PENDING'
    ).select_related('doctor__user').order_by('submitted_at')

    completed_today = Appointment.objects.filter(
        status='COMPLETED', appointment_date=date.today()
    ).count()

    unread_messages = ContactMessage.objects.filter(is_read=False).count()

    return render(request, 'superadmin/dashboard.html', {
        'total_hospitals':       Hospital.objects.count(),
        'total_doctors':         Doctor.objects.count(),
        'total_patients':        Patient.objects.count(),
        'total_appts':           Appointment.objects.count(),
        'completed_today':       completed_today,
        'unread_messages':       unread_messages,
        'pending_verifications': pending_verifications,
        'recent_hospitals':      Hospital.objects.select_related('admin').order_by('-id')[:10],
        'recent_doctors':        Doctor.objects.select_related('user').order_by('-id')[:10],
        'recent_patients':       Patient.objects.select_related('user').order_by('-id')[:10],
        'completed_patients':    Appointment.objects.filter(status='COMPLETED').select_related(
            'patient__user','doctor__user','hospital').order_by('-appointment_date')[:20],
        'contact_messages':      ContactMessage.objects.order_by('-created_at')[:10],
    })


@superadmin_required
def superadmin_review_doctor(request, pk):
    verification = get_object_or_404(DoctorVerification, pk=pk)
    return render(request, 'superadmin/review_doctor.html', {
        'verification': verification, 'doctor': verification.doctor,
    })


@superadmin_required
def superadmin_approve_doctor(request, pk):
    verification = get_object_or_404(DoctorVerification, pk=pk)
    if request.method == 'POST':
        doctor                   = verification.doctor
        verification.status      = 'APPROVED'
        verification.reviewed_at = timezone.now()
        verification.reviewed_by = request.user
        verification.save()
        doctor.is_verified    = True
        doctor.user.is_active = True
        doctor.user.save()
        doctor.save()
        send_doctor_approved(doctor)
        messages.success(request, f'Dr. {doctor} approved.')
    return redirect('superadmin_dashboard')


@superadmin_required
def superadmin_reject_doctor(request, pk):
    verification = get_object_or_404(DoctorVerification, pk=pk)
    if request.method == 'POST':
        doctor                        = verification.doctor
        verification.status           = 'REJECTED'
        verification.reviewed_at      = timezone.now()
        verification.reviewed_by      = request.user
        verification.rejection_reason = request.POST.get('reason','')
        verification.save()
        send_doctor_rejected(doctor, verification.rejection_reason)
        messages.success(request, f'Dr. {doctor} rejected.')
    return redirect('superadmin_dashboard')


@superadmin_required
def superadmin_all_doctors(request):
    q = request.GET.get('q', '').strip()

    doctors = Doctor.objects.select_related('user').order_by('-id')

    if q:
        doctors = doctors.filter(
            Q(doctor_id__icontains=q) |
            Q(user__username__icontains=q) |
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(user__email__icontains=q) |
            Q(specialist__icontains=q)
        )

    landing_count = Doctor.objects.filter(show_on_landing=True).count()

    return render(request, 'superadmin/all_doctors.html', {
        'doctors': doctors,
        'q': q,
        'landing_count': landing_count,
    })


@superadmin_required
def toggle_doctor_landing(request, doctor_id):
    doctor = get_object_or_404(Doctor, doctor_id=doctor_id)

    if request.method == 'POST':
        if doctor.show_on_landing:
            doctor.show_on_landing = False
            doctor.save(update_fields=['show_on_landing'])
            messages.success(request, f'{doctor} removed from landing page.')
        else:
            current_count = Doctor.objects.filter(show_on_landing=True).count()

            if current_count >= 6:
                messages.error(request, 'Maximum 6 doctors can be shown on the landing page.')
            else:
                doctor.show_on_landing = True
                doctor.save(update_fields=['show_on_landing'])
                messages.success(request, f'{doctor} added to landing page.')

    return redirect('superadmin_all_doctors')




@superadmin_required
def superadmin_all_hospitals(request):
    hospitals = Hospital.objects.select_related('admin').order_by('-id')
    return render(request, 'superadmin/all_hospitals.html', {'hospitals': hospitals})


@superadmin_required
def superadmin_all_patients(request):
    patients = Patient.objects.select_related('user').order_by('-id')
    return render(request, 'superadmin/all_patients.html', {'patients': patients})


@superadmin_required
def superadmin_completed_patients(request):
    completed = Appointment.objects.filter(status='COMPLETED').select_related(
        'patient__user','doctor__user','hospital'
    ).order_by('-appointment_date')
    return render(request, 'superadmin/completed_patients.html', {'completed': completed})


# ── PATIENT ───────────────────────────────────
@login_required
@role_required('PATIENT', 'DOCTOR')
def patient_portal(request):
    patient = _get_or_create_patient(request.user)

    # All appointments for appointment table/history
    appointments = Appointment.objects.filter(
        patient=patient
    ).select_related(
        'doctor__user',
        'hospital',
        'schedule'
    ).order_by(
        '-appointment_date',
        '-appointment_time',
        '-serial_number'
    )

    # Only upcoming booked appointments
    today = timezone.localdate()
    now_time = timezone.localtime().time()

    upcoming_appointments = Appointment.objects.filter(
        patient=patient,
        status__in=['PENDING', 'CONFIRMED']
    ).filter(
        Q(appointment_date__gt=today) |
        Q(appointment_date=today, appointment_time__gte=now_time)
    ).select_related(
        'doctor__user',
        'hospital',
        'schedule'
    ).order_by(
        'appointment_date',
        'appointment_time',
        'serial_number'
    )

    # Nearest upcoming appointment for dashboard card
    nearest_appointment = upcoming_appointments.first()

    # Doctors for find-doctors section
    all_doctors = Doctor.objects.filter(
        schedules__is_active=True,
        is_verified=True,
        user__is_active=True
    ).distinct().select_related('user')

    for doc in all_doctors:
        doc.active_schedules = doc.schedules.filter(
            is_active=True
        ).select_related('hospital')

        doc.schedules_cities = ' '.join(
            s.hospital.location for s in doc.active_schedules
        ).lower()

    all_specialties = Doctor.objects.filter(
        schedules__is_active=True,
        is_verified=True
    ).values_list(
        'specialist',
        flat=True
    ).distinct().order_by('specialist')

    return render(request, 'patient/portal.html', {
        'patient': patient,
        'appointments': appointments,
        'upcoming_appointments': upcoming_appointments,
        'nearest_appointment': nearest_appointment,
        'all_doctors': all_doctors,
        'all_specialties': all_specialties,
    })


@login_required
@role_required('PATIENT')
def patient_settings(request):
    patient       = _get_or_create_patient(request.user)
    account_form  = PatientAccountForm(instance=request.user)
    profile_form  = PatientProfileForm(instance=patient)
    password_form = PasswordChangeForm(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'account':
            account_form = PatientAccountForm(request.POST, instance=request.user)
            if account_form.is_valid():
                new_un = account_form.cleaned_data['username']
                if User.objects.exclude(pk=request.user.pk).filter(username=new_un).exists():
                    messages.error(request, 'Username already taken.')
                else:
                    account_form.save()
                    messages.success(request, 'Account updated!')
                    return redirect('patient_settings')
        elif action == 'profile':
            profile_form = PatientProfileForm(request.POST, request.FILES, instance=patient)
            if profile_form.is_valid():
                p = profile_form.save(commit=False)
                p.user = request.user
                p.save()
                messages.success(request, 'Profile updated!')
                return redirect('patient_settings')
        elif action == 'password':
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, password_form.user)
                messages.success(request, 'Password changed!')
                return redirect('patient_settings')

    return render(request, 'patient/settings.html', {
        'patient':      patient,
        'account_form': account_form,
        'profile_form': profile_form,
        'password_form':password_form,
    })


@login_required
@role_required('PATIENT', 'DOCTOR')
def book_appointment(request):
    schedules = DoctorSchedule.objects.filter(
        is_active=True,
        doctor__is_verified=True,
        doctor__user__is_active=True
    ).select_related(
        'doctor__user',
        'hospital'
    ).order_by(
        'doctor__id',
        'day',
        'start_time'
    )

    all_specialties = schedules.values_list(
        'doctor__specialist',
        flat=True
    ).distinct().order_by('doctor__specialist')

    all_locations = schedules.values_list(
        'hospital__location',
        flat=True
    ).distinct().order_by('hospital__location')

    if request.method == 'POST':
        schedule = get_object_or_404(
            DoctorSchedule,
            id=request.POST.get('schedule_id'),
            is_active=True
        )

        symptoms = request.POST.get('symptoms', '')
        patient = _get_or_create_patient(request.user)

        appt_date = _next_available(schedule)

        if not appt_date:
            messages.error(request, 'No slots available.')
            return redirect('book_appointment')

        serial = Appointment.next_serial(schedule.doctor, appt_date)

        appt = Appointment.objects.create(
            patient=patient,
            doctor=schedule.doctor,
            hospital=schedule.hospital,
            schedule=schedule,
            appointment_date=appt_date,
            appointment_time=schedule.start_time,
            serial_number=serial,
            symptoms=symptoms,
            status='PENDING',
            booked_by='SELF',
        )

        send_appointment_confirmation(appt)
        messages.success(request, f'Appointment booked! Serial #{serial} on {appt_date}.')

        if request.user.role == 'DOCTOR':
            return redirect('doctor_dashboard')

        return redirect('patient_portal')

    return render(request, 'patient/book_appointment.html', {
        'schedules': schedules,
        'all_specialties': all_specialties,
        'all_locations': all_locations,
    })

@login_required
@role_required('PATIENT','DOCTOR')
def appointment_detail(request, pk):
    patient = _get_or_create_patient(request.user)
    appt    = get_object_or_404(Appointment, pk=pk, patient=patient)
    try:    referral = appt.referral
    except: referral = None
    return render(request, 'patient/appointment_detail.html', {
        'appointment': appt, 'referral': referral
    })


@login_required
@role_required('PATIENT','DOCTOR')
def cancel_appointment(request, pk):
    patient = _get_or_create_patient(request.user)
    appt    = get_object_or_404(Appointment, pk=pk, patient=patient)
    if appt.status in ['PENDING','CONFIRMED']:
        appt.status = 'CANCELLED'
        appt.save()
        messages.success(request, 'Appointment cancelled.')
    if request.user.role == 'DOCTOR':
        return redirect('doctor_dashboard')
    return redirect('patient_portal')


@login_required
@role_required('PATIENT','DOCTOR')
def patient_view_prescription(request, pk):
    patient = _get_or_create_patient(request.user)
    appt    = get_object_or_404(Appointment, pk=pk, patient=patient)
    try:    prescription = appt.prescription
    except: prescription = None
    return render(request, 'patient/prescription.html', {
        'appointment': appt, 'prescription': prescription
    })


# ── DOCTOR ────────────────────────────────────
@login_required
@role_required('DOCTOR')
def doctor_dashboard(request):
    doctor = get_object_or_404(Doctor, user=request.user)
    today  = timezone.now().date()

    today_appointments = Appointment.objects.filter(
        doctor=doctor, appointment_date=today
    ).select_related('patient__user').order_by('serial_number')

    upcoming = Appointment.objects.filter(
        doctor=doctor, appointment_date__gt=today, status__in=['PENDING','CONFIRMED']
    ).select_related('patient__user','hospital').order_by('appointment_date','serial_number')

    completed_count = Appointment.objects.filter(doctor=doctor, status='COMPLETED').count()

    completed_appointments = Appointment.objects.filter(
        doctor=doctor, status='COMPLETED'
    ).select_related('patient__user','hospital').order_by('-appointment_date')[:20]

    earnings_by_hospital = []
    for m in DoctorHospital.objects.filter(doctor=doctor, status='ACTIVE').select_related('hospital'):
        h = m.hospital
        completed_at_h = Appointment.objects.filter(doctor=doctor, hospital=h, status='COMPLETED').count()
        earnings_by_hospital.append({
            'hospital': h, 'completed_patients': completed_at_h,
        })

    schedules    = DoctorSchedule.objects.filter(doctor=doctor).select_related('hospital')
    ot_bookings  = OTBooking.objects.filter(surgeon=doctor).select_related('patient__user','ot__hospital')
    memberships  = DoctorHospital.objects.filter(doctor=doctor).select_related('hospital').order_by('-joined_at')
    pending_join = DoctorJoinRequest.objects.filter(doctor=doctor, status='PENDING').select_related('hospital')

    try:    verification = doctor.verification
    except: verification = None

    return render(request, 'doctor/dashboard.html', {
        'doctor':                 doctor,
        'today_appointments':     today_appointments,
        'upcoming':               upcoming,
        'completed_count':        completed_count,
        'completed_appointments': completed_appointments,
        'earnings_by_hospital':   earnings_by_hospital,
        'schedules':              schedules,
        'ot_bookings':            ot_bookings,
        'memberships':            memberships,
        'pending_join_requests':  pending_join,
        'verification':           verification,
        'today':                  today,
    })


@login_required
@role_required('DOCTOR')
def doctor_settings(request):
    doctor        = get_object_or_404(Doctor, user=request.user)
    account_form  = DoctorAccountForm(instance=request.user)
    profile_form  = DoctorProfileForm(instance=doctor)
    password_form = PasswordChangeForm(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'account':
            account_form = DoctorAccountForm(request.POST, instance=request.user)
            if account_form.is_valid():
                new_un = account_form.cleaned_data['username']
                if User.objects.exclude(pk=request.user.pk).filter(username=new_un).exists():
                    messages.error(request, 'Username already taken.')
                else:
                    account_form.save()
                    messages.success(request, 'Account updated!')
                    return redirect('doctor_settings')
        elif action == 'profile':
            profile_form = DoctorProfileForm(request.POST, request.FILES, instance=doctor)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated!')
                return redirect('doctor_settings')
        elif action == 'password':
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, password_form.user)
                messages.success(request, 'Password changed!')
                return redirect('doctor_settings')

    return render(request, 'doctor/settings.html', {
        'doctor':       doctor,
        'account_form': account_form,
        'profile_form': profile_form,
        'password_form':password_form,
    })


@login_required
@role_required('DOCTOR')
def doctor_complete_appointment(request, pk):
    doctor = get_object_or_404(Doctor, user=request.user)
    appt   = get_object_or_404(Appointment, pk=pk, doctor=doctor)
    if appt.status not in ['COMPLETED','CANCELLED']:
        appt.status = 'COMPLETED'
        appt.save()
        messages.success(request, 'Appointment completed.')
    return redirect('doctor_write_prescription', pk=pk)


@login_required
@role_required('DOCTOR')
def doctor_write_prescription(request, pk):
    doctor = get_object_or_404(Doctor, user=request.user)
    appt   = get_object_or_404(Appointment, pk=pk, doctor=doctor)
    try:    prescription = appt.prescription
    except: prescription = None
    favourites = DoctorFavouriteMedicine.objects.filter(doctor=doctor)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_favourite':
            name = request.POST.get('medicine_name','').strip()
            if name:
                DoctorFavouriteMedicine.objects.get_or_create(
                    doctor=doctor, medicine_name=name,
                    defaults={
                        'default_dosage':    request.POST.get('default_dosage',''),
                        'default_frequency': request.POST.get('default_frequency',''),
                        'default_duration':  request.POST.get('default_duration',''),
                    }
                )
            return redirect('doctor_write_prescription', pk=pk)
        if action == 'remove_favourite':
            DoctorFavouriteMedicine.objects.filter(pk=request.POST.get('fav_id'), doctor=doctor).delete()
            return redirect('doctor_write_prescription', pk=pk)
        if action == 'save_prescription':
            rx, _ = Prescription.objects.update_or_create(
                appointment=appt,
                defaults={
                    'doctor':               doctor,
                    'patient':              appt.patient,
                    'diagnosis':            request.POST.get('diagnosis',''),
                    'general_instructions': request.POST.get('general_instructions',''),
                    'next_visit_date':      request.POST.get('next_visit_date') or None,
                }
            )
            rx.items.all().delete()
            names        = request.POST.getlist('medicine_name[]')
            dosages      = request.POST.getlist('dosage[]')
            frequencies  = request.POST.getlist('frequency[]')
            durations    = request.POST.getlist('duration[]')
            instructions = request.POST.getlist('instructions[]')
            for i, name in enumerate(names):
                if name.strip():
                    PrescriptionItem.objects.create(
                        prescription=rx, medicine_name=name.strip(),
                        dosage=dosages[i] if i<len(dosages) else '',
                        frequency=frequencies[i] if i<len(frequencies) else '',
                        duration=durations[i] if i<len(durations) else '',
                        instructions=instructions[i] if i<len(instructions) else '',
                        order=i,
                    )
            messages.success(request, 'Prescription saved!')
            return redirect('doctor_dashboard')

    return render(request, 'doctor/write_prescription.html', {
        'appointment':  appt, 'prescription': prescription,
        'favourites':   favourites, 'medicines': sorted(MEDICINES),
        'doctor':       doctor,
        'freq_choices': PrescriptionItem.FREQUENCY_CHOICES,
        'inst_choices': PrescriptionItem.INSTRUCTIONS_CHOICES,
    })


@login_required
@role_required('DOCTOR')
def doctor_refer_ot(request, appt_pk):
    doctor = get_object_or_404(Doctor, user=request.user)
    appt   = get_object_or_404(Appointment, pk=appt_pk, doctor=doctor)
    if request.method == 'POST':
        OTReferral.objects.get_or_create(
            appointment=appt,
            defaults={'referring_doctor':doctor, 'patient':appt.patient,
                      'hospital':appt.hospital, 'reason':request.POST.get('reason','')}
        )
        messages.success(request, 'Patient referred for OT.')
    return redirect('doctor_dashboard')


@login_required
@role_required('DOCTOR')
def doctor_postpone_ot(request, pk):
    doctor     = get_object_or_404(Doctor, user=request.user)
    ot_booking = get_object_or_404(OTBooking, pk=pk, surgeon=doctor)
    if request.method == 'POST':
        ot_booking.status          = 'POSTPONED'
        ot_booking.next_date       = request.POST.get('next_date')
        ot_booking.postpone_reason = request.POST.get('reason','')
        ot_booking.save()
        messages.success(request, 'Operation postponed.')
    return redirect('doctor_dashboard')


@login_required
@role_required('DOCTOR')
def doctor_request_leave(request, membership_pk):
    doctor     = get_object_or_404(Doctor, user=request.user)
    membership = get_object_or_404(DoctorHospital, pk=membership_pk, doctor=doctor, status='ACTIVE')
    if request.method == 'POST':
        membership.status = 'LEAVE_REQUESTED'
        membership.reason = request.POST.get('reason','')
        membership.save()
        messages.success(request, 'Leave request sent.')
    return redirect('doctor_dashboard')


@login_required
@role_required('DOCTOR')
def doctor_send_join_request(request):
    doctor = get_object_or_404(Doctor, user=request.user)
    if request.method == 'POST':
        try:
            hospital = Hospital.objects.get(pk=request.POST.get('hospital_id',''))
        except (Hospital.DoesNotExist, ValueError):
            messages.error(request, 'Hospital not found.')
            return redirect('doctor_dashboard')
        obj, created = DoctorJoinRequest.objects.get_or_create(
            doctor=doctor, hospital=hospital,
            defaults={'message':request.POST.get('message',''), 'status':'PENDING'}
        )
        if not created:
            if obj.status == 'REJECTED':
                obj.status = 'PENDING'; obj.save()
                messages.success(request, 'Request re-sent.')
            else:
                messages.info(request, 'Request already pending.')
        else:
            messages.success(request, f'Request sent to {hospital}.')
    return redirect('doctor_dashboard')


# ── HOSPITAL ADMIN ────────────────────────────
@login_required
@role_required('HOSPITAL')
def hospital_dashboard(request):
    hospital = get_object_or_404(Hospital, admin=request.user)
    today    = date.today()

    try:    branding = hospital.branding
    except: branding = HospitalBranding.objects.create(hospital=hospital)

    doctors = Doctor.objects.filter(
        hospital_memberships__hospital=hospital, hospital_memberships__status='ACTIVE'
    ).distinct().select_related('user')

    appointments = Appointment.objects.filter(
        hospital=hospital
    ).select_related('patient__user','doctor__user').order_by('-appointment_date')[:30]

    completed_appointments = Appointment.objects.filter(
        hospital=hospital, status='COMPLETED'
    ).select_related('patient__user','doctor__user').order_by('-appointment_date')[:30]

    raw_patients = Patient.objects.filter(appointments__hospital=hospital).distinct().select_related('user')
    patients = []
    for p in raw_patients:
        last = Appointment.objects.filter(patient=p, hospital=hospital).order_by('-appointment_date').first()
        upcoming_appt = Appointment.objects.filter(
            patient=p, hospital=hospital,
            appointment_date__gte=today, status__in=['PENDING','CONFIRMED']
        ).order_by('appointment_date').first()
        patients.append({
            'user':p.user, 'patient_id':p.patient_id, 'age':p.age,
            'blood_group':p.blood_group, 'profile_picture':p.profile_picture,
            'total_visits':Appointment.objects.filter(patient=p,hospital=hospital).count(),
            'last_doctor':last.doctor if last else None,
            'last_date':last.appointment_date if last else None,
            'upcoming_appt':upcoming_appt,
        })

    staff_list     = HospitalStaff.objects.filter(hospital=hospital, is_active=True).select_related('user').prefetch_related('doctors')
    leave_requests = DoctorHospital.objects.filter(hospital=hospital, status='LEAVE_REQUESTED').select_related('doctor__user')
    join_requests  = DoctorJoinRequest.objects.filter(hospital=hospital, status='PENDING').select_related('doctor__user')
    ot_referrals   = OTReferral.objects.filter(hospital=hospital, status='PENDING').select_related('patient__user','referring_doctor__user')

    return render(request, 'hospital/dashboard.html', {
        'hospital':              hospital,
        'branding':              branding,
        'doctors':               doctors,
        'appointments':          appointments,
        'completed_appointments':completed_appointments,
        'patients':              patients,
        'staff_list':            staff_list,
        'leave_requests':        leave_requests,
        'join_requests':         join_requests,
        'ot_referrals':          ot_referrals,
        'pending_apps':          Appointment.objects.filter(hospital=hospital, status='PENDING').count(),
        'total_beds':            Bed.objects.filter(hospital=hospital).count(),
        'available_beds':        Bed.objects.filter(hospital=hospital, status='AVAILABLE').count(),
        'today':                 today,
    })


@login_required
@role_required('HOSPITAL')
def hospital_update_branding(request):
    hospital = get_object_or_404(Hospital, admin=request.user)
    try:    branding = hospital.branding
    except: branding = HospitalBranding.objects.create(hospital=hospital)

    if request.method == 'POST':
        if 'logo' in request.FILES:
            branding.logo = request.FILES['logo']
        if 'cover_photo' in request.FILES:
            branding.cover_photo = request.FILES['cover_photo']
        branding.save()
        hospital.description = request.POST.get('description', hospital.description)
        hospital.services    = request.POST.get('services', hospital.services)
        hospital.phone       = request.POST.get('phone', hospital.phone)
        hospital.website     = request.POST.get('website', hospital.website)
        hospital.save()
        messages.success(request, 'Hospital profile updated!')
        return redirect('hospital_dashboard')
    return render(request, 'hospital/update_branding.html', {'hospital':hospital,'branding':branding})


@login_required
@role_required('HOSPITAL')
def hospital_register_doctor(request):
    hospital = get_object_or_404(Hospital, admin=request.user)
    form     = AdminDoctorRegistrationForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        d    = form.cleaned_data
        name = f"{d['first_name']} {d.get('last_name','')}".strip()
        raw_password = generate_password()
        username     = generate_username('doc', name)
        while User.objects.filter(username=username).exists():
            username = generate_username('doc', name)
        user = User.objects.create_user(
            username=username, password=raw_password,
            first_name=d['first_name'], last_name=d.get('last_name',''),
            email=d['email'], phone=d.get('phone',''), role='DOCTOR',
        )
        doctor = Doctor(
            user=user, specialist=d['specialist'], appointment_fee=d['appointment_fee'],
            bio=d.get('bio',''), hospital=hospital, registered_by='ADMIN', is_verified=True,
        )
        if d.get('profile_picture'):
            doctor.profile_picture = d['profile_picture']
        doctor.save()
        DoctorHospital.objects.create(doctor=doctor, hospital=hospital, status='ACTIVE')
        send_doctor_credentials(doctor, hospital, raw_password)
        messages.success(request, f'Doctor registered! ID: {doctor.doctor_id}. Credentials emailed.')
        return redirect('hospital_dashboard')
    return render(request, 'hospital/register_doctor.html', {'form':form, 'hospital':hospital})


@login_required
@role_required('HOSPITAL')
def hospital_create_staff(request):
    hospital = get_object_or_404(Hospital, admin=request.user)
    doctors  = Doctor.objects.filter(
        hospital_memberships__hospital=hospital, hospital_memberships__status='ACTIVE'
    ).distinct().select_related('user')

    if request.method == 'POST':
        first_name   = request.POST.get('first_name','')
        last_name    = request.POST.get('last_name','')
        email        = request.POST.get('email','')
        phone        = request.POST.get('phone','')
        doctor_ids   = request.POST.getlist('doctor_ids')
        name         = f"{first_name} {last_name}".strip()
        raw_password = generate_password()
        username     = generate_username('staff', name)
        while User.objects.filter(username=username).exists():
            username = generate_username('staff', name)
        user = User.objects.create_user(
            username=username, password=raw_password,
            first_name=first_name, last_name=last_name,
            email=email, phone=phone, role='STAFF',
        )
        staff = HospitalStaff.objects.create(user=user, hospital=hospital, is_active=True)
        if doctor_ids:
            staff.doctors.set(Doctor.objects.filter(pk__in=doctor_ids))
        send_staff_credentials(staff, raw_password)
        messages.success(request, f'Staff account created. Credentials emailed to {email}.')
        return redirect('hospital_dashboard')
    return render(request, 'hospital/create_staff.html', {'hospital':hospital,'doctors':doctors})


@login_required
@role_required('HOSPITAL')
def hospital_book_appointment(request, doctor_pk):
    hospital  = get_object_or_404(Hospital, admin=request.user)
    doctor    = get_object_or_404(Doctor, pk=doctor_pk)
    schedules = DoctorSchedule.objects.filter(doctor=doctor, hospital=hospital, is_active=True)

    if request.method == 'POST':
        booking_type = request.POST.get('booking_type')
        schedule     = get_object_or_404(DoctorSchedule, id=request.POST.get('schedule_id'), is_active=True)
        symptoms     = request.POST.get('symptoms','')

        if booking_type == 'existing':
            try:
                patient = Patient.objects.get(patient_id=request.POST.get('patient_id','').strip())
            except Patient.DoesNotExist:
                messages.error(request, 'Patient not found.')
                return redirect('hospital_book_appointment', doctor_pk=doctor_pk)
            appt_date = _next_available(schedule)
            serial    = Appointment.next_serial(doctor, appt_date)
            appt      = Appointment.objects.create(
                patient=patient, doctor=doctor, hospital=hospital, schedule=schedule,
                appointment_date=appt_date, appointment_time=schedule.start_time,
                serial_number=serial, symptoms=symptoms, status='CONFIRMED', booked_by='ADMIN',
            )
            send_appointment_confirmation(appt)
            messages.success(request, f'Appointment booked. Serial #{serial} on {appt_date}.')

        elif booking_type == 'new':
            form = AdminPatientRegistrationForm(request.POST)
            if not form.is_valid():
                return render(request, 'hospital/book_appointment.html', {
                    'hospital':hospital,'doctor':doctor,'schedules':schedules,'form':form
                })
            d = form.cleaned_data
            name = f"{d['first_name']} {d.get('last_name','')}".strip()
            raw_password = generate_password()
            username     = generate_username('pat', name)
            while User.objects.filter(username=username).exists():
                username = generate_username('pat', name)
            user = User.objects.create_user(
                username=username, password=raw_password,
                first_name=d['first_name'], last_name=d.get('last_name',''),
                email=d['email'], phone=d.get('phone',''), role='PATIENT',
            )
            patient   = Patient.objects.create(user=user, age=d.get('age') or 0,
                                                blood_group=d.get('blood_group',''), address=d.get('address',''))
            appt_date = _next_available(schedule)
            serial    = Appointment.next_serial(doctor, appt_date)
            appt      = Appointment.objects.create(
                patient=patient, doctor=doctor, hospital=hospital, schedule=schedule,
                appointment_date=appt_date, appointment_time=schedule.start_time,
                serial_number=serial, symptoms=d.get('symptoms',''), status='CONFIRMED', booked_by='ADMIN',
            )
            send_patient_credentials(patient, raw_password, appt)
            messages.success(request, f'Patient registered ({patient.patient_id}) & booked. Serial #{serial}.')
        return redirect('hospital_dashboard')

    form = AdminPatientRegistrationForm()
    return render(request, 'hospital/book_appointment.html', {
        'hospital':hospital,'doctor':doctor,'schedules':schedules,'form':form
    })


@login_required
@role_required('HOSPITAL')
def hospital_complete_appointment(request, pk):
    hospital = get_object_or_404(Hospital, admin=request.user)
    appt     = get_object_or_404(Appointment, pk=pk, hospital=hospital)
    if request.method == 'POST':
        appt.status = 'COMPLETED'; appt.notes = request.POST.get('notes',''); appt.save()
        messages.success(request, 'Appointment completed.')
    return redirect('hospital_dashboard')


@login_required
@role_required('HOSPITAL')
def hospital_approve_appointment(request, pk):
    hospital    = get_object_or_404(Hospital, admin=request.user)
    appt        = get_object_or_404(Appointment, pk=pk, hospital=hospital)
    appt.status = 'CONFIRMED'; appt.save()
    send_appointment_confirmation(appt)
    messages.success(request, 'Appointment confirmed.')
    return redirect('hospital_dashboard')


@login_required
@role_required('HOSPITAL')
def hospital_remove_doctor(request, membership_pk):
    hospital   = get_object_or_404(Hospital, admin=request.user)
    membership = get_object_or_404(DoctorHospital, pk=membership_pk, hospital=hospital)
    if request.method == 'POST':
        doctor   = membership.doctor
        affected = Appointment.objects.filter(doctor=doctor, hospital=hospital, status__in=['PENDING','CONFIRMED'])
        for appt in affected:
            appt.status = 'CANCELLED'; appt.save()
            send_appointment_cancelled_doctor_left(appt, hospital)
        DoctorSchedule.objects.filter(doctor=doctor, hospital=hospital).update(is_active=False)
        membership.status = 'LEFT'; membership.left_at = timezone.now()
        membership.reason = request.POST.get('reason','Removed by admin'); membership.save()
        send_email_safe(f"Removed from {hospital.name}",
            f"Dear {doctor.user.get_full_name() or doctor.user.username},\n\n"
            f"You have been removed from {hospital.name}.\nYour account remains active.\n\nRegards,\n{hospital.name}",
            doctor.user.email)
        messages.success(request, f'Dr. {doctor} removed.')
    return redirect('hospital_dashboard')


@login_required
@role_required('HOSPITAL')
def hospital_accept_leave(request, membership_pk):
    hospital   = get_object_or_404(Hospital, admin=request.user)
    membership = get_object_or_404(DoctorHospital, pk=membership_pk, hospital=hospital, status='LEAVE_REQUESTED')
    if request.method == 'POST':
        doctor   = membership.doctor
        affected = Appointment.objects.filter(doctor=doctor, hospital=hospital, status__in=['PENDING','CONFIRMED'])
        for appt in affected:
            appt.status = 'CANCELLED'; appt.save()
            send_appointment_cancelled_doctor_left(appt, hospital)
        DoctorSchedule.objects.filter(doctor=doctor, hospital=hospital).update(is_active=False)
        membership.status = 'LEFT'; membership.left_at = timezone.now(); membership.save()
        send_email_safe(f"Leave Accepted — {hospital.name}",
            f"Dear {doctor.user.get_full_name() or doctor.user.username},\n\nYour leave has been accepted.\n\nRegards,\n{hospital.name}",
            doctor.user.email)
        messages.success(request, 'Leave accepted.')
    return redirect('hospital_dashboard')


@login_required
@role_required('HOSPITAL')
def hospital_accept_join(request, request_pk):
    hospital     = get_object_or_404(Hospital, admin=request.user)
    join_request = get_object_or_404(DoctorJoinRequest, pk=request_pk, hospital=hospital, status='PENDING')
    if request.method == 'POST':
        doctor = join_request.doctor
        DoctorHospital.objects.update_or_create(doctor=doctor, hospital=hospital,
                                                 defaults={'status':'ACTIVE','left_at':None})
        join_request.status = 'ACCEPTED'; join_request.save()
        send_email_safe(f"Welcome to {hospital.name}!",
            f"Dear {doctor.user.get_full_name() or doctor.user.username},\n\nYou have been accepted at {hospital.name}!\n\nRegards,\n{hospital.name}",
            doctor.user.email)
        messages.success(request, f'Dr. {doctor} added.')
    return redirect('hospital_dashboard')


@login_required
@role_required('HOSPITAL')
def hospital_reject_join(request, request_pk):
    hospital     = get_object_or_404(Hospital, admin=request.user)
    join_request = get_object_or_404(DoctorJoinRequest, pk=request_pk, hospital=hospital, status='PENDING')
    if request.method == 'POST':
        join_request.status = 'REJECTED'; join_request.save()
        messages.success(request, 'Request rejected.')
    return redirect('hospital_dashboard')


@login_required
@role_required('HOSPITAL')
def hospital_manage_beds(request):
    hospital = get_object_or_404(Hospital, admin=request.user)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_ward':
            Ward.objects.create(hospital=hospital, name=request.POST.get('ward_name'), description=request.POST.get('ward_desc',''))
        elif action == 'add_bed':
            ward = Ward.objects.filter(id=request.POST.get('ward_id'), hospital=hospital).first()
            Bed.objects.create(hospital=hospital, ward=ward, bed_number=request.POST.get('bed_number'),
                               bed_type=request.POST.get('bed_type','GENERAL'), daily_cost=request.POST.get('daily_cost',0))
        elif action == 'update_bed':
            bed = get_object_or_404(Bed, id=request.POST.get('bed_id'), hospital=hospital)
            bed.status = request.POST.get('status'); bed.save()
        messages.success(request, 'Done.')
        return redirect('hospital_manage_beds')
    return render(request, 'hospital/manage_beds.html', {
        'hospital':hospital,
        'beds': Bed.objects.filter(hospital=hospital).select_related('ward'),
        'wards':Ward.objects.filter(hospital=hospital),
    })


@login_required
@role_required('HOSPITAL')
def hospital_manage_ot(request):
    hospital = get_object_or_404(Hospital, admin=request.user)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_ot':
            OperationTheatre.objects.create(hospital=hospital, name=request.POST.get('ot_name'))
        elif action == 'book_ot':
            referral = get_object_or_404(OTReferral, id=request.POST.get('referral_id'), hospital=hospital)
            ot       = get_object_or_404(OperationTheatre, id=request.POST.get('ot_id'), hospital=hospital)
            surgeon  = Doctor.objects.filter(id=request.POST.get('surgeon_id')).first()
            OTBooking.objects.create(
                ot=ot, patient=referral.patient, referred_by=referral.referring_doctor,
                surgeon=surgeon, operation_date=request.POST.get('operation_date'),
                operation_time=request.POST.get('operation_time'),
                operation_type=request.POST.get('operation_type'), notes=request.POST.get('notes',''),
            )
            referral.status = 'BOOKED'; referral.save()
        messages.success(request, 'Done.')
        return redirect('hospital_manage_ot')
    doctors = Doctor.objects.filter(hospital_memberships__hospital=hospital, hospital_memberships__status='ACTIVE').distinct().select_related('user')
    return render(request, 'hospital/manage_ot.html', {
        'hospital':hospital,
        'ots':       OperationTheatre.objects.filter(hospital=hospital),
        'ot_bookings':OTBooking.objects.filter(ot__hospital=hospital).select_related('patient__user','surgeon__user','ot'),
        'referrals': OTReferral.objects.filter(hospital=hospital, status='PENDING').select_related('patient__user','referring_doctor__user'),
        'doctors':   doctors,
    })


@login_required
@role_required('HOSPITAL')
def hospital_manage_schedules(request):
    hospital  = get_object_or_404(Hospital, admin=request.user)
    schedules = DoctorSchedule.objects.filter(hospital=hospital).select_related('doctor__user')
    doctors   = Doctor.objects.filter(hospital_memberships__hospital=hospital, hospital_memberships__status='ACTIVE').distinct().select_related('user')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            doctor = get_object_or_404(Doctor, id=request.POST.get('doctor_id'))
            DoctorSchedule.objects.update_or_create(
                doctor=doctor, hospital=hospital, day=request.POST.get('day'),
                defaults={'start_time':request.POST.get('start_time'),'end_time':request.POST.get('end_time'),
                          'max_patients':request.POST.get('max_patients',10),'is_active':True}
            )
            messages.success(request, 'Schedule saved.')
        elif action == 'delete':
            get_object_or_404(DoctorSchedule, id=request.POST.get('schedule_id'), hospital=hospital).delete()
            messages.success(request, 'Schedule removed.')
        return redirect('hospital_manage_schedules')
    return render(request, 'hospital/manage_schedules.html', {
        'hospital':hospital,'schedules':schedules,'doctors':doctors
    })


# ── STAFF ─────────────────────────────────────
@login_required
@staff_required
def staff_dashboard(request):
    staff   = get_object_or_404(HospitalStaff, user=request.user, is_active=True)
    today   = date.today()
    doctors = staff.doctors.all().select_related('user')

    # Filter by doctor if selected
    selected_doctor_id = request.GET.get('doctor')
    if selected_doctor_id:
        try:
            selected_doctor = doctors.get(pk=selected_doctor_id)
        except Doctor.DoesNotExist:
            selected_doctor = doctors.first()
    else:
        selected_doctor = doctors.first()

    today_appointments = []
    if selected_doctor:
        today_appointments = Appointment.objects.filter(
            doctor=selected_doctor,
            hospital=staff.hospital,
            appointment_date=today,
        ).select_related('patient__user').order_by('serial_number')

    return render(request, 'staff/dashboard.html', {
        'staff':              staff,
        'doctors':            doctors,
        'selected_doctor':    selected_doctor,
        'today_appointments': today_appointments,
        'today':              today,
    })


@login_required
@staff_required
def staff_update_appointment(request, pk):
    staff = get_object_or_404(HospitalStaff, user=request.user, is_active=True)
    appt  = get_object_or_404(Appointment, pk=pk, hospital=staff.hospital)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'mark_paid':
            appt.is_paid = True; appt.save()
            messages.success(request, 'Marked as paid.')
        elif action == 'complete':
            appt.status = 'COMPLETED'; appt.save()
            messages.success(request, 'Appointment completed.')
        elif action == 'incomplete':
            appt.status = 'INCOMPLETE'; appt.save()
            messages.success(request, 'Marked as incomplete.')
        elif action == 'add_referral':
            ref_name       = request.POST.get('ref_name','')
            discounted_fee = request.POST.get('discounted_fee', 0)
            if ref_name:
                Referral.objects.update_or_create(
                    appointment=appt,
                    defaults={
                        'ref_name':       ref_name,
                        'original_fee':   appt.doctor.appointment_fee,
                        'discounted_fee': int(discounted_fee),
                        'created_by':     request.user,
                    }
                )
                messages.success(request, f'Referral "{ref_name}" added.')
    return redirect(f"{request.build_absolute_uri('/staff/')}?doctor={appt.doctor_id}")


@login_required
@staff_required
def staff_book_walkin(request):
    staff   = get_object_or_404(HospitalStaff, user=request.user, is_active=True)
    doctors = staff.doctors.all().select_related('user')

    if request.method == 'POST':
        doctor_pk = request.POST.get('doctor_id')
        doctor    = get_object_or_404(Doctor, pk=doctor_pk)
        schedule  = DoctorSchedule.objects.filter(
            doctor=doctor, hospital=staff.hospital, is_active=True
        ).first()

        if not schedule:
            messages.error(request, 'No active schedule for this doctor today.')
            return redirect('staff_dashboard')

        booking_type = request.POST.get('booking_type')
        symptoms     = request.POST.get('symptoms','')

        if booking_type == 'existing':
            try:
                patient = Patient.objects.get(patient_id=request.POST.get('patient_id','').strip())
            except Patient.DoesNotExist:
                messages.error(request, 'Patient not found.')
                return redirect('staff_book_walkin')
        else:
            first_name = request.POST.get('first_name','')
            email      = request.POST.get('email','')
            phone      = request.POST.get('phone','')
            name       = f"{first_name} {request.POST.get('last_name','')}".strip()
            raw_pw     = generate_password()
            username   = generate_username('pat', name)
            while User.objects.filter(username=username).exists():
                username = generate_username('pat', name)
            user = User.objects.create_user(
                username=username, password=raw_pw,
                first_name=first_name, last_name=request.POST.get('last_name',''),
                email=email, phone=phone, role='PATIENT',
            )
            patient = Patient.objects.create(user=user, age=request.POST.get('age') or 0)
            send_patient_credentials(patient, raw_pw)

        appt_date = _next_available(schedule)
        if not appt_date:
            messages.error(request, 'No slots available.')
            return redirect('staff_dashboard')

        serial = Appointment.next_serial(doctor, appt_date)
        Appointment.objects.create(
            patient=patient, doctor=doctor, hospital=staff.hospital, schedule=schedule,
            appointment_date=appt_date, appointment_time=schedule.start_time,
            serial_number=serial, symptoms=symptoms, status='CONFIRMED', booked_by='STAFF',
        )
        messages.success(request, f'Walk-in booked. Serial #{serial}.')
        return redirect('staff_dashboard')

    return render(request, 'staff/book_walkin.html', {
        'staff': staff, 'doctors': doctors,
    })


# ── OAUTH SIGNAL ──────────────────────────────
from allauth.socialaccount.signals import pre_social_login, social_account_added
from allauth.exceptions import ImmediateHttpResponse
from django.dispatch import receiver
from django.shortcuts import redirect as dj_redirect

@receiver(pre_social_login)
def handle_social_login(sender, request, sociallogin, **kwargs):
    if sociallogin.is_existing:
        return
    email = sociallogin.account.extra_data.get('email','')
    if email:
        try:
            existing_user = User.objects.get(email=email)
            sociallogin.connect(request, existing_user)
            raise ImmediateHttpResponse(dj_redirect('dashboard_redirect'))
        except User.DoesNotExist:
            pass

@receiver(social_account_added)
def set_role_on_social_signup(sender, request, sociallogin, **kwargs):
    user = sociallogin.user
    if not user.role:
        user.role = 'PATIENT'
        user.save()
        try:
            user.patient_profile
        except Patient.DoesNotExist:
            p = Patient(user=user)
            p.save()
            send_welcome_patient(p)
