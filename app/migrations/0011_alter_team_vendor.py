# Generated by Django 5.1.1 on 2024-09-28 16:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0010_alter_team_vendor'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='vendor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Team', to='app.vendor'),
        ),
    ]
