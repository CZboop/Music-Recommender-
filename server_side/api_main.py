from flask import Flask, render_template
from flask_restful import Resource, Api, reqparse
import pandas as pd
import ast
import psycopg2
import os

# creating flask app and api based on/of it
app = Flask(__name__)
api = Api(app)

class Users(Resource):
    def get(self):
        return {'User Id': 'Username'}, 200
    # for post request taking in path variables after /resource-path?arg1=value1&arg2=value2
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', required=True, type=str, location='values')
        args = parser.parse_args()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"INSERT INTO users (name, id) VALUES ('{args['name']}', NULL);")
        conn.commit()
        cur.close()
        conn.close()
        return {'name': args['name']}, 200

class Artists(Resource):
    def get(self):
        return {'Artist Id': 'Artist Name'}, 200
    # for post request taking in path variables after /resource-path?arg1=value1&arg2=value2
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', required=True, type=int, location='values')
        parser.add_argument('name', required=True, type=str, location='values')
        args = parser.parse_args()
        return {'id': args['id'], 'name': args['name']}, 200

def get_db_connection():
    conn = psycopg2.connect(host='localhost',
                            database='recommend',
                            user=os.environ['DB_USERNAME'],
                            password=os.environ['DB_PASSWORD'])
    return conn


@app.route('/')
def home():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM artists;')
    artists = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('home.html', artists=artists)

# mapping classes to paths in api
api.add_resource(Users, '/users')
api.add_resource(Artists, '/artists')

if __name__=="__main__":
    app.run(debug=True)
