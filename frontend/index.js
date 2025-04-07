function displaySong() {
    const songDisplay = document.getElementById('songDisplay');
    const spinner = document.getElementById('spinner');

    // מנקה תוצאה קודמת ומראה את הספינר
    songDisplay.style.display = 'none';
    spinner.style.display = 'block';

    fetch('/track')
        .then(response => response.json())
        .then(data => {
            const track = data[0];
            let link = 'https://open.spotify.com/track/' + track.track_id;

            const songHTML = `
                <p><strong>Track:</strong> ${track.track_name}</p>
                <p><strong>Artist:</strong> ${track.artist_name}</p>
                <p><strong>Year:</strong> ${track.year}</p>
                <p><strong>Link:</strong> <a href="${link}" target="_blank" class="listen-link">Listen on Spotify</a></p>
            `;

            songDisplay.innerHTML = songHTML;
            spinner.style.display = 'none';
            songDisplay.style.display = 'block';
        })
        .catch(error => {
            console.error('Error fetching track:', error);
            spinner.style.display = 'none';
            songDisplay.style.display = 'block';
            songDisplay.innerHTML = '<p>Sorry, failed to load song. Please try again.</p>';
        });
}
