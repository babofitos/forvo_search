(function() {
    const list = document.querySelector('#pronunciations-list-ja')
    //word has no pronunciations if list doesn't exist
    if (!list) return JSON.stringify([]);
    //turn nodelist into array so we can map
    const playDivs = [...list.querySelectorAll("div[id^='play_']")];
    const urls = playDivs.map((div) => {
        //get the author's name
        const span = div.nextElementSibling;
        const spanInfo = span.querySelector('span');
        //if spanInfo has no child span, author name inside span,
        //otherwise author name inside child span's data-p2
        const author = spanInfo 
            ? spanInfo.getAttribute('data-p2')
            : span.innerText.split(':')[1];
        //get string value of onclick attr on each div and split by comma
        //the value is in the format "Play(45,'OTYwMD...','OTYwMD...',false,'','',..."
        const onClickValues = div.getAttribute("onclick").split(',');
        //there are potentially two mp3 filenames, in indexes 4 and 1 
        //if the fourth element is "''", there is only one mp3 url, so return the first element
        //since each type of file uses a different base url, we need to pair them together
        return onClickValues[4] !== "''" ? ['https://audio12.forvo.com/audios/mp3/', onClickValues[4], author] : ['https://audio12.forvo.com/mp3/', onClickValues[1], author];
    });
    return JSON.stringify(urls);
}())
