from bs4 import BeautifulSoup
import requests
import json

with open('jokes.json', 'r') as f:
    JOKES = json.load(f)


all_jokes = []
for i in range(1, 7):
    prompt = f'https://line.17qq.com/articles/auheaetcx_p{i}.html'
    r = requests.get(prompt)
    soup = BeautifulSoup(r.content, fromEncoding='latin-1')
    soup.prettify('latin-1')

    scraped_jokes = soup.find_all(class_='artimg')

    for j in scraped_jokes:
        tag = j.img

        title = tag['title']
        text = ''
        image = 'https:' + tag['src']

        joke = {'title': title, 'text': text, 'image': image}
        all_jokes.append(joke)

    category = 'moscas'
    JOKES[category] += all_jokes

for x in JOKES.values():
    print(x)

with open('jokes.json', 'w') as f:
    json.dump(JOKES, f)
