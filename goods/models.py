from unicodedata import category
from django.db import models
from django.urls import reverse

# Create your models here.
class Categories(models.Model):  # Создаём модель Categories (Категории) для базы данных.
    name = models.CharField(max_length=150, unique=True, verbose_name='Название') # Поле для хранения названия категории
    slug = models.SlugField(max_length=200, unique=True, blank=True, null=True, verbose_name='URL')  # Поле для хранения URL-метки (slug) категории

    class Meta:
        db_table = 'category'
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self) -> str:
        return str(self.name)


class Products(models.Model):# Создаём модель Products для базы данных
    name = models.CharField(max_length=150, unique=True, verbose_name='Название')
    slug = models.SlugField(max_length=200, unique=True, blank=True, null=True, verbose_name='URL')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    image = models.ImageField(upload_to='good_images', blank=True, null=True, verbose_name='Изображение')
    price = models.DecimalField(default=0.00, max_digits=7, decimal_places=2, verbose_name='Цена')
    discount = models.DecimalField(default=0.00, max_digits=7, decimal_places=2, verbose_name='Скидка в процентах')
    quantity = models.PositiveIntegerField(default=0, verbose_name='Количество')  # Исправлено "Колчество" на "Количество"
    category = models.ForeignKey(to=Categories, on_delete=models.CASCADE, verbose_name='Категория')


    class Meta:
        db_table = 'product'  # Убрано двоеточие
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ("id",)

    def __str__(self) -> str:
        return f'{self.name} Количество - {self.quantity}'
    
    def get_absolute_url(self):
        return reverse("catalog:product", kwargs={"product_slug": self.slug})
    
    
    def display_id(self) -> str:
        return f"{self.id:05}"
    
    def sell_price(self) -> any:
        if self.discount:
            return round(self.price - self.price*self.discount/100, 2)
        
        return self.price