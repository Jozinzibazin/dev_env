from django.core.paginator import Paginator
from django.shortcuts import render

from goods.models import Products #Импортируем модель Products из goods. Она используется для извлечения данных о продуктах из базы данных.
from goods.utils import q_search

def catalog(request, category_slug=None): # Определяеn представление view для маршрута, который отображает каталог товаров
    
    page = request.GET.get('page', 1)
    on_sale = request.GET.get('on_sale', None)
    order_by = request.GET.get('order_by', None)
    query = request.GET.get('q', None)

    if category_slug == 'all':
        goods = Products.objects.all() # Извлекаем все товары (объекты модели Products) из базы данных
    elif query:
        goods = q_search(query)
    else:
        goods = Products.objects.filter(category__slug=category_slug) # Извлекаем все товары (объекты модели Products) из базы данных

    if on_sale:
        goods = goods.filter(discount__gt=0)
    
    if order_by and order_by != "default":
        goods = goods.order_by(order_by)
        
    paginator = Paginator(goods, 9)
    current_page = paginator.page(int(page))
    
    context: dict[str, str] = {# Создаём контекст (словарь), который будет передан в шаблон
        "title": "MayFlowers - Каталог",
        "goods": current_page,# Добавляем ключ, который содержит список всех товаров, полученных из базы данных
        "slug_url": category_slug,
    }
    return render(request, "goods/catalog.html", context)


def product(request, product_slug):# Определяем представление (view) для маршрута, который отображает отдельную страницу продукта
    product: Products = Products.objects.get(slug=product_slug)
    
    context: dict[str, Products] = {
        'product': product
    }
    
    return render(request, "goods/Product.html", context=context)
