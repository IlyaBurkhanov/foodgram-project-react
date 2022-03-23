# Generated by Django 3.2.12 on 2022-03-08 20:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_auto_20220308_2249'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredientcount',
            name='ingredient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ingredient_count', to='api.ingredients'),
        ),
        migrations.AlterField(
            model_name='ingredientcount',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipe', to='api.recipes'),
        ),
    ]