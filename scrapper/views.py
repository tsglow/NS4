from django.shortcuts import render
from django.http import JsonResponse
from scrapper.scrap import init
# Create your views here.

def index(request):
    return render(request, 'scrapper/index.html')

def get_data(reqeust):
    articles = {'article': init()}
    return JsonResponse(articles)