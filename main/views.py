from django.http import HttpResponse
from django.shortcuts import redirect, render

from goods.models import Categories # Импортирует модель Categories из приложения 'goods' для работы с данными категорий

def home(request):
    return redirect('goods:catalog_index')

def index(request): # Определяет представление для главной страницы, обрабатывающее запросы по маршруту '/'


    context: dict = {# Создает контекст, который передается в шаблон
        'title': 'MayFlowers - Главная',
        'content': "Конструктор букетов MayFlowers",
       
    }

    return render(request, 'main/index.html', context)

def about(request):
    context: dict = {# Определяет представление для страницы "О нас", обрабатывающее запросы по маршруту '/about/'
        'title': 'MayFlowers - О нас',
        'content': "О нас",
        'text_on_page':"Конструктор букетов MayFlowers - удобный инструмент для формирования индивидуальных букетов."
    }

    return render(request, 'main/about.html', context)
