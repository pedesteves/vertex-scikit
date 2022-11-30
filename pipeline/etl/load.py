# STANDARD
import argparse
import json

from pyspark.sql import SparkSession
import pyspark.sql.functions as F

parser = argparse.ArgumentParser()
parser.add_argument("--temp-bucket", help="temporary gcs bucket")
parser.add_argument("--input-path", help="Input bigquery table - project:dataset.table")
parser.add_argument("--output-path", help="GCS output directory URI")
parser.add_argument("--schema", help="BQ JSON schema")
args = parser.parse_args()
temp_bucket = args.temp_bucket
input_dir = args.input_path
output_path = args.output_path
schema_json = json.loads(args.schema)

spark = SparkSession \
  .builder \
  .appName('bqload') \
  .getOrCreate()

spark.conf.set('temporaryGcsBucket', temp_bucket)

df = spark.read.json(input_dir + "/prediction.results*")

instance_fields = [field['name'] for field in schema_json[0]['fields']]

for ii in range(0, len(instance_fields)):
    df=df.withColumn(instance_fields[ii], F.col('instance').getItem(ii))
df = df.drop('instance')
df = df.select(F.struct(*instance_fields).alias('Instance'),'prediction' ).withColumnRenamed('prediction', schema_json[1]['name'])

df.write.format("bigquery") \
    .mode("overwrite") \
    .save(output_path)
