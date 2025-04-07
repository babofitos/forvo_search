(function getUrls(lang) {
    const list = document.querySelector(`#pronunciations-list-${lang}`)
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

        //the sibling div with class 'more' has a child that contains the votes
        const moreDiv = div.nextElementSibling.nextElementSibling.nextElementSibling.nextElementSibling;

        //string looks like this on the japanese website: "1 票"
        //if 0 votes there is just text inside .num_votes, no ElementChild span. voteText is undefined, so assign string
        const voteText = moreDiv.querySelector('.num_votes').firstElementChild?.innerText ?? "0 票";

        //we only care about the number
        const voteNum = voteText.split(' ')[0];

        //there are potentially two mp3 filenames, in indexes 4 and 1 
        //if the fourth element is "''", there is only one mp3 url, so return the first element
        //since each type of file uses a different base url, we need to pair them together
        return onClickValues[4] !== "''" 
            ? ['https://audio12.forvo.com/audios/mp3/', onClickValues[4], author, voteNum] 
            : ['https://audio12.forvo.com/mp3/', onClickValues[1], author, voteNum];
    });
    return JSON.stringify(urls);
})