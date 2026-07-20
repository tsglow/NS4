
// vars
const scrBtn = document.getElementById('scrapBtn');
const loadDiv = document.getElementById('loader');
const contentDiv = document.getElementById('content');
const menuTabs = document.getElementById('menuTabs');
const todayNews = document.getElementById('todayNews');
const searchNews = document.getElementById('searchNews');
const searchBar = document.getElementById('searchBar');


// functions
async function getJson(url, contextName){
    const res = await fetch(url)
    const data = await res.json();        
    if (res.ok){        
        return data[contextName];
    } else {
        throw Error(data);
    };                                
}

function renderNews(array,parentElement){
    array.forEach(item => {
        const articleDiv = document.createElement('div');
        articleDiv.innerHTML = `
            <h3>${item.cat} | <a href="${item.link}" target="_blank">${item.title}</a> - ${item.media}</h3>
            <h4>${item.pubDate} | <a href="${item.link}" target="_blank">${item.link}</a></h4>      
            <h4><i>기사 요약</i> <br>${item.description}</h4>
            <h4><i>기사 전문</i> <br>${item.text}</h4>
            <br/><br/>
            `;
        parentElement.appendChild(articleDiv)
    });
}

function invertDisplay(element){
    if (element.style.display === 'none') {
        element.style.display = 'block';
    }
    else {
        element.style.display = 'none';
    }        
}


// listeners
scrBtn.addEventListener("click", async function(){
    
    invertDisplay(loadDiv);
    console.log(menuTabs.style.display);
    invertDisplay(menuTabs);
    console.log(menuTabs.style.display);
    invertDisplay(contentDiv);

    contentDiv.innerHTML = '';
    const newsJson = await getJson('scrap-news/','article');
    await renderNews(newsJson,contentDiv);
    todayNews.innerText = `News Today (총 ${newsJson.length}개의 기사)`

    invertDisplay(loadDiv);
    invertDisplay(menuTabs);
    invertDisplay(contentDiv);

})

