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
from pyspark.ml.tuning import ParamGridBuilder, CrossValidator

class Model:
    def __init__(self):
        # needs hadoop path as env variable can set here or in terminal etc.
        # also requires .dll in same bin folder, .dll in windows system32 and may need more setup if setting up on a new machine
        os.environ['HADOOP_HOME'] = "C:/winutils"
        sys.path.append("C:/winutils/bin")

        self.spark_session = SparkSession.builder.master("local").appName("Music Recommender").getOrCreate()
        self.sp_con = self.spark_session.sparkContext
        self._load_data()
        self._make_base_model()

        params = self._tune()

        rank, max_iter, reg_param = params[0], params[1], params[2]

        self._make_and_train_model(max_iter, reg_param, rank)

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

    # setting up a model for tuning against
    def _make_base_model(self):
        self.training_df, self.test_df = self.user_listens.randomSplit([.8, .2], seed = 42)

        errors = []
        err = 0

        self.als_model = ALS(userCol='_2', itemCol='_3', ratingCol='_4', coldStartStrategy="drop")

    def _make_and_train_model(self, iterations = 12, regularisation = 0.1, rank = 8):
        errors = []
        err = 0

        self.als_model = ALS(maxIter = iterations, rank = rank, regParam = regularisation,
        userCol='_2', itemCol='_3', ratingCol='_4', coldStartStrategy="drop")

        #final model using all data, rather than train test split
        self.model = self.als_model.fit(self.user_listens)

    # tuning and evaluating model with different hyperparameters to get the best/ a better version of it
    #
    def _tune(self):
        param_grid = ParamGridBuilder()\
            .addGrid(self.als_model.rank, [i for i in range(5, 16)])\
            .addGrid(self.als_model.maxIter, [i for i in range(6, 24, 4)])\
            .addGrid(self.als_model.regParam, [0.05, 0.1, 0.15, 0.3, 0.4]).build()
        eval = RegressionEvaluator(metricName = "rmse", labelCol = '_4', predictionCol = 'prediction')
        cross_validator = CrossValidator(estimator = self.als_model, estimatorParamMaps = param_grid, evaluator = eval, numFolds = 5)
        print(cross_validator)
        models = cross_validator.fit(self.training_df)
        best_model = models.bestModel
        print(best_model)
        # extracting hyperparameters from the best model
        best_rank, best_maxIter, best_regParam = best_model.getRank(), best_model.getMaxIter(), best_model.getRegParam()

        return [best_rank, best_maxIter, best_regParam]

    def save_model(self, dir_name = 'trained_model'):
        # saving trained model to the folder specified in args
        self.model.write().overwrite().save(f"{dir_name}")

if __name__=="__main__":
    model = Model()
    # model._tune()
    model.save_model()
