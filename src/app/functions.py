from app import app
from functools import wraps
import datetime as dt
import psycopg2
import os
import jwt
from flask import jsonify, session, render_template

def authenticate(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        was_signed_in, is_valid = is_token_valid()
        # print(is_valid)
        if is_valid != True:
            if was_signed_in:
                return render_template('token_expired.html', was_signed_in = was_signed_in, logged_out = True), {"Refresh": "7; url=http://127.0.0.1:5000/log-out"}
            else:
                return render_template('token_expired.html', was_signed_in = was_signed_in), {"Refresh": "7; url=http://127.0.0.1:5000/login"}
        else:
            return func(*args, **kwargs)   
    return decorator

def get_highest_user_id():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT auto_id FROM users ORDER BY auto_id DESC LIMIT 1;')
    id = cur.fetchall()
    cur.close()
    conn.close()
    return int(id[0][0])

# note currently check for duplicates in method that adds, and the route is exposed, may want to remove and just have as func
def add_new_artist(name):
    name_escaped = name.replace("'", "''")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"INSERT INTO artists (name) VALUES ('{name_escaped}');")
    conn.commit()
    cur.close()
    conn.close()

def rating_artist(artist_name, user_id, rating):
    artist_id = get_artist_id_from_name(artist_name)
    
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

    return updated

def get_db_connection():
    conn = psycopg2.connect(host='localhost',
                            database='recommend',
                            user=os.environ['DB_USERNAME'],
                            password=os.environ['DB_PASSWORD'])
    return conn

def get_username_from_token():
    token_decode = jwt.decode(session['user'], app.config['SECRET_KEY'], algorithms=['HS256'])
    username = token_decode['username']
    return username

def store_token_user_info(token):
    json_token = jsonify({'token': token})
    session['user'] = token
    session['logged_in'] = True

def create_token(username):
    expiry_datetime = dt.datetime.utcnow() + dt.timedelta(hours=24)
    return jwt.encode({'username': username, 'expires' : expiry_datetime.strftime("%m/%d/%Y, %H:%M:%S")}, app.config['SECRET_KEY'], algorithm='HS256').decode('UTF-8')

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

def get_user_from_name(name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM users WHERE name = '{name}';")
    user_query_res = cur.fetchall()
    cur.close()
    conn.close()
    return user_query_res[0][0]

def get_artist_id_from_name(name):
    name = name.replace("'", "''")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT auto_id FROM artists WHERE name ILIKE '{name}';")
    artist_id = cur.fetchall()
    cur.close()
    conn.close()
    return artist_id[0][0]

def get_artists_rated(user_id, min_rating = None):
    conn = get_db_connection()
    cur = conn.cursor()
    if not min_rating:
        cur.execute(f"SELECT * FROM user_ratings WHERE user_id = '{user_id}';")
    else:
        cur.execute(f"SELECT * FROM user_ratings WHERE user_id = '{user_id}' AND rating >= min_rating;")
    ratings = cur.fetchall()
    cur.close()
    conn.close()
    return ratings

def get_spotify_recently_played():
    # somewhat test to see what can get back from spotify api
    access_token = session['spotify_access_token']
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    res = requests.get(url='https://api.spotify.com/v1/me/player/recently-played', headers= headers)
    # TODO: handle at least two possible errors - empty response and user not added to dev dashboard? (flash messages?)

def get_spotify_top():
    # these can be rated higher than the generally followed
    # TODO: refresh token if needed before any request?
    access_token = session['spotify_access_token']
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    res = requests.get(url='https://api.spotify.com/v1/me/top/artists?limit=50', headers= headers)
    # print(f"Top Artists: {[i['name'] for i in res.json()['items']]}")
    print("Got Top Artists")
    top_artists = [i['name'] for i in res.json()['items']]
    find_artist_in_spotify(top_artists[0])
    # TODO: all spotify need to be logged in to this web app? just via portal route etc? 
    # or anyway handle trying to add rating info when not logged in
    add_ratings_for_spotify_artists(top_artists)

@authenticate
def add_ratings_for_spotify_artists(artists, top=True, rating=10):
    # TODO: if else for rating depending on top or not
    if 'user' in session:
        for artist in artists:
            # print(artist)
            find_or_add_artist_from_spotify(artist)
            rating_artist(artist, get_user_from_name(get_username_from_token()), rating)
            print(f"Rated: {artist}")
        return True
    return False

# finding artist from spotify in our database
def find_or_add_artist_from_spotify(artist_name):
    current_artists = get_all_artists()
    # print(current_artists[0])
    current_artists = [i[1] for i in current_artists]
    current_artists = [i.lower() for i in current_artists]
    
    if artist_name.lower() in current_artists:
        return True
    else:
        # add as a new artist 
        add_new_artist(artist_name)
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
    # print(res.json())
    try:
        if res.json()['artists']['items'][0]['name'].translate(str.maketrans('', '', string.punctuation)).strip().lower() != artist_name.translate(str.maketrans('', '', string.punctuation)).strip().lower():
            print(f'{artist_name} not found')
            print(res.json()['artists']['items'][0]['name'].translate(str.maketrans('', '', string.punctuation)).strip())
            return None
    except:
        refresh_spotify_token()
        # find_artist_in_spotify(artist_name)
    try:
        return res.json()['artists']['items'][0]['id']
    except:
        print(res.json())
        return None

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
    artist_ids = {} #**COMMENT OUT/REMOVE
    # [1095:]
    for index, name in enumerate(artist_names[1095:]):
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
            # seems other errors can occur
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
    # print(str(res.json()))

    followed_artists = [item['name'] for item in res.json()['artists']['items']]
    print(followed_artists[0])

    artist_ids = []
    for artist in followed_artists:
        # TODO: skip if already rated
        find_or_add_artist_from_spotify(artist)
        # TODO: switch to use the actual route with all the other logic

    add_ratings_for_spotify_artists(followed_artists, top= False, rating= 5)

    return True

def get_top_songs_for_artist(artist_id):
    headers = {'Authorization': f'Bearer {session["spotify_access_token"]}', 'Content-Type': 'application/json'}
    
    res = requests.get(url=f'https://api.spotify.com/v1/artists/{artist_id}/top-tracks?market=GB', headers= headers)
    # print(res.json())

    top_tracks = [(str(track['name']), str(track['id'])) for track in res.json()['tracks']]
    print(top_tracks)
    return top_tracks
    # TODO: turn into a little widget with some specific songs for the artist recommended

# TODO: ask user if want to save, and ask for user submitted name? with default tho
def save_recs_as_spotify_playlist(recs, tracks, name=f'recommenderPlaylist{str(dt.date.today())}'):
    # 
    print(f'LENGTH OF PLAYLIST SHOULD BE::::::::{len(tracks)}')
    headers = {'Authorization': f'Bearer {session["spotify_access_token"]}', 'Content-Type': 'application/json'}
    post_params = {
        "name": name,
        "description": "Playlist generated from recommendations",
        "public": "false"
    }

    if not session['spotify_user_id']:
        get_user_spotify_id()
    spotify_user_id = session['spotify_user_id']
    res = requests.post(url=f'https://api.spotify.com/v1/users/{spotify_user_id}/playlists', headers= headers, data= json.dumps(post_params))
    print(res.json())
    new_playlist_id = res.json()['id']

    #TODO: add tracks 
    # - get spotify id for each artist
    # rec_spotify_ids = []
    # for artist in recs:
    #     id = find_artist_in_spotify(artist)
    #     rec_spotify_ids.append(id)
    # # - get top tracks from each artist id
    # # - select a few out of those top tracks, not sure how many will be in response...
    # tracks_for_playlist = []
    # for id in rec_spotify_ids:
    #     tracks = get_top_songs_for_artist(id)
    #     track_selection = random.sample(tracks, random.randrange(1,4))
    # - add each selected track to the playlist (separate func)
    add_tracks_to_spotify_playlist(new_playlist_id, tracks)
    # TODO: explicitly handle artists not in spotify?

def add_tracks_to_spotify_playlist(playlist_id, track_ids):
    # can add up to 100/ a lot of tracks at once, better to limit requests but can do list with one if want...
    uris = [f"spotify:track:{i[1]}" for i in track_ids]
    headers = {'Authorization': f'Bearer {session["spotify_access_token"]}', 'Content-Type': 'application/json'}
    post_params = {
        "uris" : uris
    }

    res = requests.post(url=f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks', headers= headers, data= json.dumps(post_params))
    # new_playlist_id = res.json()['id']
    print(res.json())
    print('added to playlist?')

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
    post_params = {'grant_type': 'refresh_token','refresh_token': session['spotify_refresh_token'], 
        'client_id': APP_ID, 'client_secret': APP_SECRET}
    res = requests.post(url='https://accounts.spotify.com/api/token', headers= headers, data=post_params)
    
    # print(res.json())
    new_access_token = res.json()['access_token']
    session['spotify_access_token'] = new_access_token
    
    # doesn't always send back a new refresh token?
    if 'refresh_token' in res.json():
        new_refresh_token = res.json()['refresh_token']
        session['spotify_refresh_token'] = new_refresh_token

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