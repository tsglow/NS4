
// vars from doms
const scrapBtn = document.getElementById('scrapBtn');
const loadDiv = document.getElementById('loader');
const contentDiv = document.getElementById('content');
const menuTabs = document.getElementById('menuTabs');
const todayNews = document.getElementById('todayNews');
const searchNews = document.getElementById('searchNews');
const searchBar = document.getElementById('searchBar');
const searchForm = document.getElementById('searchForm');
const searchResult = document.getElementById('searchResult');



// template for html rendering
const IndividualNewsTemplate = '<h3>${dict.cat} | <a href="${dict.link}" target="_blank">${dict.title}</a> - ${dict.media}</h3><h4>${dict.pubDate} | <a href="${dict.link}" target="_blank">${dict.link}</a></h4><h4><i>기사 요약</i> <br>${dict.description}</h4><h4 class="newsText"><i>기사 전문</i> <br>${dict.text}</h4><br/><br/>';



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


async function getJsonWithForm(url,formBody, contextName){
    const res = await fetch(url, formBody);
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


function invertDisplay(element,style){    
    element.style.display = style;         
}


function swapActivity(el1, el2, content1, content2){    
    if (el1.className === "deactive"){
        el1.className = 'active';
        el2.className = 'deactive';
        invertDisplay(content1,'block');
        invertDisplay(content2,'none');
    };
}


function getPeriod(){
    const start = new Date();
    const end = new Date();
    start.getDay() === 1 ? end.setDate(end.getDate() - 3) : end.setDate(end.getDate() - 2);
    return [start,end];
}


function dateToString(date){
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}%3A${minutes}`;
}

// listeners
window.addEventListener("load", async function() {
    const [start, end] = getPeriod();
    const query = `start_time=${dateToString(start)}&end_time=${dateToString(end)}&order=-pubDate&cat=All&field=title&word=`;  
    const resultJson = await getJsonWithForm(   
        `search-news/?${query}`,       
        {method: 'GET'},
        'article'
    );
    await renderNews(resultJson,contentDiv);    
    todayNews.innerText = `News Today (총 ${resultJson.length}개의 기사)`;

    invertDisplay(scrapBtn,"block"); 
    invertDisplay(loadDiv,"none");
    invertDisplay(menuTabs,"block");
    invertDisplay(contentDiv,"block");
});


scrapBtn.addEventListener("click", async function(){  
    invertDisplay(scrapBtn,"none");   
    invertDisplay(loadDiv,"block");    
    invertDisplay(menuTabs,"none");    
    invertDisplay(contentDiv,"none");

    contentDiv.innerHTML = '';
    const newsJson = await getJson('scrap-news/','article');
    await renderNews(newsJson,contentDiv);
    todayNews.innerText = `News Today (총 ${newsJson.length}개의 기사)`;

    invertDisplay(scrapBtn,"block");  
    invertDisplay(loadDiv,"none");
    invertDisplay(menuTabs,"block");
    invertDisplay(contentDiv,"block");

    swapActivity(todayNews,searchNews,contentDiv,searchBar);
});


searchForm.addEventListener('submit', async function (e) {    
    e.preventDefault();
    invertDisplay(loadDiv,"block");
    invertDisplay(searchResult,"hide");

    const formData = new FormData(this);     
    const queryParams = new URLSearchParams(formData);
    // const formCsrfToken = document.getElementsByName('csrfmiddlewaretoken').value;    
    searchResult.innerHTML = '';

    
    const resultJson = await getJsonWithForm(        
        `search-news/?${queryParams.toString()}`,
        {method: 'GET'},
        'article'
    );    
    /*
    post를 쓸 경우
    const resultJson = await getJsonWithForm(
        'search-news/',
        {method: 'POST', body: formData},
        'article'
    );    
    */
    await renderNews(resultJson,searchResult);

    invertDisplay(loadDiv,"none");
    invertDisplay(searchResult,"block");
});


searchNews.addEventListener("click", () => swapActivity(searchNews,todayNews,searchBar,contentDiv));
todayNews.addEventListener("click", () => swapActivity(todayNews,searchNews,contentDiv,searchBar));