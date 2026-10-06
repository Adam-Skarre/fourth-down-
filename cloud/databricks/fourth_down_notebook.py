# Databricks notebook source
# This is an optional batch extension, not the execution engine of the local app.
# Syntax checked locally. Spark/Delta execution requires a Databricks workspace.

# COMMAND ----------
dbutils.widgets.text('source_path', '/Volumes/main/fourth_down/reference/player_games.csv')
dbutils.widgets.text('catalog', 'main')
dbutils.widgets.text('schema', 'fourth_down')
dbutils.widgets.text('decision_week', '13')
dbutils.widgets.dropdown('scoring', 'half', ['standard', 'half', 'ppr'])

# COMMAND ----------
import re
from pyspark.sql import functions as F, Window
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType

source_path = dbutils.widgets.get('source_path')
catalog, schema = dbutils.widgets.get('catalog'), dbutils.widgets.get('schema')
week = int(dbutils.widgets.get('decision_week'))
scoring = dbutils.widgets.get('scoring')
ppr = {'standard': 0.0, 'half': 0.5, 'ppr': 1.0}[scoring]
assert 4 <= week <= 18, 'Expected a 2024 historical decision week, 4–18.'
assert source_path.startswith(('/Volumes/', 's3://')), 'Use a governed UC volume or authorized S3 external location.'
assert all(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', x) for x in (catalog, schema)), 'Unsafe table identifier.'
namespace = f'`{catalog}`.`{schema}`'

# COMMAND ----------
# A dedicated project schema is required. Re-running replaces only the named project tables.
spark.sql(f'CREATE SCHEMA IF NOT EXISTS {namespace}')
contract = StructType([
    StructField('player_id', StringType(), False), StructField('name', StringType(), False),
    StructField('position', StringType(), False), StructField('team', StringType(), False),
    StructField('season', IntegerType(), False), StructField('week', IntegerType(), False),
    StructField('opponent', StringType(), False), StructField('standard_points', DoubleType(), False),
    StructField('receptions', IntegerType(), False)
])
# FAILFAST rejects malformed rows. Explicit null checks below are still necessary with CSV input.
raw = spark.read.option('header', True).option('mode','FAILFAST').option('enforceSchema',False).schema(contract).csv(source_path)
for field in contract.fieldNames():
    assert raw.filter(F.col(field).isNull()).limit(1).count() == 0, f'Null in {field}'
assert raw.limit(1).count() > 0, 'Empty source'
invalid = raw.filter(
    (~F.col('position').isin('QB','RB','WR','TE')) |
    (~F.col('week').between(1,18)) | (F.col('season') != 2024) |
    (~F.col('standard_points').between(-100,150)) | F.isnan('standard_points') |
    (~F.col('receptions').between(0,50)) |
    (~F.col('player_id').rlike('^[A-Za-z0-9_-]{1,50}$')) |
    (~F.col('team').rlike('^[A-Z]{2,4}$')) | (~F.col('opponent').rlike('^[A-Z]{2,4}$')) |
    (~F.length(F.col('name')).between(1,100))
)
assert invalid.limit(1).count() == 0, 'Source failed the data contract'
assert raw.groupBy('player_id','season','week').count().filter('count > 1').limit(1).count() == 0, 'Duplicate player-week key'
assert raw.groupBy('player_id').agg(F.countDistinct('position').alias('positions')).filter('positions > 1').limit(1).count() == 0, 'Resolve position changes explicitly'
raw.write.format('delta').mode('overwrite').option('overwriteSchema','true').saveAsTable(f'{catalog}.{schema}.player_games')

# COMMAND ----------
# Crucial: exclude the target/future weeks BEFORE all window functions.
history = raw.filter((F.col('season')==2024) & (F.col('week')<week)).withColumn('points',F.col('standard_points')+F.lit(ppr)*F.col('receptions'))
by_player = Window.partitionBy('player_id','season')
newest = by_player.orderBy(F.col('week').desc())
ranked = history.withColumn('history_mean',F.avg('points').over(by_player)).withColumn('history_count',F.count('*').over(by_player)).withColumn('recency_rank',F.row_number().over(newest))
recent = ranked.filter(F.col('recency_rank')<=6).withColumn('weight',F.pow(F.lit(0.75),F.col('recency_rank')-1))
summary = recent.groupBy('player_id','season').agg(
    (F.sum(F.col('points')*F.col('weight'))/F.sum('weight')).alias('recent_weighted'),
    F.stddev_pop('points').alias('volatility'),
    F.first('history_mean').alias('history_mean'), F.first('history_count').alias('history_count'))
latest = ranked.filter(F.col('recency_rank')==1).select('player_id','season','name','team','position',F.col('week').alias('history_end'))
gold = summary.join(latest,['player_id','season']).withColumn('projection',F.lit(0.65)*F.col('recent_weighted')+F.lit(0.35)*F.col('history_mean')).withColumn('decision_week',F.lit(week)).withColumn('scoring',F.lit(scoring))
assert gold.filter(F.col('history_end')>=F.col('decision_week')).limit(1).count()==0, 'Temporal leakage'
# Eligibility is intentionally left to the local app (bye map + manual exclusions + history rules).
# This batch table is a projection artifact, NOT an automatically eligible lineup.
gold.write.format('delta').mode('overwrite').option('overwriteSchema','true').saveAsTable(f'{catalog}.{schema}.projections')
display(gold.orderBy(F.col('projection').desc()))

# COMMAND ----------
# Optional: export the normalized source for the local app, not a different scoring contract.
# Choose your own writable UC volume path, then uncomment:
# raw.coalesce(1).write.mode('overwrite').option('header',True).csv('/Volumes/main/fourth_down/reference/export')
# Download the generated part-*.csv and run: python -m fourth_down --data path/to/part.csv
