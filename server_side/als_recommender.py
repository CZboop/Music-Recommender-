import pandas as pd
import numpy as np
import random
import math
from fuzzywuzzy import fuzz
import time
from sqlalchemy import create_engine
import psycopg2
import os
import sys

from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import col, lower
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.recommendation import ALS, ALSModel
from pyspark.ml.tuning import ParamGridBuilder
from pyspark.ml.pipeline import PipelineModel

class Recommender:
    def __init__(self, iterations = 12, regularisation = 0.1, rank = 8):
        self.spark_session = SparkSession.builder.master("local").appName("Music Recommender").getOrCreate()
        self.sp_con = self.spark_session.sparkContext
        self._load_data()
        self._make_model(iterations, regularisation, rank)
        self._map_artist_id()

    def _load_data(self):
        conn = psycopg2.connect(host='localhost',
                                database='recommend',
                                user=os.environ['DB_USERNAME'],
                                password=os.environ['DB_PASSWORD'])
        cur = conn.cursor()
        cur.execute('SELECT * FROM user_ratings;')
        listen_data = cur.fetchall()
        cur.close()
        conn.close()

        self.user_listens = self.spark_session.createDataFrame(listen_data)

    # may adjust parameters/make dynamic but these seem to be decent default
    def _make_model(self, iterations = 12, regularisation = 0.1, rank = 8):
        self.model = self.load_model()


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
        subset = self.user_listens.filter(self.user_listens._3 == user_id)
        # subset.select("user_id").limit(1).show()
        return subset

    def load_model(self, path='trained_model'):
        trained_model = ALSModel.load(path)
        return trained_model
