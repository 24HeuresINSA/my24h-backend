from django.urls import include, path
from rest_framework import routers
from django.contrib.auth import views as auth_views
from . import views


router = routers.DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename="Categories")
router.register(r'athletes', views.AthleteViewSet, basename="Racers")
router.register(r'races', views.RaceViewSet, basename="Races")
router.register(r'teams', views.TeamViewSet, basename="Teams")


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('token/', views.access_token, name="token"),
    path('token/refresh/', views.refresh_tocken, name="refresh token"),
    path('reset_password', auth_views.PasswordResetView.as_view()),
    path('rest_password/done', auth_views.PasswordResetDoneView.as_view()),
    path('password/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view()),
    path('password/done/', auth_views.PasswordResetCompleteView.as_view())
]
