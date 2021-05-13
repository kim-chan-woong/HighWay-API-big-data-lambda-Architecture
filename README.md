# HighWay-API-big-data-lambda-Architecture   
   
# Preview   
1. 전국 고속도로 실시간 교통 현황 api(한국도로공사)를 받아 통계 시각화 및 선택한 고속도로의 실시간 현황을 출력하는 프로젝트입니다.   
    
2. 12대의 서버를 활용한 배치 작업과 실시간 작업이 함께 이루어지는 람다 아키텍트 형식의 데이터 파이프라인입니다.   
    
3. crontab을 통해 5분마다 python script가 api를 호출, 전국 고속도로 소통 현황을 json 형식으로 수집합니다.   
   
4. 각 고속도로의 conzoneName(고속도로명)이 중복되는 현상이 발견되어 한국도로공사에 문의한 결과, 각 json행들은 한 고속도로 내에 카메라의 개수만큼 행이 출력되는 것을 확인,   
그러므로 원천데이터의 json 개수는 고속도로의 개수가 아닌 모든 고속도로의 카메라를 합한 개수입니다. 이에 conzoneName이 같을 시, 결국 같은 고속도로 내 다른 카메라이기 때문에,      
같은 conzoneName이 나올때 마다, 점유율, 교통량, 속도, 평균 시간 컬럼을 더하고 나누는 과정을 1차적으로 거쳐 한 고속도로 내 모든 카메라 데이터 평균을 구하였습니다. 그렇게 각 행의 conzoneName이 고유해진 json데이터(1차 전처리)를 원본데이터라 가정하고 진행하였습니다.   
   
5. 친절히 답변해주신 한국도로공사에 큰 감사의 인사를 전합니다.   

# Process   
1. crontab - python script를 통해 실시간으로 수집되는 데이터는 HDFS(원본 데이터 유지)와 elasticsearch(실시간 적재)에 적재되며 HDFS에 적재 시 Nifi 기능을 통해 현재 시간에 맞게 동적인 파일명과 폴더 구조 생성됩니다.      
   
2. 배치 layer에서는 매시간 58분마다 1시간 단위로 pyspark-submit이 crontab을 통해 실행됩니다. pyspark는 5분 간격으로 HDFS에 적재된 json형식의 원본 데이터를 1시간 단위로 통합, 인덱스 컬럼 추가, 형변환 등의 가공을 거친 후 hive테이블과 HDFS/CSV에 현재 수집 시간에 맞는 이름으로 배치 적재합니다. 1시간 동안의 데이터가 hive 테이블에 적재되면, 그 시간에 해당되는 elasticsearch에 실시간으로 적재된 이전데이터들이 삭제됩니다. 이후 배치 적재된 hive 테이블들을 spark, zeppelin을 활용하여 통합, 통계 시각화를 출력합니다.   
   
3. 실시간 layer에서는 5분마다 원본 데이터들이 elasticsearch에 적재되고 flask 클라이언트의 요청에 선택한 고속도로 조건에 맞는 결과를 index select 하여 출력합니다.   
    
![Screenshot_202](https://user-images.githubusercontent.com/66659846/118095195-bbe5bc00-b40a-11eb-943e-22e8e6603085.png)   
   
![Screenshot_203](https://user-images.githubusercontent.com/66659846/118095202-be481600-b40a-11eb-8d90-a5f020cd3410.png)   
   
# Result   
   
# Server Spec   
   
# Detailed Process   
## Nifi Data Flow(프로세스들 상세 설정 파일 별도 첨부)   
1. ConsumeKafka: 실행된 파이썬 스크립트로 인해 카프카 프로듀서를 통한 데이터 전송이 이루어지고 카프카 컨슈머를 통해 데이터를 전달받습니다.   
   
2-1. MergeContent: 원본 데이터는 kafka를 통해 한 줄씩 json으로 전달 받습니다. 전송되는 행들을 하나의 json파일로 통합하고 파일명을 현재 분으로 동적 변경합니다. (-> filename:mm)  
   
2-2. PutElasticsearHTTP: consumeKafka에서 json 데이터를 한 줄씩 받아 elasticsearch traffic_elk index에 적재합니다.     
   
3. UpdateAttribute: 통합된 데이터를 .json 형식으로 변환합니다.(-> mm.json)   
   
4. PutHDFS: 변환된 데이터를 HDFS에 적재합니다. 폴더 구조는 nifi 자체 기능을 활용하여 동적인 시간으로 작명합니다.(yyyymmdd_hh/mm.json)   
   
5. SelectHiveQL: 1시간에 한 번씩 실행되는 pyspark-submit의 작업이 완료되면, hive에 배치 테이블이 생성됩니다. 이를 확인하기 위한 select문입니다.   
   
6. DeleteByQueryElasticsearch: hive에 1시간 동안의 데이터를 통합한 배치 테이블이 적재되면, 그 시간 내에 해당되는 elasticsearch에 적재된 데이터들을 삭제합니다.   
   
7. LogAttribute: 각 프로세스 실행 여부 간 로그를 출력합니다.   
![Screenshot_218](https://user-images.githubusercontent.com/66659846/118122388-c1a0c900-b42d-11eb-8948-14c19fa9bb47.png)   
   
## 데이터 수집
1. 5분 주기 getTraffic.py 실행(getdataserver)  
   
2. 약간의 전처리 된 데이터를 카프카 프로듀서로 전달하는 파이썬 스크립트(소스 파일 별도 첨부)   

![Screenshot_201](https://user-images.githubusercontent.com/66659846/118097423-a1f9a880-b40d-11eb-8e94-0f95f7278f2e.png)   
![Screenshot_204](https://user-images.githubusercontent.com/66659846/118097426-a32ad580-b40d-11eb-8216-7f2cd439e1c0.png)   
   
## kafka consumer 확인   
1. 원본 데이터 수집 확인   
2. kafka cluster(ka01:9200, ka02:9200, ka03:9200)   
![Screenshot_206](https://user-images.githubusercontent.com/66659846/118100472-74aef980-b411-11eb-8638-d16766a11478.png)   
   
## HDFS, Elasticsearch 5분 간격 실시간 적재 확인   
1. HDFS 경로(hdfs://user/source_traffic/yyyymmdd_hh/mm.json   
2. elasticsearch cluster(elkmaster:9200,5601, elkdn01:9200), index: traffic_elk, type:json   
![Screenshot_233](https://user-images.githubusercontent.com/66659846/118133873-4561b200-b43c-11eb-9277-20d606b95ba5.png)   
![Screenshot_234](https://user-images.githubusercontent.com/66659846/118133880-4692df00-b43c-11eb-8696-5ff7ea416533.png)    
![Screenshot_209](https://user-images.githubusercontent.com/66659846/118101990-2ef33080-b413-11eb-920e-4047070183f2.png)   
   
## 1시간 주기 Pyspark Submit 실행(crontab)   
1. crontab을 통해 pyspark가 매 시간 58분마다 실행(소스 파일 별도 첨부)  
2. 동적으로 구성된 폴더 내 5분 단위의 json파일들을 dataframe으로 통합, RDD 변환 후 인덱스 컬럼 추가 후 재 dataframe 변환   
3. 점유율, 교통량, 속도, 평균 시간 컬럼 형변환 후 수집 날짜 및 시간명으로 hive 테이블 및 HDFS 적재   
![Screenshot_221](https://user-images.githubusercontent.com/66659846/118128223-91f5bf00-b435-11eb-9d2b-87f213f182b9.png)   
   
## HDFS와 HIVE TABLE 배치 적재 확인   
1. Hive table: traffic_data.batch_yyyymmddhh   
2. hdfs folder: hdfs://user/batch_traffic/yyyymmdd/hh/********.csv   
![Screenshot_169](https://user-images.githubusercontent.com/66659846/118129584-53610400-b437-11eb-8a6b-1fba54f90cf8.png)   
![Screenshot_228](https://user-images.githubusercontent.com/66659846/118133368-b6ed3080-b43b-11eb-9d5b-8f3e147c35f5.png)   
![Screenshot_229](https://user-images.githubusercontent.com/66659846/118133372-b81e5d80-b43b-11eb-9f6f-e839cb1305d6.png)   
![Screenshot_232](https://user-images.githubusercontent.com/66659846/118133651-09c6e800-b43c-11eb-81aa-a9b019cc8867.png)   
![Screenshot_231](https://user-images.githubusercontent.com/66659846/118133374-b81e5d80-b43b-11eb-9cd7-94f9e8575606.png)   

## 배치 적재 시 elasticsearch 이전 데이터 삭제 확인   
1. 배치 적재된 시간의 데이터들이 삭제, 새로운 실시간 데이터 생성이 반복됨을 확인   
![Screenshot_227](https://user-images.githubusercontent.com/66659846/118130202-13e6e780-b438-11eb-8567-dad64857b585.png)   
