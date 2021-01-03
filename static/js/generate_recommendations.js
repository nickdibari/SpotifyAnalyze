'use strict';

(function IIFE() {
    function makeRecommendationRequest(target) {
        let options = {
            method: 'GET',
            credentials: 'include',
            headers: {'Content-Type': 'application/json'}
        };

        fetch(window.location.origin + '/recommend?target=' + target, options).then(response => {
            return response.json();
        }).then(json => {
            let playlistId = target + '-playlist';
            let playlist = document.getElementById(playlistId);

            for (const code of json.codes) {
                let playButton = document.createElement('iframe');
                playButton.setAttribute('allow', 'encrypted-media https://open.spotify.com;');
                playButton.src = 'https://open.spotify.com/embed/track/' + code;

                playlist.appendChild(playButton);
            }
        })
    }

    function init() {
        makeRecommendationRequest('valence');
        makeRecommendationRequest('energy');
        makeRecommendationRequest('danceability');
    }

    init();
})();
