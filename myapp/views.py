from django.shortcuts import render, HttpResponse
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import HttpResponseRedirect
from django.urls import reverse
import numpy as np
from django.http import HttpResponse
from django.conf import settings
from moviepy.editor import VideoFileClip, AudioFileClip
import requests
import json
import tempfile
import os
from django.urls import reverse
from django.core.files.storage import FileSystemStorage
from .forms import VideoProcessingForm
import subprocess
import threading


from django.shortcuts import render, HttpResponse
from .forms import VideoProcessingForm

processed_video_url = settings.MEDIA_URL + 'processed_video.mp4'

def process_video(request):
    if request.method == 'POST':
        form = VideoProcessingForm(request.POST, request.FILES)
        if form.is_valid():
            tweet_link = form.cleaned_data['tweet_link']
            video_file = request.FILES['video_file']  # Access the uploaded video file

            try:
                # Fetch the tweet image using the user-provided tweet link
                tweet_image_path = fetch_tweet_image(tweet_link)

                if tweet_image_path:

                    # Process the video with the overlay
                    final_processed_video_path = process_video_with_overlay(tweet_image_path, video_file)

                    if final_processed_video_path:
                        # Extract the filename from the processed video path
                        final_processed_video_filename = os.path.basename(final_processed_video_path)

                        # Assuming you serve static files using Django's 'static' view
                        # Adjust 'app_name' and 'proc'processed_video.mp4'essed_videos' to match your project structure
                        return render(request, 'processed_video.html')

                    else:
                        return HttpResponse("Video processing failed. Please try again later.")
                else:
                    return HttpResponse("Failed to fetch the tweet image.")
            except Exception as e:
                return HttpResponse(f"An error occurred: {str(e)}")
    else:
        form = VideoProcessingForm()

    return render(request, 'process_video.html', {'form': form})

def fetch_tweet_image(tweet_url):
    # Define the API URL
    url = "https://tweetpik.com/api/v2/images"

    # Define your API key
    api_key = "39fc8b64-5d40-4435-850e-66d36227b8e2"

    # Create a JSON payload with the user-provided tweet URL and custom options
    payload = {
        "url": tweet_url,
        "textPrimaryColor": "#FFFFFF",
        "backgroundColor": "#FF00FF",
        "dimension": "tiktok"
    }

    # Define the headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": api_key
    }

    # Send the POST request to the API
    response = requests.post(url, data=json.dumps(payload), headers=headers)

    if response.status_code == 201:
        # Parse the JSON response to get the image URL
        response_data = json.loads(response.text)
        image_url = response_data.get("url")

        # Save the image
        image_path = save_tweet_image(image_url)
        return image_path
    else:
        print("Error fetching tweet image:", response.status_code)
        return None

def save_tweet_image(image_url):
    # Download the image
    image_response = requests.get(image_url)

    # Check if the image download was successful
    if image_response.status_code == 200:
        # Save the image as screenshot.png
        screenshot_path = "screenshot.png"
        with open(screenshot_path, "wb") as image_file:
            image_file.write(image_response.content)
        print("Screenshot saved as screenshot.png")
        return screenshot_path
    else:
        print("Error downloading the image:", image_response.status_code)
        return None


def process_video_with_overlay(tweet_image_path, video_file):
    try:        
        # Open the video file
        if hasattr(video_file, 'temporary_file_path'):
            video_path = video_file.temporary_file_path()
        else:
            video_memory = video_file.read()
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video_file:
                temp_video_path = temp_video_file.name
                temp_video_file.write(video_memory)
            video_path = temp_video_path

        # Determine the path for the processed video
        processed_video_filename = 'processed_video.mp4'
        processed_video_path = os.path.join(settings.MEDIA_ROOT, processed_video_filename)

        # Use ffmpeg to overlay the image on the video
        # Also adjust brightness, contrast, and saturation
        command = [
            'ffmpeg', 
            '-y',
            '-i', video_path, 
            '-i', tweet_image_path, 
            '-filter_complex',
            f'[0:v]eq=brightness=-0.2:contrast=0.2:saturation=0.6[adjusted_video];[1:v]colorkey=0xFF00FF:0.4:0.3,crop=in_w:in_h*0.94:0:in_h*0.06,scale=iw*0.9:ih*0.9[overlay];[adjusted_video][overlay]overlay=(W-w)/2:(H-h)/2[v]',
            '-map', '[v]', 
            '-map', '0:a',
            '-c:v', 'libx264', 
            '-preset', 'ultrafast',
            '-c:a', 'aac', 
            '-strict', 'experimental', 
            '-threads', '2',
            processed_video_path
        ]

        subprocess.run(command)

        print("Processed video saved at:", processed_video_path)
        return processed_video_path

    except Exception as e:
        print(f"Video processing error: {str(e)}")
        return None

    
def playback_processed_video(request):
    # Define the path to the processed video
    processed_video_path = os.path.join(settings.MEDIA_ROOT, 'processed_video.mp4')
    processed_video_url = settings.MEDIA_URL + 'processed_video.mp4'


    if os.path.exists(processed_video_path):
        # Serve the video using the X-Sendfile header (requires appropriate server configuration)
        response = HttpResponse(content_type='video/mp4')
        response['Content-Type'] = 'video/mp4'
        response['Accept-Ranges'] = 'bytes'
        response['X-Sendfile'] = processed_video_url


        # Print the processed_video_url for debugging
        print("processed_video_url:", response.get('X-Sendfile'))

        return response
    else:
        return HttpResponse("Processed video not found.")