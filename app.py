import logging
import secrets

from flask import Flask, Response, redirect, render_template, request, session, url_for
from flask_wtf.csrf import CSRFProtect
from spotify_client import SpotifyClient, Config
from pythonjsonlogger.jsonlogger import JsonFormatter

import config

app_logger = logging.FileHandler(filename='app.log')
json_formatter = JsonFormatter(fmt='%(levelname)s %(asctime)s %s(pathname)s %(lineno)s %(name)s %(message)s')

spotify_logger_handler = app_logger
spotify_logger_handler.setFormatter(json_formatter)

app_logger_handler = app_logger
app_logger_handler.setFormatter(json_formatter)

spotify_logger = logging.getLogger('spotify_client')
spotify_logger.setLevel(logging.INFO)
spotify_logger.addHandler(spotify_logger_handler)

app_logger = logging.getLogger('spotifyanalyze')
app_logger.setLevel(logging.INFO)
app_logger.addHandler(app_logger_handler)

csrf_logger = logging.getLogger('flask_wtf.csrf')
csrf_logger.setLevel(logging.INFO)
csrf_logger.addHandler(app_logger_handler)

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Strict',
)
csrf = CSRFProtect(app)

Config.configure(config.SPOTIFY_CLIENT_ID, config.SPOTIFY_SECRET_KEY, config.TIMEOUT_VALUE)
client = SpotifyClient()


@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'

    return response


@app.route('/')
def homepage():
    # Delete previous attribute values if already present
    session.pop('valence', None)
    session.pop('energy', None)
    session.pop('danceability', None)

    state = secrets.token_urlsafe(config.SPOTIFY_SESSION_STATE_LENGTH)

    spotify_oauth_link = client.build_spotify_oauth_confirm_link(
        state,
        config.SPOTIFY_SCOPES,
        config.SPOTIFY_REDIRECT_URI
    )

    session['state'] = state

    return render_template('homepage.html', spotify_oauth_link=spotify_oauth_link)


@app.route('/spotify_auth')
def spotify_auth():
    request_state = request.args.get('state')
    session_state = session.get('state')

    if session_state and secrets.compare_digest(request_state, session_state):
        code = request.args.get('code')

        access_token = client.get_access_and_refresh_tokens(code, config.SPOTIFY_REDIRECT_URI)['access_token']
        spotify_username = client.get_user_profile(access_token)['id']

        session['access_token'] = access_token
        session['spotify_username'] = spotify_username

        return redirect(url_for('spotify_attributes'))
    else:
        return Response('Invalid state parameter', status=400)


@app.route('/spotify_attributes')
def spotify_attributes():
    access_token = session.get('access_token')

    if not access_token:
        return redirect(url_for('homepage'))

    average_valence = session.get('valence')
    average_energy = session.get('energy')
    average_danceability = session.get('danceability')

    if not all([average_valence, average_energy, average_danceability]):
        app_logger.info(
            'Making request for song attributes',
            extra={
                'spotify_username': session['spotify_username'],
            }
        )

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

        total_energy = sum([track['energy'] for track in recently_listened_track_attributes])
        average_energy = round((total_energy / len(recently_listened_track_attributes)), 2)

        total_danceability = sum([track['danceability'] for track in recently_listened_track_attributes])
        average_danceability = round((total_danceability / len(recently_listened_track_attributes)), 2)

        session['valence'] = average_valence
        session['energy'] = average_energy
        session['danceability'] = average_danceability

    average_valence_display = int(average_valence * 100)
    average_energy_display = int(average_energy * 100)
    average_danceability_display = int(average_danceability * 100)

    context = {
        'average_valence': average_valence_display,
        'average_energy': average_energy_display,
        'average_danceability': average_danceability_display,
    }

    return render_template('attributes.html', **context)


@app.route('/recommend')
def recommend():
    access_token = session.get('access_token')

    if not access_token:
        return redirect(url_for('homepage'))

    spotify_username = session['spotify_username']
    target = request.args.get('target')
    average_value = session[target]
    seed_tracks = session['seed_tracks']
    min_value = average_value - 0.05
    max_value = average_value + 0.05

    tracks = {'tracks': []}

    # Make requests to Spotify API for recommendations for target within value ranges
    # If no tracks are found for attribute targets, keep making requests with higher
    # variance in order to get tracks for recommendations
    for i in range(3):
        app_logger.info(
            'Making request for {} recommendations for user {}'.format(target, spotify_username),
            extra={
                'spotify_username': spotify_username,
                'target': target,
                'seed_tracks': seed_tracks,
                'min_value': min_value,
                'max_value': max_value,
                'request_num': i,
            }
        )

        tracks = client.get_recommendations(
            target,
            min_value,
            max_value,
            seed_tracks,
            config.SPOTIFY_RECOMMENDATIONS_TRACK_LIMIT
        )

        # Filter out tracks that the user has already been recommended
        # to prevent showing the user a song they have already seen
        session_seen_songs = session.get('seen_songs')
        if session_seen_songs:
            tracks = [track for track in tracks['tracks'] if not track['id'] in session_seen_songs]
            tracks = {'tracks': tracks}

        if len(tracks['tracks']) == config.SPOTIFY_RECOMMENDATIONS_TRACK_LIMIT:
            break
        else:
            min_value = min_value - 0.05
            max_value = max_value + 0.05

    track_codes = [track['id'] for track in tracks['tracks']]

    seen_songs = session.get('seen_songs', list())
    for track_code in track_codes:
        seen_songs.insert(0, track_code)

    seen_songs = list(set(seen_songs))
    seen_songs = seen_songs[:100]
    session['seen_songs'] = seen_songs

    return {'codes': track_codes}


@app.route('/like_song', methods=['POST'])
def like_song():
    access_token = session.get('access_token')

    if not access_token:
        return redirect(url_for('homepage'))

    spotify_username = session['spotify_username']

    song_id = request.json.get('song_id')

    client.add_track_to_saved_songs(access_token, song_id)

    app_logger.info(
        'Saved song to user {} library'.format(spotify_username),
        extra={
            'song_id': song_id,
            'spotify_username': spotify_username,
        }
    )

    return {'status': 'OK'}


if __name__ == '__main__':
    app.run(debug=config.DEBUG)
