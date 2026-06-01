from pathlib import Path
import os, ssl, certifi
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-hms-clinic-secret-key-change-in-production'
DEBUG = True
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '107b-103-181-181-193.ngrok-free.app',
]
CSRF_TRUSTED_ORIGINS = [
    'https://107b-103-181-181-193.ngrok-free.app',
]
INSTALLED_APPS = [
    'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes',
    'django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles',
    'django.contrib.sites','allauth','allauth.account','allauth.socialaccount',
    'allauth.socialaccount.providers.google','allauth.socialaccount.providers.facebook',
    'core','hospital',
]
AUTH_USER_MODEL = 'core.User'
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]
ROOT_URLCONF = 'hospital_system.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates',
    'DIRS':[os.path.join(BASE_DIR,'templates')],'APP_DIRS':True,
    'OPTIONS':{'context_processors':['django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'hospital_system.wsgi.application'
DATABASES = {'default':{'ENGINE':'django.db.backends.sqlite3','NAME':BASE_DIR/'db.sqlite3'}}
AUTH_PASSWORD_VALIDATORS = [
    {'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE='en-us'; TIME_ZONE='Asia/Dhaka'; USE_I18N=True; USE_TZ=True
STATIC_URL='/static/'; DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
LOGIN_URL='login'; MEDIA_URL='/media/'; MEDIA_ROOT=os.path.join(BASE_DIR,'media')
try:
    ssl._create_default_https_context = ssl.create_default_context(cafile=certifi.where())
except Exception:
    pass
EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'; EMAIL_HOST='smtp.gmail.com'
EMAIL_PORT=587; EMAIL_USE_TLS=True
EMAIL_HOST_USER='mdalkayes2003@gmail.com'; 
EMAIL_HOST_PASSWORD='nbyr usyo gcvp cpbq';
DEFAULT_FROM_EMAIL='MediCare HMS <mdalkayes2003@gmail.com>'
SITE_ID=1
AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend','allauth.account.auth_backends.AuthenticationBackend']
LOGIN_REDIRECT_URL='/go/'; LOGOUT_REDIRECT_URL='/'; ACCOUNT_LOGOUT_REDIRECT_URL='/'
ACCOUNT_SIGNUP_REDIRECT_URL='/go/'; ACCOUNT_EMAIL_REQUIRED=True
ACCOUNT_USERNAME_REQUIRED=True; ACCOUNT_EMAIL_VERIFICATION='none'
ACCOUNT_LOGIN_METHODS={'username','email'}; ACCOUNT_DEFAULT_HTTP_PROTOCOL='http'
SOCIALACCOUNT_AUTO_SIGNUP=True; SOCIALACCOUNT_EMAIL_REQUIRED=True
SOCIALACCOUNT_LOGIN_ON_GET=False; ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION=False
SOCIALACCOUNT_PROVIDERS={
    'google':{'SCOPE':['profile','email'],'AUTH_PARAMS':{'access_type':'online'},
              'APP':{'client_id':'YOUR_GOOGLE_CLIENT_ID','secret':'YOUR_GOOGLE_CLIENT_SECRET','key':''}},
    'facebook':{'METHOD':'oauth2','SCOPE':['email','public_profile'],
                'APP':{'client_id':'YOUR_FACEBOOK_APP_ID','secret':'YOUR_FACEBOOK_APP_SECRET','key':''}},
}
