from delta import configure_spark_with_delta_pip
from tempfile import TemporaryDirectory
from pyspark.sql import SparkSession
from secrets import *
from pyspark.sql.types import *

jdbc_url = f"jdbc:postgresql://{DB_HOST}:{DB_PORT}/{DB_NAME}"

def config_spark():
    tmpdir = TemporaryDirectory()
    builder = (
        SparkSession.builder.master("local[*]")
        .config("spark.jars", "./jar/postgresql-42.7.3.jar")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.warehouse.dir", f"file:///{tmpdir.name}")
        .config("spark.executor.memory", "4g")  # Increase executor memory
        .config("spark.driver.memory", "4g")    # Increase driver memory
    )

    return configure_spark_with_delta_pip(builder).getOrCreate()


def process_batch(df, epoch_id):
    print(f"Hi, in batch {epoch_id}")

    (
        df.write.format("jdbc")
        .mode("append")
        .option("url", jdbc_url)
        .option("driver", "org.postgresql.Driver")
        .option("dbtable", "tracks")
        .option("user", DB_USER)
        .option("password", DB_PASSWORD)
        .save()
    )

def main():
    spark = config_spark()
    print("Hi, in main")
    tracks_presentation_schema = StructType([
        StructField("track_id", StringType(), True),
        StructField("artist_name", StringType(), True),
        StructField("track_name", StringType(), True),
        StructField("popularity", DoubleType(), True),
        StructField("year", IntegerType(), True),
        StructField("genre", StringType(), True),
        StructField("danceability", FloatType(), True),
        StructField("energy", FloatType(), True),
        StructField("key", IntegerType(), True),
        StructField("loudness", DoubleType(), True),
        StructField("mode", IntegerType(), True),
        StructField("speechiness", FloatType(), True),
        StructField("acousticness", FloatType(), True),
        StructField("instrumentalness", FloatType(), True),
        StructField("liveness", FloatType(), True),
        StructField("valence", FloatType(), True),
        StructField("tempo", DoubleType(), True),
        StructField("duration_ms", IntegerType(), True),
        StructField("time_signature", IntegerType(), True),
    ])

    (
        spark
        .readStream
        .schema(tracks_presentation_schema)
        .parquet("../data/ready_parquet_to_postgress")
        .writeStream
        .trigger(availableNow=True)
        .option("checkpointLocation", "./checkpointLocation/load_to_postgres/")
        .foreachBatch(process_batch)
        .start()
        .awaitTermination()
    )

if __name__ == '__main__':
    main()