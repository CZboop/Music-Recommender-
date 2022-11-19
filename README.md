# ALS Music Recommender
[![CircleCI](https://circleci.com/gh/CZboop/Music-Recommender-.svg?style=shield&circle-token=2f769baabca3a8571ae6718d40f483f7bef3b146)](https://app.circleci.com/pipelines/github/CZboop/Music-Recommender-)

Full stack music recommendation app, allowing users to rate musical artists and get recommendations using machine learning with the alternating least squares method of matrix factorisation.  

## Technical Features

- Python Flask app base
- Spark's Python API PySpark used to create an ALS Model
- Model hyperparameters are optimised and the training and tuning is checkpointed
- PSQL database connected to the app using the psycopg2 database adapter
- JWT authentication, storing the token in the Session cookie
- jQuery Ajax used for asynchronous background tasks, and updating pages without refresh
- Pgcrypto encryption for password storage in the database
- Testing using pytest and unittest, with CircleCI pipeline running tests on each commit
- Media queries for mobile responsive CSS

## Functional Features

- Decorator used for protecting or partially protecting authenticated routes, with different treatment for users whose session expires vs those who have not yet signed in
- Users can manually rate artists or import their Spotify library using the Spotify API
- Recommendations are not repeated, but users can see all their past recommendations alognside new ones
- Links given to the recommended artist's Last.fm, as well as some of their top songs on Spotify if user has logged in via Spotify
- When users have logged in via Spotify, their recommendations are stored as a playlist to their Spotify account

## Requirements & Setup

### Requirements
- Python packages required can be found in the requirements.txt file. These can be installed with the following:
  - If Python is not installed, install it from [this link](https://www.python.org/downloads/).  
  - Clone this repository, then navigate to the directory it is in.  
  - Set up a virtual environment using:  
  ```$ python -m venv evironmentname```  
  - Activate the virtual environment. For Windows, this is done using:  
  ```$ environmentname\Scripts\activate.bat```  
  [This link](https://docs.python.org/3/library/venv.html) shows how to do this for other operating systems.
  - Install dependencies using:  
  ```$ pip install -r requirements.txt ```
 - PySpark also requires Hadoop and Java. This project was built using Java 11, the instructions for downloading this for windows can be found at [this link](https://docs.oracle.com/en/java/javase/11/install/installation-jdk-microsoft-windows-platforms.html#GUID-A7E27B90-A28D-4237-9383-A58B416071CA), which also has links to pages with instructions for other operating systems
 - Hadoop version 3.3.1 was used, using winutils rather than a full install. Steps to get Hadoop set up on Windows:
    - Create a /winutils directory in C:/
    - Create a /bin directory within the C:/winutils directory
    - Download the winutils.exe file for v3.3.1, this can be found at [this link](https://github.com/kontext-tech/winutils/blob/master/hadoop-3.3.1/bin/winutils.exe) and place it in the C:/winutils/bin folder
    - Download the hadoop.dll file vor v3.3.1, this can be found at [this link](https://github.com/kontext-tech/winutils/blob/master/hadoop-3.3.1/bin/hadoop.dll), and place this in the same C:/winutils/bin folder
    - Copy the hadoop.dll file from above and add it to the C:\Windows\System32 folder
 - PostgreSQL setup instructions can be found at [this link](https://www.prisma.io/dataguide/postgresql/setting-up-a-local-postgresql-database). If you are setting up PSQL for the first time, make sure to keep a note of the username and password you use
 
 ### Setup
 Additionally, the app requires more setup for full functionality.
 - Environment variables are used for the PSQL user and password. 
     - If using windows or a cmd terminal, the env.bat file within the repo sets these variables and can be run from the batch file that starts the virtual environment so that these are set whenever the virtual environment is active. To set this up, add ```pushd flask_recommender\src\
call env.bat``` above the ```:END``` towards the end of the file. There are various other ways to set the environment variables. 
    - The project is based on the PSQL user being 'postgres' and the password being 'password'. If you have a different username and password, this will need to be changed where it is manually set in the app, in the tests and the config.yml file.
 - An empty PSQL database called 'recommend' should be created locally. Tables can be set up and starter data added by running the db_access.py file in the src/db directory within this project
 - Spotify integration requires an app secret and app id from Spotify for developers. These are currently in a file that is not part of the repo: src/app/config_secrets.py To enable the Spotify integration part of the app:
    - Create an account or log in with your existing Spotify account [here](https://developer.spotify.com/dashboard/)
    - Create a new app within the developer dashboard
    - Edit settings for the new app, and add 'http://127.0.0.1:5000/logging-in' as a redirect URI
    - Create a config_secrets.py file in the src/app directory of the cloned repository
    - Copy the Client ID and Client Secret for the new Spotify app from the developer dashboard, and add it to the config_secrets.py file in this format:
    ```
    APP_SECRET = '<CLIENT SECRET>'  
    APP_ID = '<CLIENT ID>'
    ```
    - You may also need to add the email of any Spotify accounts that will using the app while in development under the 'Users and Access' section of the app within the Spotify developer platform

Along with the starter data, the model develops with the ratings that users add from the web app. 

Initial data was adapted from Last.fm listen data. Number of listens was converted to a rating out of 10, normalised and standardised so that users' overall number of listens did not skew their ratings.
