import newspaper, datetime, requests, bs4, urllib3
from django.apps import apps
from django.conf import settings
from . import models

# init()에서 호출되는 함수를 bottom to top 순으로 작성

def extract_media(link, headers):
    # 일단 url을 / 기준으로 잘라서 리스트로 만들고
    domain = link.split('/')
    if len(domain) < 2:
        # 그런데 리스트 길이가 2미만이면 기사에 링크를 잘못 입력한 것이므로 예외처리
        print("   도메인 : 추출 에러. 잘못된 링크입니다.")
        if models.Media.objects.filter(domain="unknown").exists():
            # unknown 개체가 있으면 해당 내용 반환
            media = models.Media(domain=domain, media_name=media_name)
            return media
        else:
            # unknown 개체가 없으면 생성 후 반환
            media = models.Media(domain = "unknown",media_name = "Unknown")
            media.save()
            return media                    
    else:
        # 정상적으로 도메인 추출이 되었는데 이미 있는 도메인이면 
        if models.Media.objects.filter(domain=domain[2]).exists():
            print("   도메인 : 기존 DB에 등록되어 있습니다.", domain[2])
            #등록된 도메인 정보를 반환
            media = models.Media.objects.get(domain=domain[2])
            return media
        else: 
            try:                
                # 1. news paperdml build를 사용한 방식. 너무 느림.
                '''
                media_ojb = newspaper.build(f'http://{domain[2]}')
                print(media_ojb)
                media_name = media_ojb.brand                
                '''
                # 2. 그냥 html > head 의 title tag 가져오는 방식                
                request = requests.get(f"https://{domain[2]}", allow_redirects=True,timeout=5, headers=headers, verify=False)                
                # request.encoding = request.apparent_encoding 을 썼는데 오히려 인코딩 깨지는 문제가 발생해서 utf-8로
                request.encoding = 'utf-8'
                # bs4 로 html parsing해서 title 태그 내용을 media_name으로 저장
                soup = bs4.BeautifulSoup(request.text, 'html.parser')
                media_name = soup.find("head").find("title").string
            except:
                # 위의 과정 중 에러나면 그냥 domain 주소만 가지고 객체 만들어서 저장 후 반환
                media = models.Media(domain=domain[2], media_name=domain)
                print("   도메인 : brand 가져오기 실패",media)
                media.save()
                return media
            else :
                # 성공하면 해당 내용으로 객체 만들어 저장하고 반환
                media = models.Media(domain=domain[2], media_name=media_name)
                print("   도메인 : 신규 도메인입니다. /", media )
                media.save()
                return media


def extract_text(link, headers):
    # newspaper4k로 본문 가져오기
    try:
        article = newspaper.article(link, headers=headers, verify=False)
        '''
        이전 사용하던 방식
        article = newspaper.Article(link, language='ko', headers=headers, verify=False)
        article.download()
        article.parse()
        '''
    except:
        article.text = "기사 본문을 스크랩하지 못했습니다"        
    return article.text


def make_article(word,news):
    # Insecure Request 방지용
    urllib3.disable_warnings()

    # newpaper4k와 bs4에서 사용할 헤더
    headers =  {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36'        
    }
    
    # newspaper4k로 텍스트 추출
    text_str = extract_text(news['originallink'], headers)

    # Keywords 모델 오브젝트 생성
    cat_obj = models.Keywords.objects.get(keyword=word)

    # bs4로 뉴스 미디어 이름을 Media 모델 오브젝트로 저장 후 오브젝트로 가져오기
    media_obj = extract_media(news['originallink'], headers)

    # 각 내용들을 가지고 News 오브젝트 생성               
    article_obj = models.News(
        title = news.get('title'),
        description = news.get('description'),
        pubDate = convert_news_pubDate_to_date(news.get('pubDate')),
        link = news.get('originallink'),
        text = text_str,
        media = media_obj
    )

    # 오브젝트 저장
    article_obj.save()

    # 검색어 오브젝트는 다대다 관계이기 때문에 위의 오브젝트를 저장한 후에 add로 추가해줌    
    article_obj.cat.add(cat_obj)    


def handle_news_list(news_list, word):
    for news in news_list:
        if models.News.objects.filter(link=news['originallink']).exists():
            print("  이미 스크랩된 기사입니다. 검색 키워드만 추가합니다.")
            add_key = models.Keywords.objects.get(keyword=word)
            models.News.objects.get(link=news['originallink']).cat.add(add_key)
        else:
            print("  신규 기사입니다. 기사를 스크랩합니다.")
            make_article(word,news)


def convert_news_pubDate_to_date(time):
    # naive 한 date 객체 경고를 없애기 위해 tz 설정
    tz = datetime.timezone(datetime.timedelta(hours=9))
    # 네이버 뉴스의 pubDate 스트링을 datetime 객체로 변환
    converted_naive = datetime.datetime.strptime(time,'%a, %d %b %Y %H:%M:%S +0900')
    # tz 정보 교체해서 반환
    return converted_naive.replace(tzinfo=tz)


def get_news_list(word,start_time,w_day):
    sorted_news_list = []

    # 네이버 API 호출을 위한 URL에서 사용할 파라메터들. 상새는 https://developers.naver.com/docs/serviceapi/search/news/news.md#%ED%8C%8C%EB%9D%BC%EB%AF%B8%ED%84%B0 참고
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
        # 네이버 뉴스 API를 호출
        print(f' {word} 기사 검색중')
        news_request = requests.get(url, headers=headers)
    except:
        # 에러 발생시 빈 리스트를 반환
        print(f' {word} 기사 검색 에러')
        return news_list
    else:
        # API 결과를 json 으로 바꾸고
        news_list = news_request.json()["items"]

        # 월요일이면 72시간, 그외엔 48시간 내의 기사만 리스트에 추가
        for news in news_list:
            # print(news['pubDate'])
            dayDiff = (start_time - convert_news_pubDate_to_date(news['pubDate'])).days
            if w_day == 0 and dayDiff < 3:
                sorted_news_list.append(news)
            elif w_day != 0 and dayDiff < 2:            
                sorted_news_list.append(news)
            else:
                pass
    # print(sorted_news_list)
    return sorted_news_list


def get_model_column_data_to_list(modelname, column): 
    # 데이터를 가져올 모델 지정    
    target = apps.get_model('scrapper', modelname)
    # 해당 모델의 지정 컬럼의 모든 데이터를 list로 변환하여 반환
    # 재사용 가능하게 만들어놓긴 했지만 Keywords 모델 외에는 사용하지 않는 것이 좋을듯
    return list(target.objects.all().values_list(column, flat=True))

def convert_date_to_string(time):
    # date 객체를 2026-07-23 09:30:22 형태의 스트링으로 변환
    return time.strftime('%Y-%m-%d %H:%M:%S')

def load_news(start_time,w_day):
    scrapped_news = []
    # 가져올 기사 범위. 월요일이면 3일분 그 외는 2일분
    news_pubDate_range = 3 if w_day == 0 else 2    
    end_time = datetime.timedelta(days=news_pubDate_range)    
    try:
        # 지정한 범위의 기사를 pubdate 기준으로 정렬하여 가져오기        
        picked_news = models.News.objects.filter(pubDate__range=(start_time - end_time,start_time)).order_by('-pubDate')
    except:        
        # 기사가 없어서 order 에러가 나는 경우
        nothing_new = {
            'title': '검색된 기사가 없습니다.',
            'description': '다음 내용을 확인하여 주십시오.',
            'text': '1. 설정된 검색어가 너무 적은 경우 실제로 관련 기사가 없을 수 있습니다. 뉴스 포탈사이트에서 지난 2~3일간의 기사를 직접 검색해 보십시오. 2. 해당 키워드로 기사가 검색되는 경우, django의 로그를 확인하여 주십시오.',
            'pubDate': convert_date_to_string(start_time),
            'cat': '기타',
            'link': 'https://pipboy.mooo.com/git/dinner_rolls/NSProject',
            'media': '시스템 메세지'
            }
        scrapped_news.append(nothing_new)
    else:
    # 가져온 기사를 json 반환하기 위해 value를 모두 string으로 변환        
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
            # 변환한 객체를 scrapped_news에 추가
            scrapped_news.append(strValue_news)             
    return scrapped_news


def get_time_day():
    # naive 한 date 객체 경고를 없애기 위해 tz 설정
    tz = datetime.timezone(datetime.timedelta(hours=9))
    
    # 스크랩 시작 시간 저장
    start_time = datetime.datetime.now(tz=tz)    

    # 오늘의 요일 저장
    w_day = start_time.weekday()
    return start_time, w_day  


def init():
    # 스크랩 시작 시간, 요일 구분
    start_time, w_day = get_time_day()
    is_today_scrapped = models.News.objects.filter(pubDate__date=datetime.date.today()).count()
    
    # 오늘 스크랩한적이 없으면
    if is_today_scrapped == 0 :
        print("최신 기사를 스크랩합니다.")
        
        # 검색어를 list로 가져오기
        keywords = get_model_column_data_to_list('Keywords', 'keyword') 
        
        # 각 검색에 대해
        for word in keywords:
            # 네이버 뉴스 api 로 기사를 검색하고
            news_list = get_news_list(word,start_time,w_day)

            if len(news_list) == 0:
                print(f'{word}로 검색된 뉴스가 없습니다.')
                pass
            else : 
                # 중복 기사를 제거하고 기사 본문을 스크랩해 DB에 저장
                handle_news_list(news_list, word)            
        
        # DB에서 저장된 뉴스를 json 형식으로 로드하여 반환
        scrapped_news = load_news(start_time, w_day)                   
        return scrapped_news
    else: 
        print("DB에서 기사를 불러옵니다")
        scrapped_news = load_news(start_time, w_day)
        return scrapped_news
        
        
        
    