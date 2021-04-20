from django.contrib.auth.models import User, Group
from rest_framework import serializers
from .models import *


class RaceSerializer(serializers.HyperlinkedModelSerializer):
    type = serializers.CharField(read_only=True)
    duration = serializers.DurationField(read_only=True)
    km_points = serializers.FloatField(read_only=True)
    elevation_gain_coeff = serializers.FloatField(read_only=True)

    class Meta:
        model = Race
        fields = ['url', 'type', 'duration', 'km_points', 'elevation_gain_coeff']


class TeamLightSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.CharField(required=True)

    class Meta:
        model = Team
        fields = ['url', 'name']


class RunnerLightSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.SlugRelatedField(many=False, read_only=True, slug_field='username')
    point = serializers.IntegerField(read_only=True)

    class Meta:
        model = Runner
        fields = ['url', 'user', 'point']


class TeamSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.CharField(required=True)
    join_code = serializers.CharField(required=True)
    nb_runner = serializers.ChoiceField(required=True, choices=[1, 4, 12])
    race = serializers.StringRelatedField(many=False, read_only=True)
    runners = RunnerLightSerializer(many=True, read_only=True)

    class Meta:
        model = Team
        fields = ['url', 'name', 'join_code', 'nb_runner', 'race', 'runners']


class UserSerializer(serializers.HyperlinkedModelSerializer):
    username = serializers.CharField(max_length=30, required=True)
    first_name = serializers.CharField(max_length=30, required=True)
    last_name = serializers.CharField(max_length=30, required=True)
    email = serializers.CharField(max_length=30, required=True)
    password = serializers.CharField(max_length=100, write_only=True)

    class Meta:
        model = User
        fields = ['url', 'username', 'first_name', 'last_name', 'email', 'password']


class RunnerSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerializer(many=False)
    birthday = serializers.DateField(required=True)
    point = serializers.IntegerField(read_only=True)
    team = TeamLightSerializer(many=False, read_only=True)

    class Meta:
        model = Runner
        fields = ['url', 'user', 'birthday', 'point', 'team']

