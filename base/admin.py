from django.contrib import admin
from  .models import Hospital, Doctor, Patient, Specialitie, Schedule, Appointment

admin.site.site_header = "SuperUser Panel"
admin.site.site_title = "SuperUser"

class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'phone_number')
    search_fields = ('name', 'address')

class SpecialitieAdmin(admin.ModelAdmin):
    search_fields = ('name',)

class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'speciality', 'nmc_number', 'experience')
    search_fields = ('name', 'speciality__name', 'nmc_number')
    autocomplete_fields = ('speciality',)

class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'hospital', 'date', 'start_time', 'end_time')
    list_filter = ('doctor', 'hospital', 'date')
    search_fields = ('doctor__name', 'hospital__name')
    autocomplete_fields = ('doctor', 'hospital')

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('doctor','patient', 'hospital', 'date', 'time', 'is_approved')
    list_filter = ('doctor', 'hospital', 'date', 'is_approved')
    search_fields = ('doctor__name', 'hospital__name', 'patient__name')

admin.site.register(Hospital, HospitalAdmin)
admin.site.register(Specialitie, SpecialitieAdmin)
admin.site.register(Doctor, DoctorAdmin)
admin.site.register(Patient)
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(Appointment, AppointmentAdmin)