# STANDARD
import argparse

from pyspark.sql import SparkSession
from pyspark.sql.functions import concat, concat_ws, lit

parser = argparse.ArgumentParser()
parser.add_argument("--temp-bucket", help="temporary gcs bucket")
parser.add_argument("--input-path", help="Input bigquery table - project:dataset.table")
parser.add_argument("--output-path", help="GCS output directory URI")
parser.add_argument("--sample-fraction", type=float, help="fraction of input rows to sample")
args = parser.parse_args()
temp_bucket = args.temp_bucket
input_table = args.input_path
output_path = args.output_path
sample_fraction = args.sample_fraction

spark = SparkSession \
  .builder \
  .appName('preprocessing') \
  .getOrCreate()

spark.conf.set('temporaryGcsBucket', temp_bucket)

df = spark.read.format('bigquery') \
  .option('table', input_table) \
  .load()
df.createOrReplaceTempView('df')

# CUSTOM PREPROCESSING

df = df.drop('Class')
df = df.sample(fraction=sample_fraction, seed=42)

# STANDARD

cols = df.columns

formatted_df = df.select(concat(lit("["), concat_ws(",",*cols), lit("]")).alias("data"))

formatted_df.write.text(path=output_path)