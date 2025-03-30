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
            pycmd(JSON.stringify([i, url]))
            copyButton.disabled = true;
        })
        container.appendChild(row);
    })
}

function downloadSuccess(i) {
    const rowIndex = i;
    const row = document.querySelectorAll('.row')[rowIndex];
    //disable button for one second minimum since it barely gets disabled normally
    setTimeout(() => {
        row.querySelector('.copy').disabled = false;
    }, 1000);
    row.querySelector('.copy-message').style.display = 'inline';
    setTimeout(() => {
        row.querySelector('.copy-message').style.display = 'none';
    }, 3000);
}