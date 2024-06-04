from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, LocationMessage, TextSendMessage, TemplateSendMessage, ConfirmTemplate, MessageAction, CarouselTemplate, CarouselColumn, URITemplateAction
import requests
from requests.exceptions import RequestException
from .models import User_Info, UserPlaceMapping, RestaurantsName, RestaurantsName



line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)
google_places_api_key = settings.GOOGLE_PLACES_API_KEY

@csrf_exempt
def callback(request):
    if request.method == 'POST':
        signature = request.META.get('HTTP_X_LINE_SIGNATURE', '')
        body = request.body.decode('utf-8')
        
        try:
            events = parser.parse(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()
        
        for event in events:
            if isinstance(event, MessageEvent):
                if isinstance(event.message, TextMessage):
                    mtext = event.message.text
                    if mtext == 'eat nearby':
                        sendConfirmTemplate(event)
                    elif mtext in ['restaurant', 'cafe']:
                        record_user_reply(event)
                    elif mtext == 'Search More Restaurants':
                        sendCarousel_2(event)

                        

                   
                elif isinstance(event.message, LocationMessage):
                    # 紀錄使用者位置資訊
                    record_user_location(event.source.user_id, event.message.latitude, event.message.longitude)
                    # 從資料庫取得使用者資訊
                    user_info = User_Info.objects.filter(user_id=event.source.user_id).first()
                    if user_info:
                        # 根據使用者位置和偏好類型查找附近餐廳
                        nearby_restaurants = get_nearby_restaurants(user_info.latitude, user_info.longitude, event.source.user_id)
                        if nearby_restaurants:
                            # 發送 Carousel 訊息顯示附近餐廳
                            sendCarousel(event, nearby_restaurants)
                        else:
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text="Sorry, I couldn't find information about nearby restaurants.")
                            )
                    else:
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text="Sorry, I couldn't find your location information.")
                        )
        
        return HttpResponse()
    else:
        return HttpResponseBadRequest()

#--------------選擇餐廳還是咖啡廳--------------
def sendConfirmTemplate(event):
    try:
        confirm_template = ConfirmTemplate(
            text='Please select the desired type',
            actions=[
                MessageAction(label='restaurant', text='restaurant'),
                MessageAction(label='cafe', text='cafe')
            ]
        )
        message = TemplateSendMessage(alt_text='Please select the desired type', template=confirm_template)
        line_bot_api.reply_message(event.reply_token, message)
    except LineBotApiError as e:
        print(f"Error replying message: {e}")


#--------------place_type存入user_info資料表--------------
def record_user_reply(event):
    user_id = event.source.user_id
    user_message = event.message.text
    if user_message in ['restaurant', 'cafe']:
        try:
            user_info = User_Info.objects.filter(user_id=user_id).first()
            #存usser_id進資料表
            if not user_info:
                user_info = User_Info.objects.create(user_id=user_id, place_type=user_message)
            else:
                user_info.place_type = user_message
                user_info.save()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="Please share your current location information by clicking on the '+' icon at the bottom left corner."))
        except LineBotApiError as e:
            print(f"Error replying message: {e}")
        except Exception as e:
            print(f"Error handling user reply: {e}")

#--------------經緯度存入user_info資料表--------------
def record_user_location(user_id, latitude, longitude):
    try:
        # 更新或創建使用者位置資訊
        user_info, created = User_Info.objects.update_or_create(
            user_id=user_id,
            defaults={'latitude': latitude, 'longitude': longitude}
        )
    except Exception as e:
        print(f"Error: Unable to record user location.{e}")

#--------------google place api抓五間最近的/place_type,經緯度要抓user_info資料表的--------------
def get_nearby_restaurants(latitude, longitude, user_id):
    try:
        # 從資料庫中取得使用者的偏好類型和經緯度
        user_info = User_Info.objects.filter(user_id=user_id).first()
        place_type = user_info.place_type if user_info else 'restaurant'
        latitude = user_info.latitude if user_info else latitude
        longitude = user_info.longitude if user_info else longitude

        # 設定 Google Places API 查詢參數
        url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
        params = {
            'key': google_places_api_key,
            'location': f"{latitude},{longitude}",
            'radius': 1500,
            'type': place_type
        }

        # 發送 API 請求並處理回應
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if 'results' in data:
            restaurants = []
            for idx, place in enumerate(data['results'][:5]):
                name = place.get('name', 'Unknown restaurant')
                rating = place.get('rating', 'N/A')
                place_id = place.get('place_id')
                photos = place.get('photos', [])
                photo_url = (f"https://maps.googleapis.com/maps/api/place/photo?"
                             f"maxwidth=400&photoreference={photos[0]['photo_reference']}"
                             f"&key={google_places_api_key}") if photos else None
                restaurants.append({
                    'name': name,
                    'rating': rating,
                    'place_id': place_id,
                    'photo_url': photo_url
                })

                # 將 place_id 存入 UserPlaceMapping 資料表中
                try:
                    mapping, created = UserPlaceMapping.objects.update_or_create(
                        user_id=user_id,
                        defaults={f'place_{idx+1}': place_id}
                    )
                except IntegrityError:
                    
                    pass

            return restaurants
        else:
            print("Google Places API returned no results.")
            return None

    except RequestException as e:
        print(f"Error: Unable to retrieve nearby restaurant information.{e}")
        return None

#--------------小卡顯示五間餐廳/最後一張是再隨機搜尋一次按鈕--------------
def sendCarousel(event, restaurants):
    columns = []

    try:
        for i, restaurant in enumerate(restaurants):
            if i == 5:
                break  # 限制只顯示前 5 家餐廳
    
            title = restaurant['name'][:40]  # 限制標題長度為 40 個字元
            text = f"Star rating: {restaurant['rating']}/5.0"
            actions = [
                URITemplateAction(
                    label='google map',

    #!!!!!!!!!!!!!!!!!!!!google map 頁面網址設定在這裡!!!!!!!!!!!!!!!!!!!!
                    uri=f"https://www.google.com/maps/place/?q=place_id:{restaurant['place_id']}"
                )
            ]

            # 檢查是否有對應的 RestaurantsName 記錄
            restaurant_name_entry = RestaurantsName.objects.filter(name=restaurant['name']).first()
            if restaurant_name_entry:
                actions.append(
                    URITemplateAction(
                        label='see the menu',
                        uri=restaurant_name_entry.url
                    )
                )
            else:
                actions.append(
                    MessageAction(
                        label='see the menu',
                        text="Sorry, I can't provide the menu."
                    )
                )

            column = CarouselColumn(
                thumbnail_image_url=restaurant['photo_url'] if restaurant['photo_url'] else 'https://via.placeholder.com/400',
                title=title,
                text=text,
                actions=actions
            )
            columns.append(column)
        
        # 添加 "Search More" 欄位
        search_more_column = CarouselColumn(
            thumbnail_image_url='https://image1.gamme.com.tw/news2/2018/32/55/q5qTpaSXkqWZqw.jpg',
            title='Search More',
            text='Find more restaurants',
            actions=[
                MessageAction(
                    label='Search More',
                    text='Search More Restaurants'
                ),
                MessageAction(
                    label=' ',
                    text='Search More Restaurants'
                )
            ]
        )
        columns.append(search_more_column)
        
        # 發送輪播訊息
        message = TemplateSendMessage(
            alt_text='Information about nearby restaurants.',
            template=CarouselTemplate(columns=columns)
        )
        line_bot_api.reply_message(event.reply_token, message)
    
    except LineBotApiError as e:
        print(f"傳送輪播訊息時發生 LineBotApiError: {e}")
        try:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))
        except LineBotApiError as err:
            print(f"傳送錯誤訊息時發生 LineBotApiError: {err}")
    
    except Exception as ex:
        print(f"發生未知錯誤: {ex}")
        try:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生未知錯誤！'))
        except LineBotApiError as err:
            print(f"傳送錯誤訊息時發生 LineBotApiError: {err}")


#--------------新五間餐廳--------------
def sendCarousel_2(event):
    try:
        # 從資料庫中取得使用者資訊
        user_info = User_Info.objects.filter(user_id=event.source.user_id).first()
        if not user_info:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Sorry, I couldn't find your location information.")
            )
            return
        
        place_type = user_info.place_type
        latitude = user_info.latitude
        longitude = user_info.longitude
        
        # 取得使用者已經儲存的餐廳 place_id
        user_place_mapping = UserPlaceMapping.objects.filter(user_id=event.source.user_id).first()
        if user_place_mapping:
            existing_place_ids = [
                user_place_mapping.place_1,
                user_place_mapping.place_2,
                user_place_mapping.place_3,
                user_place_mapping.place_4,
                user_place_mapping.place_5
            ]
        else:
            existing_place_ids = []

        # 設定 Google Places API 查詢參數
        url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
        params = {
            'key': google_places_api_key,
            'location': f"{latitude},{longitude}",
            'radius': 1500,
            'type': place_type
        }

        # 發送 API 請求並處理回應
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if 'results' in data:
            new_restaurants = []
            new_place_ids = []  # 新的 place_id 列表
            for place in data['results']:
                place_id = place.get('place_id')
                if place_id in existing_place_ids:
                    continue  # 跳過已經存在的餐廳
                
                name = place.get('name', 'Unknown restaurant')
                rating = place.get('rating', 'N/A')
                photos = place.get('photos', [])
                photo_url = (f"https://maps.googleapis.com/maps/api/place/photo?"
                             f"maxwidth=400&photoreference={photos[0]['photo_reference']}"
                             f"&key={google_places_api_key}") if photos else None
                new_restaurants.append({
                    'name': name,
                    'rating': rating,
                    'place_id': place_id,
                    'photo_url': photo_url
                })
                new_place_ids.append(place_id)

                if len(new_restaurants) == 5:
                    break  # 只取 5 間餐廳

            if new_restaurants:
                # 更新 UserPlaceMapping 資料表中的 place_1 到 place_5
                if user_place_mapping:
                    user_place_mapping.place_1 = new_place_ids[0] if len(new_place_ids) > 0 else None
                    user_place_mapping.place_2 = new_place_ids[1] if len(new_place_ids) > 1 else None
                    user_place_mapping.place_3 = new_place_ids[2] if len(new_place_ids) > 2 else None
                    user_place_mapping.place_4 = new_place_ids[3] if len(new_place_ids) > 3 else None
                    user_place_mapping.place_5 = new_place_ids[4] if len(new_place_ids) > 4 else None
                    user_place_mapping.save()
                else:
                    UserPlaceMapping.objects.create(
                        user_id=event.source.user_id,
                        place_1=new_place_ids[0] if len(new_place_ids) > 0 else None,
                        place_2=new_place_ids[1] if len(new_place_ids) > 1 else None,
                        place_3=new_place_ids[2] if len(new_place_ids) > 2 else None,
                        place_4=new_place_ids[3] if len(new_place_ids) > 3 else None,
                        place_5=new_place_ids[4] if len(new_place_ids) > 4 else None,
                    )

                # 發送 Carousel 訊息顯示新的餐廳
                sendCarousel(event, new_restaurants)
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="Sorry, I couldn't find new information about nearby restaurants.")
                )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Google Places API returned no results.")
            )

    except RequestException as e:
        print(f"Error: Unable to retrieve nearby restaurant information.{e}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='An error occurred. Please try again later.'))









