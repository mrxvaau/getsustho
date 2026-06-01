from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from hospital.models import Doctor

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display  = ('username','email','first_name','last_name','role','phone','is_active')
    list_filter   = ('role','is_active')
    fieldsets     = UserAdmin.fieldsets + (('Extra',{'fields':('role','phone')}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Extra',{'fields':('role','phone')}),)

