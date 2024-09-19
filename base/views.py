from django.shortcuts import render

# Create your views here.


def home(request):
    context={}
    return render(request, 'base/home.html', context)

def loginUser(request):
    context={}
    return render(request, 'base/login_register.html', context={})