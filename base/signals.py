from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Hospital 

@receiver(post_save, sender=User)
def create_hospital(sender, instance, created, **kwargs):
    if created: 
        Hospital.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_hospital(sender, instance, **kwargs):
    if hasattr(instance, 'hospital'):
        instance.hospital.save()
