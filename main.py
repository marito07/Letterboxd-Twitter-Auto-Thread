import tweepy
import requests
from bs4 import BeautifulSoup
import time
import os
import dotenv
import psycopg2

from telegram.ext import *


dotenv.load_dotenv()


DATABASE_URL = os.environ.get('DATABASE_URL')
con = psycopg2.connect(DATABASE_URL)
cur = con.cursor()

cur.execute("SELECT indexID FROM twitter_listID where id=1")

myresult = cur.fetchone()[0]

listIndex = int(myresult)

cur.execute("SELECT indexID FROM miniseries where id=1")

myresult = cur.fetchone()[0]

listIndexSeries = int(myresult)

cur.execute("SELECT tweet_id FROM tweet_id_table where id=1")

myresult = cur.fetchone()[0]

twitterThreadID = str(myresult)

api_token = os.environ["API_TOKEN"]

updater = Updater(api_token)
dp = updater.dispatcher

#set the headers as a browser
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

api_key = os.environ["API_KEY"]
api_key_secret = os.environ["API_KEY_SECRET"]
access_token = os.environ["ACCESS_KEY"]
access_token_secret = os.environ["ACCESS_KEY_SECRET"]

url = 'https://letterboxd.com/' + os.environ["TWITTER_NAME"] + '/films/diary/'

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
    last_movie_text = last_movie.find("h3", {"class": "headline-3 prettify"})
    rewatch = last_movie.find("td",{"class":"td-rewatch center icon-status-off"})
    if previous_movie != '' and last_movie_text.text != previous_movie and rewatch != None:
        rating = last_movie.find("span", {"class": "rating"})
        movie_url =  last_movie_text.find("a")
        movie_url_array = movie_url['href'].split('/')
        del movie_url_array[0]
        del movie_url_array[0]
        if movie_url_array[-2].isnumeric():
            del movie_url_array[-2]
        response2 = requests.get('https://letterboxd.com/' + '/'.join(movie_url_array), headers=headers)
        soup2 = BeautifulSoup(response2.text, "lxml")

        # Checks if its a movie or a tv show
        allButtons = soup2.findAll("a", {"class": "micro-button"})
        auxString = str(allButtons)
        series = auxString.find("/tv")
        if series != -1:
            listIndexFull = 'Serie ' + str(listIndexSeries)
        else:
            listIndexFull = listIndex

        # Picks the year of the movie
        movie_year = soup2.find("small", {"class": "number"})

        # Picks the directors text
        film_header = soup2.find("section", {"class": "film-header-lockup"})
        directors = film_header.find_all("span", {"class": "prettify"})
        directors_str = [dire.text for dire in directors]
        directors_text = ''
        if soup2.find("a", {"id": "more-directors"}) == None:
            directors_text = ' & '.join(', '.join(directors_str).rsplit(', ', 1))
        else:
            directors_text = ', '.join(directors_str) + ' & co.'

        # Letterboxd URL
        urlBoxId = soup2.find("input", {"class": "field -transparent"})

        # Movie Review
        response3 = requests.get('https://letterboxd.com/' + movie_url['href'], headers=headers)
        soup3 = BeautifulSoup(response3.text, "lxml")
        review = soup3.find("div", {"class": "review body-text -prose -hero -loose"})

        # Debug
        print(directors_text)
        print(last_movie_text)
        if urlBoxId is not None:
            print(urlBoxId['value'])

        # Movie Poster
        last_movie_img = soup2.find("img", {"class": "image"})
        filename = 'temp.jpg'
        requestImage = requests.get(last_movie_img['srcset'], stream=True)
        with open(filename, 'wb') as image:
            for chunk in requestImage:
                image.write(chunk)
        
        auxLastMovie = last_movie_text
        if review != None:
            review_text = review.find(("p"))
            aux_text_temp = review_text.text.strip()
            custom_text_movie = aux_text_temp.split('//')
            if len(custom_text_movie) == 2:
                last_movie_text = custom_text_movie[0]
        
        # Prepares the Tweet
        lines = []
        lines.append(str(listIndexFull) + '. ' + last_movie_text.text + ' (' + movie_year.text + ')')
        lines.append('Dir: ' + directors_text)
        lines.append('')
        lines.append(rating.text.strip())
        lines.append('')
        if review != None:
            review_text = review.find(("p"))
            aux_text_temp = review_text.text.strip()
            custom_text_movie = aux_text_temp.split('//')
            if len(custom_text_movie) == 2:
                lines.append(custom_text_movie[1])
            else:
                lines.append(review_text.text.strip())
            lines.append('')
        if urlBoxId is not None:
            lines.append(urlBoxId['value'])
        multiline_tweet = "\n".join(lines)
        # Sends Tweet
        tweett = api.update_with_media(filename, status=multiline_tweet, 
                                 in_reply_to_status_id=twitterThreadID, 
                                 auto_populate_reply_metadata=True)        
        twitterThreadID = tweett.id

        # Prepares the Tweet
        lines = []
        lines.append('*'+str(listIndexFull) + '. ' + last_movie_text.text + ' (' + movie_year.text + ')*')
        lines.append('_Dir: ' + directors_text + '_')
        lines.append('')
        lines.append(rating.text.strip())
        lines.append('')
        if review != None:
            review_text = review.find(("p"))
            aux_text_temp = review_text.text.strip()
            custom_text_movie = aux_text_temp.split('//')
            if len(custom_text_movie) == 2:
                lines.append(custom_text_movie[1])
            else:
                lines.append(review_text.text.strip())
            lines.append('')
        if urlBoxId is not None:
            lines.append(urlBoxId['value'])
        multiline_tweet = "\n".join(lines)

        if series != -1:
            listIndexSeries = listIndexSeries + 1
        else:
            listIndex = listIndex + 1

        # Store data in the ddbb
        
        sql = "UPDATE twitter_listID SET indexID = " + str(listIndex) + " WHERE id = 1"

        cur.execute(sql)

        sql = "UPDATE tweet_id_table SET tweet_id = " + str(twitterThreadID) + " WHERE id = 1"

        cur.execute(sql)

        sql = "UPDATE miniseries SET indexID = " + str(listIndexSeries) + " WHERE id = 1"

        cur.execute(sql)

        con.commit()
        
        dp.bot.send_photo(chat_id=os.environ["CHANNEL_ID"], photo=last_movie_img['srcset'], caption=multiline_tweet, parse_mode= 'Markdown')
        
        last_movie_text = auxLastMovie
    else:
        print('No new movie')
        
    previous_movie = last_movie_text.text

    time.sleep(600)
    


