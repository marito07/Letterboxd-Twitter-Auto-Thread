import tweepy
# Import requests (to download the page)
import requests
from bs4 import BeautifulSoup
import re
import time
import string


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
    last_movie = soup.find("h3", {"class": "headline-3 prettify"})
    if previous_movie != '' and last_movie != previous_movie:
        file = open('temp.txt', 'w')
        file.write(listIndex + '. ' +  + ')\n')
        tweett = api.update_status(status=last_movie.text, 
                                 in_reply_to_status_id=twitterThreadID, 
                                 auto_populate_reply_metadata=True)
        twitterThreadID = tweett.id
        ++listIndex
    else:
        print('No new movie')
    previous_movie = last_movie
    #previous_movie_rating = soup.find("span", {"class": "rating rated-5"})

    time.sleep(10)
    
