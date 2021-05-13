from kafka import KafkaProducer
from json import dumps
import time
import urllib.request 
import json
import pandas as pd

# 변수, 데이터 프레임, 카프카 프로듀서 객체 선언
url = 'http://data.ex.co.kr/openapi/odtraffic/trafficAmountByRealtime?key=your key&type=json'
response=urllib.request.urlopen(url)
json_str=response.read().decode("utf-8")
json_object=json.loads(json_str)
now = time.localtime()
df = pd.DataFrame(columns=['stdHour',
                           'routeNo',
                           'routeName',
                           'updownTypeCode',
                           'vdsId',
                           'trafficAmout',
                           'shareRatio',
                           'conzoneId',
                           'conzoneName',
                           'stdDate',
                           'speed',
                           'timeAvg',
                           'grade'])
producer = KafkaProducer(acks=0, 
                         bootstrap_servers=['ka01:9092', 'ka02:9092', 'ka03:9092'],
                         value_serializer=lambda x: dumps(x, ensure_ascii = False).encode('utf-8'))

# 컬럼 값 가공 함수
col_check = ['trafficAmout', 'shareRatio', 'speed', 'timeAvg']
def avg_cols(x):
    for j in col_check:
        cal_1 = float(df[df['conzoneName']==x['conzoneName']][j].values[0])
        cal_2 = float(x[j])
        result = round((cal_1 + cal_2) / 2)
        df.loc[df['conzoneName']==x['conzoneName'], j] = str(result)


# 정상 응답
value_check = [-1, '-1']
if json_object['code'] == 'SUCCESS':
    
    for i in json_object['list']:
        # 이상값 제거
        if i['trafficAmout'] in value_check or i['shareRatio'] in value_check or i['speed'] in value_check:
            pass
        
        else:
            # 최초 행은 삽입 후 동일 고속도로 기록일 시, 전 기록과의 평균으로 대체
            # 하나의 고속도로에 여러 카메라가 있을 수 있음
            if i['conzoneName'] in df['conzoneName'].values:
                avg_cols(i)
            
            # 최초 행은 삽입
            else:
                df=df.append(i, ignore_index=True)
                
    # 데이터 프레임 -> 최종 json create            
    json_result = df.to_dict('records')
    
    # json 한 객체 단위로 카프카 프로듀서 전송
    for a in json_result:
        producer.send('Traffic_Data', value=a)
        producer.flush()
        
        
    print("------SUCCESS------")
    print("%04d/%02d/%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec))
    print("-------------------")

# 응답 에러
else:
    print("-------ERROR-------")
    print("%04d/%02d/%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec))
