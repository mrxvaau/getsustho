from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from .models import User
from hospital.models import Hospital, Doctor, Patient, DoctorSchedule, SPECIALTIES

BLOOD_CHOICES = [('','—'),('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),
                 ('AB+','AB+'),('AB-','AB-'),('O+','O+'),('O-','O-')]

DISPOSABLE_DOMAINS = [
    'mailinator.com','guerrillamail.com','tempmail.com','throwaway.email',
    'yopmail.com','sharklasers.com','trashmail.com','trashmail.net',
    'dispostable.com','maildrop.cc','fakeinbox.com','temp-mail.org',
    'getnada.com','mohmal.com','mailnull.com','spamgourmet.com',
]

def validate_real_email(email):
    validator = EmailValidator()
    try:
        validator(email)
    except ValidationError:
        raise ValidationError('Enter a valid email address.')
    domain = email.split('@')[-1].lower()
    if domain in DISPOSABLE_DOMAINS:
        raise ValidationError('Disposable email addresses are not allowed.')
    return email


class BaseUserForm(UserCreationForm):
    first_name = forms.CharField(max_length=50)
    last_name  = forms.CharField(max_length=50, required=False)
    phone      = forms.CharField(max_length=15, required=True)
    email      = forms.EmailField(required=True, validators=[validate_real_email])

    class Meta:
        model  = User
        fields = ('username','first_name','last_name','email','phone','password1','password2')

    def clean_email(self):
        email = self.cleaned_data.get('email','').lower().strip()
        validate_real_email(email)
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email address is already registered.')
        return email


class PatientRegistrationForm(BaseUserForm):
    age = forms.IntegerField(min_value=0, required=False)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role  = 'PATIENT'
        user.phone = self.cleaned_data.get('phone','')
        if commit:
            user.save()
            Patient.objects.create(user=user, age=self.cleaned_data.get('age') or 0)
        return user


class HospitalRegistrationForm(BaseUserForm):
    hospital_name = forms.CharField(max_length=200)
    location      = forms.CharField(max_length=200)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role  = 'HOSPITAL'
        user.phone = self.cleaned_data.get('phone','')
        if commit:
            user.save()
            hospital = Hospital.objects.create(
                admin=user,
                name=self.cleaned_data['hospital_name'],
                location=self.cleaned_data['location'],
                email=self.cleaned_data['email'],
            )
            from hospital.models import HospitalBranding
            HospitalBranding.objects.create(hospital=hospital)
        return user


class DoctorSelfRegistrationForm(BaseUserForm):
    specialist         = forms.ChoiceField(choices=SPECIALTIES)
    appointment_fee    = forms.IntegerField(min_value=0, initial=0)
    workplace          = forms.CharField(max_length=300)
    bio                = forms.CharField(widget=forms.Textarea(attrs={'rows':3}), required=False)
    profile_picture    = forms.ImageField(required=True)
    license_number     = forms.CharField(max_length=100)
    degree_certificate = forms.ImageField(required=True)
    national_id_photo  = forms.ImageField(required=True)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role      = 'DOCTOR'
        user.phone     = self.cleaned_data.get('phone','')
        user.is_active = False
        if commit:
            user.save()
        return user


class AdminDoctorRegistrationForm(forms.Form):
    first_name      = forms.CharField(max_length=50)
    last_name       = forms.CharField(max_length=50, required=False)
    email           = forms.EmailField(validators=[validate_real_email])
    phone           = forms.CharField(max_length=15, required=True)
    specialist      = forms.ChoiceField(choices=SPECIALTIES)
    appointment_fee = forms.IntegerField(min_value=0)
    bio             = forms.CharField(widget=forms.Textarea(attrs={'rows':3}), required=False)
    profile_picture = forms.ImageField(required=True)


class AdminPatientRegistrationForm(forms.Form):
    first_name  = forms.CharField(max_length=50)
    last_name   = forms.CharField(max_length=50, required=False)
    email       = forms.EmailField(validators=[validate_real_email])
    phone       = forms.CharField(max_length=15, required=True)
    age         = forms.IntegerField(min_value=0, required=False)
    blood_group = forms.ChoiceField(choices=BLOOD_CHOICES, required=False)
    address     = forms.CharField(widget=forms.Textarea(attrs={'rows':2}), required=False)
    symptoms    = forms.CharField(widget=forms.Textarea(attrs={'rows':3}), required=False)


class PatientProfileForm(forms.ModelForm):
    class Meta:
        model   = Patient
        fields  = ('age','blood_group','address','medical_notes','profile_picture')
        widgets = {'profile_picture': forms.FileInput()}


class PatientAccountForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = ('username','first_name','last_name','phone')


class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model   = Doctor
        fields  = ('specialist','appointment_fee','bio','workplace','profile_picture')
        widgets = {'profile_picture': forms.FileInput()}


class DoctorAccountForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = ('username','first_name','last_name','email','phone')

    def clean_email(self):
        email = self.cleaned_data.get('email','').lower().strip()
        validate_real_email(email)
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise ValidationError('This email is already in use.')
        return email


class DoctorScheduleForm(forms.ModelForm):
    class Meta:
        model   = DoctorSchedule
        fields  = ('hospital','day','start_time','end_time','max_patients','is_active')
        widgets = {
            'start_time': forms.TimeInput(attrs={'type':'time'}),
            'end_time':   forms.TimeInput(attrs={'type':'time'}),
        }


class ContactForm(forms.Form):
    name    = forms.CharField(max_length=100)
    email   = forms.EmailField(validators=[validate_real_email])
    phone   = forms.CharField(max_length=20, required=False)
    message = forms.CharField(widget=forms.Textarea(attrs={'rows':5}))
