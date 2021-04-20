from django.db import models
from datetime import timedelta
from django.contrib.auth.models import User


class Race(models.Model):
    type = models.CharField(max_length=30)
    duration = models.DurationField(default=timedelta(hours=24.0))
    km_points = models.FloatField(default=0)
    elevation_gain_coeff = models.FloatField(default=0)


class Team(models.Model):
    name = models.CharField(max_length=50)
    join_code = models.CharField(max_length=50, null=False, blank=False, verbose_name="Join Code")
    nb_runners = [1, 4, 12]
    race_type = models.ForeignKey(Race, on_delete=models.CASCADE)


class Runner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    strava_auth = models.JSONField(blank=True)
    birthday = models.DateField()
    point = models.PositiveIntegerField(default=0, null=False, blank=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, blank=True)


class Activity(models.Model):
    activity_id = models.IntegerField(primary_key=True)
    runner = models.ForeignKey(Runner, on_delete=models.CASCADE)
    activity_date = models.DateTimeField(blank=False, null=False)
    upload_date = models.DateTimeField(auto_now=True)
    distance = models.PositiveIntegerField(blank=False, null=False)
    positive_elevation_gain = models.PositiveIntegerField(blank=False, null=False)
    negative_elevation_gain = models.PositiveIntegerField(blank=False, null=False)
    run_time = models.DurationField()
    avg_speed = models.FloatField()
