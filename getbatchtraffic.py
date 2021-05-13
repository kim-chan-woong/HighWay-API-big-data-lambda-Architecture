from pyspark.sql.session import SparkSession
from datetime import datetime

# pyspark 객체 생성
spark = SparkSession.builder.appName('traffic').config("hive.metastore.uris", "thrift://192.168.56.100:9083").enableHiveSupport().getOrCreate()

# 원본 데이터에 접근하기 위한 timestamp
dateValue = datetime.today().strftime("%Y%m%d_%H")
path = "hdfs://NNHA/user/source_traffic/" + dateValue + "/*.json"

# 가공 후 저장될 hdfs/csv, hive/table 이름을 할당
folderName1 = dateValue.split("_")[0]
folderName2 = dateValue.split("_")[1]

# dataframe으로 호출
df = spark.read.json(path)
df2 = df.selectExpr("conzoneId",
                          "conzoneName",
                          "grade",
                          "routeName",
                          "routeNo",
                          "cast(shareRatio as int) shareRatio",
                          "cast(speed as int) speed",
                          "stdDate",
                          "stdHour",
                          "cast(timeAvg as int) timeAvg",
                          "cast(trafficAmout as int) trafficAmout",
                          "updownTypeCode",
                          "vdsId")

# rdd 변환 후 인덱스 컬럼 생성
rdd_df = df2.rdd.zipWithIndex().toDF()
rdd_df = rdd_df.withColumn('conzoneId', rdd_df['_1'].getItem("conzoneId"))
rdd_df = rdd_df.withColumn('conzoneName', rdd_df['_1'].getItem("conzoneName"))
rdd_df = rdd_df.withColumn('grade', rdd_df['_1'].getItem("grade"))
rdd_df = rdd_df.withColumn('routeName', rdd_df['_1'].getItem("routeName"))
rdd_df = rdd_df.withColumn('routeNo', rdd_df['_1'].getItem("routeNo"))
rdd_df = rdd_df.withColumn('shareRatio', rdd_df['_1'].getItem("shareRatio"))
rdd_df = rdd_df.withColumn('speed', rdd_df['_1'].getItem("speed"))
rdd_df = rdd_df.withColumn('stdDate', rdd_df['_1'].getItem("stdDate"))
rdd_df = rdd_df.withColumn('stdHour', rdd_df['_1'].getItem("stdHour"))
rdd_df = rdd_df.withColumn('timeAvg', rdd_df['_1'].getItem("timeAvg"))
rdd_df = rdd_df.withColumn('trafficAmout', rdd_df['_1'].getItem("trafficAmout"))
rdd_df = rdd_df.withColumn('updownTypeCode', rdd_df['_1'].getItem("updownTypeCode"))
rdd_df = rdd_df.withColumn('vdsId', rdd_df['_1'].getItem("vdsId"))

# rdd -> dataframe
df_final = rdd_df.drop("_1").withColumnRenamed("_2", "idx").select("*")

# dataframe을 hdfs에 csv 파일 형태로 저장
df_final.coalesce(1).write.format("com.databricks.spark.csv").save("hdfs://NNHA/user/batch_traffic/" + folderName1 + "/" + folderName2)

# dataframe을 hive table에 저장
df_final.write.saveAsTable("traffic_data.batch_" + folderName1 + folderName2)

