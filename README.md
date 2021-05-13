# HighWay-API-big-data-lambda-Architecture   
   
# Preview   
1. 전국 고속도로 실시간 교통 현황 api(한국도로공사)를 받아 통계 시각화 및 선택한 고속도로의 실시간 현황을 출력하는 프로젝트입니다.   
    
2. 배치 작업과 실시간 작업이 함께 이루어지는 람다 아키텍트 형식의 데이터 파이프라인입니다.   
    
3. crontab을 통해 5분마다 python script가 api를 호출, 전국 고속도로 소통 현황을 json 형식으로 수집합니다.   

# Process   
1. 실시간으로 수집되는 데이터는 HDFS(원본 데이터 유지)와 elasticsearch(실시간 적재 및 삭제)에 적재됩니다.   
   
2. 배치 layer에서는 1시간 단위로 spark가 실행됩니다.   
   
     2-1. 1시간 단위로 crontab을 통하여 pyspark-submit이 실행되고, 5분 간격으로 HDFS에 적재된 json형식의 원본 데이터를 1시간 단위로 통합, 가공 후 hive테이블에 배치 적재합니다.   
   
     2-2. 1시간 단위로 배치 작업이 이루어지면 elasticsearch 내에 적재되었던 이전데이터들은(배치 적재된 해당 시간 내의 데이터) 삭제됩니다.   
   
     2-3. 배치 적재된 테이블들을 통합하여 통계 시각화를 출력합니다.(spark & zeppelin)   
   
3. 실시간 layer에서는 5분마다 원본 데이터들이 elasticsearch에 적재되고 flask 클라이언트의 요청에 선택한 고속도로 조건에 맞는 결과를 index select 하여 출력합니다.   
    
![Screenshot_202](https://user-images.githubusercontent.com/66659846/118095195-bbe5bc00-b40a-11eb-943e-22e8e6603085.png)   
   
![Screenshot_203](https://user-images.githubusercontent.com/66659846/118095202-be481600-b40a-11eb-8d90-a5f020cd3410.png)   
   
# Result   
   
# Server Spec   
   
# Detailed Process   
## 데이터 수집
1. 5분 주기 getTraffic.py 실행(getdataserver)  
2. 약간의 전처리 된 데이터를 카프카 프로듀서로 전달하는 파이썬 스크립트   
![Screenshot_201](https://user-images.githubusercontent.com/66659846/118097423-a1f9a880-b40d-11eb-8e94-0f95f7278f2e.png)   
![Screenshot_204](https://user-images.githubusercontent.com/66659846/118097426-a32ad580-b40d-11eb-8216-7f2cd439e1c0.png)   
