import psycopg2
from api_main import get_db_connection
import http.client
import requests
import time

# adding a new column to store lastfm link, can adjust and add to initial table
def add_url_column():
  conn = get_db_connection()
  cur = conn.cursor()
  cur.execute("ALTER TABLE artists ADD lastfm_link TEXT;")
  conn.commit()
  cur.close()
  conn.close()

# getting all artist names from db to get urls for
def get_artist_names():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM artists;")
    artist_resultset = cur.fetchall()
    artist_names = [artist[0] for artist in artist_resultset]
    cur.close()
    conn.close()
    return artist_names

# getting lastfm urls
def get_artist_urls(artist_names):
    #checking if url fits standard with status code check
    invalid_artists = []
    for index, artist in enumerate(artist_names):
        # limiting requests to 50 per minute
        if index % 50 == 0:
            time.sleep(60)
        url = f"https://www.last.fm/music/{'+'.join(artist.split())}"
        try:
            req = requests.head(url)
            # TODO: deal with invalid urls - mostly 301 redirects, some 404s for really odd names need workarounds
            if req.status_code != 200:
                print(artist)
                print(url)
                print(req.status_code)
                invalid_artists.append(artist)
        except requests.ConnectionError:
            print("connection error")

    print(invalid_artists)

if __name__=="__main__":
    # add_url_column()
    get_artist_urls(get_artist_names())
