# Emotion-Based Music Player

An AI-powered web app that analyzes your facial expression, detects your mood, and automatically plays a personalized music playlist on YouTube Music.

---

## 📑 Table of Contents
- [💡 About the Project](#-about-the-project)
- [✨ Features](#-features)
- [🖥️ Frontend](#️-frontend)
- [⚙️ Backend](#-backend)
- [🚀 Getting Started](#-getting-started)
- [🛠️ Run Backend (Docker)](#️-run-backend-docker)
- [📦 Deployment](#-deployment)
- [🤝 Contributing](#-contributing)
- [🙏 Acknowledgements](#-acknowledgements)
- [📜 License](#-license)

---

## 💡 About the Project
The Mood-Based Music Player is designed to create a seamless connection between your emotional state and your music. Instead of manually searching for songs that match your vibe, this app uses your webcam to perform real-time mood analysis and curates a listening experience just for you.

This project leverages computer vision for emotion detection and web automation for music playback, offering a unique and interactive way to discover and enjoy music.

It supports:
Real-time mood detection from a live camera feed.
Multi-language music recommendations (Hindi, Telugu, Other).
Automated browser control for a hands-free experience.
A clean, interactive frontend built with Flask and Bootstrap.

## ✨ Features

### 🖥️ Frontend
- Modern, responsive UI built with HTML, CSS, and Bootstrap 5.
- Themed design with animated music notes, a waveform background, and smooth fade-in effects.
- Live camera preview stream directly on the capture page.
- Clear user flow: Welcome → Capture → Select Language → Playback.
- Interactive playback controls for switching playlists and adjusting volume.
- Interactive UX elements: copy-to-clipboard buttons, thinking/loading spinners, auto-closing modals
- User feedback via flashed messages for success and error states.
- Mobile-friendly layout for a consistent experience on all devices.

### ⚙️ Backend
- Flask server for handling web requests and application logic.
- Real-time video streaming using OpenCV.
- Mood analysis powered by the DeepFace library for accurate emotion recognition.
- Selenium and webdriver-manager for robust, automated browser control of YouTube Music.
- Dynamic music recommendation engine with mood-to-query mapping for multiple languages.
- Structured project with separate templates for each step of the user journey.
- Graceful cleanup of camera and WebDriver resources on application exit.

### 🔒 Privacy & Security
- All image processing is done locally. No images are uploaded to external servers.
- The application runs entirely on your local machine (127.0.0.1).
- Camera access is only active on the capture page and is released immediately after use.

---

## 🛠 Tech Stack

**Frontend**
- HTML, CSS, Bootstrap 5
- Font Awesome (CDN) for icons
- Jinja2 Templating (via Flask)

**Backend**
- Python 3.7+
- Flask (Web Framework)
- OpenCV-Python (Camera & Image Handling)
- DeepFace (Emotion Detection)
- Selenium (Browser Automation)
- webdriver-manager (Automated ChromeDriver setup)

---

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd <repository-folder-name>
   ```
2. **Create and activate a virtual environment (recommended)**
   ```bash
   # For Windows
   python -m venv venv
   venv\Scripts\activate

   # For macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the application**
   ```bash
   python main.py
   ```

---
## Usage
1. Click Get Started on the welcome page.
2. Allow the browser to access your camera when prompted.
3. Position your face in the frame and click Capture Image.
4. The app will analyze your mood and display the result.
5. On the next screen, select a preferred language for your music (Hindi, Telugu, or Other).
6. A new browser window will open automatically and start playing a playlist from YouTube Music that matches your mood and language choice.
7. Use the controls on the web app page to switch playlist, adjust Volume Up/Down, or play Top Hits.

## Project Structure
MOOD_MUSIC_PLAYER/
├── static/
│   ├── captured_image.jpg       # Stores the last captured image
│   └── styles.css               # Custom styling for the frontend
├── templates/
│   ├── capture.html             # Page for camera preview and image capture
│   ├── playback.html            # Page with music controls after detection
│   ├── select_language.html     # Page to choose music language
│   └── welcome.html             # The main landing page
├── main.py                      # Main Flask application logic
└── README.md

## Troubleshooting
- If the camera feed doesn't appear: Make sure you have granted camera permissions to your browser for 127.0.0.1:5000. Reloading the page might help.
- If music doesn't play: Ensure you have Google Chrome installed. The Selenium automation is configured for Chrome.
- For DeepFace errors on first run: The library may need to download pre-trained models. Please ensure you have an active internet connection the first time you run the analysis.
- If the app fails to start: Check that all dependencies were installed correctly in your virtual environment.

---

## 🤝 Contributing
Contributions are welcome!  
If you'd like to improve this project, please follow these steps:  
1. Fork the repository  
2. Create a feature branch (`git checkout -b feature-name`)  
3. Commit your changes (`git commit -m 'Add new feature'`)  
4. Push to your branch (`git push origin feature-name`)  
5. Open a Pull Request  

---
## 🙏 Acknowledgements
This project wouldn’t be possible without these amazing tools and libraries:  
- [Flask](https://flask.palletsprojects.com/) – Backend framework  
- [DeepFace](https://github.com/serengil/deepface) – Facial analysis and emotion detection 
- [OpenCV](https://opencv.org/) – Webcam and computer vision tasks 
- [Selenium](https://www.selenium.dev/.) – Web automation 
- [Bootstrap](https://getbootstrap.com/) – Responsive frontend framework 
- [Font Awesome](https://fontawesome.com/) – Icons  

---
## License
MIT

## Author
- Developed by Gudiwada sruthi

