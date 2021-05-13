# HighWay-API-big-data-lambda-Architecture   
   
# Preview   
1. 전국 고속도로 실시간 교통 현황 api(한국도로공사)를 받아 통계 시각화 및 선택한 고속도로의 실시간 현황을 출력하는 프로젝트입니다.   
    
2. 배치 작업과 실시간 작업이 함께 이루어지는 람다 아키텍트 형식의 데이터 파이프라인입니다.   
    
3. crontab을 통해 5분마다 python script가 api를 호출, 전국 고속도로 소통 현황을 json 형식으로 수집합니다.   

# Process   
1. 실시간으로 수집되는 데이터는 HDFS(원본 데이터 유지)와 elasticsearch(실시간 적재)에 적재되며 HDFS에 적재 시 Nifi 기능을 통해 현재 시간에 맞게 동적인 파일명이 생성됩니다.      
   
2. 배치 layer에서는 1시간 단위로 spark가 실행됩니다.   
   
     2-1. 1시간 단위로 crontab을 통하여 pyspark-submit이 실행되고, 5분 간격으로 HDFS에 적재된 json형식의 원본 데이터를 1시간 단위로 통합, 가공 후 hive테이블에 배치 적재합니다.  
     (현재 시간으로 작명된 폴더 내 모든 json파일을 읽어 pyspark dataframe으로 불러옵니다. 후 index key를 생성하기 위해 RDD로 변환, increment key 생성 후, 다시 dataframe으로 변환,         점유율, 교통량, 속도, 평균 시간 컬럼을 Bigint형으로 변환한 뒤, 전체 dataframe select한 결과를 hive table로 적재합니다.(batch_yyyymmddhh.table))   
   
     2-2. 1시간 단위로 배치 작업이 이루어지면 elasticsearch 내에 적재되었던 이전데이터들은(배치 적재된 해당 시간 내의 데이터) 삭제됩니다.   
   
     2-3. 배치 적재된 테이블들을 통합하여 통계 시각화를 출력합니다.(spark & zeppelin)   
   
3. 실시간 layer에서는 5분마다 원본 데이터들이 elasticsearch에 적재되고 flask 클라이언트의 요청에 선택한 고속도로 조건에 맞는 결과를 index select 하여 출력합니다.   
    
![Screenshot_202](https://user-images.githubusercontent.com/66659846/118095195-bbe5bc00-b40a-11eb-943e-22e8e6603085.png)   
   
![Screenshot_203](https://user-images.githubusercontent.com/66659846/118095202-be481600-b40a-11eb-8d90-a5f020cd3410.png)   
   
# Result   
   
# Server Spec   
   
# Detailed Process   
## Nifi Data Flow   
1. ConsumeKafka: 실행된 파이썬 스크립트로 인해 카프카 프로듀서를 통한 데이터 전송이 이루어지고 카프카 컨슈머를 통해 데이터를 전달받습니다.   
   
2.1. MergeContent: 원본 데이터는 kafka를 통해 한 줄씩 json으로 전달 받습니다. 전송되는 행들을 하나의 json파일로 통합하고 파일명을 현재 분으로 동적 변경합니다. (-> filename:mm)  
   
2.2. PutElasticsearHTTP: consumeKafka에서 json 데이터를 한 줄씩 받아 elasticsearch traffic_elk index에 적재합니다.     
   
3. UpdateAttribute: 통합된 데이터를 .json 형식으로 변환합니다.(-> mm.json)   
   
4. PutHDFS: 변환된 데이터를 HDFS에 적재합니다. 폴더 구조는 nifi 자체 기능을 활용하여 동적인 시간으로 작명합니다.(yyyymmdd_hh/mm.json)   
   
5. SelectHiveQL: 1시간에 한 번씩 실행되는 pyspark-submit의 작업이 완료되면, hive에 배치 테이블이 생성됩니다. 이를 확인하기 위한 select문입니다.   
   
6. DeleteByQueryElasticsearch: hive에 1시간 동안의 데이터를 통합한 배치 테이블이 적재되면, 그 시간 내에 해당되는 elasticsearch에 적재된 데이터들을 삭제합니다.   
   
7. LogAttribute: 각 프로세스 실행 여부 간 로그를 출력합니다.   
![Screenshot_214](https://user-images.githubusercontent.com/66659846/118121319-4559b600-b42c-11eb-8093-d23ac398724d.png)   
   
## 데이터 수집
1. 5분 주기 getTraffic.py 실행(getdataserver)  
2. 약간의 전처리 된 데이터를 카프카 프로듀서로 전달하는 파이썬 스크립트(파일 별도 첨부)   
![Screenshot_201](https://user-images.githubusercontent.com/66659846/118097423-a1f9a880-b40d-11eb-8e94-0f95f7278f2e.png)   
![Screenshot_204](https://user-images.githubusercontent.com/66659846/118097426-a32ad580-b40d-11eb-8216-7f2cd439e1c0.png)   
   
## kafka consumer 확인   
1. 원본 데이터 수집 확인   
2. kafka cluster(ka01:9200, ka02:9200, ka03:9200)   
![Screenshot_206](https://user-images.githubusercontent.com/66659846/118100472-74aef980-b411-11eb-8638-d16766a11478.png)   
   
## HDFS, Elasticsearch 적재 확인   
1. HDFS 경로(hdfs://user/source_traffic/yyyymmdd_hh/mm.json   
2. elasticsearch cluster(elkmaster:9200,5601, elkdn01:9200), index: traffic_elk, type:json   
![Screenshot_205](https://user-images.githubusercontent.com/66659846/118101597-bc825080-b412-11eb-9a00-04b7531cf6d1.png)   
![Screenshot_208](https://user-images.githubusercontent.com/66659846/118101603-be4c1400-b412-11eb-9045-af2589466faf.png)   
![Screenshot_209](https://user-images.githubusercontent.com/66659846/118101990-2ef33080-b413-11eb-920e-4047070183f2.png)   
   
## 1시간 주기 Pyspark Submit 실행(crontab)   
