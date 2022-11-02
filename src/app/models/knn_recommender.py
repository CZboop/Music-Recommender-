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
        # print(listen_data[:5])
        rating_df = pd.DataFrame(listen_data, columns=['serial', 'user_id', 'artist_id', 'rating'])
        # print(rating_df.head)
        # prep data into user artist matrix as df
        df_listen_features = rating_df.pivot_table(index='artist_id', columns='user_id', values='rating').fillna(0)
        # as scipy sparse matrix
        # TODO: issue with the matrix need to properly assign index etc
        mat_listen_features = csr_matrix(df_listen_features)
        self.matrix = mat_listen_features
    
    def make_model(self):
        self.model = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=20, n_jobs=-1)

    def recommend(self, artist_id, n_recs):
        self.model.fit(self.matrix)
        distances, indices = self.model.kneighbors(self.matrix[artist_id], n_neighbors=n_recs+1)
        # get list of raw ids of recommendations - just putting into a nicely usable list
        raw_recommends = sorted(list(zip(indices.squeeze().tolist(), distances.squeeze().tolist())),
                key=lambda x: x[1])[:0:-1]

        # raw recommends will be artist id, distance tuple
        # may want to filter out some more eg no zero distance, not repeating the same artist
        recommended_ids = [i[0] for i in raw_recommends]

        return recommended_ids

if __name__=="__main__":
    knn_recommender = KNNRecommender()
    print(knn_recommender.recommend(8179, 10))