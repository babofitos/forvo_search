function createRow(data) {
    document.querySelector('#fetching-msg').style.display = 'none';
    const template = document.getElementById('pronunciation-template');
    const container = document.getElementById('pronunciations-container');

    data.forEach((pronunciation, i) => {
        const author = pronunciation[0];
        const url = pronunciation[1];
        const row = template.content.cloneNode(true);
        
        row.querySelector('.author').textContent = author;
        const playButton = row.querySelector('.play');
        playButton.addEventListener('click', function() {
            playButton.disabled = true;
            const audio = new Audio(url);
            audio.play();
            audio.addEventListener('ended', function() {
                playButton.disabled = false;
            });
        });
        const copyButton = row.querySelector('.copy');
        copyButton.addEventListener('click', function() {
            pycmd(url)
        })
        container.appendChild(row);
    })
}