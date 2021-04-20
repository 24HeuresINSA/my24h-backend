from django.db import models


class Race(models.Model):
    race_type = models.CharField(max_length=30)
    duration = models.IntegerField()
    km_points = models.IntegerField()
    elevation_gain_coeff = models.FloatField()


class Team(models.Model):
    team_name = models.CharField(max_length=50)
    join_code = models.IntegerField()
    nb_runners = models.IntegerField()
    race_type = models.ForeignKey(Race, on_delete=models.CASCADE)


class Runner(models.Model):
    surname = models.CharField(max_length=30)
    name = models.CharField(max_length=30)
    nickname = models.CharField(max_length=30, blank=True)
    strava_id = models.CharField(blank=True)
    strava_token = models.JSONField(blank=True)
    birthdate = models.DateField()
    email = models.EmailField()
    password = models.CharField() #géré à part?
    inside_team = models.BooleanField() # inutile peut-être
    team_name = models.ForeignKey(Team, on_delete=models.CASCADE, blank=True)
    race_type = models.ForeignKey(Race, on_delete=models.CASCADE)
    # est-ce qu'on rajoute le nb de points par runner direct dans la db où est ce qu'on y calcule à chaque fois
    # qu'on en a besoin ?


class Activity(models.Model):
    race_type = models.ForeignKey(Race, on_delete=models.CASCADE)
    runner = models.ForeignKey(Runner, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    activity_date = models.DateTimeField()
    upload_date = models.DateTimeField(auto_now=True)
    distance = models.IntegerField()
    positive_elevation_gain = models.IntegerField()
    negative_elevation_gain = models.IntegerField()
    run_time = models.TimeField()
    avg_speed = models.FloatField()
    activity_url = models.URLField()



