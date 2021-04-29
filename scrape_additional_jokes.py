from bs4 import BeautifulSoup
import requests
import re
import json


with open('jokes.json', 'r') as f:
    JOKES = json.load(f)
    
links = ['https://www.1000chistes.com/chistes-malos/pagina/']

for prompt in links:
    for i in range(1, 10):
        p = f'{prompt}{i}'
        r = requests.get(p)
        soup = BeautifulSoup(r.content, fromEncoding='latin-1')
        soup.prettify('latin-1')

        scraped_jokes = soup.find_all('article')

        final_jokes = []
        for j in scraped_jokes:
            title = j.find(itemprop='headline').find('a')['title'][7:]
            text = j.find(itemprop='articleBody').text
            #print(f'{title}\n{text}')
            joke = {'title': title, 'text': text}
            final_jokes.append(joke)
        print(p)
        category = prompt.replace('-', '|').replace('/', '|').replace('&', '|').replace('?s=', '|').split('|')[-3]
        print(category)
        if category in JOKES:
            JOKES[category] += final_jokes
        else:
            JOKES[category] = final_jokes

print(JOKES)

with open('jokes.json', 'w') as f:
    json.dump(JOKES, f)
