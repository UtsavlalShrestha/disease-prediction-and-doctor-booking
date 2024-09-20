from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from .forms import CreateUserForm

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
            messages.success(request, "logged in")
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


def signupUser(request):
    form = CreateUserForm()

    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Error occured during registration')
    context={'form': form}
    return render(request, 'base/login_register.html', context)