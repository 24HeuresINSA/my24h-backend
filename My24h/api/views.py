import datetime
import requests

from .serializer import *
from .models import *

from django.http import *
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.contrib.auth.decorators import permission_required
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.decorators import action, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated

from drf_yasg.utils import swagger_auto_schema


class CategoryViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class RaceViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    queryset = Race.objects.all()
    serializer_class = RaceSerializer
    permission_classes = [IsAuthenticated]


class AthleteViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.CreateModelMixin,
                     viewsets.GenericViewSet):
    queryset = Athlete.objects.all()
    serializer_class = AthleteSerializer

    def get_permissions(self):
        if self.action == 'list' or self.action == 'retrieve':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        print(request.user.username)
        return super(AthleteViewSet, self).list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        #Todo Integrity error
        username = request.POST.get("username")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        try:
            birthday = datetime.datetime.strptime(request.POST.get("birthdate"), "%d-%m-%Y")
            if username and first_name and last_name and email and password and birthday:
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
                    birthday=birthday.date()
                )
                athlete.save()
                return Response(AthleteSerializer(athlete).data)
            else:
                return HttpResponseBadRequest("One or more parameters are missing.")
        except TypeError:
            return HttpResponseBadRequest("Birthdate should be in dd-mm-YYYY format.")

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
        if request.method == 'POST':
            user_id = request.user.id
            try:
                athlete = Athlete.objects.get(user__id=user_id)
            except models.ObjectDoesNotExist:
                return HttpResponseNotFound(f"Racer with id {pk} not found.")
            athlete.strava_id = request.POST.get("strava_id")
            athlete.save()
        return Response("Successfully updated")

    @action(detail=True, methods=['GET'])
    def point(self, request, pk=None):
        try:
            racer = Athlete.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Racer with id {pk} not found")
        return Response()

    @action(detail=True, methods=['GET'])
    def strava_activities(self, request, pk=None):
        headers = {'Authorization': 'Bearer' + 'd43906d7756cf666c38faf6ee0f4935bdfdc0086'}

        try:
            response = requests.get(
                url="",
                headers=headers
            )
            racer = Athlete.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Racer with id {pk} not found")

    @action(detail=True, methods=['GET', 'POST', 'DELETE'])
    def activites(self, request, pk=None):
        try:
            racer = Athlete.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Racer with id {pk} not found")
        if request.method == 'POST':
            return True
        elif request.method == 'DELETE':
            return False
        return Response()

    @action(detail=True, methods=['GET'])
    def ranking(self, request, pk=None):
        return Response("Ca arrive")


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

    @action(detail=True, methods=['GET', 'DELETE'])
    def members(self, request, pk=None):
        try:
            team = Team.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Team with id {pk} not found.")
        if request.method == "DELETE":
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
            if team.members.count() < team.category.nb_participants:
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

    @action(detail=True, methods=["GET"])
    def ranking(self, request, pk=None):
        teams = Team.objects.all()


class TokenObtainPairView2(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class TokenRefreshView2(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer
