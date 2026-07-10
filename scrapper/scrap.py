import newspaper, datetime, requests, bs4, urllib3
from django.apps import apps
from django.conf import settings
from . import models


def extract_media(link, headers):
    domain = link.split('/')
    if len(domain) < 2:
        print("   도메인 : 추출 에러. 잘못된 링크입니다.")
        domain = "http://unknown"
        media_name = "Unknown"        
        media = models.Media(domain=domain, media_name=media_name)
        return media
    else:
        if models.Media.objects.filter(domain=domain[2]).exists():
            print("   도메인 : 기존 DB에 등록되어 있습니다.")
            return models.Media.objects.filter(domain=domain)
        else: 
            try:                
                # 1. news paperdml build를 사용한 방식. 너무 느림.
                '''
                media_ojb = newspaper.build(f'http://{domain[2]}')
                print(media_ojb)
                media_name = media_ojb.brand                
                '''
                # 2. 그냥 타이틀 tag 가져오는 방식                
                request = requests.get(f"https://{domain[2]}", allow_redirects=True,timeout=5, headers=headers, verify=False)                
                # request.encoding = request.apparent_encoding 오히려 에러가 발생
                request.encoding = 'utf-8'
                soup = bs4.BeautifulSoup(request.text, 'html.parser')
                media_name = soup.find("head").find("title").string
            except:
                media = models.Media(domain=domain[2], media_name=domain)
                print("   도메인 : brand 가져오기 실패",media)
                return media
            else :                
                media = models.Media(domain=domain[2], media_name=media_name)
                print("   도메인 : 신규 도메인입니다. /", media )
                return media

def extract_text(link, headers):
    try:
        article = newspaper.article(link, headers=headers, verify=False)    
    except:
        article.text = "기사 본문을 스크랩하지 못했습니다"        
    return article.text


def make_article(word,news):
    urllib3.disable_warnings()    
    headers =  {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36'        
    }
    text_str = extract_text(news['originallink'], headers)
    cat_obj = models.Keywords.objects.get(keyword=word)
    media_obj = extract_media(news['originallink'], headers)
               
    article_obj = models.News(
        title = news.get('title'),
        description = news.get('description'),
        pubDate = convert_news_pubDate_to_date(news.get('pubDate')),
        link = news.get('originallink'),
        text = text_str,
        media = media_obj
    )
    media_obj.save()
    article_obj.save()
    article_obj.cat.add(cat_obj)    


def handle_news_list(news_list, word):
    if len(news_list) < 1:
        print(f"{word}로 검색된 기사가 없습니다")
        pass
    else:
        for news in news_list:
            if models.News.objects.filter(link=news['originallink']).exists():
                print("  중복 기사입니다. 키워드만 추가합니다.")
                add_key = models.Keywords.objects.get(keyword=word)
                models.News.objects.get(link=news['originallink']).cat.add(add_key)
            else:
                print("  신규 기사입니다. 기사를 스크랩합니다.")
                make_article(word,news)


def convert_news_pubDate_to_date(time):
    tz = datetime.timezone(datetime.timedelta(hours=9))
    converted_naive = datetime.datetime.strptime(time,'%a, %d %b %Y %H:%M:%S +0900')
    return converted_naive.replace(tzinfo=tz)


def get_news_list(word,start_time,w_day):
    sorted_news_list = []
    na_id = settings.NA_ID
    na_psd = settings.NA_PWD
    encode_type = 'json'
    max_display = 10
    sort = 'sim'
    start = 1
    url = f'https://openapi.naver.com/v1/search/news.{encode_type}?query="{word}"&display={str(int(max_display))}&start={str(int(start))}&sort={sort}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
        'X-Naver-Client-Id': na_id,
        'X-Naver-Client-Secret': na_psd 
        }    
    # 이전에 사용하던 헤더
    '''    
    headers = {'User-Agent':
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36',
    'X-Naver-Client-Id': na_id,
    'X-Naver-Client-Secret': na_psd}
    '''    
    try:
        print(f' {word} 기사 검색중')
        news_request = requests.get(url, headers=headers)
    except:
        print(f' {word} 기사 검색 에러')
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


def get_model_data(modelname): 
    target = apps.get_model('scrapper', modelname)
    return list(target.objects.all().values_list('keyword', flat=True))

def convert_date_to_string(time):
    return time.strftime('%Y-%m-%d %H:%M:%S')

def load_news(start_time,w_day):
    scrappped_news = []
    news_pubDate_range = 3 if w_day == 0 else 2
    end_time = datetime.timedelta(days=news_pubDate_range)
    picked_news = models.News.objects.filter(pubDate__range=(start_time - end_time,start_time)).order_by('-pubDate')
    for news in picked_news:
        strValue_news = {
            'title': news.title,
            'description': news.description,
            'text': news.text,
            'pubDate': convert_date_to_string(news.pubDate),
            'cat': ', '.join(news.cat.all().values_list('keyword', flat=True)),
            'link': news.link,
            'media': news.media.media_name
        }
        scrappped_news.append(strValue_news)
    return scrappped_news


def get_time_day():
    tz = datetime.timezone(datetime.timedelta(hours=9))
    start_time = datetime.datetime.now(tz=tz)    
    w_day = start_time.weekday()
    return start_time, w_day  


def init():
    start_time, w_day = get_time_day()
    is_today_scrapped = models.News.objects.filter(pubDate__date=datetime.date.today()).count()
    
    if is_today_scrapped > 0 :
        print("DB에서 기사를 불러옵니다")       
        scrapped_news = load_news(start_time, w_day)
        return scrapped_news
    else: 
        print("DB에 기사가 없습니다. 스크랩을 시작합니다.")
        keywords =  get_model_data('Keywords') 
        for word in keywords:
            news_list = get_news_list(word,start_time,w_day)
            handle_news_list(news_list, word)
        scrapped_news = load_news(start_time, w_day)
        return scrapped_news
        
        
    