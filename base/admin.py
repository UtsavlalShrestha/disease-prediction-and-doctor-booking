from django.contrib import admin
from  .models import Hospital, Doctor, Patient, Specialitie


# Register your models here.
admin.site.register(Hospital)
admin.site.register(Specialitie)
admin.site.register(Doctor)
admin.site.register(Patient)