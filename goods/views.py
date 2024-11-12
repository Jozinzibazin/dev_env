from django.shortcuts import render

from goods.models import Products#Импортируем модель Products из goods. Она используется для извлечения данных о продуктах из базы данных.


def catalog(request): # Определяеn представление view для маршрута, который отображает каталог товаров


    goods = Products.objects.all() # Извлекаем все товары (объекты модели Products) из базы данных

    context: dict[str, str] = {# Создаём контекст (словарь), который будет передан в шаблон
        "title": "MayFlowers - Каталог",
        "goods": goods,# Добавляем ключ, который содержит список всех товаров, полученных из базы данных
    }
    return render(request, "goods/catalog.html", context)


def product(request):# Определяем представление (view) для маршрута, который отображает отдельную страницу продукта
    return render(request, "goods/Products.html")
