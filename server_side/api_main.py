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
from validator import PasswordValidator, UsernameValidator, EmailValidator

# creating flask app and api based on/of it
app = Flask(__name__)
api = Api(app)

secret = secrets.token_urlsafe(32)
app.config['SECRET_KEY'] = secret

#TODO:
# rate x artists after signup (or login if none/ less than x rated) - 10 to start?
# recommend to user
# log out if token timed out
# add db table to store past recommendations and add a page to view these

@app.route('/sign-up/', methods=('GET', 'POST'))
def sign_up():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']

        if "" in [username, password, confirm_password, email]:
            flash("Please ensure all fields are filled in.")
        else:

            if password != confirm_password:
                flash("Passwords do not match. Please try again.")

            else:
                password_validator = PasswordValidator(password)
                if not password_validator.is_valid():
                    flash("Password should contain at least one character, one number, one special character and should be at least 8 characters long. Please try again.")
                else:
                    username_validator = UsernameValidator(username)
                    if username_validator.is_username_in_use():
                        flash("Username already in use. Please try again.")
                    else:
                        email_validator = EmailValidator(email)
                        if email_validator.is_email_in_use():
                            flash("Email already in use. Please try again.")
                        else:
                            if not email_validator.is_email_valid():
                                flash("Email is invalid. Please try again.")
                            else:
                                conn = get_db_connection()
                                cur = conn.cursor()
                                cur.execute(f"INSERT INTO users (name, id, email, password) VALUES ('{username}', NULL, '{email}', crypt('{password}', gen_salt('bf', 8)));")
                                conn.commit()
                                cur.close()
                                conn.close()

                                # auto login once sign up, making token and adding to session
                                token = create_token(username)
                                session['user'] = token

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
    logged_in = False
    if 'user' in session:
        logged_in = True
        if request.method == 'POST':
            username = get_username_from_token()
            user_id = get_user_from_name(username)
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
    return render_template('rate_artist.html', artists=artists, logged_in=logged_in)

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
    num_rated = 0
    message = "Welcome!"
    logged_in = False
    if 'user' in session:
        logged_in = True
        username = get_username_from_token()
        message = f"Welcome, {username}!"
        num_rated = len(get_artists_rated(get_user_from_name(username)))
    return render_template('home.html', welcome_message=message, num_rated=num_rated, logged_in=logged_in)

def get_username_from_token():
    token_decode = jwt.decode(session['user'], app.config['SECRET_KEY'], algorithms=['HS256'])
    username = token_decode['username']
    return username

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
            token = create_token(username)
            json_token = jsonify({'token': token})
            session['user'] = token
            return redirect(url_for('home'))

    return render_template('login.html')

def create_token(username):
    return jwt.encode({'username': username, 'exp' : dt.datetime.utcnow() + dt.timedelta(hours=24)}, app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

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

def get_artists_rated(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM user_ratings WHERE user_id = '{user_id}';")
    ratings = cur.fetchall()
    cur.close()
    conn.close()
    return ratings

if __name__=="__main__":
    app.run(debug=True)
