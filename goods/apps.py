from django.apps import AppConfig


class GoodsConfig(AppConfig): #Это настройка для приложения goods, где будет определяться его имя, настройки базы данных и другие параметры.
    default_auto_field = 'django.db.models.BigAutoField' #efault_auto_field которое указывает тип поля для автоматических идентификаторов в моделяхm (автоинкремент)
    name = 'goods'
    verbose_name = 'Товары'
