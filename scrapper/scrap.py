import logging,newspaper, datetime, requests, bs4, urllib3
from django.apps import apps
from django.conf import settings
from . import models
# bottom to top 순으로 init_auto()에서 호출되는 함수를 나열
# 메서드 호출시 출처 가시성을 위해 되도록 상위 객체로 import함

logger = logging.getLogger(__name__)


# date 객체를 form에 입력한 형식의 스트링으로 변환
def convert_date_to_string(time, form):    
    return time.strftime(form)

# news는 Model 오브젝트기 때문에 컨텍스트로 넘기려면 string으로 변환해줘야 함
def news_to_string(news):    
    string_news = {
        'title': news.title,
        'description': news.description,
        'text': news.text,
        'pubDate': convert_date_to_string(news.pubDate, '%Y-%m-%d %H:%M:%S'),        
        'cat': ', '.join(news.cat.all().values_list('keyword', flat=True)),
        'link': news.link,
        'media': news.media.media_name
        }    
    return string_news


# 리스트에 있는 것을 get 메서드로 지정한 테이블, 컬럼에서 검색해 가져옴
def get_model_obj_from_list(list, appname,modelname, column):     
    result_list=[]
    target = apps.get_model(appname, modelname)
    for item in list:
        try:
            obj = target.objects.get(**{column: item})
            result_list.append(obj)
        except:
            pass
    return result_list

# 가독성을 위해 별도 함수로 분리
def add_search_conditions(dict,filter,tuple):
    dict[filter] = tuple


# 기사 검색용 함수
def search_news_from_db(starttime, endtime, category=[], order=['-pubDate'], field="title", word=""):
    # 검색 조건 딕셔너리 선언
    conditions = {}

    # 검색 기간. 입력된 기간이 string이면 datetime 객체로 변환하고, start_time 이 end_time보다 최근이면 역으로 전환 후 검색 조건에 추가    
    start_time = convert_string_to_date(starttime, '%Y-%m-%dT%H:%M')
    end_time = convert_string_to_date(endtime, '%Y-%m-%dT%H:%M')    
    #start_time = convert_string_to_date(starttime, '%Y-%m-%d %H:%M:%S')
    #end_time = convert_string_to_date(endtime, '%Y-%m-%d %H:%M:%S')
    if (start_time - end_time) > datetime.timedelta(0):
        start_time, end_time = end_time, start_time
    add_search_conditions(conditions,"pubDate__range", (start_time, end_time))
    # conditions['pubDate__range'] = (start_time, end_time)    

    # News 모델의 Cat 컬럼은 manytomany이므로 오브젝트를 실제로 불러와서 비교해야함    
    print(category, len(category))
    
    if len(category) == 0:
        # 카테고리를 선택하지 않았으면 pass
        pass
    else:
        # 카테고리를 선택했으면 조건에 추가
        category_obj = get_model_obj_from_list(category,'scrapper',"Keywords", "keyword")
        add_search_conditions(conditions,"cat__in",(category_obj))
        # conditions['cat__in'] = category_obj
        
    # 단어 포함여부 조건
    if not word == "":
        add_search_conditions(conditions,f'{field}__contains',(word))
        # conditions[f'{field}__contains'] = word
    
    # News에서 지정한 기간과 검색어가 포함된 뉴스를 검색해서 역정렬#    
    try :
        logger.info(f'search_news_from_db() - search conditions are: {conditions} ')
        search_result = models.News.objects.filter(**conditions).distinct().order_by(*order)
    except:
        logger.critical(f'search_news_from_db() - failed to query from DB. check condtions and connections')
        search_result = []
    return search_result


# 함수명칭을 좀 바꿔야 할 듯. get news json?
def get_news(queryset):     
    news_list = []
    # 가져올 기사 범위. 월요일이면 3일분 그 외는 2일분
        # 가져온 기사를 json 반환하기 위해 value를 모두 string으로 변환
    try:
        for news in queryset:           
            string_news = news_to_string(news)
            # 변환한 객체를 scrapped_news에 추가
            news_list.append(string_news)
    except:
        pass
    
    # 검색된 기사가 없을 경우
    if len(news_list) == 0:
        logger.warning(f'get_news() - there was no article in DB. check settings and logs')
        nothing_new = {
            'title': '검색된 기사가 없습니다.',
            'description': '다음 내용을 확인하여 주십시오.',
            'text': '1. 설정된 검색어가 너무 적은 경우 실제로 관련 기사가 없을 수 있습니다. 뉴스 포탈사이트에서 지난 2~3일간의 기사를 직접 검색해 보십시오. 2. 해당 키워드로 기사가 검색되는 경우, django의 로그를 확인하여 주십시오.',
            'pubDate': convert_date_to_string(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S'),
            'cat': '기타',
            'link': 'https://pipboy.mooo.com/git/dinner_rolls/NSProject',
            'media': '시스템 메세지'
            }
        news_list.append(nothing_new)      
    return news_list


# 스트링을 form 에 지정한 형식의 datetime 객체로 변환
def convert_string_to_date(string, form):    
    # naive 한 date 객체 경고를 없애기 위해 tz 설정
    tz = datetime.timezone(datetime.timedelta(hours=9))
    # 네이버 뉴스의 pubDate 스트링을 datetime 객체로 변환
    if type(string) == str :
        converted_naive = datetime.datetime.strptime(string,form)        
    else :
        converted_naive = string
    # tz 정보 교체해서 반환
    return converted_naive.replace(tzinfo=tz)


# 도메인을 사용해 언론사 이름 추출
def extract_media(link, headers):
    # 일단 url을 / 기준으로 잘라서 리스트로 만들고
    domain = link.split('/')
    if len(domain) < 2:
        # 그런데 리스트 길이가 2미만이면 기사에 링크를 잘못 입력한 것이므로 예외처리
        logger.warning(f'extract_media() - failed to extract domain. maybe wrong link : {link}')
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
            # 신규 도메인이면 
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
                logger.warning(f'extract_media() - failed to get media name from {domain[2]}')
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


# newspaper4k로 뉴스 본문 추출
def extract_text(link, headers):    
    try:
        article = newspaper.article(link, headers=headers, verify=False)
        text = article.text
        '''
        newspaper3k에서 사용하던 방식
        article = newspaper.Article(link, language='ko', headers=headers, verify=False)
        article.download()
        article.parse()
        '''
    except:
        text = ""    
    
    if len(text) < 10:
        logger.critical(f'extract_text() - newspaper4k failed to get article from {link}')
        text = "기사 본문을 스크랩하지 못했습니다"        
    return text


# 뉴스를 News 모델 객체로 만들어 DB에 저장
def make_article(word,news):
    logger.info("make_article() - saving an article")       
    # Insecure Request 방지용
    urllib3.disable_warnings()

    # newpaper4k와 bs4에서 공용으로 사용할 헤더
    headers =  {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36'        
    }
    
    # newspaper4k로 텍스트 추출
    text_str = extract_text(news['originallink'], headers)

    # Keywords 모델 오브젝트 생성
    cat_obj = models.Keywords.objects.get(keyword=word)

    # bs4로 뉴스 미디어 이름을 Media 모델 오브젝트로 저장 후 오브젝트로 가져오기
    media_obj = extract_media(news['originallink'], headers)

    # 각 내용들을 가지고 News 모델 객체 생성               
    article_obj = models.News(
        title = news.get('title'),
        description = news.get('description'),
        pubDate = convert_string_to_date(news.get('pubDate'),'%a, %d %b %Y %H:%M:%S +0900'),
        link = news.get('originallink'),
        text = text_str,
        media = media_obj
    )

    # 객체 저장
    article_obj.save()

    # 검색어 오브젝트는 다대다 관계이기 때문에 위의 오브젝트를 저장한 후에 add로 추가해야 함 
    article_obj.cat.add(cat_obj)   


# 중복기사와 신규기사 처리
def handle_news_list(news_list, word):
    logger.info("handle_news_list() - handling news list...")   
    for news in news_list:
        if models.News.objects.filter(link=news['originallink']).exists():
            print("  이미 스크랩된 기사입니다. 검색 키워드만 추가합니다.")
            add_key = models.Keywords.objects.get(keyword=word)
            models.News.objects.get(link=news['originallink']).cat.add(add_key)
        else:
            print("  신규 기사입니다. 기사를 스크랩합니다.")
            make_article(word,news)


# 뉴스 API로 기사 검색
def get_news_list(word,start_time,w_day):    
    sorted_news_list = []

    # API 호출용 파라메터. 상세는 https://api.ncloud-docs.com/docs/naver-api-hub-search-news 참고
    na_id = settings.NA_ID
    na_psd = settings.NA_PWD
    encode_type = 'json'        
    max_display = 10
    sort = 'sim'
    start = 1    
    url = f' https://naverapihub.apigw.ntruss.com/search/v1/news?query={word}&display={max_display}&start={start}&sort={sort}&format={encode_type}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
        'X-NCP-APIGW-API-KEY-ID': na_id,
        'X-NCP-APIGW-API-KEY': na_psd 
        }    
    '''
    네이버 구 API 용 url, 헤더
    상세는 https://developers.naver.com/docs/serviceapi/search/news/news.md#%ED%8C%8C%EB%9D%BC%EB%AF%B8%ED%84%B0 참고
    url = f'https://openapi.naver.com/v1/search/news.{encode_type}?query="{word}"&display={str(int(max_display))}&start={str(int(start))}&sort={sort}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
        'X-Naver-Client-Id': na_id,
        'X-Naver-Client-Secret': na_psd 
        }    
    '''    
     
    try:
        # API에 request
        print(f' {word} 기사 검색중')
        news_request = requests.get(url, headers=headers)
    except:
        # 에러 발생시 빈 리스트를 반환
        logger.error(f'get_newslist() - {word} 기사 검색 에러')
        print(f' {word} 기사 검색 에러')
        return news_list
    else:
        # API 결과를 json 으로 바꾸고 실제 뉴스는 items 내부에 있으므로 해당 내용만 가져옴
        news_list = news_request.json()["items"]

        # 월요일이면 72시간, 그외엔 48시간 내의 기사만 리스트에 추가
        for news in news_list:
            # print(news['pubDate'])
            dayDiff = (start_time - convert_string_to_date(news['pubDate'],'%a, %d %b %Y %H:%M:%S +0900')).days
            if w_day == 0 and dayDiff < 3:
                sorted_news_list.append(news)
            elif w_day != 0 and dayDiff < 2:            
                sorted_news_list.append(news)
            else:
                pass
    # print(sorted_news_list)
    return sorted_news_list


# 지정한 앱의 지정한 모델의 지정한 컬럼의 모든 데이터를 list로 변환하여 반환. # 재사용 가능하게 만들어놓긴 했지만 Keywords 모델 외에는 사용하지 않는 것이 좋을듯
def get_model_column_data_to_list(appname,modelname, column):     
    target = apps.get_model(appname, modelname)    
    return list(target.objects.all().values_list(column, flat=True))


# 기사 스크랩 시동 함수
def scrap_now(start_time, w_day):     
    # Keyword를 DB에서 불러와 list로 저장
    keywords = get_model_column_data_to_list('scrapper', 'Keywords', 'keyword')    
        
    # 각 검색에 대해
    for word in keywords:
        # 네이버 뉴스 api 로 기사를 검색하고
        news_list = get_news_list(word,start_time,w_day)

        # 검색된 기사가 없으면 스킵
        if len(news_list) == 0:
            logger.warning(f'scrap_now() - there was no artcle for {word}')
            print(f'{word}로 검색된 뉴스가 없습니다.')
            pass
        else : 
            # 기사가 검색되면 중복 기사를 제거하고 기사 본문을 스크랩해 DB에 저장
            handle_news_list(news_list, word)


# init 실행시의 시간과 요일을 반환
def get_time_day():
    # naive 한 date 객체 경고를 없애기 위해 tz 설정
    tz = datetime.timezone(datetime.timedelta(hours=9))
    
    # 스크랩 시작 시간 저장
    start_time = datetime.datetime.now(tz=tz)    

    # 오늘의 요일 저장
    w_day = start_time.weekday()
    return start_time, w_day  


# 사용자가 기사 검색 버튼을 누르는 경우
def init_manual():
    logger.info("init_manual() - scraaping started by manual action")
    start_time, w_day = get_time_day()
    # 스크랩하고
    scrap_now(start_time, w_day)
    # load_news 호출해서 결과 리턴
    news_pubDate_range = 3 if w_day == 0 else 2    
    end_time = start_time - datetime.timedelta(days=news_pubDate_range)
    picked_news = search_news_from_db(start_time, end_time, order=['-pubDate'])
    return get_news(picked_news)


# 스캐줄러에 의해 작동할 경우
def init_auto():
    # 스크랩 시작 시간, 요일 구분
    logger.info("init_auto() - scrapping started by cron job")
    start_time, w_day = get_time_day()    
    scrap_now(start_time, w_day)