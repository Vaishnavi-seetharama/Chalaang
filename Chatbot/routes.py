import json

from quart import send_file, Blueprint, render_template
import asyncio
import aiohttp
from aiohttp import ClientTimeout
from quart import Quart, request, jsonify
from quart_cors import cors
from quart import send_file
from googlesearch import search
from bs4 import BeautifulSoup
import pyttsx3
import moviepy.editor as mp
import time
from moviepy.editor import VideoFileClip, concatenate_videoclips
import speech_recognition as sr
from openai import OpenAI
import os
import requests
from bs4 import BeautifulSoup
from pytrends.request import TrendReq
import matplotlib.pyplot as plt
import pandas as pd
import os
current_file_path = os.path.abspath(__file__)
current_directory = os.path.dirname(current_file_path)
current_directory=current_directory.replace("\\", "/")
file_path=(current_directory + "/search_result.csv")

bp = Blueprint("routes", __name__)


@bp.route('/', methods=['GET'])
async def home():
    return await send_file('templates/index.html')


async def fetch_url(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            response.raise_for_status()
            return await response.text()
    except Exception as e:
        print(f"Error fetching URL {url}: {e}")
        return None


async def site_details(session, url):
    html = await fetch_url(session, url)
    if html:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            title = soup.title.text if soup.title else "Title not found"

            # Get meta description
            metas = soup.find_all('meta')
            description = [meta.attrs['content'] for meta in metas if
                           'name' in meta.attrs and meta.attrs['name'] == 'description']
            description = description[0] if description else ""

            # Get og:image
            og_image = [meta.attrs['content'] for meta in metas if
                        'property' in meta.attrs and meta.attrs['property'] == 'og:image']
            og_image = og_image[0] if og_image else ""

            title_with_link = f"<a href='{url}' target='_blank'>{title}</a>"
            return {'url': url, 'title': title_with_link, 'description': description, 'og_image': og_image}
        except Exception as e:
            print(f"Error parsing HTML from {url}: {e}")
    return {'url': url, 'title': '', 'description': '', 'og_image': ''}


async def search_google_async(query, num_results=10, lang="en"):
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(10)  # Limit concurrency to 10
        search_results = list(set(search(query, num_results=num_results, lang=lang)))
        tasks = [site_details(session, url) for url in search_results]
        return await asyncio.gather(*tasks)

def track_keyword_trends(keyword):
    # Initialize pytrends
    pytrends = TrendReq()

    # Build Payload
    pytrends.build_payload(kw_list=[keyword])

    # Get Interest Over Time
    interest_over_time_df = pytrends.interest_over_time()

    # Plot the trend over time
    plt.figure(figsize=(10, 6))
    interest_over_time_df[keyword].plot()
    plt.title(f'Interest Over Time for "{keyword}" on Google Search')
    plt.xlabel('Date')
    plt.ylabel('Interest')
    plt.grid(True)
    plt.show()

    # Extract x-axis and y-axis data
    x_data_time = interest_over_time_df.index
    y_data_time = interest_over_time_df[keyword]
    plot_type = 'line'

    # Get Interest by Region
    interest_by_region_df = pytrends.interest_by_region()
    top_regions = interest_by_region_df[keyword].sort_values(ascending=False).head(10)

    # Plot the interest by region
    plt.figure(figsize=(10, 6))
    top_regions.plot(kind='bar', color='skyblue')
    plt.title(f'Top 10 Regions Interested in "{keyword}" on Google Search')
    plt.xlabel('Region')
    plt.ylabel('Interest')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y')
    plt.show()

    # Extract x-axis and y-axis data for region chart
    x_data_region = top_regions.index
    y_data_region = top_regions.values

    return [{'x1': x_data_time, 'label': 'Date', 'graph_type': plot_type ,'y1': y_data_time, 'label': 'Interest', 'graph_type': plot_type},{'x2': x_data_region, 'label': 'Region', 'graph_type': 'bar','y2': y_data_region, 'label': 'Interest', 'graph_type': 'bar'}]



@bp.route('/result', methods=['GET'])
async def show_result():
    data = {}
    with open("result.json", "r") as json_file:
        data = json.load(json_file)
    return await render_template('results.html', result=data)


@bp.route('/search', methods=['POST'])
async def search_google():
    result = {}
    user_message = (await request.json)['message']
    if check_matching_phrase(user_message):
        results_with_snippets = "Hello! I am feeling wonderfull today. How can I assist you today?"
    else:
        results_with_snippets = await search_google_async(user_message)

        # Save the results to an HTML file
        for i in results_with_snippets:
            var = i["description"]
        summary = summarize_content(var)
        result["summary"] = summary

    result["searches"] = results_with_snippets
    result["graph"] = track_keyword_trends(user_message)
    with open("result.json", "w") as json_file:
        json.dump(result, json_file)

    ## Saving the search result in a dataset
    primary_key_column = 'url'
    new_df = pd.DataFrame(results_with_snippets)
    existing_data = pd.read_csv(file_path)
    concatenated_data = pd.concat([existing_data, new_df], ignore_index=True)
    concatenated_data.drop_duplicates(subset=[primary_key_column], keep='first', inplace=True)
    concatenated_data.set_index(primary_key_column, inplace=True, drop=False)
    concatenated_data.to_csv(file_path, index=False)

    # Return the JSON response
    return jsonify({'results': result})




def video_audio_overlay():
    # Get the duration of the text-to-speech audio
    #     greeting()
    audio_path = r'img\testtemp.wav'
    audio = mp.AudioFileClip(audio_path)
    video_path = r'img\fox.mp4'
    audio_duration = audio.duration
    video_clip = mp.VideoFileClip(video_path)
    print("vaishnavi")

    if audio_duration < video_clip.duration:
        print(audio_duration)
        # Cut the video to match the audio length
        video_clip1 = video_clip.subclip(0, audio_duration)
    elif audio_duration > video_clip.duration:
        # Loop the video until the audio stops
        video_clip1 = video_clip.loop(duration=audio_duration)
    WIN_WIDTH = 900
    WIN_HEIGHT = 700
    DISPLAY = (WIN_WIDTH, WIN_HEIGHT)
    end_image_path = r'img\assistant2.png'  # Replace with the path to your image
    end_image = mp.ImageClip(end_image_path).set_duration(0.1)
    end_image.resize(DISPLAY)
    video_clip1.resize(DISPLAY)
    video_clip1 = mp.concatenate_videoclips([video_clip1, end_image])
    video_clip1 = video_clip1.set_audio(audio)
    output_path = r'C:\Chalaang\Chatbot\img\testvid2.mp4'
    video_clip.write_videofile(output_path, codec='libx264', fps=30)
    asyncio.create_task(change_video_src())


# async def change_video_src():
#     # JavaScript code to change the src attribute of the iframe
#     js_code = """
#     var iframe = document.getElementById('videoFrame');
#     iframe.src = 'img\testvid2.mp4';  // Change 'new_video.mp4' to the path of your new video file
#     """

#     return js_code


def assistant(audio):
    print("vaishnavi13")
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    engine.setProperty('rate', 130)
    engine.save_to_file(audio, r'../static/img/testtemp.wav')
    engine.runAndWait()
    video_audio_overlay()
    # Call the function to change video src


# Flask route to handle the request to change video src
@bp.route('/change_video_src')
async def change_video_src_handler():
    user_message = (await request.json)['message']
    results_with_snippets = await search_google_async(user_message)
    assistant(results_with_snippets['Summary'])

    return await change_video_src()


def check_matching_phrase(input_text):
    phrases = [
        "Hi",
        "Hello",
        "how are you?",
        "how are you",
        "Hi, how are you?",
        "What's up?",
        "How's it going?",
        "Good morning!",
        "Hey there!"
    ]
    for phrase in phrases:
        if input_text.lower() == phrase.lower():
            return True
    return False


def summarize_content(var):
    client = OpenAI(
        ,
    )

    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt="Summarize text  in 10 to 20 sentences " + var,
        max_tokens=100,  # Adjust the max tokens to control the length of the summary
        temperature=0.6,  # Adjust the temperature for diversity in the generated text
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,

    )
    summary = response.choices[0].text.strip()
    return summary

# @app.route('/record_audio', methods=['POST'])
# async def record_audio():
#     try:
#         aud = sr.Recognizer()
#         with sr.Microphone() as source:
#             audio = aud.listen(source)
#             try:
#                 phrase = aud.recognize_google(audio, language='en-us')
#                 return jsonify({'transcriptions': phrase}), 200
#             except Exception as exp:
#                 return "None"
#     except Exception as e:
#         return str(e), 400
