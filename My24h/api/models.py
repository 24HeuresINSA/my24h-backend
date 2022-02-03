from django.db import models
from datetime import timedelta
from django.contrib.auth.models import User
from django.utils import timezone


class Discipline(models.Model):
    name = models.CharField(max_length=30)
    points_per_km = models.FloatField(default=0)
    elevation_gain_coeff = models.FloatField(default=0)
    duration_coeff = models.FloatField(default=0)

    class Meta:
        ordering = ["name"]
        verbose_name = "Discipline"
        verbose_name_plural = "Disciplines"

    def __str__(self):
        return self.name


class Race(models.Model):
    name = models.CharField(max_length=30)

    class Meta:
        ordering = ['name']
        verbose_name = "Race"
        verbose_name_plural = "Races"

    def __str__(self):
        return self.name


class RaceDiscipline(models.Model):
    race = models.ForeignKey(Race, related_name="disciplines", on_delete=models.CASCADE)
    discipline = models.ForeignKey(Discipline, related_name="races", on_delete=models.CASCADE)
    duration = models.DurationField(default=timedelta(hours=24.0))

    class Meta:
        db_table = "api_race_discipline"

    def __str__(self):
        return f"{self.race.name}: {self.discipline.name} -> {self.duration}"


class Category(models.Model):
    name = models.CharField(max_length=50)
    label = models.TextField(max_length=500)
    max_participants = models.IntegerField()

    class Meta:
        ordering = ["max_participants"]
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
    gender = models.CharField(max_length=20, choices=[('male', "male"), ('female', "female"), ('unknown', "unknown")])
    birthday = models.DateField()
    address = models.CharField(max_length=100, null=True)
    zip_code = models.CharField(max_length=5, null=True)
    city = models.CharField(max_length=100, null=True)
    phone = models.CharField(max_length=20, null=True)
    image = models.ImageField(null=True)
    strava_id = models.IntegerField(null=True)
    access_token = models.CharField(max_length=800, null=True)
    access_token_expiration_date = models.DateTimeField(null=True)
    refresh_token = models.CharField(max_length=800, null=True)
    last_update = models.DateTimeField(null=True)
    race = models.ForeignKey(Race, default=None, null=True, related_name="race", on_delete=models.SET_NULL)
    category = models.ForeignKey(Category, default=None, null=True, related_name="category", on_delete=models.SET_NULL)
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

    class Meta:
        ordering = ["upload_date"]
        verbose_name = "Activity"
        verbose_name_plural = "Activities"


class StravaActivity(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=500)
    type = models.CharField(max_length=50)
    distance = models.FloatField()
    moving_time = models.DurationField()
    total_elevation_gain = models.FloatField()
    start_date = models.DateTimeField()
    athlete = models.ForeignKey(Athlete, related_name="strava_activities", on_delete=models.CASCADE)

    class Meta:
        db_table = "api_strava_activity"
        ordering = ["start_date"]
        verbose_name = "Strava Activity"
        verbose_name_plural = "Strava Activities"

    def __str__(self):
        return self.name
