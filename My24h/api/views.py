import json
from random import random

from django.contrib.auth.models import User, Group
from django.db.models import Sum
from django.http import Http404
from django.db.models import Empty
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import request, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .serializer import *
from .models import *
from rest_framework import mixins
from rest_framework import viewsets


class RaceViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    queryset = Race.objects.all()
    serializer_class = RaceSerializer


class TeamViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.CreateModelMixin,
                  mixins.DestroyModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

    @action(detail=True, methods=['post'])
    def joint_code(self, request, pk=None):
        team = Team.objects.get(id=pk)
        team.join_code = request.data['joint_code']
        team.save()
        return Response(TeamSerializer(team).data)


class RunnerViewSet(mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.CreateModelMixin,
                    mixins.UpdateModelMixin,
                    viewsets.GenericViewSet):
    queryset = Runner.objects.all()
    serializer_class = RunnerSerializer

    @action(detail=True, methods=['post', 'delete'])
    def team(self, request, pk=None):
        team_id = request.data['team_id']
        team = Team.objects.get(id=team_id)
        if request.method == 'POST':
            joint_code = request.data['joint_code']
            if joint_code == team.join_code:
                runner = Runner.objects.get(id=pk)
                runner.team = team
                runner.save()
                return Response(RunnerSerializer(runner).data)
            else:
                return Http404("Wrong joint code")
        elif request.method == 'DELETE':
            runner = Runner.objects.get(id=pk)
            runner.team = None
            runner.save()
            return Response(RunnerSerializer(runner).data)

    # @action(detail=True, methods=['get', 'post'])
    # def activites(self, requests, pk=None):
    #     if resquests.method == 'GET':
    #
