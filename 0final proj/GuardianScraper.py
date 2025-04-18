import re
from bs4 import BeautifulSoup
import requests
import newspaper

def getTopHeadlines(api_key, section):
    results = []
    if section=="crime":
        response = requests.get("https://www.theguardian.com/uk/ukcrime")
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.find_all('div', class_="dcr-f9aim1")
            results.extend(
                {
                    'headline': article.find('h3').get_text(),
                    'url': "https://www.theguardian.com"+article.find('a', href=True)['href'],
                }
                for article in articles[:10]
            )
    else:
        base_url = "https://content.guardianapis.com/search"
        params = {
            'api-key': api_key,
            'page-size': 10,
            'show-fields': 'headline,trailText,byline',
            'show-tags': 'keyword',
        }

        # if genre selected dcr-f9aim1
        if section:
            params['section'] = section
        
        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            print("Failed to retrieve data")
            return []
        
        data = response.json()
        articles = data['response']['results']
        
        
        results.extend(
            {
                'headline': article['fields']['headline'],
                'url': article['webUrl'],
            }
            for article in articles
        )
    
    return results

def getArticleData(api_key, article_url):
    
    base_url = article_url.replace("www.theguardian","content.guardianapis")
    params = {
        'api-key': api_key,
        'show-fields': 'body,headline,trailText,main',
        'show-elements': 'all'
    }
    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        print("Failed to retrieve article data")
        return None
    
    # title 0, subtitle 1, body 2, captions, link
    title = ""
    subTitle = ""
    content=""
    captions = {}
    #links = []

    data = response.json()
   
    article = data['response']['content']
    title = article['fields']['headline']
    body_html = article['fields']['body']
    subTitle = article['fields']['trailText']
    soup = BeautifulSoup(body_html, "html.parser")
    body = soup.get_text()

    articleData = {
        "title": title,
        "url":article_url,
        "subTitle": subTitle,
        "content": "api " + body,
        "captions": captions,
        #"links": links
    }
    return articleData

