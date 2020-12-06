from flask import Flask, redirect, render_template, request, session, url_for
from spotify_client import SpotifyClient
import requests

from config import SECRET_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_SECRET_KEY, SPOTIFY_SCOPES, SPOTIFY_REDIRECT_URI

app = Flask(__name__)

app.secret_key = SECRET_KEY


@app.route('/')
def homepage():
    client = SpotifyClient(client_id=SPOTIFY_CLIENT_ID, secret_key=SPOTIFY_SECRET_KEY)
    spotify_oauth_link = client.build_spotify_oauth_confirm_link(
        'test-state',
        SPOTIFY_SCOPES,
        SPOTIFY_REDIRECT_URI
    )

    return render_template('homepage.html', spotify_oauth_link=spotify_oauth_link)


@app.route('/spotify_auth')
def spotify_auth():
    client = SpotifyClient(client_id=SPOTIFY_CLIENT_ID, secret_key=SPOTIFY_SECRET_KEY)
    code = request.args.get('code')

    access_token = client.get_access_and_refresh_tokens(code, SPOTIFY_REDIRECT_URI)['access_token']
    session['access_token'] = access_token

    return redirect(url_for('spotify_attributes'))


@app.route('/spotify_attributes')
def spotify_attributes():
    client = SpotifyClient(client_id=SPOTIFY_CLIENT_ID, secret_key=SPOTIFY_SECRET_KEY)
    access_token = session['access_token']

    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'limit': 30}

    recently_listened_tracks = requests.get(
        'https://api.spotify.com/v1/me/player/recently-played',
        headers=headers,
        params=params
    ).json()

    recently_listened_tracks_codes = [{'code': track['track']['uri']} for track in recently_listened_tracks['items']]
    recently_listened_track_attributes = client.get_audio_features_for_tracks(recently_listened_tracks_codes)

    total_valence = sum([track['valence'] for track in recently_listened_track_attributes])
    average_valence = round((total_valence / len(recently_listened_track_attributes) * 100), 2)

    total_energy = sum([track['energy'] for track in recently_listened_track_attributes])
    average_energy = round((total_energy / len(recently_listened_track_attributes) * 100), 2)

    total_danceability = sum([track['danceability'] for track in recently_listened_track_attributes])
    average_danceability = round((total_danceability / len(recently_listened_track_attributes) * 100), 2)

    context = {
        'average_valence': average_valence,
        'average_energy': average_energy,
        'average_danceability': average_danceability
    }

    return render_template('attributes.html', **context)


if __name__ == '__main__':
    app.run(debug=True)
