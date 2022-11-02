import os
import psycopg2
from starter_data_to_sql import CSVToSQL

# DB_USERNAME and DB_PASSWORD are environment variables will need to be set in terminal if in new environment
conn = psycopg2.connect(host="localhost", database="recommend",
        user=os.environ['DB_USERNAME'], password=os.environ['DB_PASSWORD'])

cur = conn.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS users (auto_id BIGSERIAL PRIMARY KEY NOT NULL, name TEXT, id INTEGER, email TEXT, password TEXT);')
cur.execute('CREATE TABLE IF NOT EXISTS artists (auto_id BIGSERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, id INTEGER);')
cur.execute('CREATE TABLE IF NOT EXISTS user_recommendations (auto_id BIGSERIAL PRIMARY KEY NOT NULL, user_id INTEGER NOT NULL, artist_id INTEGER NOT NULL);')
cur.execute('CREATE TABLE IF NOT EXISTS user_ratings (auto_id BIGSERIAL PRIMARY KEY NOT NULL, user_id INTEGER NOT NULL REFERENCES users(auto_id), artist_id INTEGER NOT NULL REFERENCES artists(auto_id), rating INTEGER);')
# may want to rethink or just keep in mind above for the joining table - using serial to reference the artists and users not necessarily id from original data

cur.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto;')

# add existing data to db if first time running
# creating psql friendly user data that can go straight into table, using class that does this
starter_data = CSVToSQL('./data/lastfm_user_scrobbles.csv', './data/lastfm_artist_list.csv')
user_starter_data , artist_starter_data , listen_starter_data = starter_data.create_all_sql()
# adding the data
cur.execute(user_starter_data)
cur.execute(artist_starter_data)
cur.execute(listen_starter_data)

conn.commit()

cur.close()
conn.close()
