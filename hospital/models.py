from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
import random, string

User = settings.AUTH_USER_MODEL


def generate_password(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_username(prefix, name):
    base   = f"{prefix}_{name.lower().replace(' ','_')[:10]}"
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{base}_{suffix}"

def doctor_pic_path(instance, filename):
    ext = filename.split('.')[-1]
    return f"profiles/doctors/{instance.pk or 'new'}_{random.randint(1000,9999)}.{ext}"

def patient_pic_path(instance, filename):
    ext = filename.split('.')[-1]
    return f"profiles/patients/{instance.pk or 'new'}_{random.randint(1000,9999)}.{ext}"

def verification_doc_path(instance, filename):
    return f"verifications/{instance.doctor.pk or 'new'}_{filename}"

def hospital_logo_path(instance, filename):
    ext = filename.split('.')[-1]
    return f"hospital/logos/{instance.hospital.pk}_{random.randint(1000,9999)}.{ext}"

def hospital_cover_path(instance, filename):
    ext = filename.split('.')[-1]
    return f"hospital/covers/{instance.hospital.pk}_{random.randint(1000,9999)}.{ext}"

def blog_image_path(instance, filename):
    ext = filename.split('.')[-1]
    return f"blog/{instance.slug or 'post'}_{random.randint(1000,9999)}.{ext}"


SPECIALTIES = (
    ('Cardiology','Cardiology'),('Neurology','Neurology'),('Pediatrics','Pediatrics'),
    ('Orthopedics','Orthopedics'),('Dermatology','Dermatology'),
    ('General Medicine','General Medicine'),('Gynecology','Gynecology'),
    ('Ophthalmology','Ophthalmology'),('ENT','ENT (Ear, Nose & Throat)'),
    ('Psychiatry','Psychiatry'),('Urology','Urology'),('Oncology','Oncology'),
    ('Gastroenterology','Gastroenterology'),('Endocrinology','Endocrinology'),
    ('Nephrology','Nephrology'),('Pulmonology','Pulmonology'),
    ('Rheumatology','Rheumatology'),('Hematology','Hematology'),
    ('Radiology','Radiology'),('Anesthesiology','Anesthesiology'),
    ('Surgery','General Surgery'),('Dentistry','Dentistry'),
    ('Physiotherapy','Physiotherapy'),('Pathology','Pathology'),('Other','Other'),
)

DAYS = (
    ('SAT','Saturday'),('SUN','Sunday'),('MON','Monday'),
    ('TUE','Tuesday'),('WED','Wednesday'),('THU','Thursday'),('FRI','Friday'),
)

MEDICINES = [
    "Amoxicillin","Azithromycin","Ciprofloxacin","Metronidazole","Doxycycline",
    "Clarithromycin","Cefixime","Ceftriaxone","Clindamycin","Levofloxacin",
    "Paracetamol","Ibuprofen","Naproxen","Aspirin","Diclofenac","Tramadol",
    "Omeprazole","Pantoprazole","Ranitidine","Esomeprazole","Domperidone",
    "Cetirizine","Loratadine","Fexofenadine","Chlorphenamine","Montelukast",
    "Amlodipine","Atenolol","Metoprolol","Lisinopril","Losartan","Furosemide",
    "Atorvastatin","Rosuvastatin","Simvastatin","Metformin","Glibenclamide",
    "Salbutamol","Ipratropium","Budesonide","Fluticasone","Theophylline",
    "Amitriptyline","Sertraline","Fluoxetine","Escitalopram","Diazepam",
    "Levothyroxine","Prednisolone","Hydrocortisone","Dexamethasone",
    "Vitamin C","Vitamin D3","Vitamin B12","Folic Acid","Ferrous Sulfate",
    "Clotrimazole","Miconazole","Terbinafine","Fluconazole","Albendazole",
    "Tamsulosin","Sildenafil","Methotrexate","Hydroxychloroquine","Colchicine",
]


class Hospital(models.Model):
    admin       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='hospital_admin')
    name        = models.CharField(max_length=200)
    location    = models.CharField(max_length=200)
    phone       = models.CharField(max_length=20, blank=True)
    email       = models.EmailField(blank=True)
    description = models.TextField(blank=True)
    services    = models.TextField(blank=True, help_text='Comma separated services')
    website     = models.URLField(blank=True)

    def __str__(self): return self.name

    def get_services_list(self):
        return [s.strip() for s in self.services.split(',') if s.strip()]


class HospitalBranding(models.Model):
    hospital    = models.OneToOneField(Hospital, on_delete=models.CASCADE, related_name='branding')
    logo        = models.ImageField(upload_to=hospital_logo_path, blank=True, null=True)
    cover_photo = models.ImageField(upload_to=hospital_cover_path, blank=True, null=True)
    def __str__(self): return f"Branding — {self.hospital.name}"


class HospitalStaff(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    hospital   = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='staff_members')
    doctors    = models.ManyToManyField('Doctor', blank=True, related_name='assigned_staff')
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.user.get_full_name() or self.user.username} — Staff @ {self.hospital.name}"


class Doctor(models.Model):
    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    doctor_id       = models.CharField(max_length=20, unique=True, blank=True)
    specialist      = models.CharField(max_length=100, choices=SPECIALTIES)
    appointment_fee = models.PositiveIntegerField(default=0)
    bio             = models.TextField(blank=True)
    is_available    = models.BooleanField(default=True)
    profile_picture = models.ImageField(upload_to=doctor_pic_path, blank=True, null=True)
    workplace       = models.CharField(max_length=300, blank=True)
    hospital        = models.ForeignKey(Hospital, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='primary_doctors')
    is_verified     = models.BooleanField(default=False)
    registered_by   = models.CharField(max_length=10, default='ADMIN')
    show_on_landing = models.BooleanField(default=False)
    landing_order   = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.doctor_id:
            super().save(*args, **kwargs)
            self.doctor_id = f"DOC-{self.id:04d}"
            Doctor.objects.filter(pk=self.pk).update(doctor_id=self.doctor_id)
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username} ({self.doctor_id})"

    def get_hospitals(self):
        return Hospital.objects.filter(
            schedules__doctor=self, schedules__is_active=True
        ).distinct()


class DoctorQualification(models.Model):
    doctor      = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='qualifications')
    degree      = models.CharField(max_length=100)
    institution = models.CharField(max_length=200)
    year        = models.PositiveIntegerField(null=True, blank=True)
    order       = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ['order','-year']
    def __str__(self): return f"{self.degree} — {self.institution}"


class DoctorVerification(models.Model):
    STATUS = (('PENDING','Pending'),('APPROVED','Approved'),('REJECTED','Rejected'))
    doctor             = models.OneToOneField(Doctor, on_delete=models.CASCADE, related_name='verification')
    license_number     = models.CharField(max_length=100)
    degree_certificate = models.ImageField(upload_to=verification_doc_path)
    national_id_photo  = models.ImageField(upload_to=verification_doc_path)
    workplace_address  = models.TextField()
    status             = models.CharField(max_length=10, choices=STATUS, default='PENDING')
    rejection_reason   = models.TextField(blank=True)
    submitted_at       = models.DateTimeField(auto_now_add=True)
    reviewed_at        = models.DateTimeField(null=True, blank=True)
    reviewed_by        = models.ForeignKey(User, on_delete=models.SET_NULL,
                                           null=True, blank=True, related_name='verifications_reviewed')
    def __str__(self): return f"Verification — {self.doctor} [{self.status}]"


class DoctorHospital(models.Model):
    STATUS = (('ACTIVE','Active'),('LEAVE_REQUESTED','Leave Requested'),
              ('REMOVE_REQUESTED','Remove Requested'),('LEFT','Left'))
    doctor    = models.ForeignKey(Doctor,   on_delete=models.CASCADE, related_name='hospital_memberships')
    hospital  = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='doctor_memberships')
    status    = models.CharField(max_length=20, choices=STATUS, default='ACTIVE')
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at   = models.DateTimeField(null=True, blank=True)
    reason    = models.TextField(blank=True)
    class Meta:
        unique_together = ('doctor','hospital')
    def __str__(self): return f"{self.doctor} @ {self.hospital} [{self.status}]"


class DoctorJoinRequest(models.Model):
    STATUS = (('PENDING','Pending'),('ACCEPTED','Accepted'),('REJECTED','Rejected'))
    doctor       = models.ForeignKey(Doctor,   on_delete=models.CASCADE, related_name='join_requests')
    hospital     = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='join_requests')
    status       = models.CharField(max_length=20, choices=STATUS, default='PENDING')
    message      = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('doctor','hospital')
    def __str__(self): return f"{self.doctor} -> {self.hospital} [{self.status}]"


class DoctorSchedule(models.Model):
    doctor       = models.ForeignKey(Doctor,   on_delete=models.CASCADE, related_name='schedules')
    hospital     = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='schedules')
    day          = models.CharField(max_length=3, choices=DAYS)
    start_time   = models.TimeField()
    end_time     = models.TimeField()
    max_patients = models.PositiveIntegerField(default=10)
    is_active    = models.BooleanField(default=True)
    class Meta:
        unique_together = ('doctor','hospital','day')
        ordering        = ['day','start_time']
    def __str__(self):
        return f"{self.doctor} @ {self.hospital} - {self.get_day_display()} {self.start_time:%H:%M}"
    def booked_count(self, date):
        return self.appointments.filter(appointment_date=date, status__in=['PENDING','CONFIRMED']).count()
    def is_full(self, date):
        return self.booked_count(date) >= self.max_patients
    def next_available_date(self):
        from datetime import date, timedelta
        day_map = {'MON':0,'TUE':1,'WED':2,'THU':3,'FRI':4,'SAT':5,'SUN':6}
        target  = day_map[self.day]
        check   = date.today()
        if check.weekday() == target and not self.is_full(check):
            return check
        for _ in range(60):
            check += timedelta(days=1)
            if check.weekday() == target and not self.is_full(check):
                return check
        return None


class Patient(models.Model):
    BLOOD = (('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),
             ('AB+','AB+'),('AB-','AB-'),('O+','O+'),('O-','O-'))
    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    patient_id      = models.CharField(max_length=20, unique=True, blank=True)
    age             = models.PositiveIntegerField(null=True, blank=True)
    blood_group     = models.CharField(max_length=5, choices=BLOOD, blank=True)
    address         = models.TextField(blank=True)
    medical_notes   = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to=patient_pic_path, blank=True, null=True)
    def save(self, *args, **kwargs):
        if not self.patient_id:
            super().save(*args, **kwargs)
            self.patient_id = f"PAT-{self.id:04d}"
            Patient.objects.filter(pk=self.pk).update(patient_id=self.patient_id)
        else:
            super().save(*args, **kwargs)
    def __str__(self): return f"{self.user.get_full_name() or self.user.username} ({self.patient_id})"


class Appointment(models.Model):
    STATUS = (('PENDING','Pending'),('CONFIRMED','Confirmed'),
              ('COMPLETED','Completed'),('INCOMPLETE','Incomplete'),('CANCELLED','Cancelled'))
    patient          = models.ForeignKey(Patient,        on_delete=models.CASCADE, related_name='appointments')
    doctor           = models.ForeignKey(Doctor,         on_delete=models.CASCADE, related_name='appointments')
    hospital         = models.ForeignKey(Hospital,       on_delete=models.CASCADE, related_name='appointments')
    schedule         = models.ForeignKey(DoctorSchedule, on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    serial_number    = models.PositiveIntegerField()
    symptoms         = models.TextField(blank=True)
    notes            = models.TextField(blank=True)
    status           = models.CharField(max_length=20, choices=STATUS, default='PENDING')
    is_extra         = models.BooleanField(default=False)
    booked_by        = models.CharField(max_length=10, default='SELF')
    is_paid          = models.BooleanField(default=False)
    created_at       = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('doctor','appointment_date','serial_number')
        ordering        = ['appointment_date','serial_number']
    def __str__(self):
        return f"Serial {self.serial_number} - {self.patient} with {self.doctor} on {self.appointment_date}"
    @classmethod
    def next_serial(cls, doctor, date):
        last = cls.objects.filter(
            doctor=doctor, appointment_date=date,
            status__in=['PENDING','CONFIRMED','COMPLETED']
        ).order_by('-serial_number').first()
        return (last.serial_number + 1) if last else 1


class Referral(models.Model):
    appointment    = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='referral')
    ref_name       = models.CharField(max_length=200)
    original_fee   = models.PositiveIntegerField()
    discounted_fee = models.PositiveIntegerField()
    created_by     = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, related_name='referrals_created')
    created_at     = models.DateTimeField(auto_now_add=True)
    @property
    def discount_amount(self): return self.original_fee - self.discounted_fee
    def __str__(self): return f"Ref: {self.ref_name} - {self.appointment}"


class Ward(models.Model):
    hospital    = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='wards')
    name        = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    def __str__(self): return f"{self.hospital.name} - {self.name}"


class Bed(models.Model):
    STATUS = (('AVAILABLE','Available'),('BOOKED','Booked'),
              ('OCCUPIED','Occupied'),('MAINTENANCE','Maintenance'))
    TYPE   = (('GENERAL','General'),('PRIVATE','Private'),
              ('ICU','ICU'),('VIP','VIP Suite'),('CABIN','Cabin'))
    hospital   = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='beds')
    ward       = models.ForeignKey(Ward, on_delete=models.SET_NULL, null=True, blank=True, related_name='beds')
    bed_number = models.CharField(max_length=20)
    bed_type   = models.CharField(max_length=20, choices=TYPE, default='GENERAL')
    status     = models.CharField(max_length=20, choices=STATUS, default='AVAILABLE')
    daily_cost = models.PositiveIntegerField(default=0)
    class Meta:
        unique_together = ('hospital','bed_number')
        ordering        = ['ward','bed_number']
    def __str__(self): return f"{self.bed_number} ({self.get_bed_type_display()}) - {self.get_status_display()}"


class BedBooking(models.Model):
    STATUS = (('BOOKED','Booked'),('ADMITTED','Admitted'),
              ('DISCHARGED','Discharged'),('CANCELLED','Cancelled'))
    bed            = models.ForeignKey(Bed, on_delete=models.CASCADE, related_name='bookings')
    patient        = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='bed_bookings')
    admitted_by    = models.ForeignKey(User, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='bed_admissions')
    check_in_date  = models.DateField()
    check_out_date = models.DateField(null=True, blank=True)
    status         = models.CharField(max_length=20, choices=STATUS, default='BOOKED')
    notes          = models.TextField(blank=True)
    booked_at      = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.patient} - Bed {self.bed.bed_number} ({self.status})"


class OperationTheatre(models.Model):
    hospital     = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='ots')
    name         = models.CharField(max_length=100)
    description  = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    def __str__(self): return f"{self.hospital.name} - {self.name}"


class OTBooking(models.Model):
    STATUS = (('SCHEDULED','Scheduled'),('IN_PROGRESS','In Progress'),
              ('COMPLETED','Completed'),('POSTPONED','Postponed'),('CANCELLED','Cancelled'))
    ot               = models.ForeignKey(OperationTheatre, on_delete=models.CASCADE, related_name='bookings')
    patient          = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='ot_bookings')
    referred_by      = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, related_name='ot_referrals')
    surgeon          = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, related_name='ot_surgeries')
    operation_date   = models.DateField()
    operation_time   = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    operation_type   = models.CharField(max_length=200)
    notes            = models.TextField(blank=True)
    status           = models.CharField(max_length=20, choices=STATUS, default='SCHEDULED')
    next_date        = models.DateField(null=True, blank=True)
    postpone_reason  = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['operation_date','operation_time']
    def __str__(self): return f"OT: {self.patient} - {self.operation_type} on {self.operation_date}"


class OTReferral(models.Model):
    STATUS = (('PENDING','Pending'),('APPROVED','Approved'),
              ('REJECTED','Rejected'),('BOOKED','OT Booked'))
    appointment      = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='ot_referral')
    referring_doctor = models.ForeignKey(Doctor,   on_delete=models.CASCADE, related_name='referrals_made')
    patient          = models.ForeignKey(Patient,  on_delete=models.CASCADE, related_name='ot_referrals')
    hospital         = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='ot_referrals')
    reason           = models.TextField()
    status           = models.CharField(max_length=20, choices=STATUS, default='PENDING')
    referred_at      = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Referral: {self.patient} by {self.referring_doctor} [{self.status}]"


class DoctorFavouriteMedicine(models.Model):
    doctor            = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='favourite_medicines')
    medicine_name     = models.CharField(max_length=200)
    default_dosage    = models.CharField(max_length=100, blank=True)
    default_frequency = models.CharField(max_length=100, blank=True)
    default_duration  = models.CharField(max_length=100, blank=True)
    order             = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ['order','medicine_name']
    def __str__(self): return f"{self.doctor} - {self.medicine_name}"


class Prescription(models.Model):
    appointment          = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='prescription')
    doctor               = models.ForeignKey(Doctor,  on_delete=models.CASCADE, related_name='prescriptions')
    patient              = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
    diagnosis            = models.TextField(blank=True)
    general_instructions = models.TextField(blank=True)
    next_visit_date      = models.DateField(null=True, blank=True)
    created_at           = models.DateTimeField(auto_now_add=True)
    updated_at           = models.DateTimeField(auto_now=True)
    def __str__(self): return f"Rx - {self.patient} by {self.doctor}"


class PrescriptionItem(models.Model):
    FREQUENCY_CHOICES = (
        ('Once daily','Once daily'),('Twice daily','Twice daily'),
        ('Three times daily','Three times daily'),('Four times daily','Four times daily'),
        ('Every 8 hours','Every 8 hours'),('Every 6 hours','Every 6 hours'),
        ('At bedtime','At bedtime'),('As needed','As needed'),
        ('Once weekly','Once weekly'),('Other','Other'),
    )
    INSTRUCTIONS_CHOICES = (
        ('Before food','Before food'),('After food','After food'),
        ('With food','With food'),('With water','With water'),
        ('Empty stomach','Empty stomach'),('At bedtime','At bedtime'),('As directed','As directed'),
    )
    prescription  = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medicine_name = models.CharField(max_length=200)
    dosage        = models.CharField(max_length=100, blank=True)
    frequency     = models.CharField(max_length=50, blank=True, choices=FREQUENCY_CHOICES)
    duration      = models.CharField(max_length=100, blank=True)
    instructions  = models.CharField(max_length=100, blank=True, choices=INSTRUCTIONS_CHOICES)
    order         = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ['order']
    def __str__(self): return f"{self.medicine_name} - {self.dosage}"


class BlogPost(models.Model):
    title        = models.CharField(max_length=300)
    slug         = models.SlugField(max_length=320, unique=True, blank=True)
    content      = models.TextField()
    image        = models.ImageField(upload_to=blog_image_path, blank=True, null=True)
    author       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='blog_posts')
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-published_at','-created_at']
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            orig, count = self.slug, 1
            while BlogPost.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{orig}-{count}"
                count += 1
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
    def __str__(self): return self.title


class ContactMessage(models.Model):
    name       = models.CharField(max_length=100)
    email      = models.EmailField()
    phone      = models.CharField(max_length=20, blank=True)
    message    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read    = models.BooleanField(default=False)
    class Meta:
        ordering = ['-created_at']
    def __str__(self): return f"{self.name} - {self.email}"


class PasswordResetOTP(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_otps')
    otp        = models.CharField(max_length=6)
    is_used    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    @property
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    @classmethod
    def generate(cls, user):
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        otp      = ''.join(random.choices(string.digits, k=6))
        expires  = timezone.now() + timezone.timedelta(minutes=10)
        return cls.objects.create(user=user, otp=otp, expires_at=expires)

    def __str__(self): return f"OTP {self.otp} - {self.user}"
