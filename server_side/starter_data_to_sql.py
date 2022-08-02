import pandas as pd
import math

# loading data
# normalising number of listens into a 5-10 rating
# converting to sql file and returning
class CSVToSQL:
    def __init__(self, listen_data_path, artist_data_path):
        self.listen_data_path = listen_data_path
        self.artist_data_path = artist_data_path
        self._load_data()
        self._listens_to_rating()

    def _load_data(self):
        self.listen_data = pd.read_csv(self.listen_data_path)
        self.artist_data = pd.read_csv(self.artist_data_path)

    def _to_rating(self, user_id):
        user_slice = self.listen_data.loc[self.listen_data['user_id']==user_id]

        min_for_user = min(list(user_slice['scrobbles']))
        max_for_user = max(list(user_slice['scrobbles']))

        self.listen_data.loc[self.listen_data['user_id']==user_id, 'scrobbles'] = self.listen_data.loc[self.listen_data['user_id']==user_id, 'scrobbles'].apply(lambda x: 5 if min_for_user == max_for_user else math.ceil((x - min_for_user ) / (max_for_user - min_for_user) * 5) + 5)
        return self.listen_data

    def _listens_to_rating(self):
        user_num = max(self.listen_data['user_id'])
        for i in range(1, user_num + 1):
            self.listen_data = self._to_rating(i)

    # starter data doesn't have usernames, will just make it user1 with number
    def create_sql_users(self):
        insert_statement = ""
        for c,v in enumerate(set(list(self.listen_data['user_id']))):
            sql_string = f"INSERT INTO users (name, id) VALUES ('user{c+1}', {v});\n"
            insert_statement += sql_string
        return insert_statement

    def create_sql_artists(self):
        insert_statement = ""
        for c,v in enumerate(set(list(self.artist_data['artist_id']))):
            artist_name = self.artist_data.loc[self.artist_data['artist_id'] == v]['artist_name'].values[0].replace("'", "''")
            sql_string = f"INSERT INTO artists (name, id) VALUES ('{artist_name}', {v});\n"
            insert_statement += sql_string
        return insert_statement

    def create_sql_listens(self):
        insert_statements = [f"INSERT INTO user_ratings (user_id, artist_id, rating) VALUES ({row[0]}, {row[1]}, {row[2]});\n" for row in zip(self.listen_data['user_id'], self.listen_data['artist_id'], self.listen_data['scrobbles'])]
        return "".join(insert_statements)

    def create_all_sql(self):
        return self.create_sql_users(), self.create_sql_artists(), self.create_sql_listens()

if __name__ == "__main__":
    converter = CSVToSQL('./data/lastfm_user_scrobbles.csv', './data/lastfm_artist_list.csv')
    converter.create_all_sql()
