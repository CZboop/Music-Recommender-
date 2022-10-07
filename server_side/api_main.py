from flask import Flask, render_template, request, url_for, redirect, flash, jsonify, session, render_template_string, make_response
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
from als_recommender import Recommender
import json
import urllib.parse
import random
import string
import requests
import base64
from config_secrets import APP_ID, APP_SECRET

# creating flask app and api based on/of it
app = Flask(__name__)
api = Api(app)

secret = secrets.token_urlsafe(32)
app.config['SECRET_KEY'] = secret

@app.route('/sign-up/', methods=('GET', 'POST'))
def sign_up():
    #TODO: add a message/ different page for any logged in user who gets here
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
                                user_id = get_highest_user_id() + 1

                                conn = get_db_connection()
                                cur = conn.cursor()
                                cur.execute(f"INSERT INTO users (name, id, email, password) VALUES ('{username}', {user_id}, '{email}', crypt('{password}', gen_salt('bf', 8)));")
                                conn.commit()
                                cur.close()
                                conn.close()

                                # auto login once sign up, making token and adding to session
                                token = create_token(username)
                                session['user'] = token

                                return redirect(url_for('welcome', username = username))

    return render_template('sign_up.html')

def get_highest_user_id():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT auto_id FROM users ORDER BY auto_id DESC LIMIT 1;')
    id = cur.fetchall()
    cur.close()
    conn.close()
    return int(id[0][0])

@app.route('/welcome', methods=('GET', 'POST'))
def welcome():
    was_signed_in, is_valid = is_token_valid()

    if not is_valid:
        if was_signed_in:
            return render_template('token_expired.html', was_signed_in = was_signed_in), {"Refresh": "7; url=http://127.0.0.1:5000/log-out"}
        else:
            return render_template('token_expired.html', was_signed_in = was_signed_in), {"Refresh": "7; url=http://127.0.0.1:5000/login"}

    logged_in = False
    if 'user' in session:
        logged_in = True
        username = get_username_from_token()
        user_id = get_user_from_name(username)
        if request.method == 'POST':
            artist_name = request.form['artist']
            artist_id = get_artist_id_from_name(artist_name)
            rating = request.form['rating']

            if not is_token_valid():
                return render_template('token_expired.html'), {"Refresh": "7; url=http://127.0.0.1:5000/log-out"}

            updated = False
            if is_artist_rated(artist_name) == True:
                # updating if user has already rated artist before
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(f"UPDATE user_ratings SET user_id = {user_id},  artist_id = {artist_id}, rating = {rating} WHERE user_id = {user_id} and artist_id = {artist_id};")
                conn.commit()
                cur.close()
                conn.close()
                updated = True

            else:
                # else adding in new rating row
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(f"INSERT INTO user_ratings (user_id, artist_id, rating) VALUES ({user_id}, {artist_id}, {rating});")
                conn.commit()
                cur.close()
                conn.close()
            
            # return jsonify({'numRated' : len(get_artists_rated(user_id))})

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM artists;')
        artists = cur.fetchall()
        cur.close()
        conn.close()

        num_rated = len(get_artists_rated(user_id))

        return render_template('welcome.html', username = request.args.get('username'), artists = artists, num_rated = num_rated)

@app.route('/success')
def success():
    return render_template('rating_success.html', artist = request.args.get('artist'), rating = request.args.get('rating'), updated = str(request.args.get('updated')))

@app.route('/add-artist/', methods=('GET', 'POST'))
def add_artist():
    was_signed_in, is_valid = is_token_valid()

    if not is_valid:
        if was_signed_in:
            return render_template('token_expired.html', was_signed_in = was_signed_in), {"Refresh": "7; url=http://127.0.0.1:5000/log-out"}
        else:
            return render_template('token_expired.html', was_signed_in = was_signed_in), {"Refresh": "7; url=http://127.0.0.1:5000/login"}

    if request.method == 'POST':
        name = request.form['name']

        if not is_token_valid():
            return render_template('token_expired.html'), {"Refresh": "7; url=http://127.0.0.1:5000/log-out"}

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
    was_signed_in, is_valid = is_token_valid()

    if not is_valid:
        if was_signed_in:
            return render_template('token_expired.html', was_signed_in = was_signed_in), {"Refresh": "7; url=http://127.0.0.1:5000/log-out"}
        else:
            return render_template('token_expired.html', was_signed_in = was_signed_in), {"Refresh": "7; url=http://127.0.0.1:5000/login"}

    logged_in = False
    if 'user' in session:
        logged_in = True
        if request.method == 'POST':
            username = get_username_from_token()
            user_id = get_user_from_name(username)
            artist_name = request.form['artist']
            artist_id = get_artist_id_from_name(artist_name)
            rating = request.form['rating']

            if not is_token_valid():
                return render_template('token_expired.html'), {"Refresh": "7; url=http://127.0.0.1:5000/log-out"}

            updated = False
            if is_artist_rated(artist_name) == True:
                # updating if user has already rated artist before
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(f"UPDATE user_ratings SET user_id = {user_id},  artist_id = {artist_id}, rating = {rating} WHERE user_id = {user_id} and artist_id = {artist_id};")
                conn.commit()
                cur.close()
                conn.close()
                updated = True

            else:
                # else adding in new rating row
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(f"INSERT INTO user_ratings (user_id, artist_id, rating) VALUES ({user_id}, {artist_id}, {rating});")
                conn.commit()
                cur.close()
                conn.close()

            return redirect(url_for('success', artist = artist_name, rating = rating, updated = updated))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM artists;')
    artists = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('rate_artist.html', artists=artists, logged_in=logged_in)

# checking if user already rated an artist to update rather than just re-add rating
def is_artist_rated(artist_name):
    if 'user' in session:
        username = get_username_from_token()
        user_id = get_user_from_name(username)
        artist_id = get_artist_id_from_name(artist_name)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM user_ratings WHERE artist_id = {artist_id} AND user_id = {user_id};")
        result = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()

        return False if not result else True

    else:
        return None

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
    username = None
    if 'user' in session:
        logged_in = True
        username = get_username_from_token()
        message = f"Welcome, {username}!"
        num_rated = len(get_artists_rated(get_user_from_name(username)))
    return render_template('home.html', welcome_message=message, num_rated=num_rated, logged_in=logged_in, username=username)

def get_username_from_token():
    # TODO: check user exists in session
    token_decode = jwt.decode(session['user'], app.config['SECRET_KEY'], algorithms=['HS256'])
    username = token_decode['username']
    return username

@app.route('/login', methods=('GET', 'POST'))
def login():
    #TODO: add treatment for user getting here while already logged in
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
            session['logged_in'] = True
            return redirect(url_for('home'))

    return render_template('login.html')

def create_token(username):
    expiry_datetime = dt.datetime.utcnow() + dt.timedelta(hours=24)
    return jwt.encode({'username': username, 'expires' : expiry_datetime.strftime("%m/%d/%Y, %H:%M:%S")}, app.config['SECRET_KEY'], algorithm='HS256').decode('UTF-8')

@app.route('/log-out', methods=['GET'])
def logout():
    if 'user' in session:
        del session['user']
        return render_template('log_out.html', logged_out = True)
    else:
        return render_template('log_out.html', logged_out = False)

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

@app.route('/recommendations', methods=['POST', 'GET'])
def recommendations():
    was_signed_in, is_valid = is_token_valid()

    if not is_valid:
        if was_signed_in:
            return render_template('token_expired.html', was_signed_in = was_signed_in), {"Refresh": "7; url=http://127.0.0.1:5000/log-out"}
        else:
            return render_template('token_expired.html', was_signed_in = was_signed_in), {"Refresh": "7; url=http://127.0.0.1:5000/login"}

    logged_in = False
    recs = None

    if 'user' in session:
        logged_in = True
        username = get_username_from_token()
        message = f"Welcome, {username}!"
        userid = get_user_from_name(username)
        session['username'] = username

        # returning if not rated many artists with just a message to rate more
        num_rated = len(get_artists_rated(userid))
        if num_rated < 10:
            can_recommend = False
            rec_names = None
            past_recs = None
            return render_template('recommendations.html', recs= rec_names, logged_in= logged_in,
            past_recs= past_recs, can_recommend = can_recommend, num_rated = num_rated)

        can_recommend = False
        rec_names = None
        past_recs = None

        return render_template('recommendations.html', recs= rec_names, logged_in= logged_in,
        past_recs= past_recs, can_recommend = can_recommend, num_rated = num_rated)

    else:
        return render_template('token_expired.html'), {"Refresh": "7; url=http://127.0.0.1:5000/log-out"}

@app.route('/update-rated', methods=['POST'])
def update_rated():
    username = get_username_from_token()
    user_id = get_user_from_name(username)
    return jsonify({'num_rated': len(get_artists_rated(user_id))})#

# portal to log in via spotify
@app.route('/portal', methods=['GET', 'POST'])
def portal():
    query_data = {
        'client_id' : APP_ID,
        'response_type' : 'code',
        'redirect_uri' : 'http://127.0.0.1:5000/logging-in',
        'scope' : """user-library-modify user-library-read user-top-read user-read-recently-played playlist-read-private
        playlist-read-collaborative playlist-modify-private playlist-modify-public""",
        'state_key' : ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))

    }

    auth_url = 'https://accounts.spotify.com/authorize?'

    query_params = 'response_type=code&client_id=' + query_data['client_id'] + '&redirect_uri=' + query_data['redirect_uri'] + '&scope=' + query_data['scope'] + '&state=' + query_data['state_key']
    response = make_response(redirect(auth_url + query_params))
    print(response)
    return response
    # return render_template('portal.html')

@app.route('/logging-in')
def logging_in():
    code = request.args.get("code")
    # TODO: handle user rejecting access, will have different response in query params (error instead of code?)
    # TODO: check state in response is the same as what we sent and reject if doesn't match
    encoded = base64.urlsafe_b64encode((APP_ID + ':' + APP_SECRET).encode())

    authorization = f'Authorization: Basic {encoded}'
    # ^base64 encoded combo of client id and secret format: Authorization: Basic <base64 encoded client_id:client_secret>
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    post_params = {'grant_type': 'authorization_code', 'code': code, 'redirect_uri': 'http://127.0.0.1:5000/logging-in',"client_id": APP_ID,
        "client_secret": APP_SECRET}
    res = requests.post(url='https://accounts.spotify.com/api/token', headers= headers, data=post_params)
    print('response: ' + str(res.json()))
    # above seems to be working BUT
    # TODO: actually use the returned access token and authorize etc.

def get_auth():
    pass 
    # TODO: get access_token, refresh_token from spotify response, store 

@app.route('/recommend', methods=['POST'])
def recommend():
    # TODO: potential edge case where token expires?
    username = get_username_from_token()
    userid = get_user_from_name(username)

    # returning if not rated many artists with just a message to rate more
    num_rated = len(get_artists_rated(userid))

    recommender = Recommender()
    recs = recommender.recommend_subset(recommender.single_user_subset(userid), 15)
    recs_ = [str(i[0]) for i in recs.select('recommendations').collect()]

    # getting just artist id using many string slices
    rec_artist_ids = [int(i.split("=")[1].split(", ")[0]) for i in recs_[0].split("Row(")[1:] ]

    past_recs = get_past_recs(userid)
    past_rec_names = [get_artists_name_from_id(i[0]) for i in past_recs]
    past_rec_ids = [i[0] for i in past_recs]

    # filtering out artists that have already been recommended before adding to db
    new_artist_ids = [i for i in rec_artist_ids if i not in past_rec_ids]
    new_artist_links = [get_artist_link_from_id(i) for i in new_artist_ids]

    past_rec_links = [get_artist_link_from_id(i) for i in past_rec_ids]

    store_recommendation(userid , new_artist_ids)

    rec_names = [get_artists_name_from_id(i) for i in new_artist_ids]

    rec_name_links = {rec_names[i]: new_artist_links[i] for i in range(len(rec_names))}
    past_rec_links = {past_rec_names[i]: past_rec_links[i] for i in range(len(past_rec_links))}

    return jsonify({'recs': rec_name_links, 'past_recs': past_rec_links})

def is_token_valid():
    # returns two booleans, first is whether user had ever signed in, second is whether valid
    if 'user' in session:
        token_decode = jwt.decode(session['user'], app.config['SECRET_KEY'], algorithms=['HS256'])
        expires = token_decode['expires']
        expires_datetime = dt.datetime.strptime(expires, "%m/%d/%Y, %H:%M:%S")
        return True, expires_datetime > dt.datetime.utcnow()
    else:
        return False, False

def get_past_recs(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT artist_id FROM user_recommendations WHERE user_id = '{user_id}';")
    recommendations = cur.fetchall()
    cur.close()
    conn.close()
    return recommendations

def store_recommendation(user_id, artist_ids):
    conn = get_db_connection()
    cur = conn.cursor()
    for artist_id in artist_ids:
        cur.execute(f"INSERT INTO user_recommendations (user_id, artist_id) VALUES ({user_id}, {artist_id});")
        conn.commit()
    cur.close()
    conn.close()

def get_artists_name_from_id(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT name FROM artists WHERE id = '{id}';")
    artist = cur.fetchall()
    cur.close()
    conn.close()
    return artist[0][0]

def get_artist_link_from_id(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT lastfm_link FROM artists WHERE id = '{id}';")
    artist_link = cur.fetchall()
    cur.close()
    conn.close()
    return artist_link[0][0]

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html')

if __name__=="__main__":
    app.run(debug=True)
