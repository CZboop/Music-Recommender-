from app import app
from flask import render_template, request, url_for, redirect, flash, jsonify, session, render_template_string, make_response
from flask_restful import Resource, Api, reqparse
from app.functions import authenticate, get_db_connection, create_token, store_token_user_info, get_username_from_token, get_artists_rated, get_user_from_name, get_all_artists, get_all_artist_ids, rating_artist, get_past_recs
from app.models import Recommender, KNNRecommender, Model

@app.route('/')
def home():
    # TODO:
    # flesh out homepage keeping difference for logged in/out
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

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.route('/rate-artist', methods=('GET', 'POST'))
@authenticate
def rate_artist():
    logged_in = False
    if 'user' in session:
        logged_in = True
        if request.method == 'POST':

            username = get_username_from_token()
            user_id = get_user_from_name(username)
            artist_name = request.form['artist']
            rating = request.form['rating']

            updated = rating_artist(artist_name, user_id, rating)

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

@app.route('/recommendations', methods=['POST', 'GET'])
@authenticate
def recommendations():    
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
            store_token_user_info(token)
            return redirect(url_for('home'))

    return render_template('login.html')

@app.route('/log-out', methods=['GET'])
def logout():
    if 'user' in session:
        del session['user']
        return render_template('log_out.html', logged_out = True)
    else:
        return render_template('log_out.html', logged_out = False)

@app.route('/update-rated', methods=['POST'])
@authenticate
def update_rated():
    if 'user' in session:
        username = get_username_from_token()
        user_id = get_user_from_name(username)
        return jsonify({'num_rated': len(get_artists_rated(user_id))})
    else:
        return render_template('token_expired.html'), {"Refresh": "7; url=http://127.0.0.1:5000/log-out"}

# portal to log in via spotify
@app.route('/portal', methods=['GET', 'POST'])
@authenticate
def portal():
    query_data = {
        'client_id' : APP_ID,
        'response_type' : 'code',
        'redirect_uri' : 'http://127.0.0.1:5000/logging-in',
        'scope' : """user-library-modify user-library-read user-top-read user-read-recently-played playlist-read-private
        playlist-read-collaborative playlist-modify-private playlist-modify-public user-follow-read""",
        'state_key' : ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))
    }

    auth_url = 'https://accounts.spotify.com/authorize?'

    query_params = 'response_type=code&client_id=' + query_data['client_id'] + '&redirect_uri=' + query_data['redirect_uri'] + '&scope=' + query_data['scope'] + '&state=' + query_data['state_key']
    response = make_response(redirect(auth_url + query_params))
    print(response)
    return response
    # return render_template('portal.html')

@app.route('/logging-in')
@authenticate
def logging_in():
    code = request.args.get("code")
    # TODO: handle user rejecting access, will have different response in query params (error instead of code?)
    # TODO: check state in response is the same as what we sent and reject if doesn't match

    # client id and app secret can be given as combined base64 but can also as below as explicit separate params
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    post_params = {'grant_type': 'authorization_code', 'code': code, 'redirect_uri': 'http://127.0.0.1:5000/logging-in',"client_id": APP_ID,
        "client_secret": APP_SECRET}
    res = requests.post(url='https://accounts.spotify.com/api/token', headers= headers, data=post_params)
    # print('response: ' + str(res.json()))
    if res.status_code == 200:
        get_auth_tokens(json.loads(res.text))
        get_spotify_data()
        # add_spotify_ids()
        return render_template('logging_in.html', success = True)
    else:
        return render_template('logging_in.html', success = False)

@app.route('/add-spotify-info', methods = ['GET', 'POST'])
def get_spotify_data():
    print('adding data...')
    # TODO:
    # broader func to pull together other spotify related ones
    get_spotify_top()
    get_spotify_recently_played()
    get_spotify_followed_artists()
    get_user_spotify_id()
    
    return jsonify({'data': 'placeholder'})

@app.route('/recommend-knn', methods=['POST'])
@authenticate
def recommend_knn():
    # TODO: separate out into reusable chunks across this and other recommend method
    if 'user' in session:
        username = get_username_from_token()
        userid = get_user_from_name(username)

        # returning if not rated many artists with just a message to rate more
        num_rated = len(get_artists_rated(userid))
        top_rated = get_artists_rated(userid, 8)

        recommender = KNNRecommender()

        recs = recommender.recommend_subset(recommender.single_user_subset(userid), 25)
        recs_ = [str(i[0]) for i in recs.select('recommendations').collect()]
        # print(recs_)

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
        print(rec_name_links)
        past_rec_links = {past_rec_names[i]: past_rec_links[i] for i in range(len(past_rec_links))}

        top_songs = {}
        if 'spotify_user_id' not in session:
            pass
            # TODO: add client credentials auth flow to get spotify info without user login (for top songs etc.)
        if 'spotify_user_id' in session:
            top_songs = {}
            for artist_name in rec_names:
                # TODO: maybe adjust/test properly to made sure not other errors than just artist not found/ better handle within func
                try:
                    spotify_id = find_artist_in_spotify(artist_name)
                    top_songs_for_artist = get_top_songs_for_artist(spotify_id)
                    print(top_songs_for_artist)
                    top_songs[artist_name] = top_songs_for_artist
                    # TODO: make this json friendly
                except:
                    print(f'{artist_name} not found')
                    # top_songs.append([])
            # top_songs_dict = {rec_names[i]: top_songs[i] for i in range(len(rec_names))}
            # print(f'TOP SONGS DICT : {top_songs_dict}')
            print(rec_names)
            top_songs_list = list(chain.from_iterable(i for i in top_songs.values() if len(i) > 0))
            print(f'TOP SONGS LIST::::::{top_songs_list}')
            print(f'TOP SONGS LENGTH::::::{len(top_songs_list)}')
            save_recs_as_spotify_playlist(rec_names, top_songs_list[:100])
        # print(get_top_songs_for_artist(find_artist_in_spotify(past_rec_names[0])))
        
        return jsonify({'recs': rec_name_links, 'past_recs': past_rec_links, 'top_songs': top_songs})

    return render_template('token_expired.html'), {"Refresh": "7; url=http://127.0.0.1:5000/log-out"}

@app.route('/recommend', methods=['POST'])
@authenticate
def recommend():
    # TODO: potential edge case where token expires?
    if 'user' in session:
        username = get_username_from_token()
        userid = get_user_from_name(username)

        # returning if not rated many artists with just a message to rate more
        num_rated = len(get_artists_rated(userid))

        recommender = Recommender()
        # print (f'best model rank: {recommender.model}')
        # print (f'best model maxiter: {recommender.model.getMaxIter()}')
        # print (f'best model regparam: {recommender.model._java_obj.parent().getRegParam()}')
        recs = recommender.recommend_subset(recommender.single_user_subset(userid), 25)
        recs_ = [str(i[0]) for i in recs.select('recommendations').collect()]
        # print(recs_)

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
        print(rec_name_links)
        past_rec_links = {past_rec_names[i]: past_rec_links[i] for i in range(len(past_rec_links))}

        # print(past_rec_names[0]) 
        #TODO: logic to only do if logged in to spotify, and to use this in recommendation, 
        # and what to do if not found on spotify
        #
        # top_songs_dict = None
        top_songs = {}
        if 'spotify_user_id' not in session:
            pass
            # TODO: add client credentials auth flow to get spotify info without user login (for top songs etc.)
        if 'spotify_user_id' in session:
            top_songs = {}
            for artist_name in rec_names:
                # TODO: maybe adjust/test properly to made sure not other errors than just artist not found/ better handle within func
                try:
                    spotify_id = find_artist_in_spotify(artist_name)
                    top_songs_for_artist = get_top_songs_for_artist(spotify_id)
                    print(top_songs_for_artist)
                    top_songs[artist_name] = top_songs_for_artist
                    # TODO: make this json friendly
                except:
                    print(f'{artist_name} not found')
                    # top_songs.append([])
            # top_songs_dict = {rec_names[i]: top_songs[i] for i in range(len(rec_names))}
            # print(f'TOP SONGS DICT : {top_songs_dict}')
            print(rec_names)
            top_songs_list = list(chain.from_iterable(i for i in top_songs.values() if len(i) > 0))
            print(f'TOP SONGS LIST::::::{top_songs_list}')
            print(f'TOP SONGS LENGTH::::::{len(top_songs_list)}')
            save_recs_as_spotify_playlist(rec_names, top_songs_list[:100])
        # print(get_top_songs_for_artist(find_artist_in_spotify(past_rec_names[0])))
        
        return jsonify({'recs': rec_name_links, 'past_recs': past_rec_links, 'top_songs': top_songs})

    return render_template('token_expired.html'), {"Refresh": "7; url=http://127.0.0.1:5000/log-out"}

@app.route('/add-artist', methods=('GET', 'POST'))
@authenticate
def add_artist():
    if request.method == 'POST':
        name = request.form['name']
        add_new_artist(name)
        
        return redirect(url_for('home'))

    return render_template('add_artist.html')

@app.route('/success')
def success():
    return render_template('rating_success.html', artist = request.args.get('artist'), rating = request.args.get('rating'), updated = str(request.args.get('updated')))

@app.route('/welcome', methods=('GET', 'POST'))
@authenticate
def welcome():
    logged_in = False
    if 'user' in session:
        logged_in = True
        username = get_username_from_token()
        user_id = get_user_from_name(username)
        if request.method == 'POST':
            artist_name = request.form['artist']
            artist_id = get_artist_id_from_name(artist_name)
            rating = request.form['rating']

            # if not is_token_valid():
            #     return render_template('token_expired.html'), {"Refresh": "7; url=http://127.0.0.1:5000/log-out"}

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
    
    return redirect(url_for('home'))


@app.route('/sign-up', methods=('GET', 'POST'))
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
