import cv2
from deepface import DeepFace
from flask import Flask, render_template, request, redirect, url_for, Response, flash, session
import threading
import webbrowser
import os
import random
import atexit
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Suppress TensorFlow warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
tf.get_logger().setLevel('ERROR')

# Initialize Flask
app = Flask(__name__)
app.secret_key = "supersecretkey"

# Global variables
current_mood = None
current_track = None
playing = False
image_path = None
driver = None
camera = cv2.VideoCapture(0)  # Initialize camera globally
current_volume = 50
streaming = True
selected_language = None

# Mood to YouTube Music search query mapping
mood_mapping = {
    'happy': 'happy',
    'sad': 'sad',
    'angry': 'angry',
    'neutral': 'neutral',
    'surprise': 'surprise',
    'fear': 'fear'
}

# Updated song mappings for different languages with lists of search prompts
hindi_music_mapping = {
    'happy': [
        "Bollywood dance songs upbeat",
        "Bollywood party anthems 2024",
        "Latest Hindi happy songs mix"
    ],
    'sad': [
        "Sad Bollywood songs playlist",
        "Slow soulful Hindi tracks",
        "Sad love songs Hindi",
        "Feel-good Hindi songs for positivity",
    ],
    'angry': [
        "Hindi rock songs playlist",
    ],
    'neutral': [
        "Calm Bollywood music ",
        "Relaxing Hindi music for study"
    ],
    'surprise': [
        "Bollywood upbeat pop songs",
        "Hindi pop chartbusters",
        "Catchy Hindi songs",
        "Bollywood pop music"
    ],
    'fear': [
        "Calm Hindi instrumental music",
        "Relaxing Bollywood ambient sounds",
        "Peaceful nature sounds Hindi",
        "Bollywood chillout vibes",
        "Hindi mindfulness music"
    ],
    'top': [
        "Top Bollywood songs 2024",
        "Latest Hindi trending songs",
        "Bollywood viral music hits",
        "Hindi chart-toppers ",
        "Top Hindi songs this month"
    ],
    '2000s': [
        "Bollywood 2000s songs",
        "Hindi 2000s nostalgic songs",
        "Top 2000s Bollywood hits",
        "Romantic Hindi songs 2000-2010",
        "Bollywood classics from the 2000s"
    ],
    'telugu': [
        "All Time Best Telugu Hits"
    ]
}

telugu_music_mapping = {
    'happy': [
        "Telugu upbeat party songs",
        "Feel-good Telugu music",
        "Dance hits Telugu 2024",
        "Telugu latest pop hits",
        "Top Telugu songs 2024",
        "Telugu mass songs playlist",
        "Latest Telugu music hits 2024",
        "Best Telugu movie songs ",
        "Telugu romantic songs ",
        "Top trending Telugu songs"
    ],
    'sad': [
        "Emotional Telugu melodies",
        "breakup song telugu",
        "Telugu songs for sadness",
        "Sad love songs Telugu "
    ],
    'angry': [
        "Mass Telugu fight songs",
        "Telugu powerful songs",
        "Angry mood songs Telugu",
    ],
    'neutral': [
        "Relaxing Telugu instrumental music",
        "Peaceful background music Telugu",
        "Chillout music Telugu instrumental",
        "Feel-good Telugu music for mood boost",
        "Calm melodies Telugu songs",
        "Telugu flute instrumental music"
    ],
    'surprise': [
        "Telugu surprise pop music",
        "Catchy Telugu songs ",
        "Telugu latest pop hits",
        "Telugu upbeat movie songs",
    ],
    'fear': [
        "Telugu calming music for anxiety",
        "Peaceful ambient Telugu sounds",
        "Soothing Telugu background music",
        "Telugu relaxing flute music",
        "Meditative sounds in Telugu"
    ],
    'top': [
        "Top Telugu songs 2024",
        "Latest trending Telugu hits",
        "Best Telugu chartbusters 2024",
        "Telugu viral music songs",
        "Top 10 Telugu songs this week"
    ],
    '2000s': [
        "Best Telugu songs from 2000s",
        "2000s nostalgic Telugu hits",
        "Telugu classic songs ",
        "Old Telugu songs from 2000-2010",
        "Telugu 2000s romantic hits"
    ],
    'telugu': [
        "Latest Telugu music hits 2024",
        "Best Telugu movie songs ",
        "Telugu romantic songs ",
        "Top trending Telugu songs",
        "Telugu DJ party mix 2024"
    ]
}

other_music_mapping = {
    'happy': [
        "Happy upbeat English songs",
        "Feel-good pop songs 2024",
        "International party anthems",
        "Best pop hits for happiness",
        "Energetic songs for good mood"
    ],
    'sad': [
        "Sad English songs",
        "Emotional breakup songs 2024",
        "Slow pop ballads for sadness",
        "Heartbreak songs English",
        "Sad indie songs to cry to"
    ],
    'angry': [
        "Best rock songs 2024",
        "Angry rock songs English",
        "Metal and hard rock hits",
        "Rock anthems for rage",
        "Powerful aggressive songs"
    ],
    'neutral': [
        "Lofi instrumental beats for relaxation",
        "Chill lounge music ",
        "Relaxing piano music",
        "Calm ambient background music",
        "Soft guitar instrumental songs"
    ],
    'surprise': [
        "Upbeat pop songs English 2024",
        "Catchy chart-topping pop hits",
        "Best pop anthems for dancing",
        "Feel-good pop music ",
        "Trending upbeat songs 2024"
    ],
    'fear': [
        "Peaceful ocean sounds ",
        "Meditation music ambient vibes",
        "Soft instrumental piano calming"
    ],
    'top': [
        "Top 100 English songs 2024",
    ],
    '2000s': [
        "Best English songs from the 2000s"
    ],
    'telugu': [
        "telugu music"
    ]
}

# Default mapping (will be updated based on selected language)
youtube_music_mapping = other_music_mapping

# Recommendation system
listening_history = {}

def update_listening_history(mood, track):
    if mood not in listening_history:
        listening_history[mood] = []
    listening_history[mood].append(track)

def recommend_track(mood):
    prompts = youtube_music_mapping.get(mood, ["chill music"])
    return random.choice(prompts)

# Cleanup function
def cleanup():
    global driver, camera
    if driver:
        driver.quit()
    if camera and camera.isOpened():
        camera.release()

atexit.register(cleanup)

# Generator function to stream video frames
def gen_frames():
    global camera, streaming
    while streaming and camera.isOpened():
        success, frame = camera.read()
        if success:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            break

# Route to stream video feed
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Welcome page
@app.route('/')
def welcome():
    try:
        return render_template('welcome.html')
    except Exception as e:
        flash(f"Error rendering welcome page: {e}", "error")
        return redirect(url_for('welcome'))

# Capture image and detect mood
@app.route('/capture', methods=['GET', 'POST'])
def capture():
    global current_mood, image_path, camera, streaming
    if request.method == 'POST':
        if request.form.get('capture') == 'yes':
            streaming = False  # Stop the video feed
            if not camera.isOpened():
                camera = cv2.VideoCapture(0)
                if not camera.isOpened():
                    flash("Could not open webcam.", "error")
                    return render_template('capture.html', error="Could not open webcam.")
            ret, frame = camera.read()
            if ret:
                image_path = os.path.join('static', 'captured_image.jpg')
                cv2.imwrite(image_path, frame)
                try:
                    result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                    current_mood = mood_mapping.get(result[0]['dominant_emotion'], 'neutral')
                    flash(f"Mood detected: {current_mood}", "success")
                except Exception:
                    current_mood = 'neutral'
                    flash("Defaulting to neutral mood.", "warning")
                camera.release()  # Release camera after capture
                cv2.destroyAllWindows()  # Close any OpenCV windows
                return redirect(url_for('select_language', image_url=url_for('static', filename='captured_image.jpg')))
            else:
                flash("Failed to capture image.", "error")
                return render_template('capture.html')
        else:
            return redirect(url_for('welcome'))
    streaming = True
    return render_template('capture.html')

# Language selection page
@app.route('/select_language', methods=['GET', 'POST'])
def select_language():
    global selected_language, youtube_music_mapping
    image_url = request.args.get('image_url')
    if request.method == 'POST':
        selected_language = request.form.get('language')
        youtube_music_mapping = (hindi_music_mapping if selected_language == 'hindi' else
                               telugu_music_mapping if selected_language == 'telugu' else
                               other_music_mapping)
        return redirect(url_for('play_music_route', image_url=image_url))
    return render_template('select_language.html', mood=current_mood, image_url=image_url)

# Play music on YouTube Music
@app.route('/play_music', methods=['GET', 'POST'])
def play_music_route():
    global playing, current_track
    image_url = request.args.get('image_url')
    play_music(current_mood)
    if playing:
        flash(f"Now playing: {current_track}", "success")
    else:
        flash("Failed to play music.", "error")
    return render_template('playback.html', mood=current_mood, playing=playing, current_track=current_track, image_url=image_url)

def play_music(mood):
    global current_track, playing, driver
    playing = False
    query = recommend_track(mood)
    current_track = query
    search_url = f"https://music.youtube.com/search?q={query.replace(' ', '+')}"
    try:
        if driver is None:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get(search_url)
        # Wait for search results and click the first result
        search_results = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ytmusic-shelf-renderer a.yt-simple-endpoint"))
        )
        if search_results:
            search_results[0].click()
            playing = True
            update_listening_history(mood, current_track)
            # Adjust volume if video is playing
            driver.execute_script("document.querySelector('video').volume = 0.5;")
    except Exception:
        webbrowser.open(search_url, new=2)
        playing = True
        update_listening_history(mood, current_track)

def adjust_volume(change):
    global driver, current_volume
    if driver and change != 0:
        current_volume = max(0, min(100, current_volume + change))
        driver.execute_script(f"document.querySelector('video').volume = {current_volume / 100};")
        return True
    return False

@app.route('/control', methods=['GET', 'POST'])
def control():
    global playing, driver, current_volume, current_track
    action = request.form.get('action')
    image_url = request.form.get('image_url')
    if action == 'stop' and playing:
        if driver:
            driver.execute_script("document.querySelector('video').pause();")
        playing = False
        flash("Music paused.", "success")
    elif action == 'next':
        play_music(current_mood)
        if playing:
            flash(f"Now playing: {current_track}", "success")
    elif action == 'volume_up':
        if adjust_volume(10):
            flash(f"Volume increased to {current_volume}%", "success")
    elif action == 'volume_down':
        if adjust_volume(-10):
            flash(f"Volume decreased to {current_volume}%", "success")
    elif action in ['top', '2000s', 'telugu']:
        play_music(action)
        if playing:
            flash(f"Now playing {action} music: {current_track}", "success")
    return render_template('playback.html', mood=current_mood, playing=playing, current_track=current_track, image_url=image_url)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=lambda: app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(0.5)
    webbrowser.open('http://127.0.0.1:5000/', new=2)
    flask_thread.join()
    cleanup()