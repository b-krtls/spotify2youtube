"""
Download Songs from Spotify by finding the song from Youtube and 
grabbing audio with youtube-dl in Linux.

How it works:
-:FIXME:

Checklist:
- youtube-dl AND ffmpeg must be installed/accessible beforehand in Linux
- bs4 is required
- selenium is required
- Chrome-Webdriver that is compatible with your current Google Chrome
    is required
- Chrome-Webdriver should be set as a Path enviromental variable.
"""
import os
import requests
from bs4 import BeautifulSoup
import re
from pprint import pprint
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd


def get_song_details(url:str):
    """
    Given an URL, retrieve the html code and separate it to obtain
    song info
    """

    page = requests.get(url)
    # print(dir(page)); print(page.url)
    soup = BeautifulSoup(page.text, "html.parser")
    title = str(soup.find("title"))
    # print(title)

    temp = re.split(">| \| ", title) 
    temp = temp[1].split(" - song by ")
    # print(temp)
    name_song = temp[0]
    name_artist = temp[1]

    dict_ = {
        "song": name_song,
        "artists": [i for i in name_artist.split(",") ]
    }
    # print(name_song, "==",name_artist, "\n")
    # pprint(dict_)
    # return name_song, name_artist
    return dict_


def parse_search_query(song_data:dict) -> str:
    """
    From a dictionary containing a dict with the form
    dict_ = {
        "song": name_song,
        "artists": [i for i in list_of_artist_names]
    }

    generate a search_query compatible with youtube search query
    """
    name_song = song_data["song"]
    name_artist = song_data["artists"]

    search_query = name_song + " " + " ".join(name_artist)
    search_query = search_query.replace(" ", "_")
    search_query = search_query.replace(",", "_")
    search_query = re.sub(r'\_+', '+', search_query)
    
    song_data.update({
        "search_query": search_query,
    }
    )

    pprint(song_data)
    return search_query


def find_youtube_videos(search_query):
    """
    With the current state of Youtube, the webpage is thought to be using
    a scripting language to dynamically create the webpage, which makes it
    difficult to use standard HTTP requests (with requests module) to :method:
    'get' the response object with a html '<script>' tag which does not contain 
    necessary information in a structured manner. Selenium and ChromeWebdriver 
    is used as a result of this limitation of :module:'requests' 

    :param search_query: A string literal that contains the parsed searching 
        string that is joined with youtube search query URL
    :type search_query: class:'str'
    :return: The list of strings, each of which is a title of the videos as a 
    result of the search on Youtube
    :rtype: list
    """
    chrome_options = Options()
    chrome_options.headless = True # Run chrome without UI
    # chrome_options.add_argument("--headless") # also works
    """
    #chrome_options.add_argument("--disable-extensions")
    #chrome_options.add_argument("--disable-gpu")
    #chrome_options.add_argument("--no-sandbox") # linux only
 
    """

    driver = webdriver.Chrome(options=chrome_options)
    search_url = "https://www.youtube.com/results?search_query={}".format(
        search_query
    )
    print(search_url)
    page = driver.get(search_url)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    # print(soup.prettify())
    # with open("mycontents2.html", "wb") as f:
    #     f.write(soup.prettify().encode("utf-8"))
    # pass

    # with open("mycontents.html", "wb") as f:
    #     f.write(soup.prettify().encode("utf-8"))
    # pass

    # candidates = soup.find(search_tag, {"class": search_term})
    # OR
    candidates = soup.find_all(
        "a",
        {
            "id": "video-title",
            # "class": "style-scope ytd-video-renderer"
        }
        )
    # print(len(candidates))
    # print(type(candidates[0]))

    # print(str(candidates[0]))
    """
    each candidate

    <a aria-label="Benjamin Cambridge - Comptine d'un autre été, l'après midi | Classical Piano Version by Piano Fruits Music 4 months ago 1 minute, 50 seconds 7,349 views" class="yt-simple-endpoint style-scope ytd-video-renderer" href="/watch?v=qE-sCalGpcE" id="video-title" title="Benjamin Cambridge - Comptine d'un autre été, l'après midi | Classical Piano Version">
    <yt-icon class="style-scope ytd-video-renderer" hidden="" id="inline-title-icon"><!--css-build:shady--></yt-icon>
    <yt-formatted-string aria-label="Benjamin Cambridge - Comptine d'un autre été, l'après midi | Classical Piano Version by Piano Fruits Music 4 months ago 1 minute, 50 seconds 7,349 views" class="style-scope ytd-video-renderer">Benjamin Cambridge 
    - Comptine d'un autre été, l'après midi | Classical Piano Version</yt-formatted-string>
    </a>
    """
    print("\t_Videos-Status_")
    video_list = list()
    for i, candidate in enumerate(candidates):
        pattern_title = re.findall(r"(title=)\"(.*?)\"", str(candidate))
        pattern_href = re.findall(r"(href=)\"(.*?)\"", str(candidate))
        # print(temp)
        if pattern_title != [] and pattern_href != []:  # If Regex finds at least 1 match to have a non-empty list
            title = pattern_title[0][1]
            href = pattern_href[0][1]
            video_list.append((title,href))
            message = "# Successfully grabbed title of video({:02d})"
        else:
            message = "# Failed to determine title of entity({:02d})"
        print(message.format(i), end="\n")
    print("\n")
    # del temp, message
    return video_list


def match_song_and_video(song_data, video_list):
    """:FIXME:
    Determine and grab the video that has the highest relevance to the 
    original song name. This relevance is quantified by a calculated score
    based on how many keywords in the search query appear in the video title
    in relevance to the number of words in the video title string.
    
    :FIXME:
    :return: A dictionary in the form 
        dict_['song'] = :str:'song'
        dict_['artists'] = :list:'artists'
        dict_['search_query'] = :str:'search_query'
        dict_['matched_video_title'] = :str:'matched_video_title'
        dict_['matched_video_url'] = :str:'matched_video_url'
    :rtype: dict
    """
       
    search_query = song_data["search_query"]
    keywords = search_query.lower().split("+")

    chars_to_remove = ["-", ".", "\\", "/" ]
    rx = '[' + re.escape(''.join(chars_to_remove)) + ']'

    print("\t_Scores_")
    scores_list = list()
    for video, href in video_list:
        video = video.lower()
        video =  re.sub(rx, ' ', video) #Replace all chars_to_remove with spcce
        video = re.sub(r'(\s)\1+', r'\1', video) #Reduce whitespaces to 1 space
        
        # Calculate the score
        # # Determine if each keyword is a substring of video title, and
        # #     determine how many of such keyword(s) is actually contained
        score = sum([(keyword in video) for keyword in keywords])
        # # Attempt to "Normalize" the score with the number of words that
        # #     that is in the video-title
        score = score/len(video.split(" ")) if len(video.split(" "))!=0 else 0
        scores_list.append(score)

        print("({:03f}) - {}".format(score, video)) 

    # print(scores_list)

    maxval = max(scores_list)
    i = scores_list.index(maxval)
    matched_video_title = video_list[i][0]
    matched_video_url = "https://www.youtube.com" + video_list[i][1]

    # print(i, video_list[i][0])
    # print(video_list[i][1])
    # print("www.youtube.com" + video_list[i][1])

    print("\n\t_ANS:BEST-GUESS_")
    print(matched_video_title)
    print(matched_video_url)
    print("\n")

    # Live Te
    chrome_options = Options()
    chrome_options.headless = False  # Run chrome without UI
    # chrome_options.add_argument("--headless") # also works
    driver = webdriver.Chrome(options=chrome_options)
    page = driver.get(matched_video_url)
    input("# Press AnyKey to Leave")
    driver.quit()


if __name__ == '__main__':

    # read_spotify_urls() :TODO:
    URL = "https://open.spotify.com/track/64f5bf2jyAkrsucnG9FXot"
    URL = "https://open.spotify.com/track/7LNAIE5fdvAjrUJH18x5P4"
    URL = "https://open.spotify.com/track/7M13FwBAKWNa2jqcZeUhL6"
    URL = "https://open.spotify.com/track/6NYqFxemN4ZdpIO8HGrCzC"
    URL = "https://open.spotify.com/track/4O2N861eOnF9q8EtpH8IJu"
    # URL = "https://open.spotify.com/track/1JYxCgv4Jlx2X4SYNtXgkB"
    # URL = "https://open.spotify.com/track/25ViKfgVhbDr3IzhsjeQzU"
    URL = "https://open.spotify.com/track/03wqvxOYgomDNUWTzesadS"

    song_data = get_song_details(URL)
    search_query = parse_search_query(song_data)
    video_list = find_youtube_videos(search_query)
    match_song_and_video(song_data, video_list)
