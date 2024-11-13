from django.shortcuts import get_object_or_404, render

from goods.models import Products#Импортируем модель Products из goods. Она используется для извлечения данных о продуктах из базы данных.


def catalog(request, category_slug): # Определяеn представление view для маршрута, который отображает каталог товаров

    if category_slug == 'all':
        goods = Products.objects.all() # Извлекаем все товары (объекты модели Products) из базы данных
    else:
        goods = Products.objects.filter(category__slug=category_slug) # Извлекаем все товары (объекты модели Products) из базы данных

    context: dict[str, str] = {# Создаём контекст (словарь), который будет передан в шаблон
        "title": "MayFlowers - Каталог",
        "goods": goods,# Добавляем ключ, который содержит список всех товаров, полученных из базы данных
    }
    return render(request, "goods/catalog.html", context)


def product(request, product_slug):# Определяем представление (view) для маршрута, который отображает отдельную страницу продукта
    product: Products = Products.objects.get(slug=product_slug)
    
    context: dict[str, Products] = {
        'product': product
    }
    
    return render(request, "goods/Product.html", context=context)
