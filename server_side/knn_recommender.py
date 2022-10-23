import math
from sklearn.neighbors import NearestNeighbors
from scipy.sparse import csr_matrix
import pandas as pd
import numpy as np
import psycopg2
import os

class KNNRecommender:
    def __init__(self):
        self.make_model()
        self.read_data()

    def read_data(self):
        # into df from db
        conn = psycopg2.connect(host='localhost',
                                database='recommend',
                                user=os.environ['DB_USERNAME'],
                                password=os.environ['DB_PASSWORD'])
        cur = conn.cursor()
        cur.execute('SELECT * FROM user_ratings;')
        listen_data = cur.fetchall()
        cur.close()
        conn.close()

        # prep data into user artist matrix as df
        # df_listen_features = pd.read_sql(listen_data).pivot_table(index='artist_id', columns='user_id', values='scrobbles').fillna(0)
        # as scipy sparse matrix
        mat_listen_features = csr_matrix(listen_data)
        self.matrix = mat_listen_features
    
    def make_model(self):
        self.model = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=25, n_jobs=-1)

    def recommend(self, artist_id, n_recs):
        self.model.fit(self.matrix)
        # artist_id = match_artist(fav_artist)[1][1]
        distances, indices = self.model.kneighbors(self.matrix[artist_id], n_neighbors=n_recs+1)
        # get list of raw ids of recommendations - just putting into a nicely usable list
        raw_recommends = sorted(list(zip(indices.squeeze().tolist(), distances.squeeze().tolist())),
                key=lambda x: x[1])[:0:-1]

        # return recommendation (artist_id, distance)
        return raw_recommends

if __name__=="__main__":
    knn_recommender = KNNRecommender()
    print(knn_recommender.recommend(9817, 10))