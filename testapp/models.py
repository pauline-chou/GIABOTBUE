from django.db import models
from django.utils import timezone
# Create your models here.

class User_Info(models.Model):
    user_id = models.CharField(max_length=50)
    place_type = models.CharField(max_length=50, null=True, blank=True) 
    latitude = models.CharField(max_length=255, blank=True, null=True, default='')
    longitude = models.CharField(max_length=255, blank=True, null=True, default='')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user_id


# UserPlaceMapping 資料表
class UserPlaceMapping(models.Model):
    user_id = models.CharField(max_length=50)
    place_1 = models.CharField(max_length=255, blank=True, null=True, default='')
    place_2 = models.CharField(max_length=255, blank=True, null=True, default='')
    place_3 = models.CharField(max_length=255, blank=True, null=True, default='')
    place_4 = models.CharField(max_length=255, blank=True, null=True, default='')
    place_5 = models.CharField(max_length=255, blank=True, null=True, default='')

    def __str__(self):
        return f"{self.user_id} - {self.place_1}, {self.place_2}, {self.place_3}, {self.place_4}, {self.place_5}"

class RestaurantsName(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True, default='')
    url = models.CharField(max_length=255, blank=True, null=True, default='')
    
    def __str__(self):
        return self.name
