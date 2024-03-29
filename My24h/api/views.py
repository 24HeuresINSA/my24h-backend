import datetime
import requests
import os
import time

from django.utils.timezone import now
from django.db import IntegrityError
from django.contrib.auth import authenticate

from rest_framework import mixins, viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, permission_classes, api_view
from rest_framework.permissions import IsAuthenticated, AllowAny

from drf_yasg.utils import swagger_auto_schema

from .serializer import *
from .models import *


class CategoryViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    tags = ['Categories']

    @swagger_auto_schema(operation_id='List categories',
                         operation_description='List all the races availables',
                         tags=tags,
                         security=[])
    def list(self, request, *args, **kwargs):
        return super(CategoryViewSet, self).list(request=request, args=args, kwargs=kwargs)

    @swagger_auto_schema(operation_id='Get category',
                         operation_description="Retrieve information about a category",
                         tags=tags,
                         security=[])
    def retrieve(self, request, *args, **kwargs):
        return super(CategoryViewSet, self).retrieve(request=request, args=args, kwargs=kwargs)


class RaceViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    queryset = Race.objects.all()
    serializer_class = RaceSerializer
    permission_classes = [AllowAny]
    tags = ['Races']

    @swagger_auto_schema(operation_id='List races',
                         operation_description='List all the races availables.',
                         tags=tags,
                         security=[])
    def list(self, request, *args, **kwargs):
        return super(RaceViewSet, self).list(request=request, args=args, kwargs=kwargs)

    @swagger_auto_schema(operation_id='Get race',
                         operation_description="Retrieve information about a race.",
                         tags=tags,
                         security=[])
    def retrieve(self, request, *args, **kwargs):
        super(RaceViewSet, self).retrieve(
            request=request, args=args, kwargs=kwargs)


class AthleteViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.CreateModelMixin,
                     mixins.UpdateModelMixin,
                     viewsets.GenericViewSet):
    queryset = Athlete.objects.all()
    serializer_class = AthleteSerializer
    permission_classes = [AllowAny]
    tags = ['Athletes']

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @swagger_auto_schema(operation_id='Get athlete',
                         operation_description='Retrieve information about an athlete.',
                         tags=tags)
    def retrieve(self, request, *args, **kwargs):
        return super(AthleteViewSet, self).retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_id='List athletes',
                         operation_description='List all the athletes registered.',
                         tags=tags)
    def list(self, request, *args, **kwargs):
        return super(AthleteViewSet, self).retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_id='Create athlete',
                         operation_description='Create a new athlete',
                         tags=tags)
    def create(self, request, *args, **kwargs):
        username = request.POST.get("username")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        gender = request.POST.get("gender")
        address = request.POST.get("address")
        zip_code = request.POST.get("zip_code")
        city = request.POST.get("city")
        phone = request.POST.get("phone")
        race_id = request.POST.get("race_id")
        try:
            try:
                race = Race.objects.get(id=race_id)
            except models.ObjectDoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'err': f"Race {race_id} does not exist."})
            birthday = datetime.datetime.strptime(
                request.POST.get("birthdate"), "%Y-%m-%d")
            if username and first_name and last_name and email and password and birthday and address and zip_code \
                    and city and gender:
                try:
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password
                    )
                    user.first_name, user.last_name = first_name, last_name
                    user.is_staff = False
                    user.save()
                    athlete = Athlete.objects.create(
                        user=user,
                        gender=gender,
                        birthday=birthday.date(),
                        address=address,
                        zip_code=zip_code,
                        city=city,
                        phone=phone,
                        race=race
                    )
                    athlete.save()
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        "id": athlete.id,
                        "access": str(refresh.access_token),
                        "refresh": str(refresh)
                    })
                except IntegrityError:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={'err': "Username is already used."})
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'err': "One or more parameters are missing."})
        except TypeError:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={'err': "Birthdate should be in dd-mm-YYYY format."})

    @swagger_auto_schema(operation_id='Update athlete',
                         operation_description="Update athlete information.",
                         tags=tags)
    def update(self, request, *args, **kwargs):
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        address = request.POST.get("address")
        zip_code = request.POST.get("zip_code")
        city = request.POST.get("city")
        try:
            athlete = Athlete.objects.get(id=kwargs["pk"])
            if phone:
                athlete.phone = phone
            if email:
                athlete.user.email = email
                athlete.user.save()
            if address:
                athlete.address = address
            if zip_code:
                athlete.zip_code = zip_code
            if city:
                athlete.city = city
            athlete.save()
            return Response(AthleteSerializer(athlete).data)
        except models.ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'err': "Athlete not found"})

    @swagger_auto_schema(operation_id='Partially update athlete',
                         operation_description="Update an athlete user",
                         tags=tags)
    def partial_update(self, request, *args, **kwargs):
        return super(AthleteViewSet, self).partial_update(request=request, args=args, kwargs=kwargs)

    @swagger_auto_schema(method='GET',
                         operation_id='Get profile picture',
                         operation_description='Retrieve the profile picture of an athlete',
                         tags=tags)
    @swagger_auto_schema(method='POST',
                         operation_id='Create profile picture',
                         operation_description="Add a profile picture to a racer profile",
                         tags=tags)
    @action(detail=True, methods=['GET', 'POST'])
    def profile_pictures(self, request, pk=None):
        try:
            racer = Athlete.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'err': f"Racer with id {pk} not found."})
        if request.method == "POST":
            racer.image = request.POST.get("profile_picture")
            racer.save()
        return Response(racer)

    @swagger_auto_schema(method='POST',
                         operation_id='Connect to Strava',
                         operation_description="Connect to the athlete's Strava account.",
                         tags=tags)
    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def strava(self, request):
        authorization_code = request.POST.get("authorization_code")
        if authorization_code:
            data = {
                "client_id": os.getenv("CLIENT_ID"),
                "client_secret": os.getenv("CLIENT_SECRET"),
                "code": authorization_code,
                "grant": "authorization_code"
            }
            response = requests.post(
                url="https://www.strava.com/oauth/token",
                data=data
            )
            if response.status_code < 300:
                user_id = request.user.id
                athlete = Athlete.objects.get(user__id=user_id)
                data = response.json()
                athlete.access_token = data.get("access_token")
                athlete.access_token_expiration_date = datetime.datetime.fromtimestamp(
                    data.get("expires_at"))
                athlete.refresh_token = data.get("refresh_token")
                athlete.strava_id = data.get("athlete").get("id")
                athlete.save()
                return Response("Successfully updated/ En cours de réparation")
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(method='GET',
                         operation_id='List Strava activities',
                         operation_description="Retrieve athlete's Strava activities",
                         tags=tags)
    @action(detail=True, methods=['GET'])
    def strava_activities(self, request, pk=None):

        user_id = request.user.id
        try:
            athlete = Athlete.objects.get(user__id=user_id)
        except models.ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'err': f'Athlete {user_id} not found.'})
        if time.time() > athlete.last_update.time():
            if time.time() > athlete.access_token_expiration_date:
                refresh_strava_token(athlete)
            headers = {'Authorization': 'Bearer ' + athlete.access_token}
            try:
                params = {
                    "per_page": 30,
                    "before": 1619179200,
                    "after": 1618401600,
                }
                response = requests.get(
                    url="https://www.strava.com/api/v3/athlete/activities",
                    headers=headers,
                    params=params
                )
                if response.status_code == 200:
                    athlete.last_update = now()
                    activities = response.json()
                    for activity in activities:
                        StravaActivity.objects.create(
                            id=activity.get("id"),
                            name=activity.get("name"),
                            type=activity.get("type"),
                            distance=activity.get("distance"),
                            moving_time=activity.get("moving_time"),
                            total_elevation_gain=activity.get(
                                "total_elevation_gain"),
                            start_date=datetime.datetime.strptime(activity.get("start_date_local"),
                                                                  "%Y-%m-%dT%H:%M:%SZ"),
                            athlete=athlete
                        )
            except models.ObjectDoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'err': f"Athlete {pk} not found"})
        return Response("Todo")


class TeamViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.CreateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]
    tags = ["Teams"]

    @swagger_auto_schema(operation_id='List teams',
                         operation_description='Retrieve the list of all the teams registered',
                         tags=tags)
    def list(self, request, *args, **kwargs):
        return super(TeamViewSet, self).list(request=request, args=args, kwargs=kwargs)

    @swagger_auto_schema(operation_id='Get team',
                         operation_description="Retrieve team's information.",
                         tags=tags)
    def retrieve(self, request, *args, **kwargs):
        return super(TeamViewSet, self).retrieve(request=request, args=args, kwargs=kwargs)

    @swagger_auto_schema(operation_id='Create team',
                         operation_description="Create a new team.",
                         tags=tags)
    def create(self, request, *args, **kwargs):
        user_id = request.user.id
        name = request.POST.get("name")
        join_code = request.POST.get("join_code")
        race_id = request.POST.get("race_id")
        category_id = request.POST.get("category_id")
        if user_id and name and join_code and race_id:
            try:
                athlete = Athlete.objects.get(user__id=user_id)
                if athlete.team is None:
                    race = Race.objects.get(id=race_id)
                    category = Category.objects.get(id=category_id)
                    team = Team.objects.create(
                        name=name,
                        join_code=join_code,
                        race=race,
                        category=category
                    )
                    athlete.team = team
                    athlete.admin = team
                    team.save()
                    athlete.save()
                    return Response(TeamSerializer(team).data)
                return Response(status=status.HTTP_400_BAD_REQUEST,
                                data={'err': "This athlete is already member of a team"})
            except models.ObjectDoesNotExist as e:
                print(e)
                return Response(status=status.HTTP_404_NOT_FOUND, data={'err': "Error w/ parameters received"})
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'err': "Missing one or more parameters"})

    @swagger_auto_schema(operation_id='Delete team',
                         operation_description='Delete a team',
                         tags=tags)
    def destroy(self, request, *args, **kwargs):
        user_id = request.user.id
        try:
            athlete = Athlete.objects.get(user__id=user_id)
            team = Team.objects.get(id=int(kwargs["pk"]))
            if athlete.admin is not None:
                if athlete.admin.id == team.id:
                    team.delete()
                    return Response(TeamLightSerializer(Team.objects.all(), many=True).data)
            return Response("Athlete is not admin of this team")
        except models.ObjectDoesNotExist:
            return Response("Error")

    @swagger_auto_schema(method='PUT',
                         operation_id='Update join code',
                         operation_description="Update team's join code.",
                         tags=tags)
    @action(detail=True, methods=['PUT'])
    def join_codes(self, request, pk=None):
        user_id = request.user.id
        try:
            team = Team.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'err': f"Team {pk} not found."})
        try:
            athlete = Athlete.objects.get(user__id=user_id)
        except models.ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND,
                            data={'err': f"Athlete with id {request.POST.get('racer_id')} not found"})
        if athlete.admin is not None:
            if athlete.admin.id == team.id:
                team.join_code = request.POST.get("join_code")
                team.save()
                return Response("Join code successfully updated")
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST,
                                data={'err': f"Athlete with id {athlete.id} does not have enough rights."})
        return Response(status=status.HTTP_403_FORBIDDEN,
                        data={'err': "Athlete must be an admin of the team to change join code"})

    @swagger_auto_schema(method='GET',
                         operation_id='Get members',
                         operation_description="Retrieve team's members",
                         tags=tags)
    @swagger_auto_schema(method='DELETE',
                         operation_id='Delete member',
                         operation_description="Allow a team's admin to remove a member of his/her team.",
                         tags=tags)
    @action(detail=True, methods=['GET', 'DELETE'])
    def members(self, request, pk=None):
        try:
            team = Team.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'err': f"Team with id {pk} not found."})
        if request.method == "DELETE":
            user_id = request.user.id
            try:
                admin = Athlete.objects.get(user__id=user_id)
                athlete = Athlete.objects.get(
                    id=request.POST.get("athlete_id"))
            except models.ObjectDoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND,
                                data={'err': f"Racer with id {request.POST.get('racer_id')} not found."})
            if athlete != admin:
                if admin.admin is not None:
                    if admin.admin.id == team.id:
                        if athlete.team is not None and athlete.admin is None:
                            if athlete.team.id == team.id:
                                athlete.team = None
                                athlete.save()
        return Response(TeamSerializer(team).data)

    @swagger_auto_schema(method='POST',
                         operation_id='Join team',
                         operation_description="Allow an athlete to join a team by providing a join code",
                         tags=tags)
    @action(detail=True, methods=['POST'])
    def join(self, request, pk=None):
        user_id = request.user.id
        try:
            team = Team.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'err': f"Team with id {pk} not found"})
        join_code = request.POST.get("join_code")
        try:
            athlete = Athlete.objects.get(user__id=user_id)
        except models.ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'err': f"Racer with id {user_id} not found"})
        if join_code == team.join_code:
            if team.members.count() < team.category.nb_participants:
                if athlete.team is not None:
                    if not athlete.team.id == team.id:
                        athlete.team = team
                        athlete.save()
                        return Response(TeamSerializer(team).data)
                    else:
                        return Response(status=status.HTTP_400_BAD_REQUEST, data={
                            'err': f"Racer with id {user_id} is already a member of the team {team.id}"})
                else:
                    athlete.team = team
                    athlete.save()
                    return Response(TeamSerializer(team).data)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST,
                                data={'err': f"The team with id {team.id} has already reach its maximal capacity"})
        else:
            return Response(status=status.HTTP_403_FORBIDDEN, data={'err': "Wrong join code"})

    @swagger_auto_schema(method='POST',
                         operation_id='Leave team',
                         operation_description="Allow an athlete to leave a team by him/herself. If the athlete leaving"
                                               "is the only admin of the team, the admin role is transferred to a "
                                               "random member of the team.",
                         tags=tags)
    @action(detail=True, methods=["POST"])
    def leave(self, request, pk=None):
        user_id = request.user.id
        try:
            athlete = Athlete.objects.get(user__id=user_id)
            team = Team.objects.get(id=pk)
            if athlete.team is not None:
                if athlete.team.id == team.id:
                    if athlete.admin is not None:
                        if athlete.admin.id == team.id:
                            if team.admins.count() == 1 and team.members.count() >= 2:
                                members = team.members.all()
                                for member in members:
                                    if member != athlete:
                                        member.admin = team
                                        member.save()
                                        break
                            elif team.admins.count() == 0 and team.members.count() == 1:
                                team.delete()
                    athlete.team = None
                    athlete.admin = None
                    athlete.save()
                    return Response("Athlete leaves the team successfully.")
                return Response(status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except models.ObjectDoesNotExist as e:
            print(e)
            return Response(status=status.HTTP_404_NOT_FOUND, data={'err': "Team or athlete not found."})

    @swagger_auto_schema(method='GET',
                         operation_id="List team admins",
                         operation_description="List the team's admin",
                         tags=tags)
    @swagger_auto_schema(method='POST',
                         operation_id='Add team admin',
                         operation_description='Allow an admin to add a new admin to the team.',
                         tags=tags)
    @swagger_auto_schema(method='DELETE',
                         operation_id='Remove team admin',
                         operation_description='Allow a team admin to remove another admin of his/her team.',
                         tags=tags)
    @action(detail=True, methods=["GET", "POST", "DELETE"])
    def admin(self, request, pk=None):
        user_id = request.user.id
        try:
            team = Team.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'err': f"Team with id {pk} not found."})
        try:
            admin = Athlete.objects.get(user__id=user_id)
            athlete = Athlete.objects.get(
                id=int(request.POST.get("athlete_id")))
            if admin.admin is not None:
                if request.method == 'POST':
                    if athlete.team.id == team.id and admin.admin.id == team.id:
                        athlete.admin = team
                        athlete.save()
                    else:
                        return Response(status=status.HTTP_400_BAD_REQUEST, data={
                            'err': f"Racer with id {athlete.id} cannot be an admin: he/she is not a member of"
                                   f" the team"})

                if request.method == 'DELETE':
                    if athlete.admin.id == team.id and admin.admin.id == team.id:
                        if team.admins.count() > 1:
                            athlete.admin = None
                            athlete.save()
                        else:
                            return Response(status=status.HTTP_400_BAD_REQUEST,
                                            data={'err': "A team must have an administrator"})
                    else:
                        return Response(status=status.HTTP_400_BAD_REQUEST)
                return Response(TeamSerializer(team).data)
        except models.ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'err': f"Racer with id {request.POST.get('id')}"})


@swagger_auto_schema(method='POST',
                     operation_id='Get tokens',
                     operation_description='Retrieve a pair of access/refresh JWT token.',
                     tags=['Tokens'])
@api_view(['POST'])
@permission_classes([AllowAny])
def access_token(request):
    username = request.POST.get("username")
    password = request.POST.get("password")
    if request.method == 'POST':
        user = authenticate(username=username, password=password)
        if user:
            if Athlete.objects.filter(user=user).exists():
                athlete = Athlete.objects.get(user=user)
                refresh = RefreshToken.for_user(user)
                return Response(
                    {
                        "id": athlete.id,
                        "access": str(refresh.access_token),
                        "refresh": str(refresh)
                    }
                )
    return Response(status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='POST',
                     operation_id='Refresh tokens',
                     operation_description='Refresh the access token by providing a valid refresh token.',
                     tags=['Tokens'])
@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_tocken(request):
    refresh = request.POST.get("refresh")
    if refresh:
        refresh_token = RefreshToken(refresh)
        return Response(
            {
                "access": str(refresh_token.access_token),
                "refresh": str(refresh_token)
            }
        )
    return Response(status=status.HTTP_400_BAD_REQUEST)


def refresh_strava_token(athlete: Athlete):
    data = {
        "client_id": os.getenv("CLIENT_ID"),
        "client_secret": os.getenv("CLIENT_SECRET"),
        "grant": "refresh_token",
        "refresh": athlete.refresh_token
    }
    response = requests.get(
        url="https://www.strava.com/api/v3/oauth/token",
        data=data
    )
    if response.status_code == 200:
        data = response.json()
        athlete.access_token = data.get("access_token")
        athlete.access_token_expiration_date = datetime.datetime.fromtimestamp(
            data.get("expires_at"))
        athlete.refresh_token = data.get("refresh_token")
        athlete.strava_id = data.get("athlete").get("id")
        athlete.save()
