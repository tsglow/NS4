import newspaper, datetime, requests
from django.apps import apps
from django.conf import settings
from . import models

def get_model_data(modelname): 
    target = apps.get_model('scrapper', modelname)
    return list(target.objects.all().values_list('keyword', flat=True))


def get_time_day():
    start_time = datetime.datetime.now()    
    w_day = start_time.weekday()
    return start_time, w_day  

def convert_date_to_string(time):
    return time.strftime('%Y-%m-%d %H:%M:%S')

def convert_news_pubDate_to_date(time):
    return datetime.datetime.strptime(time,'%a, %d %b %Y %H:%M:%S +0900')

def get_news(word,start_time,w_day):
    sorted_news_list = []
    na_id = settings.NA_ID
    na_psd = settings.NA_PWD
    encode_type = 'json'
    max_display = 10
    sort = 'sim'
    start = 1
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
        'X-Naver-Client-Id': na_id,
        'X-Naver-Client-Secret': na_psd 
        }
    '''
    old header
    header = {'User-Agent':
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36',
    'X-Naver-Client-Id': na_id,
    'X-Naver-Client-Secret': na_psd}
    '''
    url = f'https://openapi.naver.com/v1/search/news.{encode_type}?query="{word}"&display={str(int(max_display))}&start={str(int(start))}&sort={sort}'
    
    try:
        print(f'{word} 기사 검색중')
        news_request = requests.get(url, headers=header)
    except:
        print(f'{word} 기사 검색 에러')
        return news_list
    else:
        news_list = news_request.json()["items"]
        for news in news_list:
            # print(news['pubDate'])
            dayDiff = (start_time - convert_news_pubDate_to_date(news['pubDate'])).days
            if w_day == 0 and dayDiff < 3:
                sorted_news_list.append(news)
            elif w_day != 0 and dayDiff <= 1:            
                sorted_news_list.append(news)
            else:
                pass
    # print(sorted_news_list)
    return sorted_news_list
            

def scrap_news(word,news):
    return ""




def init():
    keywords =  get_model_data('Keywords')   
    start_time, w_day = get_time_day()
    for word in keywords:
        news_list = get_news(word,start_time,w_day)
        if len(news_list) < 1:
            print(f"{word}로 검색된 기사가 없습니다")
            pass
        else:
            for news in news_list:
                if models.News.objects.filter(link=news['originallink']).exists():
                    print("중복 기사입니다. 키워드만 추가합니다.")
                    add_key = models.Keywords.objects.get(keyword=word)
                    models.News.objects.get(link=news['originallink']).cat.add(add_key)
                else:
                    print("신규 기사입니다. 기사를 스크랩합니다.")
                    scrap_news(word,news)


