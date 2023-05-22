import pandas as pd
import numpy as np
import io
import datetime
import requests
import psycopg2

url="https://data.epa.gov.tw/api/v2/aqf_p_01?api_key=e8dd42e6-9b8b-43f8-991e-b3dee723a52d&limit=1000&sort=publishtime desc&format=CSV"
s=requests.get(url).content
df=pd.read_csv(io.StringIO(s.decode('utf-8')))

usingdf=df.iloc[:,1:6]
usingdf.forecastdate=usingdf.forecastdate.astype('datetime64')
usingdf.publishtime=usingdf.publishtime.astype('datetime64')

maskdiff = ((usingdf.forecastdate-usingdf.publishtime).astype('timedelta64[h]') <= 24)
maskmini = (usingdf.forecastdate > usingdf.publishtime)
masktomo = (usingdf.forecastdate == np.datetime64('today')+np.timedelta64(1, 'D'))
newdf=usingdf[maskdiff & maskmini & masktomo]
newdf = newdf.reset_index(drop=True)

gendf = newdf[['publishtime','forecastdate']]
sqldf1 = newdf.drop(columns='forecastdate')
sql2df = gendf.drop_duplicates()

database = "Finals"
dbUser = "postgres"
dbPwd = "postgres"
conn = psycopg2.connect(database=database, user=dbUser, password=dbPwd, host="database-3.c0pxewrpxvj2.us-east-1.rds.amazonaws.com", port="5432")
cur = conn.cursor()

"""
cur.execute(
    '''
    CREATE TABLE aqi_prediction (
        publishtime timestamp,
        area varchar(255),
        majorpollutant varchar(255),
        aqi integer
    );
    CREATE TABLE forecast_publish (
        publishtime timestamp,
        forecastdate date
    );
    CREATE TABLE area_cities (
        area varchar(255),
        cities varchar(255)
    );
    '''
)
"""

"""
cur.executemany(
    '''
    INSERT INTO area_cities (area, cities)
    VALUES (%s, %s)
    ''',
    [
        ('北部', '基隆市'),
        ('北部', '台北市'),
        ('北部', '臺北市'),
        ('北部', '新北市'),
        ('北部', '桃園市'),
        ('竹苗', '新竹市'),
        ('竹苗', '新竹縣'),
        ('竹苗', '苗栗縣'),
        ('中部', '台中市'),
        ('中部', '臺中市'),
        ('中部', '南投縣'),
        ('中部', '彰化縣'),
        ('雲嘉南', '雲林縣'),
        ('雲嘉南', '嘉義縣'),
        ('雲嘉南', '嘉義市'),
        ('雲嘉南', '台南市'),
        ('雲嘉南', '臺南市'),
        ('高屏', '高雄市'),
        ('高屏', '屏東縣'),
        ('宜蘭', '宜蘭縣'),
        ('花東', '花蓮縣'),
        ('花東', '臺東縣'),
        ('花東', '台東縣'),
        ('澎湖', '澎湖縣'),
        ('金門', '金門縣'),
        ('馬祖', '連江縣'),
        ('北部', '基隆'),
        ('北部', '台北'),
        ('北部', '臺北'),
        ('北部', '新北'),
        ('北部', '桃園'),
        ('竹苗', '新竹'),
        ('竹苗', '新竹'),
        ('竹苗', '苗栗'),
        ('中部', '台中'),
        ('中部', '臺中'),
        ('中部', '南投'),
        ('中部', '彰化'),
        ('雲嘉南', '雲林'),
        ('雲嘉南', '嘉義'),
        ('雲嘉南', '嘉義'),
        ('雲嘉南', '台南'),
        ('雲嘉南', '臺南'),
        ('高屏', '高雄'),
        ('高屏', '屏東'),
        ('宜蘭', '宜蘭'),
        ('花東', '花蓮'),
        ('花東', '臺東'),
        ('花東', '台東'),
        ('澎湖', '澎湖'),
        ('金門', '金門'),
        ('馬祖', '連江'),
    ]
)
"""

for i, row in sql2df.iterrows():
    cur.execute(
        '''
        INSERT INTO forecast_publish (publishtime, forecastdate)
        VALUES (%s, %s)
        ''',
        tuple(row)
    )
    
for i, row in sqldf1.iterrows():
    cur.execute(
        '''
        INSERT INTO aqi_prediction (publishtime, area, majorpollutant, aqi)
        VALUES (%s, %s, %s, %s)
        ''',
        tuple(row)
    )

yesterday = datetime.datetime.now() - datetime.timedelta(days=2)
date_before_yesterday = yesterday.strftime('%Y-%m-%d')

cur.execute(
    '''
    DELETE FROM forecast_publish
    WHERE date(publishtime) = %s
    ''',
    (date_before_yesterday,)
)
cur.execute(
    '''
    DELETE FROM aqi_prediction
    WHERE date(publishtime) = %s
    ''',
    (date_before_yesterday,)
)

conn.commit()
cur.close()
conn.close()