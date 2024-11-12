from django.urls import path  # Импортирует функцию path для определения маршрутов URL

from main import views  # Импортирует views из приложения 'main' для обработки запросов

app_name = 'main'  # Устанавливает имя пространства имен для маршрутов в этом приложении, чтобы избежать конфликтов имен URL

urlpatterns = [  # Список маршрутов, которые связывают URL с представлениями (views)
    path('', views.index, name='index'),  # Путь для главной страницы, использует представление 'index' из views и задает имя маршрута 'index'
    path('about/', views.about, name='about'),  # Путь для страницы "О нас", использует представление 'about' из views и задает имя маршрута 'about'
]