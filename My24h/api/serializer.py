from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Athlete, Category, Team, Discipline, RaceDiscipline, Race
from rest_framework_simplejwt.serializers import TokenObtainSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"""                                                        Light Serializers                                         """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class AthleteLightSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(many=False, read_only=True, slug_field='username')
    point = serializers.IntegerField(read_only=True)

    class Meta:
        model = Athlete
        fields = ['id', 'user', 'point']


class CategoryLightSerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ['id', 'name']


class TeamLightSerializer(serializers.ModelSerializer):

    class Meta:
        model = Team
        fields = ['id', 'name']


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"""                                                        Serializers                                               """
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = "__all__"


class DisciplineSerializer(serializers.ModelSerializer):

    class Meta:
        model = Discipline
        fields = "__all__"


class RaceDisciplineSerializer(serializers.ModelSerializer):
    discipline = DisciplineSerializer()

    class Meta:
        model = RaceDiscipline
        fields = ["discipline", "duration"]


class RaceSerializer(serializers.ModelSerializer):
    disciplines = RaceDisciplineSerializer(many=True)

    class Meta:
        model = Race
        fields = ["id", "name", "disciplines"]


class TeamSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    race = serializers.StringRelatedField(many=False)
    category = CategoryLightSerializer(many=False)
    members = AthleteLightSerializer(many=True)
    admins = AthleteLightSerializer(many=True)

    class Meta:
        model = Team
        fields = ['id', 'name', 'race', 'category', 'members', 'admins']


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=30, required=True)
    first_name = serializers.CharField(max_length=30, required=True)
    last_name = serializers.CharField(max_length=30, required=True)
    email = serializers.CharField(max_length=30, required=True)
    password = serializers.CharField(max_length=100, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']


class AthleteSerializer(serializers.ModelSerializer):
    user = UserSerializer(many=False)
    image = serializers.ImageField()
    team = TeamLightSerializer()
    race = RaceSerializer()

    class Meta:
        model = Athlete
        fields = ['id', 'user', 'image', 'birthday', 'team', 'strava_id', 'race']


class TeamRankingSerializer(serializers.ModelSerializer):
    points = serializers.SerializerMethodField()
    race = RaceSerializer()
    category = CategoryLightSerializer()

    def get_points(self, obj):
        team = Team.objects.get(id=obj.pk)
        team_activities = team.members.activities.all()
        points = 0
        for activity in team_activities:
            points += activity.point
        return points

    class Meta:
        model = Team
        fields = ["id", "name", "race", "category", "points"]


class AthleteRankingSerializer(serializers.ModelSerializer):
    points = serializers.SerializerMethodField()

    def get_points(self, obj):
        athlete = Athlete.objects.get(id=obj.id)
        activities = athlete.activities.all()
        points = 0
        for activity in activities:
            points += activity.point
        return points

    class Meta:
        model = Athlete
        fields = ["id", "username", "points"]


class CustomTokenObtainPairSerializer(TokenObtainSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['name'] = user.username
        return token

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
