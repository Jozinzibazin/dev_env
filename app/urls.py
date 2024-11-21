"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin 
from django.urls import include, path #Импорт функций include и path из модуля urls для создания URL-маршрутов
from django.conf.urls.static import static #Импорт функции static из conf.urls для настройки URL-маршрутов к статическим файлам

from app import settings

#Объявление списка URL-шаблонов
urlpatterns = [
    path('admin/', admin.site.urls), #/admin/ который связывается с административным сайтом (admin.site.urls)
    path('', include('main.urls', namespace='main')), #главная страница сайта ''
    path('catalog/', include('goods.urls', namespace='catalog')), #Путь /catalog/ который включает маршруты из файла urls.py в приложении goods с пространством имен 'catalog'.
    path('user/', include('users.urls', namespace='user'))
    ]

#Проверка, что режим отладки включен для этапа разработки
if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")), #Добавление URL-шаблона __debug__/, который включает маршруты для панели отладки debug_toolbar

        ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) #Добавление маршрутов для доступа к медиафайлам при включенном DEBUG
                                                                                 #settings.MEDIA_URL это URL-адрес для медиафайлов, а settings.MEDIA_ROOT директория, в которой хранятся эти файлы
