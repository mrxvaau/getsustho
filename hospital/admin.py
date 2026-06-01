from django.contrib import admin
from .models import (
    Hospital, HospitalBranding, HospitalStaff,
    Doctor, DoctorQualification, DoctorVerification,
    DoctorHospital, DoctorJoinRequest, DoctorSchedule,
    Patient, Appointment, Referral,
    Ward, Bed, BedBooking,
    OperationTheatre, OTBooking, OTReferral,
    DoctorFavouriteMedicine, Prescription, PrescriptionItem,
    BlogPost, ContactMessage, PasswordResetOTP,
)

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name','location','phone','email')

@admin.register(HospitalStaff)
class HospitalStaffAdmin(admin.ModelAdmin):
    list_display = ('__str__','hospital','is_active')
    filter_horizontal = ('doctors',)

from django.utils.html import format_html


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = (
        'doctor_id',
        'image_preview',
        'doctor_name',
        'specialist',
        'appointment_fee',
        'is_verified',
        'is_available',
        'registered_by',
        'show_on_landing',
        'landing_order',
    )

    list_editable = (
        'show_on_landing',
        'landing_order',
    )

    list_filter = (
        'show_on_landing',
        'specialist',
        'is_verified',
        'is_available',
        'registered_by',
    )

    search_fields = (
        'doctor_id',
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
        'specialist',
    )

    ordering = (
        'landing_order',
        'doctor_id',
    )

    readonly_fields = (
        'image_preview',
    )

    def doctor_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    doctor_name.short_description = 'Doctor'

    def image_preview(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" style="width:55px;height:55px;object-fit:cover;border-radius:8px;" />',
                obj.profile_picture.url
            )
        return 'No image'
    image_preview.short_description = 'Image'

@admin.register(DoctorVerification)
class DoctorVerificationAdmin(admin.ModelAdmin):
    list_display = ('doctor','license_number','status','submitted_at')
    list_filter  = ('status',)

@admin.register(DoctorQualification)
class DoctorQualificationAdmin(admin.ModelAdmin):
    list_display = ('doctor','degree','institution','year')

@admin.register(DoctorHospital)
class DoctorHospitalAdmin(admin.ModelAdmin):
    list_display = ('doctor','hospital','status','joined_at')
    list_filter  = ('status',)

@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ('doctor','hospital','day','start_time','end_time','max_patients','is_active')
    list_filter  = ('hospital','day','is_active')

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('patient_id','__str__','age','blood_group')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('serial_number','patient','doctor','hospital','appointment_date','status','is_paid','booked_by')
    list_filter  = ('status','appointment_date','hospital')

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('ref_name','appointment','original_fee','discounted_fee','created_by','created_at')

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display  = ('title','author','is_published','published_at')
    list_filter   = ('is_published',)
    prepopulated_fields = {'slug': ('title',)}

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name','email','phone','created_at','is_read')
    list_filter  = ('is_read',)

admin.site.register(HospitalBranding)
admin.site.register(DoctorJoinRequest)
admin.site.register(Ward)
admin.site.register(Bed)
admin.site.register(BedBooking)
admin.site.register(OperationTheatre)
admin.site.register(OTBooking)
admin.site.register(OTReferral)
admin.site.register(DoctorFavouriteMedicine)
admin.site.register(Prescription)
admin.site.register(PrescriptionItem)
admin.site.register(PasswordResetOTP)
