from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('',                              views.landing,                   name='landing'),
    path('doctor/<str:doctor_id>/',       views.doctor_public_profile,     name='doctor_public_profile'),
    path('hospital/<int:hospital_id>/',   views.hospital_public_profile,   name='hospital_public_profile'),
    path('blog/',                         views.blog_list,                 name='blog_list'),
    path('blog/<slug:slug>/',             views.blog_detail,               name='blog_detail'),

    # Auth
    path('login/',                        views.login_view,                name='login'),
    path('logout/',                       views.logout_view,               name='logout'),
    path('go/',                           views.dashboard_redirect,        name='dashboard_redirect'),
    path('register/patient/',             views.patient_register,          name='patient_register'),
    path('register/hospital/',            views.hospital_register,         name='hospital_register'),
    path('register/doctor/',              views.doctor_self_register,      name='doctor_self_register'),

    # Forgot password
    path('forgot-password/',              views.forgot_password,           name='forgot_password'),
    path('verify-otp/',                   views.verify_otp,                name='verify_otp'),
    path('reset-password/',               views.reset_password,            name='reset_password'),

    # Super-admin
    path('superadmin/',                                   views.superadmin_dashboard,          name='superadmin_dashboard'),
    path('superadmin/doctors/',                           views.superadmin_all_doctors,        name='superadmin_all_doctors'),
    path(
    'superadmin/doctors/<str:doctor_id>/toggle-landing/',
    views.toggle_doctor_landing,
    name='toggle_doctor_landing'
),
    path('superadmin/hospitals/',                         views.superadmin_all_hospitals,      name='superadmin_all_hospitals'),
    path('superadmin/patients/',                          views.superadmin_all_patients,       name='superadmin_all_patients'),
    path('superadmin/completed/',                         views.superadmin_completed_patients, name='superadmin_completed_patients'),
    path('superadmin/verify/<int:pk>/',                   views.superadmin_review_doctor,      name='superadmin_review_doctor'),
    path('superadmin/verify/<int:pk>/approve/',           views.superadmin_approve_doctor,     name='superadmin_approve_doctor'),
    path('superadmin/verify/<int:pk>/reject/',            views.superadmin_reject_doctor,      name='superadmin_reject_doctor'),

    # Patient
    path('patient/',                                      views.patient_portal,                name='patient_portal'),
    path('patient/settings/',                             views.patient_settings,              name='patient_settings'),
    path('patient/book/',                                 views.book_appointment,              name='book_appointment'),
    path('patient/appointment/<int:pk>/',                 views.appointment_detail,            name='appointment_detail'),
    path('patient/appointment/<int:pk>/cancel/',          views.cancel_appointment,            name='cancel_appointment'),
    path('patient/appointment/<int:pk>/prescription/',    views.patient_view_prescription,     name='patient_view_prescription'),

    # Doctor
    path('doctor/',                                               views.doctor_dashboard,           name='doctor_dashboard'),
    path('doctor/settings/',                                      views.doctor_settings,            name='doctor_settings'),
    path('doctor/appointment/<int:pk>/complete/',                 views.doctor_complete_appointment,name='doctor_complete_appointment'),
    path('doctor/appointment/<int:pk>/prescription/',             views.doctor_write_prescription,  name='doctor_write_prescription'),
    path('doctor/appointment/<int:appt_pk>/refer-ot/',            views.doctor_refer_ot,            name='doctor_refer_ot'),
    path('doctor/ot/<int:pk>/postpone/',                          views.doctor_postpone_ot,         name='doctor_postpone_ot'),
    path('doctor/membership/<int:membership_pk>/leave/',          views.doctor_request_leave,       name='doctor_request_leave'),
    path('doctor/join-request/',                                  views.doctor_send_join_request,   name='doctor_send_join_request'),

    # Hospital Admin
    path('hospital/',                                                  views.hospital_dashboard,           name='hospital_dashboard'),
    path('hospital/branding/',                                         views.hospital_update_branding,     name='hospital_update_branding'),
    path('hospital/register-doctor/',                                  views.hospital_register_doctor,     name='hospital_register_doctor'),
    path('hospital/create-staff/',                                     views.hospital_create_staff,        name='hospital_create_staff'),
    path('hospital/book/<int:doctor_pk>/',                             views.hospital_book_appointment,    name='hospital_book_appointment'),
    path('hospital/appointment/<int:pk>/complete/',                    views.hospital_complete_appointment,name='hospital_complete_appointment'),
    path('hospital/appointment/<int:pk>/approve/',                     views.hospital_approve_appointment, name='hospital_approve_appointment'),
    path('hospital/membership/<int:membership_pk>/remove/',            views.hospital_remove_doctor,       name='hospital_remove_doctor'),
    path('hospital/membership/<int:membership_pk>/accept-leave/',      views.hospital_accept_leave,        name='hospital_accept_leave'),
    path('hospital/join-request/<int:request_pk>/accept/',             views.hospital_accept_join,         name='hospital_accept_join'),
    path('hospital/join-request/<int:request_pk>/reject/',             views.hospital_reject_join,         name='hospital_reject_join'),
    path('hospital/beds/',                                             views.hospital_manage_beds,         name='hospital_manage_beds'),
    path('hospital/ot/',                                               views.hospital_manage_ot,           name='hospital_manage_ot'),
    path('hospital/schedules/',                                        views.hospital_manage_schedules,    name='hospital_manage_schedules'),

    # Staff
    path('staff/',                  views.staff_dashboard,        name='staff_dashboard'),
    path('staff/book/',             views.staff_book_walkin,       name='staff_book_walkin'),
    path('staff/appointment/<int:pk>/update/', views.staff_update_appointment, name='staff_update_appointment'),
]
