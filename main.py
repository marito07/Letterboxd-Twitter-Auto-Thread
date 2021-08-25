import tweepy
# Import requests (to download the page)
import requests
from bs4 import BeautifulSoup
import re
import time
import string
import os


#set the headers as a browser
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

data = open('data', 'r').read().splitlines()

api_key = data[0]
api_key_secret = data[1]
access_token = data[2]
access_token_secret = data[3]

url = 'https://letterboxd.com/' + data[4] + '/films/diary/'

twitterThreadID = data[5]
listIndex = int(data[6])

authenticator = tweepy.OAuthHandler(api_key, api_key_secret)
authenticator.set_access_token(access_token, access_token_secret)

api = tweepy.API(authenticator, wait_on_rate_limit=True)

previous_movie = ''
while True:
    #download the homepage
    response = requests.get(url, headers=headers)
    #parse the downloaded homepage and grab all text
    soup = BeautifulSoup(response.text, "lxml")
    last_movie = soup.find("tr", {"class": "diary-entry-row"})
    if previous_movie != '' and last_movie != previous_movie:
        last_movie_text = last_movie.find("h3", {"class": "headline-3 prettify"})
        rating = last_movie.find("span", {"class": "rating"})
        movie_url =  last_movie_text.find("a")
        movie_url_array = movie_url['href'].split('/')
        del movie_url_array[0]
        del movie_url_array[0]
        if movie_url_array[-2].isnumeric():
            del movie_url_array[-2]
        response2 = requests.get('https://letterboxd.com/' + '/'.join(movie_url_array), headers=headers)
        soup2 = BeautifulSoup(response2.text, "lxml")
        last_movie_img = soup2.find("img", {"class": "image"})
        movie_year = soup2.find("small", {"class": "number"})
        film_header = soup2.find("section", {"class": "film-header-lockup"})
        directors = film_header.find_all("span", {"class": "prettify"})
        directors_text = ''
        for dir in directors:
            directors_text += dir.text
            if directors.index(dir) != len(directors)-2 and len(directors) != 1:
                directors_text += ', '
            if directors.index(dir) == len(directors)-2 and len(directors) != 1:
                directors_text += ' & '
        urlBoxId = soup2.find("input", {"class": "field -transparent"})
        print(directors_text)
        print(last_movie_text)
        print(last_movie_img['srcset'])
        print(urlBoxId['value'])
        filename = 'temp.jpg'
        requestImage = requests.get(last_movie_img['srcset'], stream=True)
        with open(filename, 'wb') as image:
            for chunk in requestImage:
                image.write(chunk)
        lines = []
        lines.append(str(listIndex) + '. ' + last_movie_text.text + ' (' + movie_year.text + ')')
        listIndex = listIndex + 1
        lines.append('Dir: ' + directors_text)
        lines.append('')
        lines.append(rating.text.strip())
        lines.append('')
        lines.append(urlBoxId['value'])
        multiline_tweet = "\n".join(lines)
        tweett = api.update_with_media(filename, status=multiline_tweet, 
                                 in_reply_to_status_id=twitterThreadID, 
                                 auto_populate_reply_metadata=True)
        twitterThreadID = tweett.id
    else:
        print('No new movie')
    previous_movie = last_movie
    #previous_movie_rating = soup.find("span", {"class": "rating rated-5"})

    time.sleep(3)
    
