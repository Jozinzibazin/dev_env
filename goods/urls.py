from django.urls import path# Импортируем функцию path из модуля django.urls для определения маршрутов URL в Django

from goods import views# Импортируем views из  goods. Позволяет использовать функции, определённые в views, для обработки запросов.

app_name = 'goods'# Устанавливаем имя приложения, чтобы избежать конфликтов имен URL

 # Список, который содержит все маршруты URL для данного приложения. Каждый маршрут сопоставляется с представлением
urlpatterns = [
    path('seacrh/', views.catalog, name='search'),
    path('<slug:category_slug>/', views.catalog, name='index'),  # URL '' будет соответствовать представлению catalog из файла views
    path('product/<slug:product_slug>/', views.product, name='product'), #URL 'product/' будет соответствовать представлению product из файла views
]