from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage, send_mail
from .forms import CreateUserForm
from .tokens import account_activation_token
from django.conf import settings
from .services.disease_prediction import get_disease_prediction
from django.http import JsonResponse
from .models import Doctor, Appointment, Schedule
from itertools import groupby
from operator import attrgetter
from .forms import BookAppointmentForm
from django.utils import timezone
from datetime import timedelta, date


# Create your views here.


def home(request):
    context={}
    return render(request, 'base/home.html', context)

def loginUser(request):
    page='login'
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    context={'page':page}
    return render(request, 'base/login_register.html', context)
        


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


def confirmOption(request):
    context={}
    return render(request, 'base/confirmOption.html', context)


def predict(request):
    symp_list = ['anxiety and nervousness', 'depression', 'shortness of breath',
    'depressive or psychotic symptoms', 'sharp chest pain', 
    'dizziness', 'insomnia', 'abnormal involuntary movements', 
    'chest tightness', 'palpitations', 'irregular heartbeat', 
    'breathing fast', 'hoarse voice', 'sore throat', 
    'difficulty speaking', 'cough', 'nasal congestion', 
    'throat swelling', 'diminished hearing', 'lump in throat', 
    'throat feels tight', 'difficulty in swallowing', 'skin swelling', 
    'retention of urine', 'groin mass', 'leg pain', 
    'hip pain', 'suprapubic pain', 'blood in stool', 
    'lack of growth', 'emotional symptoms', 'elbow weakness', 
    'back weakness', 'pus in sputum', 'symptoms of the scrotum and testes', 
    'swelling of scrotum', 'pain in testicles', 'flatulence', 
    'pus draining from ear', 'jaundice', 'mass in scrotum', 
    'white discharge from eye', 'irritable infant', 'abusing alcohol', 
    'fainting', 'hostile behavior', 'drug abuse', 
    'sharp abdominal pain', 'feeling ill', 'vomiting', 
    'headache', 'nausea', 'diarrhea', 'vaginal itching', 
    'vaginal dryness', 'painful urination', 'involuntary urination', 
    'pain during intercourse', 'frequent urination', 
    'lower abdominal pain', 'vaginal discharge', 'blood in urine', 
    'hot flashes', 'intermenstrual bleeding', 'hand or finger pain', 
    'wrist pain', 'hand or finger swelling', 'arm pain', 
    'wrist swelling', 'arm stiffness or tightness', 'arm swelling', 
    'hand or finger stiffness or tightness', 'wrist stiffness or tightness', 
    'lip swelling', 'toothache', 'abnormal appearing skin', 
    'skin lesion', 'acne or pimples', 'dry lips', 
    'facial pain', 'mouth ulcer', 'skin growth', 
    'eye deviation', 'diminished vision', 'double vision', 
    'cross-eyed', 'symptoms of eye', 'pain in eye', 
    'eye moves abnormally', 'abnormal movement of eyelid', 
    'foreign body sensation in eye', 'irregular appearing scalp', 
    'swollen lymph nodes', 'back pain', 'neck pain', 
    'low back pain', 'pain of the anus', 'pain during pregnancy', 
    'pelvic pain', 'impotence', 'infant spitting up', 
    'vomiting blood', 'regurgitation', 'burning abdominal pain', 
    'restlessness', 'symptoms of infants', 'wheezing', 
    'peripheral edema', 'neck mass', 'ear pain', 
    'jaw swelling', 'mouth dryness', 'neck swelling', 
    'knee pain', 'foot or toe pain', 'bowlegged or knock-kneed', 
    'ankle pain', 'bones are painful', 'knee weakness', 
    'elbow pain', 'knee swelling', 'skin moles', 
    'knee lump or mass', 'weight gain', 'problems with movement', 
    'knee stiffness or tightness', 'leg swelling', 'foot or toe swelling', 
    'heartburn', 'smoking problems', 'muscle pain', 
    'infant feeding problem', 'recent weight loss', 
    'problems with shape or size of breast', 'underweight', 
    'difficulty eating', 'scanty menstrual flow', 'vaginal pain', 
    'vaginal redness', 'vulvar irritation', 'weakness', 
    'decreased heart rate', 'increased heart rate', 
    'bleeding or discharge from nipple', 'ringing in ear', 
    'plugged feeling in ear', 'itchy ear(s)', 'frontal headache', 
    'fluid in ear', 'neck stiffness or tightness', 
    'spots or clouds in vision', 'eye redness', 'lacrimation', 
    'itchiness of eye', 'blindness', 'eye burns or stings', 
    'itchy eyelid', 'feeling cold', 'decreased appetite', 
    'excessive appetite', 'excessive anger', 'loss of sensation', 
    'focal weakness', 'slurring words', 'symptoms of the face', 
    'disturbance of memory', 'paresthesia', 'side pain', 
    'fever', 'shoulder pain', 'shoulder stiffness or tightness', 
    'shoulder weakness', 'arm cramps or spasms', 'shoulder swelling', 
    'tongue lesions', 'leg cramps or spasms', 
    'abnormal appearing tongue', 'ache all over', 
    'lower body pain', 'problems during pregnancy', 
    'spotting or bleeding during pregnancy', 'cramps and spasms', 
    'upper abdominal pain', 'stomach bloating', 
    'changes in stool appearance', 'unusual color or odor to urine', 
    'kidney mass', 'swollen abdomen', 'symptoms of prostate', 
    'leg stiffness or tightness', 'difficulty breathing', 
    'rib pain', 'joint pain', 'muscle stiffness or tightness', 
    'pallor', 'hand or finger lump or mass', 'chills', 
    'groin pain', 'fatigue', 'abdominal distention', 
    'regurgitation.1', 'symptoms of the kidneys', 
    'melena', 'flushing', 'coughing up sputum', 
    'seizures', 'delusions or hallucinations', 
    'shoulder cramps or spasms', 'joint stiffness or tightness', 
    'pain or soreness of breast', 'excessive urination at night', 
    'bleeding from eye', 'rectal bleeding', 'constipation', 
    'temper problems', 'coryza', 'wrist weakness', 
    'eye strain', 'hemoptysis', 'lymphedema', 
    'skin on leg or foot looks infected', 'allergic reaction', 
    'congestion in chest', 'muscle swelling', 'pus in urine', 
    'abnormal size or shape of ear', 'low back weakness', 
    'sleepiness', 'apnea', 'abnormal breathing sounds', 
    'excessive growth', 'elbow cramps or spasms', 
    'feeling hot and cold', 'blood clots during menstrual periods', 
    'absence of menstruation', 'pulling at ears', 'gum pain', 
    'redness in ear', 'fluid retention', 'flu-like syndrome', 
    'sinus congestion', 'painful sinuses', 'fears and phobias', 
    'recent pregnancy', 'uterine contractions', 
    'burning chest pain', 'back cramps or spasms', 
    'stiffness all over', 'muscle cramps, contractures, or spasms', 
    'low back cramps or spasms', 'back mass or lump', 
    'nosebleed', 'long menstrual periods', 'heavy menstrual flow', 
    'unpredictable menstruation', 'painful menstruation', 
    'infertility', 'frequent menstruation', 'sweating', 
    'mass on eyelid', 'swollen eye', 'eyelid swelling', 
    'eyelid lesion or rash', 'unwanted hair', 
    'symptoms of bladder', 'irregular appearing nails', 
    'itching of skin', 'hurts to breath', 'nailbiting', 
    'skin dryness, peeling, scaliness, or roughness', 
    'skin on arm or hand looks infected', 'skin irritation', 
    'itchy scalp', 'hip swelling', 'incontinence of stool', 
    'foot or toe cramps or spasms', 'warts', 'bumps on penis', 
    'too little hair', 'foot or toe lump or mass', 
    'skin rash', 'mass or swelling around the anus', 
    'low back swelling', 'ankle swelling', 'hip lump or mass', 
    'drainage in throat', 'dry or flaky scalp', 
    'premenstrual tension or irritability', 'feeling hot', 
    'feet turned in', 'foot or toe stiffness or tightness', 
    'pelvic pressure', 'elbow swelling', 'elbow stiffness or tightness', 
    'early or late onset of menopause', 'mass on ear', 
    'bleeding from ear', 'hand or finger weakness', 
    'low self-esteem', 'throat irritation', 'itching of the anus', 
    'swollen or red tonsils', 'irregular belly button', 
    'swollen tongue', 'lip sore', 'vulvar sore', 
    'hip stiffness or tightness', 'mouth pain', 'arm weakness', 
    'leg lump or mass', 'disturbance of smell or taste', 
    'discharge in stools', 'penis pain',     'loss of sex drive', 'obsessions and compulsions', 
    'antisocial behavior', 'neck cramps or spasms', 
    'pupils unequal', 'poor circulation', 'thirst', 
    'sleepwalking', 'skin oiliness', 'sneezing', 
    'bladder mass', 'knee cramps or spasms', 
    'premature ejaculation', 'leg weakness', 
    'posture problems', 'bleeding in mouth', 
    'tongue bleeding', 'change in skin mole size or color', 
    'penis redness', 'penile discharge', 
    'shoulder lump or mass', 'polyuria', 'cloudy eye', 
    'hysterical behavior', 'arm lump or mass', 
    'nightmares', 'bleeding gums', 'pain in gums', 
    'bedwetting', 'diaper rash', 'lump or mass of breast', 
    'vaginal bleeding after menopause', 'infrequent menstruation', 
    'mass on vulva', 'jaw pain', 'itching of scrotum', 
    'postpartum problems of the breast', 'eyelid retracted', 
    'hesitancy', 'elbow lump or mass', 'muscle weakness', 
    'throat redness', 'joint swelling', 'tongue pain', 
    'redness in or around nose', 'wrinkles on skin', 
    'foot or toe weakness', 'hand or finger cramps or spasms', 
    'back stiffness or tightness', 'wrist lump or mass', 
    'skin pain', 'low back stiffness or tightness', 
    'low urine output', 'skin on head or neck looks infected', 
    'stuttering or stammering', 'problems with orgasm', 
    'nose deformity', 'lump over jaw', 'sore in nose', 
    'hip weakness', 'back swelling', 'ankle stiffness or tightness', 
    'ankle weakness', 'neck weakness'
]   
    sorted_symptoms = sorted(symp_list)  
    context = {"list": sorted_symptoms, "range": range(1, 6)}
    return render(request, 'base/predict.html', context)

def predict_view(request):
    if request.method == 'POST':
        selected_symptoms = [
            request.POST.get(f'symptom{y}')
            for y in range(1, 6)
            if request.POST.get(f'symptom{y}')
        ]

        prediction = get_disease_prediction(selected_symptoms)
        return render(request, 'base/Prediction.html', {
            'prediction': prediction,
        })
    context = {}
    return render(request, 'base/home.html', context)
    

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



def doctor_schedule_view(request):
    doctors = Doctor.objects.prefetch_related('schedules').all()
    context = {
        'doctors': doctors,
    }
    return render(request, 'doctor_schedule.html', context)

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

def book_appointment(request, schedule_id):
    # doctor = get_object_or_404(Doctor, id=doctor_id)
    schedule = get_object_or_404(Schedule, id=schedule_id)
    # user = request.user
    if request.method == 'POST':
        form = BookAppointmentForm(request.POST)
        if form.is_valid():
            print(form.cleaned_data)
            appointment = form.save(commit=False)
            appointment.doctor = schedule.doctor
            # appointment.patient = user
            appointment.hospital = form.cleaned_data['hospital']
            appointment.save()

            return redirect('appointment_confirmation', appointment_id=appointment.id)
    else:
        form = BookAppointmentForm()

    return render(request, 'base/book_appointment.html', {'form': form, 'doctor': schedule.doctor, 'schedule': schedule})

def appointment_confirmation(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    return render(request, 'base/confirmation.html', {'appointment': appointment})