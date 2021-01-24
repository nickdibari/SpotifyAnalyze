'use strict';

(function IIFE() {
    function makeLikeRequest() {
        let options = {
            method: 'POST',
            credentials: 'include',
            headers: {'Content-Type': 'application/json'}
        };

        let songId = this.dataset.songId;

        fetch(window.location.origin + '/like_song?song_id=' + songId, options).then(response => {
            return response.json();
        }).then(json => {
            let likeButton = document.getElementById('like-button-' + songId);
            likeButton.disabled = true;
        })
    }

    function createLikeButton(songId) {
        let button = document.createElement('button');
        button.id = 'like-button-' + songId;
        button.className = 'btn btn-success';
        button.appendChild(document.createTextNode('Like'));
        button.dataset.songId = songId;
        button.addEventListener('click', makeLikeRequest);

        return button
    }

    function createRecommendationPlaylist(data, target) {
        let playlistId = target + '-playlist';
        let playlistErrorMessage = document.getElementById(target + '-playlist-error-message');
        let playlist = document.getElementById(playlistId);

        playlistErrorMessage.hidden = true;

        if (!Boolean(data.codes.length)) {
            playlistErrorMessage.hidden = false;
            return;
        }

        for (const code of data.codes) {
            let songContainer = document.createElement('div');
            songContainer.className = 'col text-center';

            let playButton = document.createElement('iframe');
            playButton.className = 'play-button';
            playButton.setAttribute('allow', 'encrypted-media https://open.spotify.com;');
            playButton.src = 'https://open.spotify.com/embed/track/' + code;

            let likeButton = createLikeButton(code);

            songContainer.appendChild(playButton);
            songContainer.appendChild(likeButton);
            playlist.appendChild(songContainer);
        }
    }

    function makeRecommendationRequest(target) {
        let options = {
            method: 'GET',
            credentials: 'include',
            headers: {'Content-Type': 'application/json'}
        };

        fetch(window.location.origin + '/recommend?target=' + target, options).then(response => {
            return response.json();
        }).then(json => {
            createRecommendationPlaylist(json, target);
        })
    }

    function init() {
        makeRecommendationRequest('valence');
        makeRecommendationRequest('energy');
        makeRecommendationRequest('danceability');
    }

    init();
})();
