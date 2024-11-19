import requests
import urllib.parse
import datetime 
from flask import Flask,redirect,jsonify,session,request
import datetime
from json import loads
import pymssql


app = Flask(__name__) #Create an instance of flask app
app.secret_key = 'Gurramkonda@192006'

#Spotify API Configuration
client_id = '24bea80b6db14949acf892a03b023edf'
client_secret = '41bf504f538f48a0ade2ab3d934be0d3'
redirect_url = 'http://localhost:5000/callback'

auth_url = 'https://accounts.spotify.com/authorize'
token_url = 'https://accounts.spotify.com/api/token'
api_base_url = 'https://api.spotify.com/v1/'


@app.route('/')
def index():
    return "Welcome to Spotify App <a href='/login'>Login with Spotify</a>"


@app.route('/login')
def login():
    scope = 'user-read-private user-read-email user-top-read'
    params = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri' : redirect_url,
        'scope': scope,
    }
    login_url = f"{auth_url}?{urllib.parse.urlencode(params)}"
    return redirect(login_url)


@app.route('/callback')
def callback():
    if 'error' in request.args:
        error = request.args.get('error')
        return jsonify({"error": request.args['error']})

    if 'code' in request.args:
        req_body = {
            'code': request.args.get('code'),
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_url,
            'client_id': client_id,
            'client_secret': client_secret
        }
        response = requests.post(token_url, data=req_body)
        response_data = response.json()
        print("token_info", response_data)

        session['access_token'] = response_data['access_token']
        session['refresh_token'] = response_data['refresh_token']
        session['expires_at']= datetime.datetime.now(datetime.timezone.utc).timestamp() + response_data['expires_in']

        return redirect('/playlists')



@app.route('/playlists')
def playlists():
    if 'access_token' not in session:
        return redirect('/login')
    if datetime.datetime.now(datetime.timezone.utc).timestamp() > session['expires_at']:
        return redirect('/refresh_token')

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(api_base_url + 'me/top/artists', headers=headers)
    artists = response.json()
    conn = pymssql.connect(
        server='varun',         
        user='sa',
        password ='Gurramkonda@192006',    
        database='spotify' 
    )
    cursor = conn.cursor()
    cursor.execute("""
    IF OBJECT_ID('top_artist','U') is not null  
            DROP TABLE top_artist   
    CREATE TABLE top_artist(
        name VARCHAR(50),
        genres VARCHAR(500),
        popularity VARCHAR(50),
        followers VARCHAR(50)
    )
    """)
    cursor.connection.commit()
    conn.commit()

    for v in artists['items']:

        genres = ','.join(v['genres'])
        name = v['name']
        popularity = v['popularity'] 
        followers =v['followers']['total']
        query = "INSERT INTO top_artist(name, genres, popularity, followers) VALUES (%(name)s, %(genres)s, %(popularity)s, %(followers)s)"
        params = {'name': name, 'genres': genres, 'popularity': popularity, 'followers': followers}
        cursor.execute(query, params)
    

    conn.commit()
    cursor.close()
    conn.close()
    
    
    return "Data is returned"

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)