import spotipy
from spotipy.oauth2 import SpotifyOAuth
import speech_recognition as sr
import webbrowser
import pyttsx3
import musicLibrary
import openai  # Import OpenAI library
import os
import wikipediaapi

# Initialize recognizer and TTS engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# OpenAI API details
OPENAI_API_KEY = "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"  # Replace with your OpenAI API key

# Spotify API details
SPOTIPY_CLIENT_ID = 'f1fe5288f8134ae38f650ad041ab2385'
SPOTIPY_CLIENT_SECRET = 'aa6baa5aec6c4a9593a66fec68ae4b0a'
SPOTIPY_REDIRECT_URI = 'http://localhost:8888/callback'  # This can be any valid URI

# Initialize Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope="user-modify-playback-state,user-read-playback-state"))

# Initialize Wikipedia with a user agent
wiki_wiki = wikipediaapi.Wikipedia(
    language='en',  # Language of Wikipedia
    user_agent='MyVoiceAssistant/1.0 (contact@myvoiceassistant.com)'  # User agent string
)

def speak(text):
    try:
        print(text)  # Print the text before speaking it
        rate = engine.getProperty('rate')
        engine.setProperty('rate', rate + 5)  # Increase the rate by 5 words per minute
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        error_msg = f"Error in speak: {e}"
        print(error_msg)

def aiProcess(command):
    openai.api_key = OPENAI_API_KEY  # Set the OpenAI API key

    try:
        # Call the OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Specify the model (e.g., gpt-3.5-turbo or gpt-4)
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": command}
            ],
            max_tokens=100  # Limit the response length
        )
        # Extract and return the assistant's reply
        return response["choices"][0]["message"]["content"]
    except openai.error.OpenAIError as e:
        return f"Sorry, there was an error connecting to OpenAI: {str(e)}"

def play_spotify_song(song_name):
    try:
        # Get the list of available devices
        devices = sp.devices()
        if not devices['devices']:
            speak("No active Spotify devices found.")
            return

        # Select the first active device
        active_device_id = devices['devices'][0]['id']

        # Search for the song
        results = sp.search(q=song_name, limit=1)
        if results['tracks']['items']:
            track_uri = results['tracks']['items'][0]['uri']
            # Start playback on the active device
            sp.start_playback(device_id=active_device_id, uris=[track_uri])
            speak(f"Playing {song_name} on Spotify.")
        else:
            speak("Song not found on Spotify.")
    except Exception as e:
        speak(f"Error playing song on Spotify: {e}")

def stop_spotify_playback():
    try:
        # Get the list of available devices
        devices = sp.devices()
        if not devices['devices']:
            speak("No active Spotify devices found.")
            return

        # Select the first active device
        active_device_id = devices['devices'][0]['id']

        # Pause playback on the active device
        sp.pause_playback(device_id=active_device_id)
        speak("Stopping playback on Spotify.")
    except Exception as e:
        speak(f"Error stopping Spotify playback: {e}")

def processCommand(c):
    try:
        c_lower = c.lower()
        if "stop the music" in c_lower:  # Check for stop command
            stop_spotify_playback()  # Stop Spotify playback
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
            song = " ".join(c_lower.split(" ")[1:])  # Extract the full song name
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
        return None  # Continue listening unless "stop" is said
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
        speak(f"Here's what I found on Wikipedia: {page.summary[:1000]}")  # Limit summary length
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
                if result == "stop":  # If stop is detected, break the loop
                    speak("Stopping the assistant. Say hello to wake me up again.")
                    break
        except sr.UnknownValueError:
            print("Could not understand audio.")
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
        except Exception as e:
            print(f"General error: {e}")

if __name__ == "__main__":
    speak("Initializing the agent sir......")
    while True:  # Outer loop for wake word
        print("Listening for wake word...")
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = recognizer.listen(source, timeout=3, phrase_time_limit=3)
            word = recognizer.recognize_google(audio)
            if word.lower() == "hello":
                speak("Hello! sir, how can I be of any help to you?")
                listen_for_commands()  # Enter continuous listening mode
        except sr.UnknownValueError:
            print("Could not understand audio.")
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
        except Exception as e:
            print(f"General error: {e}")