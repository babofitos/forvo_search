function createRow(data) {
    //data is [author, url, votes]
    document.querySelector('#msg').style.display = 'none';
    const template = document.getElementById('pronunciation-template');
    const container = document.getElementById('pronunciations-container');

    data.forEach((pronunciation, i) => {
        const author = pronunciation[0];
        const url = pronunciation[1];
        const votes = pronunciation[2];
        const row = template.content.cloneNode(true);
        
        row.querySelector('.author').textContent = author;
        row.querySelector('.votes').textContent = `Votes: ${votes}`;

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
            const res = {
                type: 'copy',
                val: [i, url]
            };

            pycmd(JSON.stringify(res));
            copyButton.disabled = true;
        })
        container.appendChild(row);
    })
}

function searchWord() {
    const word = document.querySelector('#search-box').value;
    const res = {
        type: 'search',
        val: word
    };

    pycmd(JSON.stringify(res));
}

function pageNotFound() {
    document.querySelector('#msg').innerText = 'Page not found';
}

function noPronunciationsFound() {
    document.querySelector('#msg').innerText = 'No pronunciations found';
}

function showFetchForvoMessage() {
    document.querySelector('#msg').innerText = 'Fetching Forvo Data...';
}

function fillWordInInput(word) {
    document.querySelector('#search-box').value = word;
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

document.addEventListener("DOMContentLoaded", function() {
    document.querySelector('#search-button').addEventListener('click', function() {
        searchWord();
    });

    document.querySelector('#search-form').addEventListener('submit', function(ev) {
        ev.preventDefault();
    });
});