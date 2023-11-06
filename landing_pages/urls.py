from django.urls import path
# from django.views.generic import TemplateView
from .views import LandingPageView


urlpatterns = [
    path('ielts-writing-task-2-ai-scorer/', LandingPageView.as_view()),
]