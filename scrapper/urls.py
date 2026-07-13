from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="index"), 
    path('scrap-news/', views.scrap_news, name="scrap-news")
]
