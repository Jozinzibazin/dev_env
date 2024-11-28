from django.urls import path# Импортируем функцию path из модуля django.urls для определения маршрутов URL в Django

from carts import views# Импортируем views из  goods. Позволяет использовать функции, определённые в views, для обработки запросов.

app_name = 'carts'# Устанавливаем имя приложения, чтобы избежать конфликтов имен URL

 # Список, который содержит все маршруты URL для данного приложения. Каждый маршрут сопоставляется с представлением
urlpatterns = [
    path('cart_add/<slug:product_slug>/', views.cart_add, name='cart_add'),
    path('cart_change/<slug:product_slug>/', views.cart_change, name='cart_change'),  # URL '' будет соответствовать представлению catalog из файла views
    path('cart_remove/<int:cart_id>/', views.cart_remove, name='cart_remove'), #URL 'product/' будет соответствовать представлению product из файла views
]