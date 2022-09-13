import psycopg2
from api_main import get_db_connection
import http.client
import requests
import time
import httplib2
from bs4 import BeautifulSoup, SoupStrainer

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
    http = httplib2.Http()
    #checking if url fits standard with status code check
    invalid_artists = []
    artist_urls = {}
    for index, artist in enumerate(artist_names):
        url = "https://www.last.fm/music/" + requests.utils.quote(artist)
        artist_urls[artist] = url

    return artist_urls

def add_artist_urls_to_db(artist_urls):
    for key in artist_urls:
        artist_name = key.replace("'","''")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"UPDATE artists SET lastfm_link = '{artist_urls[key]}' WHERE name = '{artist_name}';")
        conn.commit()
        cur.close()
        conn.close()


if __name__=="__main__":
    # add_url_column()
    urls = get_artist_urls(get_artist_names())
    add_artist_urls_to_db(urls)
