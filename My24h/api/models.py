from django.db import models
from datetime import timedelta
from django.contrib.auth.models import User
from django.utils import timezone

from django_cryptography.fields import encrypt


class Discipline(models.Model):
    name = models.CharField(max_length=30)
    points_per_km = models.FloatField(default=0)
    elevation_gain_coeff = models.FloatField(default=0)

    class Meta:
        ordering = ["name"]
        verbose_name = "Discipline"
        verbose_name_plural = "Disciplines"

    def __str__(self):
        return self.name


class Race(models.Model):
    name = models.CharField(max_length=30)
    duration = models.DurationField(default=timedelta(hours=24.0))
    disciplines = models.ManyToManyField(Discipline, related_name="races")

    class Meta:
        ordering = ['name']
        verbose_name = "Race"
        verbose_name_plural = "Races"

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=50)
    label = models.TextField(max_length=500)
    nb_participants = models.IntegerField()

    class Meta:
        ordering = ["nb_participants"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=50, unique=True)
    join_code = models.CharField(max_length=50, verbose_name="Join Code")
    image = models.ImageField()
    race = models.ForeignKey(Race, related_name='teams', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, related_name='teams', on_delete=models.CASCADE)

    class Meta:
        ordering = ['name']
        verbose_name = 'Team'
        verbose_name_plural = 'Teams'

    def __str__(self):
        return self.name


class Athlete(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField()
    access_token = encrypt(models.CharField(max_length=800, null=True))
    access_token_expiration_date = encrypt(models.DateTimeField(null=True))
    refresh_token = encrypt(models.CharField(max_length=800, null=True))
    birthday = models.DateField()
    team = models.ForeignKey(Team, default=None, null=True, related_name="members", on_delete=models.SET_NULL)
    admin = models.ForeignKey(Team, default=None, null=True, related_name="admins", on_delete=models.SET_NULL)

    class Meta:
        ordering = ['user__username']
        verbose_name = 'Athlete'
        verbose_name_plural = 'Athletes'

    def __str__(self):
        return self.user.username


class Activity(models.Model):
    activity_id = models.IntegerField(primary_key=True)
    athlete = models.ForeignKey(Athlete, related_name='activities', on_delete=models.CASCADE)
    date = models.DateTimeField(blank=False, null=False)
    upload_date = models.DateTimeField(default=timezone.now)
    distance = models.FloatField(blank=False, null=False)
    positive_elevation_gain = models.PositiveIntegerField(blank=False, null=False)
    negative_elevation_gain = models.PositiveIntegerField(blank=False, null=False)
    run_time = models.DurationField()
    avg_speed = models.FloatField()
    point = models.IntegerField()

    class Meta:
        ordering = ["upload_date"]
        verbose_name = "Activity"
        verbose_name_plural = "Activities"
