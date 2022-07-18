import pandas as pd
import numpy as np
import random
from scipy.sparse import csr_matrix
import math
from sklearn.neighbors import NearestNeighbors
from fuzzywuzzy import fuzz
import time

from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import col, lower
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.recommendation import ALS
from pyspark.ml.tuning import ParamGridBuilder

spark_session = SparkSession.builder.appName("Music Recommender").getOrCreate()
sp_con = spark_session.sparkContext

artists = spark_session.read.csv('./data/lastfm_artist_list.csv', inferSchema=True, header=True)
# switch the user_listens one with 5-10 rating processed?
user_listens = spark_session.read.csv('./data/lastfm_user_scrobbles.csv', inferSchema=True, header=True)
artists.printSchema()
user_listens.printSchema()

training_df, test_df = user_listens.randomSplit([.8, .2])

# parameters for the model
iterations = 12
regularisation = 0.1
rank = 8
errors = []
err = 0

als_model = ALS(maxIter = iterations, rank = rank, regParam = regularisation,
userCol='user_id', itemCol='artist_id', ratingCol='scrobbles', coldStartStrategy="drop")

# training it
model = als_model.fit(training_df)
model.recommendForAllUsers(5)

if __name__=="__main__":
    print("run")
