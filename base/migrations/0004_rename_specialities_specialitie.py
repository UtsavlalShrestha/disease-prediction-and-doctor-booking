# Generated by Django 5.1.1 on 2024-09-23 00:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_rename_speciality_specialities'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Specialities',
            new_name='Specialitie',
        ),
    ]