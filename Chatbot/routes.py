from quart import send_file, Blueprint
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
            
            title_with_link = f"• <b><a href='{url}' target='_blank'>{title}</a></b>"
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


@bp.route('/search', methods=['POST'])
async def search_google():
    user_message = (await request.json)['message']
    if check_matching_phrase(user_message):
        results_with_snippets="Hello! I am feeling wonderfull today. How can I assist you today?"
    else:
        results_with_snippets = await search_google_async(user_message)

    # Save the results to an HTML file
    await save_results_to_html(results_with_snippets, user_message)
    print("Vaishnavi   ",{'results': results_with_snippets})
    # Return the JSON response
    return jsonify({'results': results_with_snippets})


async def save_results_to_html(results, user_message):
    # Create or open the HTML file for writing with UTF-8 encoding
    with open('results.html', 'w', encoding='utf-8') as f:
        # Write the HTML content to the file
        # user_message = (await request.json)['message']
        title_res = "Your Search: " + user_message
        f.write(
            '<!DOCTYPE html>\n<html lang="en" data-bs-theme="dark">\n<head>\n<meta charset="UTF-8">\n<meta http-equiv="X-UA-Compatible" content="IE=edge">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<link rel="stylesheet" href="style.css">\n <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">\n<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />\n<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300&display=swap" rel="stylesheet">\n<title>Chalaang Queens</title>\n<body><nav class="navbar">\n<a class="navbar-brand" href="#">\n<img src="img\logo.png" width="40" height="40" alt="">\n</a>\n<a class="navbar-brand" href="#"><b>Chalaang-Queens</b></a>\n<ul class="nav">\n<li class="nav-item">\n<a class="nav-link active" aria-current="page" href="index.html">Home</a>\n</li>\n<li class="nav-item">\n<a class="nav-link" href="#">Your Search</a>\n</li>\n</ul>\n</nav>\n<h1><center>{}</center></h1>\n'.format(
                title_res))
        for result in results:
            f.write(
                f"<li><a href='{result['url']}' target='_blank'>{result['title']}</a><br>{result['description']}</li>\n")
        f.write('</ul>\n</body>\n</html>')


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


async def change_video_src():
    # JavaScript code to change the src attribute of the iframe
    js_code = """
    var iframe = document.getElementById('videoFrame');
    iframe.src = 'img\testvid2.mp4';  // Change 'new_video.mp4' to the path of your new video file
    """

    return js_code


def assistant(audio):
    print("vaishnavi13")
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    engine.setProperty('rate', 130)
    engine.save_to_file(audio, r'img\testtemp.wav')
    engine.runAndWait()
    video_audio_overlay()
    # Call the function to change video src


# Flask route to handle the request to change video src
@bp.route('/change_video_src')
async def change_video_src_handler():
    user_message = (await request.json)['message']
    results_with_snippets = await search_google_async(user_message)
    assistant(results_with_snippets[0]['description'])

    return await change_video_src()

def check_matching_phrase(input_text):
    phrases = [
    "Hi",
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

def summarize_content(content):
    client = OpenAI(
    api_key="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",
    )
    prompt_text = [{"role":"system","content":"You are a serach engine.Summarize/analyze webpages to give comprehensive information"},{"role":"user","content":content}]
    response = client.completions.create(        
        model="gpt-3.5-turbo-instruct",
        prompt=prompt_text,
        max_tokens=1000,  # Adjust the max tokens to control the length of the summary
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
