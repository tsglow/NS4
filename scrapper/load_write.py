import os, csv
from django.conf import settings
from . import models

csv_path = os.path.join(settings.DATA_DIR, 'scrapper')

def load_csv_to_list(args):        
    list = []
    csv_file = open(f'{csv_path}/{args}.csv')
    csv_data = csv.DictReader(csv_file)
    for row in csv_data:
        list.append(row)
    csv_file.close()
    return list

def write_media_from_list():
    list = load_csv_to_list('media')
    for media in list:
        media_obj = models.Media(
            domain = media['domain'],
            media_name = media['media_name']
        )
        if models.Media.objects.filter(domain=media['domain']).exists():
            pass
        else:
            media_obj.save()
    