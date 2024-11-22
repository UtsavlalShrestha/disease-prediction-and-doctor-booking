from django.contrib import admin
from  .models import Hospital, Doctor, Patient, Specialitie, Schedule, Appointment


# Register your models here.
admin.site.register(Hospital)
admin.site.register(Specialitie)
admin.site.register(Doctor)
admin.site.register(Patient)
admin.site.register(Schedule)
admin.site.register(Appointment)