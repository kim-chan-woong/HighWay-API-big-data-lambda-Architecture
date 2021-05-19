from flask import Flask, render_template, request
from flask.wrappers import Request
from elasticsearch import Elasticsearch
import datetime
app = Flask(__name__)

# 고속도로명 종류 하드 코딩
route_kind = [['0010', '경부선'],
              ['1200', '경인선'],
              ['0140', '고창담양선'],
              ['0120', '광주대구선'],
              ['0520', '광주원주선'],
              ['0290', '구리포천선'],
              ['4002', '구리포천지선'],
              ['1020', '남해1지선'],
              ['1040', '남해2지선'],
              ['0100', '남해선(순천-부산)'],
              ['0101', '남해선(영암-순천)'],
              ['0252', '논산천안선'],
              ['0301', '당진대전선'],
              ['0552', '대구부산선'],
              ['0200', '대구포항선'],
              ['3000', '대전남부선'],
              ['0652', '동해선(부산-포항)'],
              ['0650', '동해선(삼척-속초)'],
              ['0121', '무안광주선'],
              ['4000', '봉담동탄선'],
              ['4003', '봉담송산선'],
              ['0105', '부산신항선'],
              ['6000', '부산외곽선'],
              ['0651', '부산울산선'],
              ['3010', '상주영천선'],
              ['0172', '서울문산선'],
              ['0173', '서울문산지선'],
              ['0600', '서울양양선'],
              ['1201', '서울제물포선'],
              ['1510', '서천공주선'],
              ['0150', '서해안선'],
              ['1000', '수도권제1순환선'],
              ['0270', '순천완주선'],
              ['0500', '영동선'],
              ['0171', '오산화성선'],
              ['0320', '옥산오창선'],
              ['1710', '용인서울선'],
              ['0160', '울산선'],
              ['0201', '익산장수선'],
              ['1300', '인천공항선'],
              ['4001', '인천김포선'],
              ['1102', '인천대교선'],
              ['1103', '인천대교지선'],
              ['1100', '제2경인선'],
              ['0370', '제2중부선'],
              ['0450', '중부내륙선'],
              ['4510', '중부내륙지선'],
              ['0352', '중부선'],
              ['0550', '중앙선'],
              ['5510', '중앙선지선'],
              ['0300', '청주영덕선'],
              ['0351', '통영대전선'],
              ['0153', '평택시흥선'],
              ['0400', '평택제천선'],
              ['0170', '평택화성선'],
              ['0141', '함양울산선'],
              ['0251', '호남선'],
              ['2510', '호남지선']]

# get elasticsearch data
es = Elasticsearch('192.168.56.130:9200')

# 시간, conzoneName에 맞게 select
body_getconzoneName = {
    "query": {
        "bool": {
            "must":
            [
                {
                    "match": {
                        "routeNo": ""
                    }
                },
                {
                    "match": {
                        "stdHour": ""
                    }
                }
            ]
        }
    },
    "size": '',
    "_source": ["conzoneName"]
}

body_getresult = {
    "query": {
        "bool": {
            "must":
            [
                {
                    "match_phrase": {
                        "conzoneName": ""
                    }
                },
                {
                    "match": {
                        "stdHour": ""
                    }
                }
            ]
        }
    },
    "_source": ["stdHour", "speed", "timeAvg", "trafficAmout", "shareRatio", "routeNo"]
}

# 첫 화면


@app.route('/')
def index():
    return render_template('index.html', route_kind=route_kind)


# 고속도로 대분류 버튼 클릭 시
@app.route('/resultIC', methods=['POST', 'GET'])
def menu():
    routeValue = request.form['selectIC']
    conzoneNamelist = []

    # 요청 시간
    now = datetime.datetime.now()

    # routeNo, conzoneName 받은 후 같은 고속도로 내 도로명 모두 추출
    index = 'traffic_elk'
    body_getconzoneName['query']['bool']['must'][0]['match']['routeNo'] = routeValue[0:4]
    body_getconzoneName['size'] = 500

    # 검색 키워드 확인, 고속도로, 도로명, 현재 시간 동적 파싱 후 elk 쿼리 결과
    # 실수집 시각 구하기 (현재 시간에서 10분 이전 까지 검색)
    for i in range(0, 11):
        time_cal = now - datetime.timedelta(minutes=i)
        time_value = str(time_cal.hour) + str(time_cal.minute)
        body_getconzoneName['query']['bool']['must'][1]['match']['stdHour'] = time_value
        res_getconzoneName = es.search(index=index, body=body_getconzoneName)

        if len(res_getconzoneName['hits']['hits']) == 0:
            pass
        else:
            for j in res_getconzoneName['hits']['hits']:
                if j in conzoneNamelist:
                    pass
                else:
                    conzoneNamelist.append(j['_source']['conzoneName'])
            break

    return render_template('resultIC.html',
                           routeValue=routeValue,
                           conzoneNamelist=conzoneNamelist)


# 세부 도로명 선택
@app.route('/resultIC/<conzoneName>', methods=['POST', 'GET'])
def final(conzoneName):
    conzoneNameValue = conzoneName
    conzoneNamelist = []

    # 요청 시간
    now = datetime.datetime.now()

    # 세부 도로명 받은 후 검색
    index = 'traffic_elk'
    body_getresult['query']['bool']['must'][0]['match_phrase']['conzoneName'] = conzoneNameValue

    for i in range(0, 11):
        time_cal = now - datetime.timedelta(minutes=i)
        time_value = str(time_cal.hour) + str(time_cal.minute)
        body_getresult['query']['bool']['must'][1]['match']['stdHour'] = time_value
        res_getresult = es.search(index=index, body=body_getresult)

        if len(res_getresult['hits']['hits']) == 0:
            pass
        else:
            result_json = res_getresult['hits']['hits'][0]['_source']
            break

    reqTime = str(now.hour) + str(now.minute)
    reqTimeValue = reqTime[0:2] + "시 " + reqTime[2:] + "분"
    stdHour = result_json['stdHour']
    stdHourValue = stdHour[0:2] + "시 " + stdHour[2:] + "분"
    speedValue = result_json['speed'] + "Km/h"
    timeAvgValue = result_json['timeAvg']

    # 시간 변환
    if int(timeAvgValue) < 60:
        timeAvgValue = timeAvgValue + "분"
    else:
        time_changer = str(datetime.timedelta(
            seconds=int(timeAvgValue) * 60)).split(':')
        timeAvgValue = time_changer[0] + '시간 ' + time_changer[1] + '분'

    trafficAmoutValue = result_json['trafficAmout']
    shareRatioValue = result_json['shareRatio'] + "%"
    routeNoValue = result_json['routeNo']

    # 결과들 저장 후 다시 선택 창에 같은 고속도로 내 도로명 출력
    body_getconzoneName['query']['bool']['must'][0]['match']['routeNo'] = routeNoValue
    body_getconzoneName['size'] = 500

    for i in range(0, 11):
        time_cal = now - datetime.timedelta(minutes=i)
        time_value = str(time_cal.hour) + str(time_cal.minute)
        body_getconzoneName['query']['bool']['must'][1]['match']['stdHour'] = time_value
        res_getconzoneName = es.search(index=index, body=body_getconzoneName)

        if len(res_getconzoneName['hits']['hits']) == 0:
            pass
        else:
            for j in res_getconzoneName['hits']['hits']:
                if j in conzoneNamelist:
                    pass
                else:
                    conzoneNamelist.append(j['_source']['conzoneName'])
            break

    return render_template('resultIC.html',
                           reqTimeValue=reqTimeValue,
                           conzoneNameValue=conzoneNameValue,
                           stdHourValue=stdHourValue,
                           speedValue=speedValue,
                           timeAvgValue=timeAvgValue,
                           trafficAmoutValue=trafficAmoutValue,
                           shareRatioValue=shareRatioValue,
                           conzoneNamelist=conzoneNamelist)


if __name__ == '__main__':
    app.run(debug=True)
