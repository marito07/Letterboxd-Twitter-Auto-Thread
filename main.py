import tweepy
import requests
from bs4 import BeautifulSoup
import time
import os
import dotenv


def replace_line(file_name, line_num, text):
    lines = open(file_name, 'r').readlines()
    lines[line_num] = text + '\n'
    out = open(file_name, 'w')
    out.writelines(lines)
    out.close()

#set the headers as a browser
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

data = open('data', 'r').read().splitlines()

dotenv.load_dotenv()

api_key = os.environ["API_KEY"]
api_key_secret = os.environ["API_KEY_SECRET"]
access_token = os.environ["ACCESS_KEY"]
access_token_secret = os.environ["ACCESS_KEY_SECRET"]

url = 'https://letterboxd.com/' + os.environ["TWITTER_NAME"] + '/films/diary/'

twitterThreadID = data[0]
listIndex = int(data[1])

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
    rewatch = last_movie.find("td",{"class":"td-rewatch center icon-status-off"})
    if previous_movie != '' and last_movie != previous_movie and rewatch != None:
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
        print(urlBoxId['value'])

        # Movie Poster
        last_movie_img = soup2.find("img", {"class": "image"})
        filename = 'temp.jpg'
        requestImage = requests.get(last_movie_img['srcset'], stream=True)
        with open(filename, 'wb') as image:
            for chunk in requestImage:
                image.write(chunk)

        # Prepares the Tweet
        lines = []
        lines.append(str(listIndex) + '. ' + last_movie_text.text + ' (' + movie_year.text + ')')
        listIndex = listIndex + 1
        lines.append('Dir: ' + directors_text)
        lines.append('')
        lines.append(rating.text.strip())
        lines.append('')
        if review != None:
            review_text = review.find(("p"))
            lines.append(review_text.text.strip())
            lines.append('')
        lines.append(urlBoxId['value'])
        multiline_tweet = "\n".join(lines)
        # Sends Tweet
        tweett = api.update_with_media(filename, status=multiline_tweet, 
                                 in_reply_to_status_id=twitterThreadID, 
                                 auto_populate_reply_metadata=True)        
        twitterThreadID = tweett.id


        # Store data in the file
        
        replace_line('data', 0, str(twitterThreadID))
        replace_line('data', 1, str(listIndex))
    else:
        print('No new movie')
        
    previous_movie = last_movie

    time.sleep(300)
    


