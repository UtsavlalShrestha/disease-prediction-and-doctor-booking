from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class Hospital(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)

    def __str__(self):
        return self.name
    
class Specialitie(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Doctor(models.Model):
    name = models.CharField(max_length=100)
    speciality = models.ForeignKey(Specialitie, on_delete=models.CASCADE)
    experience = models.IntegerField(null=True)
    hospitals = models.ManyToManyField(Hospital)
    description = models.TextField(default="")
    nmc_number = models.IntegerField(default=0)
    profile_picture = models.ImageField(upload_to='media/doctor_images/',default='media/doctor_images/Default.png' , null=False, blank=True)

    def __str__(self):
        return f"Dr. {self.name} ({self.speciality})"

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True) #Null?
    dob = models.DateField(null=True)
    gender = models.CharField(max_length=10)
    address = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)
    doctors = models.ManyToManyField('Doctor', related_name='patients')

    def __str__(self):
        return f"{self.user.first_name}{self.user.last_name}"


class Schedule(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedules')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='schedules', default=1)
    date = models.DateField(default=timezone.now)
    start_time = models.TimeField(default="10:00:00")
    end_time = models.TimeField(default="12:00:00")

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be earlier than end time.")

        overlapping_schedules = Schedule.objects.filter(
            doctor=self.doctor,
            hospital=self.hospital,
            date=self.date,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        )
        if self.pk:
            overlapping_schedules = overlapping_schedules.exclude(pk=self.pk)

        if overlapping_schedules.exists():
            raise ValidationError("This schedule overlaps with an existing schedule.")

    def __str__(self):
        return f"{self.doctor}"

class Appointment(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, default=1)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True)
    date = models.DateField()
    time = models.TimeField(default='12:00:00')
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"Appointment with {self.doctor.name} - {self.hospital}  on {self.date} at {self.time}"