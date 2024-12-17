from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage, send_mail
from .forms import CreateUserForm, PatientForm
from .tokens import account_activation_token
from .services.disease_prediction import get_disease_prediction
from .models import Doctor, Appointment, Schedule, Patient
from itertools import groupby
from operator import attrgetter
from .forms import BookAppointmentForm
from django.utils import timezone
from datetime import timedelta, date


# Create your views here.


def home(request):
    context={}
    return render(request, 'base/home.html', context)

# def loginUser(request):
#     page='login'
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')

#         user = authenticate(request, username=username, password=password)

#         if user is not None:
#             login(request, user)
#             return redirect('home')
#         else:
#             messages.error(request, 'Invalid username or password.')
#     context={'page':page}
#     return render(request, 'base/login_register.html', context)

def loginUser(request):
    page = 'login'
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Redirect to the user's hospital dashboard or default page
            if hasattr(user, 'hospital'):
                # If the user has a hospital, redirect to their dashboard
                return redirect('hospital_dashboard')
            else:
                # If they don't have a hospital, redirect to a default page (like home)
                return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')

    context = {'page': page}
    return render(request, 'base/login_register.html', context)

        

@login_required
def logoutUser(request):
    if request.method == 'POST':
        if request.POST.get("Logout") == "Logout":
            logout(request)
            return redirect('home')
        else:
            return redirect('home')

    context ={}
    return render (request,'base/logout.html', context)


def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        messages.success(request, "Thank you for your email confirmation. Now you can login your account.")
        return redirect('login')
    else:
        messages.error(request, "Activation link is invalid!")

    return redirect('home')

def activateEmail(request, user, to_email):
    mail_subject = "Activate your user account."
    message = render_to_string("base/template_activate_account.html", {
        'user': user.username,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        "protocol": 'https' if request.is_secure() else 'http'
    })
    # Send email
    email = EmailMessage(mail_subject, message, to=[to_email])
    if email.send():
        # Success message
        messages.success(request, f'Dear <b>{user.username}</b>, please check your email <b>{to_email}</b> inbox and click on the activation link to complete registration. <b>Note:</b> Check your spam folder.')
    else:
        # Error message in case of failure
        messages.error(request, f'Problem sending email to {to_email}, please check if you typed it correctly.')
    
    return request
    

def signupUser(request):
    form = CreateUserForm()

    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  
            user.username = user.username.lower()
            user.save()
            activateEmail(request, user, form.cleaned_data.get('email'))
            
              
        else:
            # Handle form errors
            messages.error(request, "Please correct the errors below.")  

    # Context for rendering the form
    context = {'form': form}
    return render(request, 'base/login_register.html', context)

@login_required
def profile(request):
    appointments = Appointment.objects.filter(patient__user=request.user)
    patient = Patient.objects.filter(user=request.user).first()
    context = {
        'appointments': appointments,
        'patient':patient,
    }
    return render(request, 'base/profile.html', context)

def confirmOption(request):
    context={}
    return render(request, 'base/confirmOption.html', context)

@login_required
def predict(request):  
    from .data.symptoms import symp_list
    sorted_symptoms = sorted(symp_list)  
    context = {"list": sorted_symptoms, "range": range(1, 6)}
    return render(request, 'base/predict.html', context)

def recommend_doctor(predicted_disease, doctors, disease_to_specialty):
    recommended_specialty = disease_to_specialty.get(predicted_disease, None)
    if recommended_specialty is None:
        return []
    recommended_doctors = [
        doctor for doctor in doctors if str(doctor.speciality) == recommended_specialty
    ]
    return recommended_doctors, recommended_specialty

@login_required
def predict_view(request):
    if request.method == 'POST':
        selected_symptoms = [
            request.POST.get(f'symptom{y}')
            for y in range(1, 6)
            if request.POST.get(f'symptom{y}')
        ]
        prediction = get_disease_prediction(selected_symptoms)
        doctors = Doctor.objects.all()
        from .data.diseases import disease_doctor_mapping
        recommended_doctors, recommended_specialty = recommend_doctor(prediction, doctors, disease_doctor_mapping)
        return render(request, 'base/Prediction.html', {
            'prediction': prediction.title(),
            'doctors': recommended_doctors,
            'specialty': recommended_specialty,
        })
    
    context = {}
    return render(request, 'base/home.html', context)

    
@login_required
def appoint(request):
    doctors = Doctor.objects.prefetch_related('schedules').all()
    current_time = timezone.now()
    cutoff_date = current_time.date() + timedelta(days=3)
    for doctor in doctors:
        schedules = doctor.schedules.filter(
            date__range=(current_time.date(), cutoff_date)
        ).exclude(
            date=current_time.date(),
            end_time__lte=current_time.time()
        ).order_by('hospital', 'date', 'start_time')

        grouped_schedules = {}
        for hospital, hospital_group in groupby(schedules, key=lambda x: x.hospital):
            grouped_schedules[hospital] = {}
            for date, date_group in groupby(hospital_group, key=lambda x: x.date):
                grouped_schedules[hospital][date] = list(date_group)
        doctor.grouped_schedules = grouped_schedules

    context = {
        'doctors': doctors,
    }
    return render(request, 'base/appoint.html', context)


@login_required
def doctor_schedule_view(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    schedules = doctor.schedules.filter(date__gte=date.today()).order_by('hospital', 'date', 'start_time')

    grouped_schedules = [
        (hospital, list(schedule_group)) 
        for hospital, schedule_group in groupby(schedules, key=attrgetter('hospital'))
    ]
    return render(request, 'base/doctor_schedule.html', {
        'doctor': doctor,
        'grouped_schedules': grouped_schedules,
    }) 

@login_required
def doctor_profile(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)

    schedules = doctor.schedules.filter(date__gte=date.today()).order_by('hospital', 'date', 'start_time')

    grouped_schedules = [
        (hospital, list(schedule_group)) 
        for hospital, schedule_group in groupby(schedules, key=attrgetter('hospital'))
    ]
    
    return render(request, 'base/doctor_profile.html', {
        'doctor': doctor,
        'grouped_schedules': grouped_schedules,
    }) 

@login_required
def book_appointment(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id)

    if not Patient.objects.filter(user=request.user).exists():
        return redirect('add_patient_details', schedule_id=schedule.id)

    if request.method == 'POST':
        form = BookAppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.doctor = schedule.doctor
            appointment.patient = Patient.objects.get(user=request.user)
            appointment.hospital = form.cleaned_data['hospital']
            appointment.save()

            return redirect('appointment_confirmation', appointment_id=appointment.id)
    else:
        form = BookAppointmentForm()

    return render(
        request,
        'base/book_appointment.html',
        {'form': form, 'doctor': schedule.doctor, 'schedule': schedule}
    )


@login_required
def add_patient_details(request, schedule_id):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.user = request.user
            patient.save()
            return redirect('book_appointment', schedule_id=schedule_id)
    else:
        form = PatientForm()

    return render(request, 'base/add_patient_details.html', {'form': form})


@login_required
def appointment_confirmation(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    return render(request, 'base/confirmation.html', {'appointment': appointment})



@login_required
def hospital_dashboard(request):
    if hasattr(request.user, 'hospital'):
        hospital = request.user.hospital
        return render(request, 'hospital_admin/base_generic.html', {'hospital': hospital})
    else:
        return redirect('no_permission')
