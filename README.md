# ALS Music Recommender
[![CircleCI](https://circleci.com/gh/CZboop/Music-Recommender-.svg?style=shield&circle-token=2f769baabca3a8571ae6718d40f483f7bef3b146)](https://app.circleci.com/pipelines/github/CZboop/Music-Recommender-)

Full stack music recommendation app, allowing users to rate musical artists and get recommendations using machine learning with the alternating least squares method of matrix factorisation.  

## Technical Features

- Python Flask app base
- Spark's Python API PySpark used to create an ALS Model
- PSQL database connected to the app using the psycopg2 database adapter
- JWT authentication, storing the token in the Session cookie
- jQuery Ajax used for asynchronous background tasks, and updating pages without refresh
- Pgcrypto encryption for password storage in the database
- Testing using pytest and unittest
- Media queries for mobile responsive CSS

## Functional Features

- Decorator used for protecting or partially protecting authenticated routes, with different treatment for users whose session expires vs those who have not yet signed in
- Users can manually rate artists or import their Spotify library using the Spotify API
- Recommendations are not repeated, but users can see all their past recommendations alognside new ones
- Links given to the recommended artist's Last.fm, as well as some of their top songs on Spotify if user has logged in via Spotify
- When users have logged in via Spotify, their recommendations are stored as a playlist to their Spotify account

Starter data is already in the database, but the model develops with the ratings that users add from the web app. 

Initial data was adapted from Last.fm listen data. Number of listens was converted to a rating out of 10, normalised and standardised so that users' overall number of listens did not skew their ratings.
