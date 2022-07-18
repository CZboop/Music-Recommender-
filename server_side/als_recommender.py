import pandas as pd
import numpy as np
import random
import math
from fuzzywuzzy import fuzz
import time

from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import col, lower
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.recommendation import ALS
from pyspark.ml.tuning import ParamGridBuilder

class Recommender:
    def __init__(self):
        self.spark_session = SparkSession.builder.appName("Music Recommender").getOrCreate()
        self.sp_con = self.spark_session.sparkContext
        self._load_data()
        self._make_model()

    def _load_data(self):
        self.artists = self.spark_session.read.csv('./data/lastfm_artist_list.csv', inferSchema=True, header=True)
        self.user_listens = self.spark_session.read.csv('./data/lastfm_user_scrobbles.csv', inferSchema=True, header=True)

    def _make_model(self):
        self.training_df, self.test_df = self.user_listens.randomSplit([.8, .2])

        # parameters for the model
        iterations = 12
        regularisation = 0.1
        rank = 8
        errors = []
        err = 0

        self.als_model = ALS(maxIter = iterations, rank = rank, regParam = regularisation,
        userCol='user_id', itemCol='artist_id', ratingCol='scrobbles', coldStartStrategy="drop")

        self.model = self.als_model.fit(self.training_df)

    def recommend_all(self, n_artists = 5):
        self.model.recommendForAllUsers(n_artists)

if __name__=="__main__":
    recommender = Recommender()
    recommender.recommend_all()
