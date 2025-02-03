from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from .models import Doctor, Hospital, Specialitie, Schedule, Appointment
from .forms import DoctorForm, ScheduleForm, AppointmentForm

@login_required
def doctor_list(request):
    if hasattr(request.user, 'hospital'):
        hospital = request.user.hospital
        doctors = Doctor.objects.filter(hospitals=hospital)  # Filter by the user's hospital
        return render(request, 'hospital_admin/doctor_list.html', {'doctors': doctors, 'hospital': hospital})
    else:
        return redirect('no_permission')
    
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def doctor_add(request):
    if not hasattr(request.user, 'hospital'):
        messages.error(request, "You do not have permission to add a doctor.")
        return redirect('no_permission')

    hospital = request.user.hospital

    if request.method == "POST":
        form = DoctorForm(request.POST, request.FILES)
        if form.is_valid():
            doctor = form.save(commit=False)
            doctor.save()
            doctor.hospitals.add(hospital)
            messages.success(request, f"Doctor '{doctor.name}' has been added successfully!")
            return redirect('doctor_list')
        else:
            messages.error(request, "There was an error adding the doctor. Please try again.")
    else:
        form = DoctorForm()

    return render(request, 'hospital_admin/doctor_add.html', {'form': form, 'hospital': hospital})

@login_required
def doctor_edit(request, pk):
    if hasattr(request.user, 'hospital'):
        hospital = request.user.hospital
        doctor = get_object_or_404(Doctor, pk=pk, hospitals=hospital)  # Ensure the doctor belongs to the user's hospital
        
        if request.method == "POST":
            form = DoctorForm(request.POST, request.FILES, instance=doctor)
            if form.is_valid():
                form.save()
                return redirect('doctor_list')
        else:
            form = DoctorForm(instance=doctor)
        return render(request, 'hospital_admin/doctor_edit.html', {'form': form, 'hospital': hospital})
    else:
        return redirect('no_permission')


@login_required
def doctor_delete(request, pk):
    if hasattr(request.user, 'hospital'):
        hospital = request.user.hospital
        doctor = get_object_or_404(Doctor, pk=pk, hospitals=hospital)  
        doctor.delete()
        return redirect('doctor_list')
    else:
        return redirect('no_permission')

@login_required
def schedule_list(request):
    if hasattr(request.user, 'hospital'):
        hospital = request.user.hospital
        schedules = Schedule.objects.filter(hospital=hospital)
        return render(request, 'hospital_admin/schedule_list.html', {'schedules': schedules, 'hospital': hospital})
    else:
        return redirect('no_permission')
    
@login_required
def schedule_add(request):
    if hasattr(request.user, 'hospital'):
        hospital = request.user.hospital
        if request.method == "POST":
            form = ScheduleForm(request.POST, hospital=hospital)
            if form.is_valid():
                schedule = form.save(commit=False)
                schedule.hospital = hospital
                schedule.save()
                return redirect('schedule_list')
        else:
            form = ScheduleForm(hospital=hospital)

        return render(request, 'hospital_admin/schedule_add.html', {'form': form, 'hospital': hospital})
    else:
        return redirect('no_permission')
    
@login_required
def schedule_edit(request, pk):
    if hasattr(request.user, 'hospital'):
        hospital = request.user.hospital
        schedule = get_object_or_404(Schedule, pk=pk, hospital=hospital)
        if request.method == "POST":
            form = ScheduleForm(request.POST, instance=schedule, hospital=hospital)
            if form.is_valid():
                updated_schedule = form.save(commit=False)
                if updated_schedule.doctor in Doctor.objects.filter(hospitals=hospital):
                    updated_schedule.save()
                    return redirect('schedule_list')
                else:
                    form.add_error('doctor', 'Selected doctor does not belong to your hospital.')
        else:
            form = ScheduleForm(instance=schedule, hospital=hospital)
            form.fields['doctor'].queryset = Doctor.objects.filter(hospitals=hospital)
        return render(request, 'hospital_admin/schedule_edit.html', {'form': form, 'hospital': hospital})
    else:
        return redirect('no_permission')

@login_required
def schedule_delete(request, pk):
    if hasattr(request.user, 'hospital'):
        hospital = request.user.hospital
        schedule = get_object_or_404(Schedule, pk=pk, hospital=hospital)
        schedule.delete()
        return redirect('schedule_list')
    else:
        return redirect('no_permission')

@login_required
def appointment_list(request):
    if hasattr(request.user, 'hospital'):
        hospital = request.user.hospital
        appointments = Appointment.objects.filter(hospital=hospital, is_approved=False)
        return render(request, 'hospital_admin/appointment_list.html', {'appointments': appointments, 'hospital': hospital})
    else:
        return redirect('no_permission')

@login_required
def appointment_add(request):
    if hasattr(request.user, 'hospital'):
        hospital = request.user.hospital
        if request.method == "POST":
            form = AppointmentForm(request.POST, hospital=hospital)
            if form.is_valid():
                appointment = form.save(commit=False)
                appointment.hospital = hospital
                print(hospital)
                appointment.save()
                return redirect('appointment_list')
        else:
            form = AppointmentForm(hospital=hospital)

        return render(request, 'hospital_admin/appointment_add.html', {'form': form})
    else:
        return redirect('no_permission')


@login_required
def appointment_edit(request, pk):
    if hasattr(request.user, 'hospital'):
        hospital = request.user.hospital
        appointment = get_object_or_404(Appointment, pk=pk, hospital=hospital)
        if request.method == "POST":
            form = AppointmentForm(request.POST, instance=appointment, hospital=hospital)
            if form.is_valid():
                updated_appointment = form.save(commit=False)
                if updated_appointment.doctor in Doctor.objects.filter(hospitals=hospital):
                    updated_appointment.save()
                    return redirect('appointment_list')
                else:
                    form.add_error('doctor', 'Selected doctor does not belong to your hospital.')
        else:
            form = AppointmentForm(instance=appointment, hospital=hospital)
            form.fields['doctor'].queryset = Doctor.objects.filter(hospitals=hospital)
        return render(request, 'hospital_admin/appointment_edit.html', {'form': form})
    else:
        return redirect('no_permission')


@login_required
def approve_appointments(request):
    if hasattr(request.user, 'hospital'):
        hospital = request.user.hospital
        selected_appointments = request.POST.getlist('selected_appointments')
        appointments = Appointment.objects.filter(pk__in=selected_appointments, hospital=hospital)

        approved_emails = []
        for appointment in appointments:
            appointment.is_approved = True
            appointment.save()

            send_mail(
                subject="Appointment Approved",
                message=f"Dear {appointment.patient.user.first_name} {appointment.patient.user.last_name},\n\n"
                        f"Your appointment with Dr. {appointment.doctor.name} "
                        f"on {appointment.date} at {appointment.time} has been approved.\n\n"
                        f"Thank you,\n{hospital.name}",
                from_email="disease.panel@gmail.com",
                recipient_list=[appointment.patient.user.email], 
                fail_silently=False, 
            )
            approved_emails.append(appointment.patient.user.email)

       
        messages.success(request, f"Appointments approved and emails sent to: {', '.join(approved_emails)}")
        return redirect('appointment_list')
    else:
        return redirect('no_permission')
    
@login_required
def approved_appointments(request):
    if hasattr(request.user, 'hospital'):
        hospital = request.user.hospital
        approved_appointments = Appointment.objects.filter(hospital=hospital, is_approved=True).order_by('-date', '-time')
        return render(request, 'hospital_admin/approved_appointment_history.html', {'appointments': approved_appointments, 'hospital': hospital})
    else:
        return redirect('no_permission')

@login_required
def appointment_delete(request, pk):
    if hasattr(request.user, 'hospital'):
        hospital = request.user.hospital
        appointment = get_object_or_404(Appointment, pk=pk, hospital=hospital)
        send_mail(
            subject="Appointment Cancelled",
            message=f"Dear {appointment.patient.user.first_name} {appointment.patient.user.last_name},\n\n"
                    f"Your appointment with Dr. {appointment.doctor.name} "
                    f"on {appointment.date} at {appointment.time} has been cancelled.\n\n"
                    f"Please Contact for more Information."
                    f"Thank you,\n{hospital.name}",
            from_email="disease.panel@gmail.com",
            recipient_list=[appointment.patient.user.email], 
            fail_silently=False, 
        )
        appointment.delete()
        messages.success(request, f"Appointment deleted and email sent to {appointment.patient.user.email}.")
        return redirect('appointment_list')
    else:
        return redirect('no_permission')

