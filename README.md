# Newsscrapper

- 프레임워크 : django 5.2

- DB: postgres 18

- 뉴스 검색 API : 네이버news api

- 뉴스 스크래이핑 모듈 : newspaper4k



# 사용법

0. 사전 준비 사항

네이버 뉴스 API를 사용해 기사를 검색하므로 해당 API ID / PW가 필요하다. https://developers.naver.com/docs/serviceapi/search/news/news.md 를 참고하여 ID / PW를 발급한다.


python3 버전이 3.12 미만이라면 업데이트한다.


1. git과 docker 설치(Rockylinux 10 기준)

sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

sudo dnf -y install docker-ce docker-ce-cli containerd.io docker-compose-plugin git

sudo usermod -aG docker <로그인 계정명>

sudo systemctl enable docker

git config --global user.name "<원하는 유저명>"

git config --global user.email "<원하는 이메일>"

이후 os 재시작



2. venv 생성 및 리파지토리 클론, 의존성 패키지 설치

mkdir <원하는 폴더명>

cd <생성한 폴더경로>

python3 -m venv <원하는 가상환경 폴더명>

git clone https://pipboy.mooo.com/git/dinner_rolls/NS4.git

source <생성한가상환경 폴더명>/bin/activate

venv> cd ns4

venv> pip install -r requirements.txt



3. DB 설치

compose.yaml을 djanogo 프로젝트와는 별도의 폴더를 만들어 이동

해당 경로로 이동하여 mkdir secrets

db_password.txt, db_user.txt 파일 생성 후 내용 작성

docker compose up

4432 포트가 리슨상태인지 확인



4. django env, secret 설정 

.env_sample 을 .env로 리네이밍 후 해당 파일을 열어 필요한 값 입력

secrets_sample.json 을 secrets.json으로 리네이밍 후 해당 파일을 열어 필요한 값 입력



5. migration 및 기동

ns4 프로젝트 폴더로 이동 후 마이그레이션 진행

venv> python3 manage.py makemigrations

venv> python3 manage.py migrate

슈퍼 유저 생성

venv> python3 manage.py createsuperuser

서비스 기동

venv> python3 manage.py runserver 0.0.0.0:<원하는 포트>

웹브라우저에서 admin 페이지 접속

http://127.0.0.1:<지정한포트>/admin

Keywords 모델을 클릭하여 검색할 키워드 등록

http://127.0.0.1:<지정한포트>/scrapper 로 접속하면 기사 수집 후 결과가 출력된다.
