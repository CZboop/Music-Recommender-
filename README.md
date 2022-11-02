# ALS Music Recommender
[![CircleCI](https://circleci.com/gh/CZboop/Music-Recommender-.svg?style=shield&circle-token=2f769baabca3a8571ae6718d40f483f7bef3b146)](https://app.circleci.com/pipelines/github/CZboop/Music-Recommender-)

Full stack music recommendation app, allowing users to rate musical artists and get recommendations using machine learning with the alternating least squares method of matrix factorisation. 

Build with Flask and PySpark, with a PSQL database. Passwords are stored encrypted within the database. JWT authentication is used to protect or partially protect routes from users who are not logged in. Authentication also eases user experience as their information is automatically retrieved using the token.

Starter data is added into the database, but the model develops with the ratings that users add from the web app. 

Initial data was adapted from Last.fm listen data. Number of listens was converted to a rating out of 10, normalised and standardised so that users' overall number of listens did not skew their ratings.
