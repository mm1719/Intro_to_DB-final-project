# Intro_to_DB-final-project
**主要有兩份檔案:**
* **爬蟲_資料庫更新.py**
* **linebot_連接資料庫.py**
### 爬蟲_資料庫更新.py
> 由電腦的工作排程器每天執行3次，每次從政府資料開放平台抓下「空氣品質資料」，擷取所需資料後將其正規化(Normalization)，並存入用PostgreSQL建置的資料庫。
> 同時每天會更新資料庫的資料，確保裡面只會有2天(昨、今)內的資料，過時的資料會刪除。
>> 註: 資料來源: https://data.gov.tw/dataset/6349 。  
#### 資料庫說明
* aqi_prediction   `儲存日期時間(timestamp)、地區、主要汙染物、空氣品質指標`
* forecast_publish `儲存發布的日期，以及對應到的預測日期`
* area_cities      `儲存地區、縣市 (e.g. 北區, 台北市)`
### linebot_連接資料庫.py
> 當用戶輸入一城市的名稱時，用Django建置的LINE BOT會將信息(城市名稱)擷取出來後，打開用PostgreSQL建置的資料庫，並取出對應到該則信息的資料(空氣品質指標、主要汙染物)。
> 取出來的資料加以分類、整理後再回傳給用戶(當地空氣品質、當地主要汙染物、提醒與建議)。
>> 註: 提醒與建議是根據空氣品質指標的結果提供的，參考網址: https://air.epa.gov.tw/EnvTopics/AirQuality_1.aspx 。  
>> 註: 回傳資料給用戶之前，先傳 HTTP 200，告訴LINE這封訊息有成功回覆。
#### 函數說明
* forecast(mtext) `打開資料庫，並且找到對應到 mtext 的城市名稱，最後輸出對應的資料: 今日指標(result[0]), 明日指標(result[1]), 今日汙染物(result[2]), 明日汙染物(result[3])`
* aqilevel(idx) `根據傳入的空汙數值，回傳對應的提醒與建議(suggest)`
