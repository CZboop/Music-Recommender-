# making, tuning and saving model
import numpy as np
from sqlalchemy import create_engine
import psycopg2
import sys
import os

from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import col, lower
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.recommendation import ALS
from pyspark.ml.tuning import ParamGridBuilder

class Model:
    def __init__(self, iterations = 12, regularisation = 0.1, rank = 8):
        # needs hadoop path as env variable can set here or in terminal etc.
        # also requires .dll in same bin folder, .dll in windows system32 and may need more setup if setting up on a new machine
        os.environ['HADOOP_HOME'] = "C:/winutils"
        sys.path.append("C:/winutils/bin")

        self.spark_session = SparkSession.builder.master("local").appName("Music Recommender").getOrCreate()
        self.sp_con = self.spark_session.sparkContext
        self._load_data()
        self._make_and_train_model(iterations, regularisation, rank)

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
        self.user_listens = self.spark_session.createDataFrame(listen_data).repartition(200)

    def _make_and_train_model(self, iterations = 12, regularisation = 0.1, rank = 8):
        self.training_df, self.test_df = self.user_listens.randomSplit([.8, .2])

        errors = []
        err = 0

        self.als_model = ALS(maxIter = iterations, rank = rank, regParam = regularisation,
        userCol='_2', itemCol='_3', ratingCol='_4', coldStartStrategy="drop")

        self.model = self.als_model.fit(self.training_df)

    def save_model(self, dir_name = 'trained_model'):
        # saving trained model to the folder specified in args
        self.model.write().overwrite().save(f"{dir_name}")

if __name__=="__main__":
    model = Model()
    model.save_model()
