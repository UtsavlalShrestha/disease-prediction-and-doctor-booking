from django.shortcuts import render, redirect
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
    context={}
    return render(request, 'base/predict.html', context)


def appoint(request):
    context={}
    return render(request, 'base/appoint.html', context)

def predict_view(request):
    symptoms = ['mass on eyelid', 'swollen eye', 'eyelid swelling', 'eyelid lesion or rash', 'unwanted hair']
    prediction = get_disease_prediction(symptoms)
    context = {'prediction': prediction}
    return render(request, 'base/Prediction.html', context)