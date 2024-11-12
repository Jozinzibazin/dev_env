from django.apps import AppConfig # Импортирует класс AppConfig


class MainConfig(AppConfig):# Создает класс конфигурации для приложения 'main', который наследует от AppConfig
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'
