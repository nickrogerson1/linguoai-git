from django.urls import path
from .views import Homepage
from django.views.generic import TemplateView


urlpatterns = [
    path('', Homepage.as_view()),
    path('hangman/', TemplateView.as_view(template_name="home/hangman.html"), name='hangman'),
    path('word-game/', TemplateView.as_view(template_name="home/word-game.html"), name='word-game'),
]