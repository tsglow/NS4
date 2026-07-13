from django.shortcuts import render
from django.http import JsonResponse
from . import scrap
from . import models
# Create your views here.

def index(request):    
    articles = {             
        'article': scrap.load_news(),        
    }
    return render(request, 'scrapper/index.html', articles)

def scrap_news(reqeust):
    # 이 함수는 일단 index가 로딩된 후에 수동으로만 실행되니까 latest count 체크는 필요 없음
    articles = { 
        # 단 기사가 스크랩 된 후에 latest를 검색하게 해야함
        'article': scrap.init_manual()        
    }
    return JsonResponse(articles)