import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Hospital',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('location', models.CharField(max_length=200)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('email', models.EmailField(blank=True)),
                ('description', models.TextField(blank=True)),
                ('admin', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='hospital_admin', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Doctor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('specialist', models.CharField(max_length=100)),
                ('appointment_fee', models.PositiveIntegerField(default=0)),
                ('bio', models.TextField(blank=True)),
                ('is_available', models.BooleanField(default=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='doctor_profile', to=settings.AUTH_USER_MODEL)),
                ('hospital', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='primary_doctors', to='hospital.hospital')),
            ],
        ),
        migrations.CreateModel(
            name='DoctorApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('PENDING','Pending'),('ACCEPTED','Accepted'),('REJECTED','Rejected')], default='PENDING', max_length=20)),
                ('message', models.TextField(blank=True)),
                ('applied_at', models.DateTimeField(auto_now_add=True)),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='hospital.doctor')),
                ('hospital', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='hospital.hospital')),
            ],
            options={'unique_together': {('doctor', 'hospital')}},
        ),
        migrations.CreateModel(
            name='DoctorSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('day', models.CharField(choices=[('SAT','Saturday'),('SUN','Sunday'),('MON','Monday'),('TUE','Tuesday'),('WED','Wednesday'),('THU','Thursday'),('FRI','Friday')], max_length=3)),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('max_patients', models.PositiveIntegerField(default=10)),
                ('is_active', models.BooleanField(default=True)),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedules', to='hospital.doctor')),
                ('hospital', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedules', to='hospital.hospital')),
            ],
            options={'ordering': ['day', 'start_time'], 'unique_together': {('doctor', 'hospital', 'day')}},
        ),
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('age', models.PositiveIntegerField(blank=True, null=True)),
                ('blood_group', models.CharField(blank=True, choices=[('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),('AB+','AB+'),('AB-','AB-'),('O+','O+'),('O-','O-')], max_length=5)),
                ('address', models.TextField(blank=True)),
                ('medical_notes', models.TextField(blank=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='patient_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('appointment_date', models.DateField()),
                ('appointment_time', models.TimeField()),
                ('serial_number', models.PositiveIntegerField()),
                ('symptoms', models.TextField(blank=True)),
                ('notes', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('PENDING','Pending'),('CONFIRMED','Confirmed'),('COMPLETED','Completed'),('INCOMPLETE','Incomplete'),('CANCELLED','Cancelled')], default='PENDING', max_length=20)),
                ('is_extra', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='hospital.doctor')),
                ('hospital', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='hospital.hospital')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='hospital.patient')),
                ('schedule', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appointments', to='hospital.doctorschedule')),
            ],
            options={'ordering': ['appointment_date', 'serial_number'], 'unique_together': {('doctor', 'appointment_date', 'serial_number')}},
        ),
        migrations.CreateModel(
            name='Ward',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('hospital', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wards', to='hospital.hospital')),
            ],
        ),
        migrations.CreateModel(
            name='Bed',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('bed_number', models.CharField(max_length=20)),
                ('bed_type', models.CharField(choices=[('GENERAL','General'),('PRIVATE','Private'),('ICU','ICU'),('VIP','VIP Suite'),('CABIN','Cabin')], default='GENERAL', max_length=20)),
                ('status', models.CharField(choices=[('AVAILABLE','Available'),('BOOKED','Booked'),('OCCUPIED','Occupied'),('MAINTENANCE','Under Maintenance')], default='AVAILABLE', max_length=20)),
                ('daily_cost', models.PositiveIntegerField(default=0)),
                ('hospital', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='beds', to='hospital.hospital')),
                ('ward', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='beds', to='hospital.ward')),
            ],
            options={'ordering': ['ward', 'bed_number'], 'unique_together': {('hospital', 'bed_number')}},
        ),
        migrations.CreateModel(
            name='BedBooking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('check_in_date', models.DateField()),
                ('check_out_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('BOOKED','Booked'),('ADMITTED','Admitted'),('DISCHARGED','Discharged'),('CANCELLED','Cancelled')], default='BOOKED', max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('booked_at', models.DateTimeField(auto_now_add=True)),
                ('bed', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='hospital.bed')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bed_bookings', to='hospital.patient')),
                ('admitted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bed_admissions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='OperationTheatre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('is_available', models.BooleanField(default=True)),
                ('hospital', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ots', to='hospital.hospital')),
            ],
        ),
        migrations.CreateModel(
            name='OTBooking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('operation_date', models.DateField()),
                ('operation_time', models.TimeField()),
                ('duration_minutes', models.PositiveIntegerField(default=60)),
                ('operation_type', models.CharField(max_length=200)),
                ('notes', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('SCHEDULED','Scheduled'),('IN_PROGRESS','In Progress'),('COMPLETED','Completed'),('POSTPONED','Postponed'),('CANCELLED','Cancelled')], default='SCHEDULED', max_length=20)),
                ('next_date', models.DateField(blank=True, null=True)),
                ('postpone_reason', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='hospital.operationtheatre')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ot_bookings', to='hospital.patient')),
                ('referred_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ot_referrals', to='hospital.doctor')),
                ('surgeon', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ot_surgeries', to='hospital.doctor')),
            ],
            options={'ordering': ['operation_date', 'operation_time']},
        ),
        migrations.CreateModel(
            name='OTReferral',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('reason', models.TextField()),
                ('status', models.CharField(choices=[('PENDING','Pending'),('APPROVED','Approved'),('REJECTED','Rejected'),('BOOKED','OT Booked')], default='PENDING', max_length=20)),
                ('referred_at', models.DateTimeField(auto_now_add=True)),
                ('appointment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='ot_referral', to='hospital.appointment')),
                ('hospital', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ot_referrals', to='hospital.hospital')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ot_referrals', to='hospital.patient')),
                ('referring_doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='referrals_made', to='hospital.doctor')),
            ],
        ),
    ]
