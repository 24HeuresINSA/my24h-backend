import datetime
import requests
import os
import time

from itertools import chain

from .serializer import *
from .models import *

from django.http import *
from django.db import IntegrityError
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.decorators import api_view

from django.utils.timezone import now

from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from rest_framework_simplejwt.tokens import RefreshToken

from drf_yasg.utils import swagger_auto_schema


class CategoryViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class RaceViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    queryset = Race.objects.all()
    serializer_class = RaceSerializer
    permission_classes = [AllowAny]

    @action(detail=True, methods=['GET'])
    def challenge_elevation(self, request, pk=None):
        athletes = Athlete.objects.all()
        elevation_points = 0
        username = ""
        for athlete in athletes:
            activities = Activity.objects.filter(athlete=athlete)
            elevation_athlete = 0
            for activity in activities:
                elevation_athlete += activity.positive_elevation_gain * activity.discipline.elevation_gain_coeff
            if elevation_athlete > elevation_points:
                username = athlete.user.username
                elevation_points = elevation_athlete
        return Response({
            "username": username,
            "elevation_points": elevation_points
        })

    @action(detail=True, methods=['GET'])
    def challenge_duration(self, request, pk=None):
        athletes = Athlete.objects.all()
        duration_points = 0
        username = ""
        for athlete in athletes:
            activities = Activity.objects.filter(athlete=athlete)
            for activity in activities:
                duration_activity = activity.run_time.total_seconds() * activity.discipline.duration_coeff
                if duration_activity > duration_points:
                    username = athlete.user.username
                    duration_points = duration_activity
        return Response({
            "username": username,
            "duration_points": duration_points
        })




class AthleteViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.CreateModelMixin,
                     mixins.UpdateModelMixin,
                     viewsets.GenericViewSet):
    queryset = Athlete.objects.all()
    serializer_class = AthleteSerializer
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        print(request.user.username)
        return super(AthleteViewSet, self).list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        # Todo Integrity error
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
        print(race_id)
        try:
            try:
                race = Race.objects.get(id=race_id)
            except models.ObjectDoesNotExist as e:
                print(e)
                return HttpResponseBadRequest(f"Race {race_id} does not exist.")
            birthday = datetime.datetime.strptime(request.POST.get("birthdate"), "%Y-%m-%d")
            if username and first_name and last_name and email and password and birthday and address and zip_code and city and gender:
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
                except IntegrityError as e:
                    print(e)
                    return HttpResponseBadRequest("Username is already used.")
            else:
                return HttpResponseBadRequest("One or more parameters are missing.")
        except TypeError:
            return HttpResponseBadRequest("Birthdate should be in dd-mm-YYYY format.")

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
            return HttpResponseNotFound("Athlete not found")

    @swagger_auto_schema(method='GET',
                         operation_id='Get profile picture',
                         operation_description='Retrieve the profile picture of a racer')
    @swagger_auto_schema(method='POST',
                         operation_id='Create profile picture',
                         operation_description="Add a profile picture to a racer profile")
    @action(detail=True, methods=['GET', 'POST'])
    def profile_pictures(self, request, pk=None):
        try:
            racer = Athlete.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Racer with id {pk} not found.")
        if request.method == "POST":
            racer.image = request.POST.get("profile_picture")
            racer.save()
        return Response(racer)

    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def strava(self, request, pk=None):
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
                athlete.access_token_expiration_date = datetime.datetime.fromtimestamp(data.get("expires_at"))
                athlete.refresh_token = data.get("refresh_token")
                athlete.strava_id = data.get("athlete").get("id")
                athlete.save()
                return Response("Successfully updated")
            return HttpResponseServerError()
        return HttpResponseBadRequest()

    @action(detail=True, methods=['GET'])
    def point(self, request, pk=None):
        race_id = request.POST.get("race_id")
        category_id = request.POST.get("category_id")
        try:
            race = Race.objects.get(id=race_id)
        except models.ObjectDoesNotExist as e:
            print(e)
            return Response(status=404, data={"err": f"Race {id} not found"})
        try:
            category = Category.objects.get(id=category_id)
        except models.ObjectDoesNotExist as e:
            print(e)
            return Response(status=404, data={"err": f"Category {category_id} not found."})
        athletes = Athlete.objects.filter()
        return Response("Salut")

    @action(detail=True, methods=['GET'])
    def stat(self, request, pk=None):
        user_id = request.user.id
        try:
            athlete = Athlete.objects.get(user__id=user_id)
        except models.ObjectDoesNotExist as e:
            print(e)
            return Response(status=400, data={"err": f"Athlete {user_id} not found."})

        if athlete.team is None:
            race = athlete.race
        else:
            race = athlete.team.race
        response = {}
        disciplines = RaceDiscipline.objects.filter(race=race)
        for discipline in disciplines:
            total_km = 0
            avg_speed = 0
            total_time = 0
            total_elevation = 0
            record_distance = 0
            record_time = 0
            record_elevation = 0
            record_avg_speed = 0
            points = 0
            discip = discipline.discipline
            activities = Activity.objects.filter(athlete=athlete, discipline=discip)
            i = 0
            if activities:
                for activity in activities:
                    total_km += activity.distance
                    total_elevation += activity.positive_elevation_gain
                    total_time += activity.run_time.total_seconds()
                    avg_speed = (avg_speed * i + activity.avg_speed) / (i + 1)
                    if activity.distance > record_distance:
                        record_distance = activity.distance
                    if activity.run_time.total_seconds() > record_time:
                        record_time = activity.run_time.total_seconds()
                    if activity.positive_elevation_gain > record_elevation:
                        record_elevation = activity.positive_elevation_gain
                    if activity.avg_speed > record_avg_speed:
                        record_avg_speed = activity.avg_speed
                    points += activity.distance * activity.discipline.points_per_km
                    i += 1
                response[discip.name] = {
                    "total_km": total_km,
                    "total_time": total_time,
                    "total_elevation": total_elevation,
                    "avg_speed": avg_speed,
                    "record_distance": record_distance,
                    "record_time": record_time,
                    "record_elevation": record_elevation,
                    "record_avg_speed": record_avg_speed,
                    "points": points,
                    "nb_activities": i
                }
        return Response(response)

    @action(detail=True, methods=['GET'])
    def strava_activities(self, request, pk=None):
        try:
            athlete = Athlete.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return HttpResponseForbidden
        if athlete.last_update is not None:
            if athlete.access_token_expiration_date is not None:
                if time.time() >= athlete.access_token_expiration_date.timestamp():
                    refresh, msg = self.refresh_strava_token(athlete)
                    if not refresh:
                        return Response(status=403, data=msg)
            else:
                refresh, msg = self.refresh_strava_token(athlete)
                if not refresh:
                    return Response(status=403, data=msg)
            headers = {'Authorization': 'Bearer ' + athlete.access_token}
            if "pintade" in athlete.user.username:
                params = {
                    "per_page": 30,
                }
            else:
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
            print(response)
            if response.status_code < 300:
                # athlete.last_update = now()
                activities = response.json()
                print("Activities", activities)
                for activity in activities:
                    if not StravaActivity.objects.filter(strava_id=activity.get("id")).exists():
                        strava_activity, created = StravaActivity.objects.get_or_create(
                            strava_id=activity.get("id"),
                            name=activity.get("name"),
                            type=activity.get("type"),
                            distance=activity.get("distance"),
                            moving_time=datetime.timedelta(seconds=int(activity.get("moving_time"))),
                            total_elevation_gain=activity.get("total_elevation_gain"),
                            start_date=datetime.datetime.strptime(activity.get("start_date_local"),
                                                                  "%Y-%m-%dT%H:%M:%SZ"),
                            athlete=athlete
                        )
            else:
                return Response(response.status_code)

        else:
            if athlete.access_token_expiration_date is not None:
                if time.time() >= athlete.access_token_expiration_date.timestamp():
                    refresh, msg = self.refresh_strava_token(athlete)
                    if not refresh:
                        return Response(status=403, data=msg)
            else:
                refresh, msg = self.refresh_strava_token(athlete)
                if not refresh:
                    return Response(status=403, data=msg)
            headers = {'Authorization': 'Bearer ' + athlete.access_token}
            if "pintade" in athlete.user.username:
                params = {
                    "per_page": 30,
                }
            else:
                params = {
                    "per_page": 30,
                    # "before": 1619179200,
                    # "after": 1618401600,
                }
            response = requests.get(
                url="https://www.strava.com/api/v3/athlete/activities",
                headers=headers,
                params=params
            )
            if response.status_code < 300:
                activities = response.json()
                print("Activities", activities)
                for activity in activities:
                    if not StravaActivity.objects.filter(strava_id=activity.get("id")).exists():
                        strava_activity, created = StravaActivity.objects.get_or_create(
                            strava_id=activity.get("id"),
                            name=activity.get("name"),
                            type=activity.get("type"),
                            distance=activity.get("distance"),
                            moving_time=datetime.timedelta(seconds=int(activity.get("moving_time"))),
                            total_elevation_gain=activity.get("total_elevation_gain"),
                            start_date=datetime.datetime.strptime(activity.get("start_date_local"),
                                                                  "%Y-%m-%dT%H:%M:%SZ"),
                            athlete=athlete
                        )
                        print(strava_activity)
            else:
                return Response(response.status_code)
        activities = Activity.objects.filter(athlete=athlete)
        id = []
        if activities is not None:
            for activity in activities:
                id.append(activity.activity_id)
        strava_activities = StravaActivity.objects.filter(athlete=athlete).exclude(strava_id__in=id)
        type = []
        race = ""
        if athlete.team is None:
            race = athlete.race
        else:
            race = athlete.team.race
        disciplines = RaceDiscipline.objects.filter(race=race)
        for discipline in disciplines:
            if discipline.discipline.name == "Course à pied":
                type = ["Hike", "Walk", "Run"]
            else:
                type = ["Ride"]
        strava_activities = StravaActivity.objects.filter(athlete=athlete, type__in=type).exclude(strava_id__in=id)
        return Response(StravaActivitySerializer(strava_activities, many=True).data)

    def refresh_strava_token(self, athlete: Athlete):
        print(athlete.refresh_token)
        data = {
            "client_id": os.getenv("CLIENT_ID"),
            "client_secret": os.getenv("CLIENT_SECRET"),
            "grant_type": "refresh_token",
            "refresh_token": athlete.refresh_token
        }
        response = requests.post(
            url="https://www.strava.com/api/v3/oauth/token",
            data=data
        )
        if response.status_code == 200:
            data = response.json()
            print(data)
            athlete.access_token = data.get("access_token")
            athlete.access_token_expiration_date = datetime.datetime.fromtimestamp(data.get("expires_at"))
            athlete.refresh_token = data.get("refresh_token")
            athlete.save()
            return [True, ""]
        else:
            print(response.status_code)
            print(response.text)
            return [False, response.text]

    @action(detail=True, methods=['GET', 'POST', 'DELETE'])
    def activities(self, request, pk=None):
        print("Hello")
        try:
            athlete = Athlete.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Racer with id {pk} not found")
        if request.method == 'POST':
            strava_id = request.POST.get("strava_id")
            try:
                strava_activity = StravaActivity.objects.get(strava_id=strava_id)
                print("Ok")
            except models.ObjectDoesNotExist as e:
                print(e)
                return Response(status=404, data={f"Strava activity {strava_id} not found"})
            print("Hop")
            if strava_activity.athlete == athlete:
                if strava_activity.type == "Hike" or strava_activity.type == "Walk" or strava_activity.type == "Run":
                    print("Run")
                    discipline = Discipline.objects.get(name="Course à pied")
                elif strava_activity.type == "Ride":
                    print("Bike")
                    discipline = Discipline.objects.get(name="Vélo")
                else:
                    return HttpResponseBadRequest
                activity, created = Activity.objects.get_or_create(
                    activity_id=strava_activity.strava_id,
                    athlete=Athlete.objects.get(user__id=request.user.id),
                    date=strava_activity.start_date,
                    distance=strava_activity.distance,
                    positive_elevation_gain=strava_activity.total_elevation_gain,
                    discipline=discipline,
                    run_time=strava_activity.moving_time,
                    avg_speed=strava_activity.distance / (strava_activity.moving_time.total_seconds() / 3600 * 1000)
                )
                print(activity.activity_id)
                return Response(ActivitySerializer(activity, many=False).data)
            else:
                return Response("Tentative de filouterie")
        elif request.method == 'DELETE':
            activity_id = request.POST.get("activity_id")
            user_id = request.user.id
            try:
                activity = Activity.objects.get(activity_id)
            except models.ObjectDoesNotExist as e:
                print(e)
                return Response(status=404, data={"err": f"Activity {activity_id} not found"})
            try:
                athlete = Athlete.objects.get(user__id=user_id)
            except models.ObjectDoesNotExist as e:
                print(e)
                return HttpResponseServerError
            if activity.athlete == athlete:
                activity.delete()
                return Response(status=204, data={"succ": "Activity Deleted"})
            return False
        return Response(
            ActivitySerializer(Activity.objects.filter(athlete=Athlete.objects.get(user__id=request.user.id))).data)

    @action(detail=True, methods=['POST'])
    def ranking(self, request, pk=None):
        race_id = request.POST.get("race_id")
        try:
            race = Race.objects.get(id=race_id)
        except models.ObjectDoesNotExist as e:
            return Response(status=404, data={"err": f"Race {race_id} not found"})
        athletes = Athlete.objects.all()
        list_athletes = []
        for athlete in athletes:
            if athlete.team is not None:
                if athlete.team.race == race:
                    list_athletes.append(athlete)
            else:
                if athlete.race is not None:
                    if athlete.race == race:
                        list_athletes.append(athlete)
        print(list_athletes)
        athletes_serializer = []
        for athlete in list_athletes:
            activities = Activity.objects.filter(athlete=athlete)
            race_disciplines = RaceDiscipline.objects.filter(race=race)
            athlete_serializer = {}
            if activities:
                for race_discipline in race_disciplines:
                    discipline_activities = []
                    for activity in activities:
                        if activity.discipline == race_discipline.discipline:
                            discipline_activities.append(activity)
                    dict_activities = []
                    for discipline_activity in discipline_activities:
                        dict_activities.append((discipline_activity,
                                                discipline_activity.distance / discipline_activity.run_time.total_seconds()))
                    sorted_dict = sorted(dict_activities, key=lambda tup: tup[1])
                    points = 0
                    duration = 0
                    saved_activities = []
                    for elem in sorted_dict:
                        if duration < race_discipline.duration.total_seconds():
                            if duration + elem[0].run_time.total_seconds() > race_discipline.duration.total_seconds():
                                temp = race_discipline.duration.total_seconds() - duration
                                activity_duration = elem[0].run_time.total_seconds()
                                activity_distance = elem[0].distance
                                duration = race_discipline.duration.total_seconds()
                                points += (
                                                  temp * activity_distance / activity_duration) * race_discipline.discipline.points_per_km
                                saved_activities.append(elem[0].activity_id)
                                break
                            else:
                                duration += elem[0].run_time.total_seconds()
                                points += (elem[0].distance * race_discipline.discipline.points_per_km)
                                saved_activities.append(elem[0].activity_id)

                    athlete_serializer[race_discipline.discipline.name] = {
                        "points": points,
                        "activities": saved_activities,
                        "duration": duration
                    }
                total_points = 0
                for key, value in athlete_serializer.items():
                    total_points += value["points"]
                athletes_serializer.append((total_points, {
                    "athlete_id": athlete.id,
                    "username": athlete.user.username,
                    "total_points": total_points,
                    "details": athlete_serializer,
                }))
            else:
                athletes_serializer.append((0, {
                    "athlete_id": athlete.id,
                    "username": athlete.user.username,
                    "total_points": 0,
                    "details": None,
                }))
        sorted_athletes = sorted(athletes_serializer, key=lambda tup: tup[0])
        other_final_serializer = {}
        i = 1
        for sorted_athlete in sorted_athletes:
            other_final_serializer[i] = sorted_athlete[1]
            i += 1
        return Response(data=other_final_serializer)


class TeamViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.CreateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user_id = request.user.id
        print(user_id, request.user.username)
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
                return HttpResponse("This athlete is already member of a team")
            except models.ObjectDoesNotExist as e:
                print(e)
                return HttpResponseNotFound("Error w/ parameters received")
        else:
            return HttpResponseBadRequest("Missing one or more parameters")

    @action(detail=True, methods=['GET'])
    def stat(self, request, pk=None):
        user_id = request.user.id
        try:
            team = Team.objects.get(id=pk)
        except models.ObjectDoesNotExist as e:
            print(e)
            return Response(status=404, data={'err': f"Team {pk} not found"})
        try:
            athlete = Athlete.objects.get(user__id=user_id)
        except models.ObjectDoesNotExist as e:
            print(e)
            return HttpResponseServerError
        if team.members.filter(id=athlete.id).exists():
            athletes = team.members.all()
            disciplines = RaceDiscipline.objects.filter(race=team.race)
            response = {}
            for discipline in disciplines:
                record_distance = 0
                user_distance = None
                record_time = 0
                user_time = None
                record_elevation = 0
                user_elevation = None
                record_avg_speed = 0
                user_avg_speed = None
                points = 0
                discipline_elem = discipline.discipline
                if athletes:
                    for athlete in athletes:
                        activities = Activity.objects.filter(athlete=athlete, discipline=discipline_elem)
                        distance = 0
                        time = 0
                        elevation = 0
                        avg_speed = 0
                        i = 0
                        if activities:
                            for activity in activities:
                                distance += activity.distance
                                time += activity.run_time.total_seconds()
                                elevation += activity.positive_elevation_gain
                                avg_speed = (avg_speed * i + activity.avg_speed) / (1 + i)
                                points += activity.distance * activity.discipline.points_per_km
                                i += 1
                            if distance > record_distance:
                                record_distance = distance
                                user_distance = athlete.user.username
                            if time > record_time:
                                record_time = time
                                user_time = athlete.user.username
                            if elevation > record_elevation:
                                record_elevation = elevation
                                user_elevation = athlete.user.username
                            if avg_speed > record_avg_speed:
                                record_avg_speed = avg_speed
                                user_avg_speed = athlete.user.username
                        response[discipline_elem.name] = {
                            "record_distance": record_distance,
                            "user_distance": user_distance,
                            "record_time": record_time,
                            "user_time": user_time,
                            "record_elevation": record_elevation,
                            "user_elevation": user_elevation,
                            "record_avg_speed": record_avg_speed,
                            "user_avg_speed": user_avg_speed,
                            "points": points
                        }
            return Response(response)
        return Response(status=400, data={"err": "Tentative de filouterie"})

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
        except models.ObjectDoesNotExist as e:
            return Response("Error")

    @action(detail=True, methods=['POST'])
    def join_codes(self, request, pk=None):
        user_id = request.user.id
        try:
            team = Team.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Team {pk} not found.")
        try:
            athlete = Athlete.objects.get(user__id=user_id)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Athlete with id {request.POST.get('racer_id')} not found")
        if athlete.admin is not None:
            if athlete.admin.id == team.id:
                team.join_code = request.POST.get("join_code")
                team.save()
                return Response("Join code successfully updated")
            else:
                return HttpResponseBadRequest(f"Athlete with id {athlete.id} does not have enough rights.")
        return HttpResponseBadRequest(f"Athlete must be an admin of the team to change join code")

    @action(detail=True, methods=['GET', 'POST'])
    def members(self, request, pk=None):
        try:
            team = Team.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Team with id {pk} not found.")
        if request.method == "POST":
            user_id = request.user.id
            try:
                admin = Athlete.objects.get(user__id=user_id)
                athlete = Athlete.objects.get(id=request.POST.get("athlete_id"))
            except models.ObjectDoesNotExist:
                return HttpResponseNotFound(f"Racer with id {request.POST.get('racer_id')} not found.")
            if athlete != admin:
                if admin.admin is not None:
                    if admin.admin.id == team.id:
                        if athlete.team is not None and athlete.admin is None:
                            if athlete.team.id == team.id:
                                athlete.team = None
                                athlete.save()
        return Response(TeamSerializer(team).data)

    @action(detail=True, methods=['POST'])
    def join(self, request, pk=None):
        user_id = request.user.id
        try:
            team = Team.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Team with id {pk} not found")
        join_code = request.POST.get("join_code")
        try:
            athlete = Athlete.objects.get(user__id=user_id)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Racer with id {user_id} not found")
        if join_code == team.join_code:
            if team.members.count() <= team.category.nb_participants:
                if athlete.team is not None:
                    if not athlete.team.id == team.id:
                        athlete.team = team
                        athlete.save()
                        return Response(TeamSerializer(team).data)
                    else:
                        return HttpResponseBadRequest(
                            f"Racer with id {user_id} is already a member of the team {team.id}")
                else:
                    athlete.team = team
                    athlete.save()
                    return Response(TeamSerializer(team).data)
            else:
                return HttpResponseNotAllowed(f"The team with id {team.id} has already reach its maximal capacity")
        else:
            return HttpResponseNotAllowed(f"Wrong join code")

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
                return HttpResponseBadRequest()
            return HttpResponseBadRequest()
        except models.ObjectDoesNotExist as e:
            print(e)
            return HttpResponseNotFound("Team or athlete not found.")

    @action(detail=True, methods=["GET", "POST", "DELETE"])
    def admin(self, request, pk=None):
        user_id = request.user.id
        try:
            team = Team.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Team with id {pk} not found.")
        try:
            admin = Athlete.objects.get(user__id=user_id)
            athlete = Athlete.objects.get(id=int(request.POST.get("athlete_id")))
            if admin.admin is not None:
                if request.method == 'POST':
                    if athlete.team.id == team.id and admin.admin.id == team.id:
                        athlete.admin = team
                        athlete.save()
                    else:
                        return HttpResponseNotAllowed(
                            f"Racer with id {athlete.id} cannot be an admin: he/she is not a member of"
                            f" the team")
                if request.method == 'DELETE':
                    if athlete.admin.id == team.id and admin.admin.id == team.id:
                        if team.admins.count() > 1:
                            athlete.admin = None
                            athlete.save()
                        else:
                            return HttpResponseNotAllowed("A team must have an administrator")
                    else:
                        return HttpResponseBadRequest()
                return Response(TeamSerializer(team).data)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Racer with id {request.POST.get('id')}")

    @action(detail=True, methods=["POST"])
    def ranking(self, request, pk=None):
        race_id = request.POST.get("race_id")
        category_id = request.POST.get("category_id")
        try:
            race = Race.objects.get(id=race_id)
        except models.ObjectDoesNotExist as e:
            return Response(status=404, data={"err": f"Race {race_id} not found"})
        try:
            category = Category.objects.get(id=category_id)
        except models.ObjectDoesNotExist as e:
            print(e)
            return Response(status=404, data={"err", f'Race {category_id} not found'})
        teams = Team.objects.filter(race=race, category=category)
        teams_serializers = {}
        for team in teams:
            activities = []
            athletes = team.members.all()
            for athlete in athletes:
                activities_athlete = athlete.activities.all()
                if activities_athlete:
                    activities = list(chain(activities, activities_athlete))
            race = team.race
            race_disciplines = RaceDiscipline.objects.filter(race=race)
            team_serializer = {}
            for race_discipline in race_disciplines:
                discipline_activities = []
                if activities:
                    for activity in activities:
                        if activity.discipline == race_discipline.discipline:
                            discipline_activities.append(activity)
                    dict_activities = []
                    for discipline_activity in discipline_activities:
                        dict_activities.append((discipline_activity,
                                                discipline_activity.distance / discipline_activity.run_time.total_seconds()))
                    sorted_dict = sorted(dict_activities, key=lambda tup: tup[1])
                    points = 0
                    duration = 0
                    saved_activities = []
                    for elem in sorted_dict:
                        if duration < race_discipline.duration.total_seconds():
                            if duration + elem[0].run_time.total_seconds() > race_discipline.duration.total_seconds():
                                temp = race_discipline.duration.total_seconds() - duration
                                activity_duration = elem[0].run_time.total_seconds()
                                activity_distance = elem[0].distance
                                duration = race_discipline.duration.total_seconds()
                                points += (
                                                  temp * activity_distance / activity_duration) * race_discipline.discipline.points_per_km
                                saved_activities.append(elem[0].activity_id)
                                break
                            else:
                                duration += elem[0].run_time.total_seconds()
                                points += (elem[0].distance * race_discipline.discipline.points_per_km)
                                saved_activities.append(elem[0].activity_id)

                    team_serializer[race_discipline.discipline.name] = {
                        "points": points,
                        "activities": saved_activities,
                        "duration": duration
                    }
            total_points = 0
            for key, value in team_serializer.items():
                total_points += value["points"]
            teams_serializers[team.id] = {
                "name": team.name,
                "team_id": team.id,
                "total_points": total_points,
                "details": team_serializer,
            }
        final_serializer = {k: v for k, v in
                            sorted(teams_serializers.items(), key=lambda item: item[1]["total_points"])}
        other_final_serializer = {}
        i = 1
        for key, value in final_serializer.items():
            other_final_serializer[i] = value
        print(other_final_serializer)
        return Response(data=other_final_serializer)


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
    return HttpResponseBadRequest("Oups")


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
    return HttpResponseBadRequest()
