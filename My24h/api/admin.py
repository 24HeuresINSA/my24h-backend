from django.contrib import admin
from .models import Category, Race, Athlete, Activity, Team, Discipline, RaceDiscipline


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Race)
class RaceAdmin(admin.ModelAdmin):
    pass


@admin.register(Athlete)
class AthleteAdmin(admin.ModelAdmin):
    pass


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    pass


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    pass


@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    pass


@admin.register(RaceDiscipline)
class RaceDisciplineAdmin(admin.ModelAdmin):
    pass
