# Generated by Django 5.1.1 on 2024-09-23 00:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_speciality_alter_doctor_speciality'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Speciality',
            new_name='Specialities',
        ),
    ]
