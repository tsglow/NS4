
// vars from doms
const scrapBtn = document.getElementById('scrapBtn');
const loadDiv = document.getElementById('loader');
const contentDiv = document.getElementById('content');
const menuTabs = document.getElementById('menuTabs');
const todayNews = document.getElementById('todayNews');
const searchNews = document.getElementById('searchNews');
const searchBar = document.getElementById('searchBar');


// template for html rendering
const IndividualNewsTemplate = '<h3>${dict.cat} | <a href="${dict.link}" target="_blank">${dict.title}</a> - ${dict.media}</h3><h4>${dict.pubDate} | <a href="${dict.link}" target="_blank">${dict.link}</a></h4><h4><i>기사 요약</i> <br>${dict.description}</h4><h4><i>기사 전문</i> <br>${dict.text}</h4><br/><br/>';


// functions
function templateToHtml(dict,template){
    return template.replace(/\$\{dict\.([^}]+)\}/g, function(match, key) {
        return dict[key] !== undefined ? dict[key] : '';});
}


async function getJson(url, contextName){
    const res = await fetch(url);
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
        articleDiv.innerHTML = templateToHtml(item,IndividualNewsTemplate);
        parentElement.appendChild(articleDiv);
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



function swapActivity(el1, el2, content1, content2){    
    if (el1.className === "deactive"){
        el1.className = 'active';
        el2.className = 'deactive';
        content1.style.display = 'block';
        content2.style.display = 'none';

    };
    /*
    const el1Style = window.getComputedStyle(el1);
    const el2Style = window.getComputedStyle(el2);

    const tempBg =  el1Style.getPropertyValue("background-color");
    const tempColor =  el1Style.getPropertyValue("color");

    el1.style.backgroundColor = el2Style.getPropertyValue("background-color");
    el1.style.color = el2Style.getPropertyValue("color");

    el2.style.backgroundColor = tempBg;
    el2.style.color = tempColor;

    el2.removeEventListener("click", () => swapStyles(el1,el2));
    el1.addEventListener("click", () => swapStyles(el2, el1));
    */
}





// listeners
scrapBtn.addEventListener("click", async function(){
    
    invertDisplay(loadDiv);    
    invertDisplay(menuTabs);    
    invertDisplay(contentDiv);

    contentDiv.innerHTML = '';
    const newsJson = await getJson('scrap-news/','article');
    await renderNews(newsJson,contentDiv);
    todayNews.innerText = `News Today (총 ${newsJson.length}개의 기사)`;

    invertDisplay(loadDiv);
    invertDisplay(menuTabs);
    invertDisplay(contentDiv);
})


searchNews.addEventListener("click", () => swapActivity(searchNews,todayNews,searchBar,contentDiv));
todayNews.addEventListener("click", () => swapActivity(todayNews,searchNews,contentDiv,searchBar));