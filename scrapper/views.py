from django.shortcuts import render
from django.http import JsonResponse
import datetime
from . import scrap, models, forms
# Create your views here.

def index(request):
    start_time, w_day = scrap.get_time_day()   
    news_pubDate_range = 3 if w_day == 0 else 2    
    end_time = start_time - datetime.timedelta(days=news_pubDate_range)
    picked_news = scrap.search_news_from_db(start_time, end_time, order=['-pubDate'])

    form = forms.SearchForm
    return render(request, 'scrapper/index.html', {'articles': scrap.get_news(picked_news),'searchform':form})


def scrap_news(reqeust):    
    articles = {'article': scrap.init_manual()}
    return JsonResponse(articles)


def search_news(request):
    start_time = request.GET['start_time']
    end_time = request.GET['end_time']
    cat = request.GET['cat']
    order = request.GET['order']    
    field = request.GET['field']
    word = request.GET['word']     
    result = scrap.search_news_from_db(start_time, end_time, [cat], [order], field, word)    
    result_json = {'article': scrap.get_news(result)}
    return JsonResponse(result_json)