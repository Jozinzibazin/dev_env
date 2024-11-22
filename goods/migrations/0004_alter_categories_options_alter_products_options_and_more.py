# Generated by Django 5.1.2 on 2024-11-21 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0003_alter_categories_options_alter_categories_name_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='categories',
            options={'verbose_name': 'Категория', 'verbose_name_plural': 'Категории'},
        ),
        migrations.AlterModelOptions(
            name='products',
            options={'ordering': ('id',), 'verbose_name': 'Продукт', 'verbose_name_plural': 'Продукты'},
        ),
        migrations.AlterField(
            model_name='products',
            name='quantity',
            field=models.PositiveIntegerField(default=0, verbose_name='Количество'),
        ),
    ]