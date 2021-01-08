from flask import Flask, redirect, render_template, request, session, url_for, abort
from spotify_client import SpotifyClient

import config

app = Flask(__name__)

app.secret_key = config.SECRET_KEY


@app.route('/')
def homepage():
    client = SpotifyClient(client_id=config.SPOTIFY_CLIENT_ID, secret_key=config.SPOTIFY_SECRET_KEY)
    spotify_oauth_link = client.build_spotify_oauth_confirm_link(
        'test-state',
        config.SPOTIFY_SCOPES,
        config.SPOTIFY_REDIRECT_URI
    )

    return render_template('homepage.html', spotify_oauth_link=spotify_oauth_link)


@app.route('/spotify_auth')
def spotify_auth():
    client = SpotifyClient(client_id=config.SPOTIFY_CLIENT_ID, secret_key=config.SPOTIFY_SECRET_KEY)
    code = request.args.get('code')

    access_token = client.get_access_and_refresh_tokens(code, config.SPOTIFY_REDIRECT_URI)['access_token']
    session['access_token'] = access_token

    return redirect(url_for('spotify_attributes'))


@app.route('/spotify_attributes')
def spotify_attributes():
    access_token = session.get('access_token')

    if not access_token:
        return redirect(url_for('homepage'))

    client = SpotifyClient(client_id=config.SPOTIFY_CLIENT_ID, secret_key=config.SPOTIFY_SECRET_KEY)

    recently_listened_tracks = client.get_recently_played_tracks_for_user(
        access_token,
        limit=config.SPOTIFY_RECENTLY_LISTENED_TRACKS_LIMIT
    )

    recently_listened_tracks_codes = [{'code': track['track']['uri']} for track in recently_listened_tracks['items']]
    recently_listened_track_attributes = client.get_audio_features_for_tracks(recently_listened_tracks_codes)

    tracks = [client.get_code_from_spotify_uri(track['code']) for track in recently_listened_tracks_codes]
    seed_tracks = ','.join(tracks[:config.SPOTIFY_SEED_TRACK_LIMIT])
    session['seed_tracks'] = seed_tracks

    total_valence = sum([track['valence'] for track in recently_listened_track_attributes])
    average_valence = round((total_valence / len(recently_listened_track_attributes)), 2)
    average_valence_display = int(average_valence * 100)

    total_energy = sum([track['energy'] for track in recently_listened_track_attributes])
    average_energy = round((total_energy / len(recently_listened_track_attributes)), 2)
    average_energy_display = int(average_energy * 100)

    total_danceability = sum([track['danceability'] for track in recently_listened_track_attributes])
    average_danceability = round((total_danceability / len(recently_listened_track_attributes)), 2)
    average_danceability_display = int(average_danceability * 100)

    session['valence'] = average_valence
    session['energy'] = average_energy
    session['danceability'] = average_danceability

    context = {
        'average_valence': average_valence_display,
        'average_energy': average_energy_display,
        'average_danceability': average_danceability_display,
    }

    return render_template('attributes.html', **context)


@app.route('/recommend')
def recommend():
    client = SpotifyClient(client_id=config.SPOTIFY_CLIENT_ID, secret_key=config.SPOTIFY_SECRET_KEY)

    target = request.args.get('target')
    average_value = session[target]
    seed_tracks = session['seed_tracks']

    tracks = client._make_spotify_request(
        'GET',
        'https://api.spotify.com/v1/recommendations',
        params={
            f'max_{target}': average_value + .05,
            f'min_{target}': average_value - .05,
            'seed_tracks': seed_tracks,
            'limit': config.SPOTIFY_SEED_TRACK_LIMIT
        }
    )

    track_codes = [client.get_code_from_spotify_uri(track['uri']) for track in tracks['tracks']]

    return {
        'codes': track_codes
    }


if __name__ == '__main__':
    app.run(debug=config.DEBUG)
