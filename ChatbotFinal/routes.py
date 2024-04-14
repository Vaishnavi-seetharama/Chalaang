import json
import threading


from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk import pos_tag
from pytrends.request import TrendReq
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
from transformers import pipeline
import queue


# from openai import OpenAI
import os
import requests
from bs4 import BeautifulSoup

bp = Blueprint("routes", __name__)
# Initialize Event object
video_thread_completed = threading.Event()

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
    try:
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
                og_image = og_image[0] if og_image and og_image[
                    0] != '' else "https://www.simplilearn.com/ice9/free_resources_article_thumb/Types_of_Artificial_Intelligence.jpg"

                title_with_link = f"<a href='{url}' target='_blank'>{title}</a>"
                return {'url': url, 'title': title_with_link, 'description': description, 'og_image': og_image}
            except Exception as e:
                print(f"Error parsing HTML from {url}: {e}")
    except aiohttp.ClientError as e:
        print(f"Error fetching URL {url}: {e}")
    return {'url': url, 'title': '', 'description': '',
            'og_image': "https://www.simplilearn.com/ice9/free_resources_article_thumb/Types_of_Artificial_Intelligence.jpg"}


async def search_google_async(query, num_results=10, lang="en"):
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(10)  # Limit concurrency to 10
        search_results = list(set(search(query, num_results=num_results, lang=lang)))
        tasks = [site_details(session, url) for url in search_results]
        return await asyncio.gather(*tasks)


def extract_focus_keyword(text):
    # Tokenize the text into words
    tokens = word_tokenize(text.lower())
    # Filter out stop words
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [word for word in tokens if word not in stop_words]
    # Tag parts of speech
    tagged_tokens = pos_tag(filtered_tokens)
    # Extract nouns as potential focus keywords
    nouns = [word for word, pos in tagged_tokens if pos.startswith('NN')]
    # Return the first noun as the focus keyword
    if nouns:
        return nouns[0]
    else:
        return None


@bp.route('/result', methods=['GET'])
async def show_result():
    data = {}
    with open("result.json", "r") as json_file:
        data = json.load(json_file)

    return await render_template('results.html', result=data)


@bp.route('/search', methods=['POST'])
async def search_google():
    result = {}
    summary = ""
    result["graph"] = []
    user_message = (await request.json)['message']
    # pdb.set_trace()
    if check_matching_phrase(user_message):
        results_with_snippets = "Hello! I am feeling wonderfull today. How can I assist you today?"
    else:
        results_with_snippets = await search_google_async(user_message)

        # Save the results to an HTML file
        
        res_queue=queue.Queue()
        summarythread = threading.Thread(target=summarize_content,args=(results_with_snippets,res_queue)).start()
        summary=res_queue.get()

        
        sentences = summary.split('. ')
        first_three_sentences = '. '.join(sentences[:3])
        result["summary"] = first_three_sentences
        result["query"] = user_message

        video_thread = threading.Thread(target=change_video_src_handler, args=(first_three_sentences,))  
        video_thread.start()    
        video_thread.join()
    
        thread = threading.Thread(target=write_into_file, args=(results_with_snippets, summary,user_message,))
        thread.start()
        thread.join()

    result["searches"] = results_with_snippets

    
    # Return the JSON response
    return jsonify({'results': result})

@bp.route('/change_video_src', methods=["GET"])
async def get_video():
     # Wait for the video_thread to complete
    video_thread_completed.wait()
    
    # Reset the event for future use
    video_thread_completed.clear()
    return jsonify({})

def write_into_file(results_with_snippets, summary, user_message):
    result = {}
    result["graph"] = []
    result["searches"] = results_with_snippets
    result["summary"] = summary
    retry_cnt = 0
    while retry_cnt < 4:
        try:
            result["graph"] = track_keyword_trends(user_message)
            retry_cnt = 7
        except Exception as e:
            retry_cnt += 1
            print("errror", e)

    with open("result.json", "w") as json_file:
        json.dump(result, json_file)
    result["query"] = user_message


def track_keyword_trends(keyword):
    keyword = "india"
    # Initialize pytrends
    pytrends = TrendReq()

    # Build Payload
    pytrends.build_payload(kw_list=["india"], timeframe='today 12-m')

    # Get Interest Over Time
    interest_over_time_df = pytrends.interest_over_time()

    # Extract x-axis and y-axis data
    x_data_time = interest_over_time_df.index.strftime('%Y-%m-%d').tolist()
    y_data_time = interest_over_time_df.index.strftime('%Y-%m-%d').tolist()
    plot_type = 'line'

    # Get Interest by Region
    interest_by_region_df = pytrends.interest_by_region()
    top_regions = interest_by_region_df[keyword].sort_values(ascending=False).head(10)

    # Extract x-axis and y-axis data for region chart
    x_data_region = top_regions.index.tolist()  # Convert Index object to list
    y_data_region = top_regions.values.tolist()

    return [{'x1': x_data_time, 'label': 'Date', 'graph_type': plot_type, 'y1': y_data_time, 'label': 'Interest',
             'graph_type': plot_type},
            {'x2': x_data_region, 'label': 'Region', 'graph_type': 'bar', 'y2': y_data_region, 'label': 'Interest',
             'graph_type': 'bar'}]


def video_audio_overlay():
    audio_path = r'static/img/testtemp.wav'
    audio = mp.AudioFileClip(audio_path)
    video_path = r'static/img/fox.mp4'
    audio_duration = audio.duration
    video_clip = mp.VideoFileClip(video_path)

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
    end_image_path = r'static/img/assistant2.png'  # Replace with the path to your image
    end_image = mp.ImageClip(end_image_path).set_duration(0.1)
    end_image.resize(DISPLAY)
    video_clip1.resize(DISPLAY)
    video_clip1 = mp.concatenate_videoclips([video_clip1, end_image])
    video_clip1 = video_clip1.set_audio(audio)
    output_path = r'static/img/testvid2.mp4'
    video_clip1.write_videofile(output_path, codec='libx264', fps=30)
    # asyncio.create_task()


# async def change_video_src():
#     # JavaScript code to change the src attribute of the iframe
#     js_code = """
#     var iframe = document.getElementById('videoFrame');
#     iframe.src = 'img\testvid2.mp4';  // Change 'new_video.mp4' to the path of your new video file
#     """

#     return js_code


def assistant(audio):
   
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    engine.setProperty('rate', 130)
    engine.save_to_file(audio, r'static/img/testtemp.wav')
    engine.runAndWait()
    video_audio_overlay()
    # Call the function to change video src


# Flask route to handle the request to change video src
def change_video_src_handler(summary):
    sentences = summary.split('. ')
    first_three_sentences = '. '.join(sentences[:3])
    assistant(first_three_sentences)
    video_thread_completed.set()

    return {}


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


def summarize_content(results_with_snippets, res_queue):
    try:
        for result in results_with_snippets:
            url = result["url"]
            # Set user agent and other headers
            hdr = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                'Accept-Encoding': 'none',
                'Accept-Language': 'en-US,en;q=0.8',
                'Connection': 'keep-alive'
            }
            
            # Send a GET request to the URL
            response = requests.get(url, headers=hdr)
            response.raise_for_status()  # Raise an exception for HTTP errors (e.g., 404, 403)

            # Parse the HTML content
            soup = BeautifulSoup(response.text, "html.parser")

            # Find all paragraph elements
            paragraphs = soup.find_all("p")

            # Initialize variables
            # Initialize variables
            var1 = ""
            word_count = 0

            # Iterate over the paragraphs and accumulate words until the word count reaches 1000
            for paragraph in paragraphs:
                if word_count + len(paragraph.text.split()) < 1000:
                    var1 += paragraph.text + " "
                    word_count += len(paragraph.text.split())
                else:
                    remaining_words = 1000 - word_count
                    var1 += " ".join(paragraph.text.split()[:remaining_words])
                    break
                
                # Calculate the maximum length for summarization
            max_len = len(var1.split()) - 20

            # Use a summarization model to generate a summary
            summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
            summary = summarizer(var1, max_length=max_len, min_length=5, do_sample=False)[0]['summary_text']

            # Put the summary into the result queue
            res_queue.put(summary)
                
                # Break the loop as we found a URL with at least 1000 words
            break
    
    except requests.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as e:
        print(f"Error occurred: {e}")

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
