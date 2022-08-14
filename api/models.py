from email.policy import default
from unicodedata import name
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from ckeditor_uploader.fields import RichTextUploadingField


class Card(models.Model):
    """Class describes Card entity"""
    name = models.CharField(max_length=100, unique=True)
    short_description = models.CharField(max_length=200)
    long_description = RichTextUploadingField()
    image = models.ImageField()
    image_grayscaled = models.ImageField(blank=True)
    related_collection = models.ForeignKey('Collection', blank=True, null=True, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    rarity = models.CharField(max_length=20, blank=True)
    turn_to_dust_value = models.IntegerField(default=10)
    craft_cost = models.IntegerField(default=20)

    def __str__(self):
        return self.name


class Collection(models.Model):
    """Class describes Collection entity"""
    name = models.CharField(max_length=100, unique=True)
    short_description = models.CharField(max_length=500)
    long_description = RichTextUploadingField()
    n_cards = models.IntegerField()
    image1 = models.ImageField()
    image2 = models.ImageField(default=None, blank=True)
    image3 = models.ImageField(default=None, blank=True)
    cards = models.ManyToManyField('Card', blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CardEntry(models.Model):
    """Class describes CardEntry entity"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card = models.ForeignKey('Card', on_delete=models.CASCADE)
    source = models.CharField(max_length=50)
    acquired = models.DateTimeField(auto_now_add=True)


class Profile(models.Model):
    """Class describes Profile entity"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cards = models.ManyToManyField('Card', blank=True)
    collections = models.ManyToManyField('Collection', blank=True)
    dust = models.IntegerField(default=0)


# Create Profile within user creation
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


# Update Profile if user saved
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
