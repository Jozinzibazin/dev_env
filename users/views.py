import re
from django.shortcuts import render

# Create your views here.
def login(request):
    context = {
        'title': 'MayFlowers - Авторизация'
    }
    return render(request, 'users/login.html', context)

def registration(request):
    context = {
        'title': 'MayFlowers - Регистрация'
    }
    return render(request, 'users/registration.html', context)

def profile(request):
    context = {
        'title': 'MayFlowers - Кабинет'
    }
    return render(request, 'users/profile.html', context)

def logout(request):
    ...