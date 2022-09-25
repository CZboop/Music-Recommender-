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
    def __init__(self, model_path='trained_model'):
        self.spark_session = SparkSession.builder.master("local").appName("Music Recommender").getOrCreate()
        self.sp_con = self.spark_session.sparkContext
        self.model_path = model_path
        self._load_data()
        self._make_model()

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

    # will be loading in existing model, made by running make_model.py
    def _make_model(self):
        self.model = self.load_model()

    def recommend_all(self, n_artists = 5):
        return self.model.recommendForAllUsers(n_artists)

    def recommend_subset(self, subset, n_artists):
        recommends = self.model.recommendForUserSubset(subset, n_artists)
        return recommends

    def single_user_subset(self, user_id):
        subset = self.user_listens.filter(self.user_listens._3 == user_id)
        # subset.select("user_id").limit(1).show()
        return subset

    def load_model(self):
        trained_model = ALSModel.load(self.model_path)
        return trained_model
