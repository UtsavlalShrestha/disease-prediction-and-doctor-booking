from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db.models import Count, Q
from .forms import CreateUserForm, PatientForm, BookAppointmentForm
from .tokens import account_activation_token
from .services.disease_prediction import get_disease_prediction
from .models import Doctor, Appointment, Schedule, Patient
from itertools import groupby
from operator import attrgetter
from datetime import timedelta, date
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import process
import pandas as pd


def home(request):
    top_doctors = Doctor.objects.annotate(num_appointments=Count('appointment')).order_by('-num_appointments')[:3]
    context = {
        'top_doctors': top_doctors
    }
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
    error_message = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            if hasattr(user, 'hospital'):
                return redirect('hospital_dashboard')
            else:
                return redirect('home')
        else:
            error_message = 'Invalid username or password.'

    context = {'page': page, 'error_message': error_message}
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
        messages.success(request, f'Dear {user.username}, please check your email {to_email} inbox and click on the activation link to complete registration. Note: Check your spam folder.')
    else:
        messages.error(request, f'Problem sending email to {to_email}, please check if you typed it correctly.')
    
    return request
    

def signupUser(request):
    form = CreateUserForm()
    error_message = None
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  
            user.username = user.username.lower()
            user.save()
            activateEmail(request, user, form.cleaned_data.get('email'))
                    
        else:
            error_message = "Password/Username error, please recheck and try again"

    context = {'form': form , 'error_message_signup': error_message}
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

# def probabilities(predictions):
#     if not predictions:
#         return []

#     # Extract `label` and `prob` from dictionaries
#     predictions = [
#         (prediction['disease'], max(0.0, min(1.0, float(prediction['probability']))))
#         for prediction in predictions
#     ]

#     predictions = sorted(predictions, key=lambda x: x[1], reverse=True)

#     if predictions and predictions[0][1] >= 1.0:
#         total_adjustment = 0.05
#         predictions[0] = (predictions[0][0], 0.95)
#         adjustment_per_other = total_adjustment / (len(predictions) - 1) if len(predictions) > 1 else 0
#         for i in range(1, len(predictions)):
#             predictions[i] = (predictions[i][0], predictions[i][1] + adjustment_per_other)

#     return predictions

def disease_and_specialty(predicted_disease, disease_to_specialty):
    disease_names = list(disease_to_specialty.keys())
    
    for prediction in predicted_disease:
        disease = prediction['disease']
        best_match, score, _ = process.extractOne(disease, disease_names)
        
        if score > 70:  # Only accept matches with a confidence above 70%
            recommended_info = disease_to_specialty[best_match]
            prediction['specialty'] = recommended_info.get('specialist', 'Unknown')
            prediction['description'] = recommended_info.get('description', 'No description available')
        else:
            prediction['specialty'] = "Unknown"
            prediction['description'] = "No description available"
    return predicted_disease

@login_required
def predict_view(request):
    if request.method == 'POST':
        selected_symptoms = [
            request.POST.get(f'symptom{y}')
            for y in range(1, 6)
            if request.POST.get(f'symptom{y}')
        ]
        predictions = get_disease_prediction(selected_symptoms)

        flattened_predictions = []
        for key, values in predictions.items():
            flattened_predictions.extend([tuple(item) for item in values])

        predictions = [
            {
                "id": idx + 1,
                "disease": prediction[0],
                "probability": prediction[1],
                "probability_percentage": prediction[1] * 100,
            }
            for idx, prediction in enumerate(flattened_predictions)
        ]

        from .data.diseases import disease_doctor_mapping
        updated_predictions = disease_and_specialty(predictions, disease_doctor_mapping)
        request.session['updated_predictions'] = updated_predictions

        return render(request, 'base/Prediction.html', {
            'predictions': updated_predictions,
        })

@login_required
def recommend_doctors_view(request, prediction_id):
    predictions = request.session.get('updated_predictions', [])
    if not predictions:
        return HttpResponse("No predictions found in session", status=404)

    prediction = next((p for p in predictions if p['id'] == prediction_id), None)
    if not prediction:
        return HttpResponse("Prediction not found", status=404)

    specialty = prediction.get('specialty')
    doctors = Doctor.objects.filter(speciality__name=specialty).values('id', 'name', 'speciality__name', 'description')
    if doctors:
        df = pd.DataFrame(list(doctors))

        df.rename(columns={'speciality__name': 'speciality'}, inplace=True)
        df['description'] = df['description'].fillna('')
        df['combined_features'] = df['speciality'] + " " + df['description']

        tfidf = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf.fit_transform(df['combined_features'])

        disease_description = prediction.get('description', '').strip()

        if disease_description:
            disease_vector = tfidf.transform([disease_description])
            sim_scores = cosine_similarity(disease_vector, tfidf_matrix).flatten()
            df['similarity_score'] = sim_scores
            df_sorted = df.sort_values(by='similarity_score', ascending=False)
        else:
            df_sorted = df
        recommended_doctors_list = df_sorted.to_dict('records')
    else:
        recommended_doctors_list = []

    return render(request, 'base/recommend_doctors.html', {
        'doctors': recommended_doctors_list,
        'prediction': prediction,
        'specialty': specialty,
    })

@login_required
def appoint(request):
    query = request.GET.get('search', '')
    doctors = Doctor.objects.prefetch_related('schedules').all()

    if query:
        doctors = doctors.filter(
            Q(name__icontains=query) |
            Q(speciality__name__icontains=query) | 
            Q(hospitals__name__icontains=query)
        ).distinct()

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
    patient = Patient.objects.get(user=request.user)
    if Appointment.objects.filter(
        date=schedule.date,
        time=schedule.start_time,
        doctor=schedule.doctor,
        patient=patient
    ).exists():
        error_message = "You have already booked an appointment for this schedule."
        form = BookAppointmentForm()
        return render(
            request,
            'base/book_appointment.html',
            {'form': form, 'doctor': schedule.doctor, 'schedule': schedule, 'error_message': error_message}
        )

    if request.method == 'POST':
        form = BookAppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.doctor = schedule.doctor
            appointment.patient = patient
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
