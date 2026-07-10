from django.db import models

# Create your models here.
class Media(models.Model):
    media_name = models.CharField(max_length=200)
    domain = models.CharField(unique=True)

    def display_url(self):
        return f"{self.media_name} : {self.domain}"
    
    def __str__(self):
        return self.display_url()
    
    class Meta:
        verbose_name_plural = "Media"


class Keywords(models.Model):
    keyword = models.CharField(max_length=100)
    
    def __str__(self):
        return self.keyword
    
    class Meta:
        verbose_name_plural = "Keywords"


class News(models.Model):
    title = models.CharField(max_length=300)
    description = models.TextField()
    text = models.TextField()
    pubDate = models.DateTimeField()
    cat = models.ManyToManyField(Keywords, related_name="category")
    link = models.URLField()     
    media = models.ForeignKey(Media, default="unknown", on_delete=models.SET_DEFAULT)
    
    def __str__(self):
        return f"{self.title}"
    
    class Meta:
        verbose_name_plural = "News"
