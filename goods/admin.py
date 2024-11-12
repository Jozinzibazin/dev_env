from django.contrib import admin

# Register your models here.
from goods.models import Categories, Products #Импорn модели Categories и Products из приложения goods, чтобы зарегистрировать их в админке

#admin.site.register(Categories)
#admin.site.register(Products)



@admin.register(Categories)
class CategoriesAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}



@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}