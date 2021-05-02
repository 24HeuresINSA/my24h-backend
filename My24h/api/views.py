import datetime

from .serializer import *
from .models import *

from django.http import *
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.contrib.auth.decorators import permission_required
from rest_framework_simplejwt.views import TokenViewBase

from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

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


class RacerViewSet(mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.CreateModelMixin,
                   mixins.UpdateModelMixin,
                   viewsets.GenericViewSet):
    queryset = Racer.objects.all()
    serializer_class = RacerSerializer

    def create(self, request, *args, **kwargs):
        username = request.POST.get("username")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        birthdate = int(request.POST.get("birthdate"))
        if username and first_name and last_name and email and password and birthdate:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            user.fist_name, user.last_name = first_name, last_name
            user.is_staff = False
            user.save()
            racer = Racer.objects.create(
                user=user,
                birthdate=datetime.datetime.fromtimestamp(birthdate)
            )
            racer.save()
            return Response
        else:
            return HttpResponseBadRequest("One or more parameters are missing.")

    @swagger_auto_schema(method='GET',
                         operation_id='Get profile picture',
                         operation_description='Retrieve the profile picture of a racer')
    @swagger_auto_schema(method='POST',
                         operation_id='Create profile picture',
                         operation_description="Add a profile picture to a racer profile")
    @action(detail=True, methods=['GET', 'POST'])
    def profile_pictures(self, request, pk=None):
        try:
            racer = Racer.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Racer with id {pk} not found.")
        if request.method == "POST":
            racer.image = request.POST.get("profile_picture")
            racer.save()
        return Response(racer)

    @action(detail=True, methods=['GET', 'POST'])
    def strava(self, request, pk=None):
        try:
            racer = Racer.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Racer with id {pk} not found.")
        if request.method == 'POST':
            racer.strava_id = request.POST.get("strava_id")
            racer.save()
        return Response()

    @action(detail=True, methods=['GET'])
    def point(self, request, pk=None):
        try:
            racer = Racer.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Racer with id {pk} not found")
        return Response()

    @action(detail=True, methods=['GET'])
    def strava_activities(self, request, pk=None):
        try:
            racer = Racer.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Racer with id {pk} not found")

    @action(detail=True, methods=['GET', 'POST', 'DELETE'])
    def activites(self, request, pk=None):
        try:
            racer = Racer.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Racer with id {pk} not found")
        if request.method == 'POST':
            return True
        elif request.method == 'DELETE':
            return False
        return Response()



class TeamViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.CreateModelMixin,
                  mixins.DestroyModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

    @action(detail=True, methods=['POST'])
    def join_codes(self, request, pk=None):
        try:
            team = Team.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Team {pk} not found.")
        try:
            racer = Racer.objects.get(id=request.POST.get("racer_id"))
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Racer with id {request.POST.get('racer_id')} not found")
        if team.admins.filter(id=racer.id).exists():
            team.join_code = request.POST.get("join_code")
        else:
            return HttpResponseNotAllowed(f"Racer with id {racer.id} does not have enough rights.")
        return Response()

    @action(detail=True, methods=['GET', 'DELETE'])
    def members(self, request, pk=None):
        try:
            team = Team.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Team with id {pk} not found.")
        if request.method == "DELETE":
            try:
                racer = Racer.objects.get(id=request.POST.get("racer_id"))
            except models.ObjectDoesNotExist:
                return HttpResponseNotFound(f"Racer with id {request.POST.get('racer_id')} not found.")
            team.members.remove(racer)
        return Response()

    @action(detail=True, methods=['POST'])
    def join(self, request, pk=None):
        try:
            team = Team.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Team with id {pk} not found")
        racer_id = request.POST.get("racer_id")
        join_code = request.POST.get("join_code")
        try:
            racer = Racer.objects.get(id=racer_id)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Racer with id {racer_id} not found")
        if join_code == team.join_code:
            if team.members.count() < team.category.nb_participants:
                if not team.members.filter(id=racer_id).exists():
                    team.members.add(racer)
                    return Response()
                else:
                    return HttpResponseBadRequest(f"Racer with id {racer_id} is already a member of the team {team.id}")
            else:
                return HttpResponseNotAllowed(f"The team with id {team.id} has already reach its maximal capacity")
        else:
            return HttpResponseNotAllowed(f"Wrong join code")

    @action(detail=True, methods=["GET", "POST", "DELETE"])
    def admin(self, request, pk=None):
        try:
            team = Team.objects.get(id=pk)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Team with id {pk} not found.")
        try:
            racer = Race.objects.get(request.user.username)
        except models.ObjectDoesNotExist:
            return HttpResponseNotFound(f"Racer with id {request.POST.get('id')}")
        if request.method == 'POST':
            if team.members.filter(racer).exists():
                team.admins.add(racer)
            else:
                return HttpResponseNotAllowed(f"Racer with id {racer.id} cannot be an admin: he/she is not a member of"
                                              f" the team")
        if request.method == 'DELETE':
            if team.admins.filter(racer).exists():
                if team.admins.count() > 1:
                    team.admins.remove(racer)
                else:
                    return HttpResponseNotAllowed("")
            else:
                return HttpResponseBadRequest()


class TokenObtainPairView(TokenViewBase):
    serializer_class = CustomTokenObtainPairSerializer


class TokenRefreshView(TokenViewBase):
    serializer_class = CustomTokenRefreshSerializer
