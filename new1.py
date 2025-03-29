import spotipy
from spotipy.oauth2 import SpotifyOAuth
import speech_recognition as sr
import webbrowser
import pyttsx3
import musicLibrary
import os
import wikipediaapi
import requests
import json  

# Initialize recognizer and TTS engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Groq API details
GROQ_API_KEY = "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"  # Replace with your actual Groq API key
GROQ_API_URL = "https://api.groq.com/v1/models/groq-pro:generateContent"  # Replace with the actual Groq API URL

# Spotify API details
SPOTIPY_CLIENT_ID = 'f1fe5288f8134ae38f650ad041ab2385'
SPOTIPY_CLIENT_SECRET = 'aa6baa5aec6c4a9593a66fec68ae4b0a'
SPOTIPY_REDIRECT_URI = 'http://localhost:8888/callback'

# Initialize Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                                client_secret=SPOTIPY_CLIENT_SECRET,
                                                redirect_uri=SPOTIPY_REDIRECT_URI,
                                                scope="user-modify-playback-state,user-read-playback-state"))

# Initialize Wikipedia with a user agent
wiki_wiki = wikipediaapi.Wikipedia(
    language='en',
    user_agent='MyVoiceAssistant/1.0 (contact@myvoiceassistant.com)'
)

def speak(text):
    try:
        print(text)
        rate = engine.getProperty('rate')
        engine.setProperty('rate', rate + 5)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        error_msg = f"Error in speak: {e}"
        print(error_msg)

def aiProcess(command):
    try:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"}
        payload = {
            "model": "groq-pro",  # Specify the model
            "prompt": command,  # The user command or input
            "temperature": 0.7,  # Optional: Adjust creativity (0.0 = deterministic, 1.0 = more random)
            "maxOutputTokens": 100,  # Limit the response length
            "topP": 0.9,  # Optional: Adjust diversity (probability mass)
            "topK": 40  # Optional: Adjust diversity (number of highest-probability tokens considered)
        }

        # Send the request to the Groq API
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise an error for bad HTTP responses

        # Parse the response
        data = response.json()
        if "candidates" in data and len(data["candidates"]) > 0:
            return data["candidates"][0]["output"]  # Extract the output text
        else:
            return "Sorry, I couldn't process your request."
    except requests.exceptions.RequestException as e:
        return f"Sorry, there was an error connecting to Groq: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

def play_spotify_song(song_name):
    try:
        devices = sp.devices()
        if not devices['devices']:
            speak("No active Spotify devices found.")
            return

        active_device_id = devices['devices'][0]['id']
        results = sp.search(q=song_name, limit=1)
        if results['tracks']['items']:
            track_uri = results['tracks']['items'][0]['uri']
            sp.start_playback(device_id=active_device_id, uris=[track_uri])
            speak(f"Playing {song_name} on Spotify.")
        else:
            speak("Song not found on Spotify.")
    except Exception as e:
        speak(f"Error playing song on Spotify: {e}")

def stop_spotify_playback():
    try:
        devices = sp.devices()
        if not devices['devices']:
            speak("No active Spotify devices found.")
            return

        active_device_id = devices['devices'][0]['id']
        sp.pause_playback(device_id=active_device_id)
        speak("Stopping playback on Spotify.")
    except Exception as e:
        speak(f"Error stopping Spotify playback: {e}")

def processCommand(c):
    try:
        c_lower = c.lower()
        if "stop the music" in c_lower:
            stop_spotify_playback()
            return "stop the music"
        elif "open google" in c_lower:
            webbrowser.open("https://google.com")
            speak("Opening Google")
        elif "open facebook" in c_lower:
            webbrowser.open("https://facebook.com")
            speak("Opening Facebook")
        elif "open youtube" in c_lower:
            webbrowser.open("https://youtube.com")
            speak("Opening YouTube")
        elif "open linkedin" in c_lower:
            webbrowser.open("https://linkedin.com")
            speak("Opening LinkedIn")
        elif c_lower.startswith("play"):
            song = " ".join(c_lower.split(" ")[1:])
            if "on spotify" in c_lower:
                play_spotify_song(song)
            else:
                link = musicLibrary.music.get(song, None)
                if link:
                    webbrowser.open(link)
                    speak(f"Playing {song}")
                else:
                    speak("Song not found in library.")
        elif "search for" in c_lower:
            query = c_lower.split("search for")[1].strip()
            webbrowser.open(f"https://www.google.com/search?q={query}")
            speak(f"Searching for {query}")
        elif "calculate" in c_lower:
            expression = c_lower.split("calculate")[1].strip()
            calculate(expression)
        elif "wikipedia" in c_lower:
            query = c_lower.split("for")[1].strip()
            search_wikipedia(query)
        else:
            output = aiProcess(c)
            speak(output)
        return None
    except Exception as e:
        error_msg = f"Error processing command: {e}"
        speak(error_msg)
        return None

def calculate(expression):
    try:
        result = eval(expression)
        speak(f"The result is {result}.")
    except Exception as e:
        speak(f"Sorry, I couldn't calculate that. Error: {e}")

def search_wikipedia(query):
    page = wiki_wiki.page(query)
    if page.exists():
        speak(f"Here's what I found on Wikipedia: {page.summary[:1000]}")
    else:
        speak("Sorry, I couldn't find any information on that topic.")

def listen_for_commands():
    while True:
        print("Listening for command...")
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                command = recognizer.recognize_google(audio)
                print(f"Command received: {command}")
                result = processCommand(command)
                if result == "stop":
                    speak("Stopping the assistant. Say hello to wake me up again.")
                    break
        except sr.UnknownValueError:
            print("Could not understand audio.")
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
        except Exception as e:
            print(f"General error: {e}")

def listen_for_typed_commands():
    print("Type 'start' to begin typing commands. Type 'exit' to stop.")
    while True:
        command = input("Enter your command: ").strip()
        if command.lower() == "exit":
            print("Exiting typed command mode.")
            break
        elif command.lower() == "start":
            print("You can now type your commands now.")
        else:
            result = processCommand(command)
            if result == "stop":
                print("Stopping the assistant.")
                break

if __name__ == "__main__":
    speak("Initializing the agent sir......")
    while True:
        print("Listening for wake word or type 'start' to begin typing commands...")
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = recognizer.listen(source, timeout=3, phrase_time_limit=3)
                word = recognizer.recognize_google(audio)
                if word.lower() == "hello":
                    speak("Hello! sir, how can I be of any help to you?")
                    listen_for_commands()
        except sr.UnknownValueError:
            print("Could not understand audio.")
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
        except Exception as e:
            print(f"General error: {e}")

        typed_command = input("Enter 'start' to type commands or press Enter to continue listening: ").strip()
        if typed_command.lower() == "start":
            listen_for_typed_commands()