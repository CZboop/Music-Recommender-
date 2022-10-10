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
import time

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

        artists = get_all_artists()

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

    artists = get_all_artists()

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
    cur.execute(f"SELECT auto_id FROM artists WHERE name ILIKE '{name}';")
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
    if res.status_code == 200:
        get_auth_tokens(json.loads(res.text))
        get_spotify_data()
        add_spotify_ids()
        return render_template('logging_in.html', success = True)
    else:
        return render_template('logging_in.html', success = False)

def get_spotify_recently_played():
    # somewhat test to see what can get back from spotify api
    access_token = session['spotify_access_token']
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    # get_params = {}
    res = requests.get(url='https://api.spotify.com/v1/me/player/recently-played', headers= headers)
    # print("Recently played response: " + str(res.text))
    # TODO: handle at least two possible errors - empty response and user not added to dev dashboard?

def get_spotify_data():
    # TODO:
    # broader func to pull together other spotify related ones
    get_spotify_top()
    get_spotify_recently_played()

def get_spotify_top():
    # these can be rated higher than the generally followed
    # TODO: refresh token if needed before any request?
    access_token = session['spotify_access_token']
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    res = requests.get(url='https://api.spotify.com/v1/me/top/artists?limit=50', headers= headers)
    print(f"Top Artists: {[i['name'] for i in res.json()['items']]}")
    top_artists = [i['name'] for i in res.json()['items']]
    find_artist_in_spotify(top_artists[0])
    # TODO: all spotify need to be logged in to this web app? just via portal route etc? 
    # or anyway handle trying to add rating info when not logged in
    add_ratings_for_spotify_artists(top_artists)

def add_ratings_for_spotify_artists(artists, top=True, rating=10):
    # TODO: if else for rating depending on top or not
    for artist in artists:
        # print(artist)
        find_or_add_artist_from_spotify(artist)
        # TODO: switch to use the actual route with all the other logic
        artist_id = get_artist_id_from_name(artist.replace("'","''"))

        username = get_username_from_token()
        user_id = get_user_from_name(username)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"INSERT INTO user_ratings (user_id, artist_id, rating) VALUES ({user_id}, {artist_id}, {rating});")
        conn.commit()
        cur.close()
        conn.close()

# finding artist from spotify in our database
def find_or_add_artist_from_spotify(artist_name):
    current_artists = get_all_artists()
    if artist_name.lower() in [i[1].lower() for i in current_artists]:
        return True
    else:
        # add as a new artist 
        # TODO: switch to use the endpoint with authentication etc
        artist_escaped = artist_name.replace("'","''")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"INSERT INTO artists (name) VALUES ('{artist_escaped}');")
        conn.commit()
        cur.close()
        conn.close()
        return False

def get_all_artists():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM artists;')
    artists = cur.fetchall()
    cur.close()
    conn.close()
    
    return artists

# getting spotify artist id and info - eg for finding top songs/some songs from spotify
def find_artist_in_spotify(artist_name):
    # using search endpoint to find artist by name
    # note, this for 
    headers = {'Authorization': f'Bearer {session["spotify_access_token"]}', 'Content-Type': 'application/json'}
    
    res = requests.get(url=f'https://api.spotify.com/v1/search?type=artist&q={artist_name}', headers= headers)
    # print(f"Artist Search Response: {res.json()['artists']['items'][0]['id']}")
    # TODO: will be using this method to add for existing last fm dataset artists who may not all be on spotify, handle this
    if res.json()['artists']['items'][0]['name'].translate(str.maketrans('', '', string.punctuation)).strip().lower() != artist_name.translate(str.maketrans('', '', string.punctuation)).strip().lower():
        print(f'{artist_name} not found')
        print(res.json()['artists']['items'][0]['name'].translate(str.maketrans('', '', string.punctuation)).strip())
        return None
    return res.json()['artists']['items'][0]['id']

# getting all artist names from db to get ids for
def get_artist_names():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM artists;")
    artist_resultset = cur.fetchall()
    artist_names = [artist[0] for artist in artist_resultset]
    cur.close()
    conn.close()
    return artist_names

# getting spotify ids
def get_all_artist_ids(artist_names):
    # artist_ids = {}
    # [1095:]
    for index, name in enumerate(artist_names):
        print(index)
        if index % 20 == 15:
            time.sleep(60)
        try:
            id = find_artist_in_spotify(name)
            # artist_ids[name] = id if id != None else 'NULL'
            add_artist_id_to_db(id, name)
        except:
            print(f'Error with artist: {name}')
            # seems auth expiring, refresh...
            refresh = refresh_spotify_token()

    return artist_ids

def add_artist_id_to_db(artist_id, artist_name):
    # for key in artist_ids:
    artist_name = artist_name.replace("'","''")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"UPDATE artists SET spotify_id = '{artist_id}' WHERE name = '{artist_name}';")
    conn.commit()
    cur.close()
    conn.close()

def add_spotify_ids():
    ids = get_all_artist_ids(get_artist_names())
    # add_artist_id_to_db(ids)

def get_spotify_followed_artists():
    headers = {'Authorization': f'Bearer {session["spotify_access_token"]}', 'Content-Type': 'application/json'}
    
    res = requests.get(url='https://api.spotify.com/v1/me/following?type=artist&limit=50', headers= headers)

    followed_artists = [item['name'] for item in res.json()['artists']['items']]

    for artist in followed_artists:
        # TODO: skip if already rated
        find_or_add_artist_from_spotify(artist)
        # TODO: switch to use the actual route with all the other logic
        artist_id = get_artist_id_from_name(artist.replace("'","''"))

        username = get_username_from_token()
        user_id = get_user_from_name(username)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"INSERT INTO user_ratings (user_id, artist_id, rating) VALUES ({user_id}, {artist_id}, {rating});")
        conn.commit()
        cur.close()
        conn.close()

    return True

def get_top_songs_for_artist(artist_id):
    headers = {'Authorization': f'Bearer {session["spotify_access_token"]}', 'Content-Type': 'application/json'}
    
    res = requests.get(url=f'https://api.spotify.com/v1/artists/{artist_id}/top-tracks', headers= headers)

    top_tracks = [(track['name'], track['id']) for track in res.json()['tracks']]

    return top_tracks
    # TODO: turn into a little widget with some specific songs for the artist recommended

# TODO: ask user if want to save, and ask for user submitted name? with default tho
def save_recs_as_spotify_playlist(recs, name=f'recommenderPlaylist{str(date.today())}'):
    # 
    headers = {'Authorization': f'Bearer {session["spotify_access_token"]}', 'Content-Type': 'application/json'}
    post_params = {
        "name": name,
        "description": "Playlist generated from recommendations",
        "public": false
    }

    if not session['spotify_user_id']:
        get_user_spotify_id()

    res = requests.post(url=f'https://api.spotify.com/v1/users/{session['spotify_user_id']}/playlists', headers= headers, data= post_params)
    new_playlist_id = res.json()['id']

    #TODO: add tracks 
    # - get spotify id for each artist
    rec_spotify_ids = []
    for artist in recs:
        id = find_artist_in_spotify(artist)
        recs_spotify_ids.append(id)
    # - get top tracks from each artist id
    # - select a few out of those top tracks, not sure how many will be in response...
    tracks_for_playlist = []
    for id in rec_spotify_ids:
        tracks = get_top_songs_for_artist(id)
        track_selection = random.sample(tracks, random.randrange(1,4))
    # - add each selected track to the playlist (separate func)
    add_track_to_spotify_playlist(new_playlist_id, tracks_for_playlist)
    # TODO: explicitly handle artists not in spotify?

def add_track_to_spotify_playlist(playlist_id, track_ids):
    # can add up to 100/ a lot of tracks at once, better to limit requests but can do list with one if want...
    headers = {'Authorization': f'Bearer {session["spotify_access_token"]}', 'Content-Type': 'application/json'}
    post_params = {
        "uris" : [*track_ids]
    }

    res = requests.post(url=f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks', headers= headers, data= post_params)
    new_playlist_id = res.json()['id']

def get_user_spotify_id():
    headers = {'Authorization': f'Bearer {session["spotify_access_token"]}', 'Content-Type': 'application/json'}
    res = requests.get(url=f'https://api.spotify.com/v1/me', headers= headers)

    spotify_user_id = res.json()['id']
    session['spotify_user_id'] = spotify_user_id

    return spotify_user_id

def get_auth_tokens(response):
    session['spotify_access_token'] = response['access_token'] 
    session['spotify_refresh_token'] = response['refresh_token']

def refresh_spotify_token():
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    post_params = {'grant_type': 'refresh_token',"client_id": APP_ID,
        "client_secret": APP_SECRET}
    res = requests.post(url='https://accounts.spotify.com/api/token', headers= headers, data=post_params)
    
    new_access_token = res.json()['access_token']
    session['spotify_access_token'] = new_access_token
    
    # doesn't always send back a new refresh token?
    if 'refresh_token' in res.json():
        new_refresh_token = res.json()['refresh_token']
        session['spotify_refresh_token'] = new_refresh_token

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
