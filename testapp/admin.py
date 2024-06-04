from django.contrib import admin

# Register your models here.

from .models import User_Info, UserPlaceMapping, RestaurantsName

# User_Info 管理
class User_Info_Admin(admin.ModelAdmin):
    list_display = ('user_id', 'place_type', 'latitude', 'longitude', 'created_at', 'updated_at')

# UserPlaceMapping 管理
class UserPlaceMapping_Admin(admin.ModelAdmin):
    list_display = ('user_id', 'place_1', 'place_2', 'place_3', 'place_4', 'place_5')

#菜單
class RestaurantsName_Admin(admin.ModelAdmin):
    list_display = ('name', 'url')

# 註冊模型到管理界面
admin.site.register(User_Info, User_Info_Admin)
admin.site.register(UserPlaceMapping, UserPlaceMapping_Admin)
admin.site.register(RestaurantsName, RestaurantsName_Admin)