from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ArticleViewSet, ScheduleView, SeriesViewSet, VideoViewSet, health

router = DefaultRouter()
router.register("series", SeriesViewSet, basename="series")
router.register("videos", VideoViewSet, basename="video")
router.register("articles", ArticleViewSet, basename="article")

urlpatterns = [
    path("schedule/", ScheduleView.as_view(), name="schedule"),
    path("health/", health, name="health"),
    *router.urls,
]
