from django.shortcuts import render

# Create your views here.
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage

import psycopg2
import datetime

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

@csrf_exempt
def callback(request):
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')

        try:
            events = parser.parse(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()

        for event in events:
            if isinstance(event, MessageEvent):
                HttpResponse(status=200)
                #user_id=event.source.user_id
                mtext=event.message.text
                result=forecast(mtext)
                message=[]
                if result[0] is None:
                    message.append(TextSendMessage(text="抱歉\n預報員找不到 " + mtext + " 的資料\n請輸入正確的台灣縣市名稱"))
                else:
                    text1 = ("預估今天 " + mtext +" 的空氣品質為: " + str(result[0]))
 
                    if result[2] is not None:
                        text1 += ("\n主要污染物為: " + str(result[2]))
                    message.append(TextSendMessage(text=text1))
                
                    suggest = aqilevel(result[0])
                    message.append(TextSendMessage(text=suggest))
                    
                    if result[1] is not None:
                        text2 = ("預估明天 " + mtext +" 的空氣品質為: " + str(result[1]))
                        
                        if result[3] is not None:
                            text2 += ("\n主要污染物為: " + str(result[3]))
                        
                        message.append(TextSendMessage(text=text2))
                        
                        suggest = aqilevel(result[1])
                        message.append(TextSendMessage(text=suggest))
                    
                line_bot_api.reply_message(event.reply_token,message)

        return HttpResponse()
    else:
        return HttpResponseBadRequest()
    
def forecast(mtext):
    database = "Finals"
    dbUser = "postgres"
    dbPwd = "postgres"
    host = "database-3.c0pxewrpxvj2.us-east-1.rds.amazonaws.com"
    conn = psycopg2.connect(database=database, user=dbUser, password=dbPwd, host=host, port="5432")
    cur = conn.cursor()
    
    city=mtext
    cur.execute(
        '''
        with T as(
            SELECT area
            FROM area_cities
            WHERE cities = %s
        ), S as(
            SELECT *
            FROM aqi_prediction
            WHERE DATE(publishtime)=CURRENT_DATE - INTERVAL '1 day'
        )
        SELECT avg(aqi)
        FROM S, T
        WHERE S.area = T.area
        GROUP BY(S.area)
        ''',
        (city,)
    )
    output1 = cur.fetchone()
    if output1 is None:
        conn.commit()
        cur.close()
        conn.close()
        return (None,None,None,None)
    else:
        value1 = round(output1[0])
        
    cur.execute(
        '''
        with T as(
            SELECT area
            FROM area_cities
            WHERE cities = %s
        )
        SELECT DISTINCT majorpollutant
        FROM aqi_prediction as S, T
        WHERE S.area = T.area and DATE(S.publishtime)=CURRENT_DATE - INTERVAL '1 day'
        ''',
        (city,)
    )
    output3 = cur.fetchone()
    pollut1 = output3[0]
    if pollut1 == 'NaN':
        pollut1 = None
        
    now = datetime.datetime.now()
    hour = now.hour
    if hour>=18:
        cur.execute(
            '''
            with T as(
                SELECT area
                FROM area_cities
                WHERE cities = %s
            ), S as(
                SELECT *
                FROM aqi_prediction
                WHERE DATE(publishtime)=CURRENT_DATE
            )
            SELECT avg(aqi)
            FROM S, T
            WHERE S.area = T.area
            GROUP BY(S.area)
            ''',
            (city,)
        )
        output2 = cur.fetchone()
        value2 = round(output2[0])
        #假若進到這個if敘述，則不會有output2是None的情形，反之output1也會是None，則先前就會return
        
        cur.execute(
            '''
            with T as(
                SELECT area
                FROM area_cities
                WHERE cities = %s
            )
            SELECT DISTINCT majorpollutant
            FROM aqi_prediction as S, T
            WHERE S.area = T.area and DATE(S.publishtime)=CURRENT_DATE
            ''',
            (city,)
        )
        output4 = cur.fetchone()
        pollut2 = output4[0]
        if pollut2 == 'NaN':
            pollut2 = None
            
    else:
        value2 = None
        pollut2 = None
    
    conn.commit()
    cur.close()
    conn.close()
    
    return (value1, value2, pollut1, pollut2)

def aqilevel(idx):
    if(0<=idx<=50):
        suggest="空氣品質良好\n污染程度低或無污染"
    elif(51<=idx<=100):
        suggest="空氣品質普通\n但對非常少數之極敏感族群產生輕微影響"
    elif(101<=idx<=150):
        suggest="空氣品質可能會對敏感族群的健康造成影響\n但是對一般大眾的影響不明顯\n建議減少戶外活動"
    elif(151<=idx<=200):
        suggest="空氣品質對所有人的健康都有影響!\n\n對於敏感族群可能產生較嚴重的健康影響\n建議減少戶外活動"
    elif(201<=idx<=300):
        suggest="空氣品質達到健康警報!!!\n\n所有人都可能產生較嚴重的健康影響\n建議一般民眾減少戶外活動\n學生應立即停止戶外活動"
    elif(301<=idx<=500):
        suggest="\n空氣品質對健康威脅達到緊急!!!!!\n\n一般民眾應避免戶外活動\n學生應立即停止戶外活動\n室內應緊閉門窗\n必要外出應配戴口罩等防護用具"
        
    return suggest