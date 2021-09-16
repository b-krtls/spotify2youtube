"""
Download Songs from Spotify by finding the song from Youtube and 
grabbing audio with youtube-dl in Linux.

How it works:
- Web-scraping 
-:FIXME:

Checklist:
- youtube-dl AND ffmpeg must be installed/accessible beforehand in Linux
- :module:'bs4'  is required
- :module:'selenium' is required
- Chrome-Webdriver that is compatible with your current Google Chrome
    is required
- Chrome-Webdriver should be set as a Path enviromental variable.

 TODO:
 - [ ] Implement asynchronous calls for WebDriver 
    - with selenium?/asyncio/multithreading/multiprocessing or alike
 - [ ] Write docstrings for functions & comments in Sphinx/reST format
 - [ ] Check and validate style for PEP-8, i.e. check code margins and spaces
    - Max. Line Length = 79 chars, Max. Comment & Docstring line length = 72
 - [ ] Clean up unneccessary imports 
 - [ ] Argument Parsing for using the script through a CLI
 - [ ] Possibly update the code to be hosted on a website like Github-Pages
 - [ ] Possibly incorporate different Webdrivers that the user specifies
"""
import os
import sys
import platform
import argparse
import requests
from bs4 import BeautifulSoup
import re
from pprint import pprint
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd

def spotify2youtube(url):
    """
    Given a Spotify song URL, find and retrieve the most relevant video to the song,
    from Youtube.

    :param url: Spotify URL of an individual song
    :type url: class:'str'
    :return: Youtube URL of the most relevant video to the song in Spotify URL
    :rtype: class:'str'

    :TODO:
    This may be implemented not as functional programming but as a 
    class like :class:'VideoMatcher' or :class:'spotify2youtube' with
    internal methods. The functional programming method may be more beneficial
    if a programmer wants to import indiviual functions for their own use.
    """

    song_data = get_song_details(url)
    search_query = parse_search_query(song_data)
    # video_list = find_youtube_videos(search_query)
    video_list = find_youtube_videos_v2(search_query)
    matched_video_url = match_song_and_video(song_data, video_list)
    return_code = download_youtube_song(matched_video_url)
    return return_code


def read_cli_inputs():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "-f", "--file",
        help = "Execute the script for a text file"
        )
    argparser.add_argument(
        "-s", "--single",
        help = "Execute the script for a single URL"
        )
    argparser.add_argument(
        "--headless", 
        help = "Run WebDriver in headless mode",
        action = "store_true"
        )
    argparser.add_argument(
        "--log", 
        help = "Log the execution history in cwd",
        action = "store_true"
        )
    cli_args = argparser.parse_args()

    # :TODO: :FIXME: 
    # Redirect argparser attributes to correct functions to modify
    # execution

    with open(sys.argv[1], 'r') as f:
        urls = f.readlines()
    for i, line in enumerate(urls):
        urls[i] = line.rstrip("\n")
    return urls


def get_song_details(url: str):
    """
    Given an URL, retrieve the html code and separate it to obtain
    song info

    :param url: Spotify song URL
    :type url: class:'str'
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


def parse_search_query(song_data: dict) -> str:
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


# :XXX: Possibly deprecated due to scoring and insufficient scraping of tags
def find_youtube_videos_v1(search_query):
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


def find_youtube_videos_v2(search_query):
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
    chrome_options.headless = True  # Run chrome without UI
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

    candidates = []
    candidates = soup.find_all(
        "a",
        {
            "id": "video-title",
            # "class": "style-scope ytd-video-renderer"
        }
    )

    # print(len(candidates))

    candidates_uploaders = soup.find_all(
        "a",
        {
            "class": "yt-simple-endpoint style-scope yt-formatted-string",
            "dir": "auto",
            "spellcheck": "false"
        }
    )

    # pprint(len(candidates_uploaders := candidates_uploaders[::2]))
        # # pprint(candidate_uploaders)


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
        pattern_channelname = re.findall(
            r"\>(.*?)\</a\>", 
            str(candidates_uploaders[i])
            )\
            
        
        # print(pattern_channelname)
        # print(temp)
        if pattern_title != [] and pattern_href != []:  # If Regex finds at least 1 match to have a non-empty list
            title = pattern_title[0][1]
            href = pattern_href[0][1]
            channelname = pattern_channelname[0]
            video_list.append((title, href, channelname))
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

    chars_to_remove = ["-", ".", "\\", "/" , "(", ")", "\'"]
    rx = '[' + re.escape(''.join(chars_to_remove)) + ']'

    print("\t_Scores_")
    scores_list = list()
    enum = -1
    for title, href, channelname in video_list:
        enum += 1
        video = title.lower() + " " + channelname.lower()
        video = re.sub("&(amp;)+", ' ', video)
        video =  re.sub(rx, ' ', video) #Replace all chars_to_remove with spcce
        video = re.sub(r'(\s)\1+', r'\1', video) #Reduce whitespaces to 1 space
        # Calculate the scores

        # # Determine if each keyword is a substring of  
        # #     video (title + channelname), and
        # #     determine how many of such keyword(s) is actually contained
        score1 = sum([(keyword in video) for keyword in keywords])

        # # Determine the number of words in video (title + channelname) 
        # #     that is also a keyword for the search_query
        # # e.g. The more words in the video that contains a keyword for search
        # #     the better
        score2 = sum([(word in keywords) for word in video.split(" ")])


        # # Attempt to "Normalize" the score with the number of words that
        # #     that is in the video-title
        factor = (1/len(video.split(" "))) if len(video.split(" ")) != 0 else 0
        score1 = score1*factor
        score2 = score2*factor
        scores_list.append(
            max(score1,score2)
            )

        print("{:02d}({:0.3f} {:0.3f}) - {}".format(
                enum,
                score1, 
                score2, 
                video
                )
            ) 

    # print(scores_list)

    maxval = max(scores_list)
    ind = scores_list.index(maxval)
    matched_video_title = video_list[ind][0]
    matched_video_url = "https://www.youtube.com" \
                        + video_list[ind][1] # Add href

    # print(i, video_list[i][0])
    # print(video_list[i][1])
    # print("www.youtube.com" + video_list[i][1])

    print("\n\t_ANS:BEST-GUESS_")
    print(ind)
    print(matched_video_title)
    print(matched_video_url)
    print("\n")

    # Live Te
    chrome_options = Options()
    chrome_options.headless = False  # Run chrome without UI
    # chrome_options.add_argument("--headless") # also works
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(matched_video_url)
    input("# Press AnyKey to Leave")
    driver.quit()

    return matched_video_url


def download_youtube_song(matched_video_url): #:FIXME:
    """
    OS-dependent, 
    :TODO: 
    check if it works in virtual machines,
    Check if it works in WSL and other emulator-like environments
    """
    cli_os = platform.system().lower()
    print("\t_Download-Status_")

    if cli_os == "linux":
        os.system("alias youtube2mp3=\"youtube-dl --extract-audio --audio-format mp3\"")
        cmd = "youtube2mp3 {}".format(matched_video_url)
        return_code = os.system(cmd)
        print(return_code)
        return return_code

    if cli_os == "windows":
        print("Downloader is not implemented yet")
        return NotImplemented


if __name__ == '__main__':
    

    # urls = read_cli_inputs()  
    # #:HACK:
    URL = "https://open.spotify.com/track/64f5bf2jyAkrsucnG9FXot"
    URL = "https://open.spotify.com/track/7LNAIE5fdvAjrUJH18x5P4"
    URL = "https://open.spotify.com/track/7M13FwBAKWNa2jqcZeUhL6" 
    URL = "https://open.spotify.com/track/6NYqFxemN4ZdpIO8HGrCzC" 
    URL = "https://open.spotify.com/track/4O2N861eOnF9q8EtpH8IJu" #Difficult
    URL = "https://open.spotify.com/track/1JYxCgv4Jlx2X4SYNtXgkB"
    URL = "https://open.spotify.com/track/25ViKfgVhbDr3IzhsjeQzU"
    URL = "https://open.spotify.com/track/03wqvxOYgomDNUWTzesadS"
    URL = "https://open.spotify.com/track/4TqYHkRMUc5XpBGUcpYNep"

    spotify2youtube(URL)
