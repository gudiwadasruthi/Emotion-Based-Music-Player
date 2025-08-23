import cv2
from deepface import DeepFace
from flask import Flask, render_template, request, redirect, url_for, Response, flash, session
import threading
import webbrowser
import os
import time
import atexit
import random  # For random prompt selection
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# Suppress TensorFlow warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN optimizations
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow logging (0 = all, 1 = filter INFO, 2 = filter WARNING, 3 = filter ERROR)
import tensorflow as tf
tf.get_logger().setLevel('ERROR')  # Only show ERROR messages from TensorFlow

# Initialize Flask
app = Flask(__name__)
app.secret_key = "supersecretkey"

# Global variables
current_mood = None
current_track = None
playing = False
image_path = None
driver = None
camera = None
current_volume = 50
streaming = True
selected_language = None  # To store the selected language

# Mood to YouTube Music search query mapping
mood_mapping = {
    'happy': 'happy',
    'sad': 'sad',
    'angry': 'angry',
    'neutral': 'neutral',
    'surprise': 'surprise',
    'fear': 'fear'
}

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
        "Feel-good Telugu music",
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
youtube_music_mapping = other_music_mapping  # Default to "Other"

# Recommendation system (simple content-based filtering)
listening_history = {}

def update_listening_history(mood, track):
    if mood not in listening_history:
        listening_history[mood] = []
    listening_history[mood].append(track)

def recommend_track(mood):
    # Return a random search prompt from the list based on the selected language mapping
    prompts = youtube_music_mapping.get(mood, ["chill music"])
    return random.choice(prompts)

# Cleanup function to close the WebDriver and camera
def cleanup():
    global driver, camera
    if driver is not None:
        print("Closing WebDriver...")
        driver.quit()
        driver = None
    if camera is not None:
        print("Releasing camera...")
        camera.release()
        camera = None

# Register cleanup function to run on script exit
atexit.register(cleanup)

# Generator function to stream video frames
def gen_frames():
    global camera, streaming
    if camera is None:
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            print("Could not open webcam for streaming")
            return

    while streaming:
        if camera is None or not camera.isOpened():
            print("Camera is closed, stopping video feed...")
            break
        success, frame = camera.read()
        if not success:
            print("Failed to read frame from camera")
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    print("Video feed stopped")

# Route to stream the video feed
@app.route('/video_feed')
def video_feed():
    print("Streaming video feed...")
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Welcome page
@app.route('/')
def welcome():
    print("Serving welcome page - Route accessed")
    try:
        response = render_template('welcome.html')
        print("Welcome page rendered successfully")
        return response
    except Exception as e:
        print(f"Error rendering welcome page: {e}")
        flash(f"Error rendering welcome page: {e}", "error")
        return redirect(url_for('welcome'))

# Capture image and detect mood
@app.route('/capture', methods=['GET', 'POST'])
def capture():
    global current_mood, image_path, camera, streaming
    print(f"Handling capture request: {request.method}")
    if request.method == 'POST':
        if request.form.get('capture') == 'yes':
            # Stop the video feed
            streaming = False
            time.sleep(1)  # Give a brief moment for the streaming loop to exit
            # Capture the image manually
            if camera is None:
                camera = cv2.VideoCapture(0)
            if not camera.isOpened():
                camera.release()
                camera = None
                print("Could not open webcam")
                flash("Could not open webcam.", "error")
                return render_template('capture.html', error="Could not open webcam.")
            ret, frame = camera.read()
            if ret:
                image_path = os.path.join('static', 'captured_image.jpg')
                cv2.imwrite(image_path, frame)
                try:
                    result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                    dominant_emotion = result[0]['dominant_emotion']
                    current_mood = mood_mapping.get(dominant_emotion, 'neutral')
                    print(f"Mood detected: {current_mood}")
                    flash(f"Mood detected: {current_mood}", "success")
                except Exception as e:
                    print(f"Error in mood detection: {e}")
                    current_mood = 'neutral'
                    flash("Error in mood detection. Defaulting to neutral mood.", "warning")
                # Release the camera after capturing
                camera.release()
                camera = None
                cv2.destroyAllWindows()
                # Redirect to language selection page instead of playback
                return redirect(url_for('select_language', image_url=url_for('static', filename='captured_image.jpg')))
            else:
                camera.release()
                camera = None
                cv2.destroyAllWindows()
                print("Failed to capture image")
                flash("Failed to capture image.", "error")
                return render_template('capture.html', error="Failed to capture image.")
        else:
            print("Redirecting to welcome page")
            return redirect(url_for('welcome'))
    streaming = True  # Reset streaming flag when loading the capture page
    return render_template('capture.html')

# Language selection page
@app.route('/select_language', methods=['GET', 'POST'])
def select_language():
    global selected_language, youtube_music_mapping
    image_url = request.args.get('image_url')
    if request.method == 'POST':
        selected_language = request.form.get('language')
        print(f"Selected language: {selected_language}")
        
        # Update the youtube_music_mapping based on the selected language
        if selected_language == 'hindi':
            youtube_music_mapping = hindi_music_mapping
        elif selected_language == 'telugu':
            youtube_music_mapping = telugu_music_mapping
        else:
            youtube_music_mapping = other_music_mapping

        # After selecting the language, proceed to play music automatically
        return redirect(url_for('play_music_route', image_url=image_url))
    
    return render_template('select_language.html', mood=current_mood, image_url=image_url)

# Play music on YouTube Music
@app.route('/play_music', methods=['GET', 'POST'])
def play_music_route():
    global playing, current_track
    image_url = request.args.get('image_url')
    play_music(current_mood)
    print(f"Playing music for mood: {current_mood} in language: {selected_language}")
    if playing:
        flash(f"Now playing: {current_track}", "success")
    else:
        flash("Failed to play music.", "error")
    return render_template('playback.html', mood=current_mood, playing=playing, current_track=current_track, image_url=image_url)

def play_music(mood):
    global current_track, playing, driver, current_volume
    playing = False
    query = recommend_track(mood)
    print(f"Recommended query for {mood}: {query}")

    try:
        print("Attempting to play music using Selenium...")
        print("Initializing Selenium WebDriver with Chrome options...")
        if driver is None:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
            chrome_options.add_argument("--disable-notifications")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            print("WebDriver initialized successfully.")

        print("Navigating to YouTube Music...")
        driver.get("https://music.youtube.com/")
        print("Navigated to YouTube Music.")
        
        # Handle potential consent dialog
        try:
            consent_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Agree')]"))
            )
            ActionChains(driver).move_to_element(consent_button).click().perform()
            print("Consent dialog dismissed.")
        except:
            print("No consent dialog found, proceeding...")

        print("Waiting for search bar to load...")
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input#input"))
        )
        print("Search bar found using CSS selector.")
        
        print("Interacting with search bar...")
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        print("Search query submitted.")
        
        print("Waiting for search results to load...")
        search_results = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ytmusic-shelf-renderer a.yt-simple-endpoint"))
        )
        if not search_results:
            print("No search results found.")
            current_track = "Unknown Track"
            playing = False
            return

        first_result = search_results[0]
        print("First result found using CSS selector.")
        ActionChains(driver).move_to_element(first_result).click().perform()
        print("First result clicked using ActionChains.")
        time.sleep(3)

        current_volume = 50
        adjust_volume(0)

        playing = True
        current_track = query
        update_listening_history(mood, current_track)
        print(f"Playing on YouTube Music: {current_track}")
    except Exception as e:
        print(f"Failed to play on YouTube Music using Selenium: {e}")
        print("Falling back to opening YouTube Music search URL directly...")
        search_url = f"https://music.youtube.com/search?q={query.replace(' ', '+')}"
        print(f"Attempting to open YouTube Music search URL: {search_url}")
        try:
            webbrowser.get('chrome').open(search_url, new=2)
            print("YouTube Music search URL opened in Chrome")
            playing = True
            current_track = query
            update_listening_history(mood, current_track)
            print(f"Opened YouTube Music search for: {current_track}")
        except Exception as fallback_e:
            print(f"Failed to open YouTube Music search URL in Chrome: {fallback_e}")
            try:
                webbrowser.open(search_url, new=2)
                print("YouTube Music search URL opened in default browser")
                playing = True
                current_track = query
                update_listening_history(mood, current_track)
                print(f"Opened YouTube Music search for: {current_track}")
            except Exception as default_browser_e:
                print(f"Failed to open YouTube Music search URL in default browser: {default_browser_e}")
                playing = False

def adjust_volume(change):
    global driver, current_volume
    if driver is None:
        print("No WebDriver instance available to adjust volume.")
        return False

    try:
        if change != 0:
            current_volume = max(0, min(100, current_volume + change))
        driver.execute_script(f"document.querySelector('video').volume = {current_volume / 100};")
        print(f"Volume set to {current_volume}%")
        return True
    except Exception as e:
        print(f"Failed to adjust volume: {e}")
        return False

@app.route('/control', methods=['GET', 'POST'])
def control():
    global playing, driver, current_volume, current_track
    action = request.form.get('action') if request.method == 'POST' else request.args.get('action')
    image_url = request.form.get('image_url') if request.method == 'POST' else request.args.get('image_url')
    print(f"Control action: {action}")
    if action == 'play' and not playing:
        play_music(current_mood)
        if playing:
            flash(f"Now playing: {current_track}", "success")
        else:
            flash("Failed to play music.", "error")
    elif action == 'stop':
        try:
            if driver:
                driver.execute_script("document.querySelector('video').pause();")
                print("Music paused successfully using JavaScript")
                flash("Music paused.", "success")
            playing = False
            print("Playback stopped")
        except Exception as e:
            print(f"Failed to pause music: {e}")
            playing = False
            print("Playback stopped (no Selenium driver)")
            flash("Failed to pause music.", "error")
    elif action == 'next':
        play_music(current_mood)
        if playing:
            flash(f"Now playing: {current_track}", "success")
        else:
            flash("Failed to play next track.", "error")
    elif action == 'volume_up':
        if adjust_volume(10):
            flash(f"Volume increased to {current_volume}%", "success")
        else:
            flash("Failed to increase volume.", "error")
    elif action == 'volume_down':
        if adjust_volume(-10):
            flash(f"Volume decreased to {current_volume}%", "success")
        else:
            flash("Failed to decrease volume.", "error")
    elif action == 'top':
        play_music('top')
        if playing:
            flash(f"Now playing top hits: {current_track}", "success")
        else:
            flash("Failed to play top hits.", "error")
    elif action == '2000s':
        play_music('2000s')
        if playing:
            flash(f"Now playing 2000s music: {current_track}", "success")
        else:
            flash("Failed to play 2000s music.", "error")
    elif action == 'telugu':
        play_music('telugu')
        if playing:
            flash(f"Now playing Telugu music: {current_track}", "success")
        else:
            flash("Failed to play Telugu music.", "error")
    return render_template('playback.html', mood=current_mood, playing=playing, current_track=current_track, image_url=image_url)

if __name__ == "__main__":
    try:
        print("Starting application...")
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 5000))
        if result == 0:
            print("Port 5000 is already in use. Please free the port or use a different one.")
            sock.close()
            exit(1)
        sock.close()

        flask_thread = threading.Thread(target=lambda: app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False))
        flask_thread.daemon = True
        flask_thread.start()
        print("Flask thread started")

        time.sleep(2)
        
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        print("Attempting to open welcome page...")
        try:
            webbrowser.register('chrome', None, webbrowser.GenericBrowser(chrome_path))
            webbrowser.get('chrome').open('http://127.0.0.1:5000/', new=2)
            print("Welcome page opened in Chrome")
        except Exception as chrome_error:
            print(f"Failed to open Chrome: {chrome_error}")
            try:
                webbrowser.open('http://127.0.0.1:5000/', new=2)
                print("Welcome page opened in default browser")
            except Exception as default_error:
                print(f"Failed to open default browser: {default_error}")
                print("Please manually open http://127.0.0.1:5000/ in your browser")

        flask_thread.join()
    except KeyboardInterrupt:
        print("Script interrupted by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        cleanup()
