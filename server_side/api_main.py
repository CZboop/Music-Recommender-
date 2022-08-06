from flask import Flask, render_template, request, url_for, redirect, flash, jsonify, session
from flask_restful import Resource, Api, reqparse
import pandas as pd
import ast
import psycopg2
import os
import secrets
import jwt
import datetime as dt
import re
from validator import PasswordValidator

# creating flask app and api based on/of it
app = Flask(__name__)
api = Api(app)

secret = secrets.token_urlsafe(32)
app.config['SECRET_KEY'] = secret

#TODO:
# validations
# log in on signup 
# rate x artists after signup (or login if none rated)
# recommend to user

#TODO:
# add validations for password security and username email not in use
# note what if submit and not all filled in?
@app.route('/sign-up/', methods=('GET', 'POST'))
def sign_up():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']

        if password != confirm_password:
            flash("Passwords do not match. Please try again.")

        # TODO: more validation here...
        else:
            password_validator = PasswordValidator(password)
            if not password_validator.is_valid():
                flash("Password should contain at least one character, one number, one special character and should be at least 8 characters long. Please try again.")
            else:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(f"INSERT INTO users (name, id, email, password) VALUES ('{username}', NULL, '{email}', crypt('{password}', gen_salt('bf', 8)));")
                conn.commit()
                cur.close()
                conn.close()

                return redirect(url_for('home'))

    return render_template('sign_up.html')

@app.route('/add-artist/', methods=('GET', 'POST'))
def add_artist():
    if request.method == 'POST':
        name = request.form['name']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"INSERT INTO artists (name) VALUES ('{name}');")
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('home'))

    return render_template('add_artist.html')

@app.route('/rate-artist/', methods=('GET', 'POST'))
def rate_artist():
    if request.method == 'POST':
        user_id = request.form['userid']
        artist_name = request.form['artist']
        artist_id = get_artist_id_from_name(artist_name)
        rating = request.form['rating']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"INSERT INTO user_ratings (user_id, artist_id, rating) VALUES ({user_id}, {artist_id}, {rating});")
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('home'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM artists;')
    artists = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('rate_artist.html', artists=artists)

def get_db_connection():
    conn = psycopg2.connect(host='localhost',
                            database='recommend',
                            user=os.environ['DB_USERNAME'],
                            password=os.environ['DB_PASSWORD'])
    return conn

@app.route('/')
def home():
    # TODO:
    # flesh out different homepage if logged in or not
    message = "Welcome!"
    if 'user' in session:
        token_decode = jwt.decode(session['user'], app.config['SECRET_KEY'], algorithms=['HS256'])
        username = token_decode['username']
        message = f"Welcome, {username}!"
    return render_template('home.html', welcome_message=message)

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM users WHERE name = '{username}' AND password = crypt('{password}', password);")
        user = cur.fetchall()
        cur.close()
        conn.close()
        if len(user) != 1:
            flash("Invalid login details")
        else:
            token = jwt.encode({'username': username, 'exp' : dt.datetime.utcnow() + dt.timedelta(hours=24)}, app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')
            json_token = jsonify({'token': token})
            session['user'] = token
            return redirect(url_for('home'))

    return render_template('login.html')

@app.route('/log-out', methods=['GET'])
def logout():
    del session['user']
    return render_template('log_out.html')

def get_user_from_name(name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM users WHERE name = '{name}';")
    user_query_res = cur.fetchall()
    cur.close()
    conn.close()
    return user_query_res[0][0]

def get_artist_id_from_name(name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT auto_id FROM artists WHERE name = '{name}';")
    artist_id = cur.fetchall()
    cur.close()
    conn.close()
    return artist_id[0][0]

if __name__=="__main__":
    app.run(debug=True)
