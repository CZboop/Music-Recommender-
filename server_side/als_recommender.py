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

if __name__=="__main__":
    print("run")
