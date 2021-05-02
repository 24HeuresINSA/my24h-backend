from django.db import models
from datetime import timedelta
from django.contrib.auth.models import User
from django.utils import timezone


class Race(models.Model):
    type = models.CharField(max_length=30)
    duration = models.DurationField(default=timedelta(hours=24.0))
    km_points = models.FloatField(default=0)
    elevation_gain_coeff = models.FloatField(default=0)
    duration_gain_coeff = models.FloatField(default=0)

    class Meta:
        ordering = ['type']
        verbose_name = "Race"
        verbose_name_plural = "Races"

    def __str__(self):
        return self.type


class Category(models.Model):
    name = models.CharField(max_length=50)
    label = models.TextField(max_length=500)
    nb_participants = models.IntegerField()

    class Meta:
        ordering = ["nb_participants"]

    def __str__(self):
        return self.name


class Racer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField()
    strava_id = models.IntegerField(null=True)
    birthday = models.DateField()

    class Meta:
        ordering = ['user__username']
        verbose_name = 'Racer'
        verbose_name_plural = 'Racers'

    def __str__(self):
        return self.user.username


class Team(models.Model):
    name = models.CharField(max_length=50)
    join_code = models.CharField(max_length=50, verbose_name="Join Code")
    image = models.ImageField()
    race = models.ForeignKey(Race, related_name='teams', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, related_name='teams', on_delete=models.CASCADE)
    members = models.ManyToManyField(Racer, related_name="teams")
    admins = models.ManyToManyField(Racer, related_name="teams")

    class Meta:
        ordering = ['name']
        verbose_name = 'Team'
        verbose_name_plural = 'Teams'

    def __str__(self):
        return self.name


class Activity(models.Model):
    activity_id = models.IntegerField(primary_key=True)
    runner = models.ForeignKey(Racer, related_name='activities', on_delete=models.CASCADE)
    date = models.DateTimeField(blank=False, null=False)
    upload_date = models.DateTimeField(default=timezone.now())
    distance = models.FloatField(blank=False, null=False)
    positive_elevation_gain = models.PositiveIntegerField(blank=False, null=False)
    negative_elevation_gain = models.PositiveIntegerField(blank=False, null=False)
    run_time = models.DurationField()
    avg_speed = models.FloatField()
    point = models.IntegerField()

