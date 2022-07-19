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
        self._map_artist_id()

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

    def _map_artist_id(self):
        artist_df = pd.read_csv('./data/lastfm_artist_list.csv')
        self.artist_id_dict = {}
        # in df it's artist_id and artist_name
        for i in range(1, len(artist_df.index) + 1):
            self.artist_id_dict[i] = str(artist_df.loc[artist_df['artist_id'] == i]['artist_name'].values[0])
        return self.artist_id_dict

    def recommend_all(self, n_artists = 5):
        return self.model.recommendForAllUsers(n_artists)

    def match_artist(self, artist):
        artist_match = {}
        for i, v in self.artist_id_dict.items():
        # key = artist name
        # value = [match ratio, artist id]
            artist_match[v] = [fuzz.ratio(artist.lower(), v.lower()), i]
        artist_match = sorted(artist_match.items(), key=lambda item: item[1], reverse = True)
        # returning best match, could later do some more to evaluate based on match level
        # match returned format will be ("Artist Name", [confidence/match ratio, artist_id])
        return artist_match[0]

    def recommend_subset(self, subset, n_artists):
        recommends = self.model.recommendForUserSubset(subset, n_artists)
        return recommends

    def single_user_subset(self, user_id):
        subset = self.user_listens.filter(self.user_listens.user_id == user_id)
        # subset.select("user_id").limit(1).show()
        return subset

if __name__=="__main__":
    recommender = Recommender()
    print(recommender.recommend_all())
    print(recommender.match_artist("qtipp"))
    recommender.recommend_subset(recommender.single_user_subset(3), 10).show()
