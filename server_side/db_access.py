import os
import psycopg2

# DB_USERNAME and DB_PASSWORD are environment variables will need to be set in terminal if in new environment
conn = psycopg2.connect(host="localhost", database="recommend",
        user=os.environ['DB_USERNAME'], password=os.environ['DB_PASSWORD'])

cur = conn.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS users (auto_id BIGSERIAL PRIMARY KEY NOT NULL, name TEXT, id INTEGER);')
cur.execute('CREATE TABLE IF NOT EXISTS artists (auto_id BIGSERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, id INTEGER);')
cur.execute('CREATE TABLE IF NOT EXISTS user_ratings (auto_id BIGSERIAL PRIMARY KEY NOT NULL, user_id INTEGER NOT NULL REFERENCES users(id), artist_id INTEGER NOT NULL REFERENCES artists(id), rating INTEGER);')

# TODO:
# add existing data to db if first time running
# add user creation method api and database
# add new users + ratings from api
# retrieve all data to then put into spark df
# artist creation method

conn.commit()

cur.close()
conn.close()
