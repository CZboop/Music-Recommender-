import os
import psycopg2

# DB_USERNAME and DB_PASSWORD are environment variables will need to be set in terminal if in new environment
conn = psycopg2.connect(host="localhost", database="recommend",
        user=os.environ['DB_USERNAME'], password=os.environ['DB_PASSWORD'])

cur = conn.cursor()

# TODO:
# add existing data to db if first time running
# create user db
# add user creation method api and database
# add new users + ratings from api
# retrieve all data to then put into spark df
