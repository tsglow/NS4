from django.shortcuts import render
from django.http import JsonResponse
from . import scrap
from . import models
# Create your views here.

def index(request):        
    return render(request, 'scrapper/index.html', {'articles': scrap.load_news()})

def scrap_news(reqeust):    
    articles = {         
        'article': scrap.init_manual()        
    }
    return JsonResponse(articles)