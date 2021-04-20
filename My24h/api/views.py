import json
from random import random

from django.contrib.auth.models import User, Group
from django.db.models import Sum
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import request, status
from rest_framework.response import Response
from .serializer import *
from .models import *


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


# class SetNewRunner(request):
#     # Manque le hash du mdp, à voir si ya pas un bail déjà dans django
#     race = Race.objects.get(race_type=request.data.race_type)
#     r = Runner(name=request.data.name,
#                surname=request.data.surname,
#                birthdate=request.data.birthdate,
#                email=request.data.email,
#                inside_team=request.data.inside_team,
#                nickname=request.data.nickname,
#                race=race)  # race.id plutôt ?
#     r.save()
#     Response(json.dumps({"message": "user created"}), status=status.HTTP_201_CREATED)
#
#
# class SetTeamToRunner(request):
#     r = Runner.objects.get(id=request.data.user_id)
#     team = Team.objects.get(join_code=request.data.join_code)
#     team.nb_runners += 1  # on incrémente le nb de runner dans la team
#     r.team_name = team  # team.id plutôt ?
#     r.save()
#     team.save()
#     Response(json.dumps({"message": "Team assigned"}), status=status.HTTP_200_OK)
#
#
# class SetNewTeam(request):
#     race = Race.objects.get(race_type=request.data.race_type)
#     team_code = int(random() * 100000)
#     t = Team(name=request.data.team_name,
#              nb_runner=0,
#              join_code=team_code,
#              race=race)  # race.id plutôt ?
#     t.save()
#     Response(json.dumps({"message": "Team created", "join_code": team_code}), status=status.HTTP_201_CREATED)
#
#
# class GetRunnerTotalPoints(request):
#     km_sum = Activity.objects.aggregate(Sum('distance')).get(runner=request.data.runner_id)
#     km_points = Race.objects.get(
#         race_type=Runner.objects.get(id=request.data.runner_id).race_type).km_points  # à vérifier
#     # coeff_deniv = Race.objects.get(race_type=Runner.objects.get(id=request.data.runner_id).race_type).elevation_gain_coeff  # à vérifier
#
#     points = km_sum * km_points  # Attention, manque dénivelé
#
#     Response(json.dumps({"total_points": points}), status=status.HTTP_200_OK)
