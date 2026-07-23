from django import forms
from . import models
from . import scrap



class SearchForm(forms.Form):
    
    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local'}
        ),
        label="시작 일시"
    )

    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local'}
        ),
        label="종료 일시"
    )

    cat_options = [(item,item) for item in scrap.get_model_column_data_to_list("scrapper","Keywords","keyword")]
    cat_options.insert(0,('All','전체'))
    cat = forms.ChoiceField(choices=cat_options, label="뉴스 카테고리")

    
    field_options = [        
        ('title', '제목'),
        ('description', '기사 요약'),
        ('text', '기사 본문'),
    ]
    field = forms.ChoiceField(choices=field_options, label="검색 위치")


    order_options = [        
        ('-pubDate','최신 기사부터'),
        ('pubDate','오래된 기사부터')
    ]
    order = forms.ChoiceField(choices=order_options, label="정렬 순서")

    
    word = forms.CharField(label="검색어", max_length=100, required=False)


    