from django.contrib.auth.models import User, Group
from rest_framework import serializers
from .models import *
from rest_framework_simplejwt.serializers import TokenObtainSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken


class RaceSerializer(serializers.HyperlinkedModelSerializer):
    type = serializers.CharField(read_only=True)
    duration = serializers.DurationField(read_only=True)
    km_points = serializers.FloatField(read_only=True)
    elevation_gain_coeff = serializers.FloatField(read_only=True)

    class Meta:
        model = Race
        fields = ['url', 'type', 'duration', 'km_points', 'elevation_gain_coeff']


class CategoryLightSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Category
        fields = ['url', 'name']


class TeamLightSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.CharField(required=True)

    class Meta:
        model = Team
        fields = ['url', 'name']


class RunnerLightSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.SlugRelatedField(many=False, read_only=True, slug_field='username')
    point = serializers.IntegerField(read_only=True)

    class Meta:
        model = Racer
        fields = ['url', 'user', 'point']


class TeamSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.CharField()
    join_code = serializers.CharField()
    image = serializers.ImageField(required=False)
    race = serializers.StringRelatedField(many=False)
    racers = RunnerLightSerializer(many=True)
    category = CategoryLightSerializer()

    class Meta:
        model = Team
        fields = ['url', 'name', 'join_code', 'racers', 'race', 'category']


class UserSerializer(serializers.HyperlinkedModelSerializer):
    username = serializers.CharField(max_length=30, required=True)
    first_name = serializers.CharField(max_length=30, required=True)
    last_name = serializers.CharField(max_length=30, required=True)
    email = serializers.CharField(max_length=30, required=True)
    password = serializers.CharField(max_length=100, write_only=True)

    class Meta:
        model = User
        fields = ['url', 'username', 'first_name', 'last_name', 'email', 'password']


class RacerSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerializer(many=False)
    image = serializers.ImageField()
    team = TeamLightSerializer(many=False, read_only=True)

    class Meta:
        model = Racer
        fields = ['url', 'user', 'image', 'birthday', 'team']


class CategorySerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Category
        fields = ['url', 'name', 'nb_participants']


class CustomTokenObtainPairSerializer(TokenObtainSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data['lifetime'] = int(refresh.access_token.lifetime.total_seconds())
        return data

class CustomTokenRefreshSerializer(TokenRefreshSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = RefreshToken(attrs['refresh'])
        data['lifetime'] = int(refresh.access_token.lifetime.total_seconds)
        return data


