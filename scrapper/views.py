from django.shortcuts import render
from django.http import JsonResponse
from . import scrap
from . import models
# Create your views here.

def index(request):
    if models.News.objects.all().count() == 0:
        latest = {"latest": "none"}
    else: 
        latest = {"latest": scrap.convert_date_to_string(models.News.objects.all().order_by('-pubDate')[0].pubDate)}
    return render(request, 'scrapper/index.html', latest)

def get_data(reqeust):
    articles = {'article': scrap.init()}
    return JsonResponse(articles)