from django.urls import include, path
from rest_framework import routers
from django.contrib.auth import views as auth_views
from . import views


router = routers.DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename="Categories")
router.register(r'racers', views.RacerViewSet, basename="Racers")
router.register(r'races', views.RaceViewSet, basename="Races")
router.register(r'teams', views.TeamViewSet, basename="Teams")


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/token', views.TokenObtainPairView.as_view(), name="token"),
    path('api/token/refresh', views.TokenObtainPairView.as_view(), name="refresh token"),
    path('api/reset_password', auth_views.PasswordResetView.as_view()),
    path('api/rest_password/done', auth_views.PasswordResetDoneView.as_view()),
    path('api/password/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view()),
    path('api/password/done/', auth_views.PasswordResetCompleteView.as_view())
]