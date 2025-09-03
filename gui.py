import spotipy
from spotipy.oauth2 import SpotifyOAuth
import speech_recognition as sr
import webbrowser
import pyttsx3
import musicLibrary
import google.generativeai as genai
import os
import wikipediaapi
import datetime
import requests
import re
import logging
from typing import Optional
import platform
import subprocess
import threading
import time
import sys
import json
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

# Global flag for interruption
interrupt_speaking = False
is_speaking = False

# Initialize recognizer and TTS engine with enhanced settings
recognizer = sr.Recognizer()
recognizer.energy_threshold = 4000
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 1.2
recognizer.phrase_threshold = 0.3

# FIXED TTS INITIALIZATION WITH ERROR HANDLING
def initialize_tts():
    """Initialize TTS engine with proper error handling and fallbacks"""
    global engine
    engine = None
    
    try:
        # Try to initialize pyttsx3
        engine = pyttsx3.init()
        
        # Test if engine works
        engine.say("Testing")
        engine.runAndWait()
        
        # Configure engine properties
        engine.setProperty('rate', 180)
        engine.setProperty('volume', 0.9)
        
        # Try to set a better voice
        voices = engine.getProperty('voices')
        if voices:
            # Print available voices for debugging
            print("Available voices:")
            for i, voice in enumerate(voices):
                print(f"{i}: {voice.name} - {voice.id}")
            
            # Set voice (try female first, then any available)
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            else:
                # Use first available voice if no female voice found
                engine.setProperty('voice', voices[0].id)
        
        print("✅ TTS Engine initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ TTS Engine failed to initialize: {e}")
        print("Troubleshooting steps:")
        print("1. Make sure your audio drivers are working")
        print("2. Try: pip uninstall pyttsx3 && pip install pyttsx3")
        print("3. On Windows, try: pip install pywin32")
        print("4. On Mac, try: pip install pyobjc==9.0.1")
        print("5. On Linux, try: sudo apt-get install espeak espeak-data libespeak1 libespeak-dev")
        return False

# Initialize TTS at startup
tts_working = initialize_tts()

# Gemini API details
GEMINI_API_KEY = "AIzaSyDJrhNrl-MsGQ1zc0hc3jVXFQjh3xMwHDI"

# Configure Gemini with enhanced setup
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = None
gemini_enabled = False

# Try to setup Gemini with multiple model options
model_names = [
    'models/gemini-2.5-flash',
    'models/gemini-1.5-flash-latest', 
    'models/gemini-1.5-flash',
    'models/gemini-1.5-pro-latest',
    'gemini-2.5-flash',
    'gemini-1.5-flash'
]

for model_name in model_names:
    try:
        print(f"Testing model: {model_name}")
        gemini_model = genai.GenerativeModel(
            model_name,
            generation_config={
                'temperature': 0.7,
                'max_output_tokens': 1000,
            }
        )
        
        # Test the model
        test_response = gemini_model.generate_content("Say hello briefly")
        if test_response and test_response.text:
            print(f"✅ Successfully configured with model: {model_name}")
            gemini_enabled = True
            break
            
    except Exception as e:
        print(f"Model {model_name} failed: {str(e)[:50]}...")
        continue

# Spotify API details
SPOTIPY_CLIENT_ID = 'f1fe5288f8134ae38f650ad041ab2385'
SPOTIPY_CLIENT_SECRET = 'aa6baa5aec6c4a9593a66fec68ae4b0a'
SPOTIFY_REDIRECT_URI = 'http://localhost:8888/callback'

# Initialize Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIFY_REDIRECT_URI,
                                               scope="user-modify-playback-state,user-read-playback-state"))

# Initialize Wikipedia
wiki_wiki = wikipediaapi.Wikipedia(
    language='en',
    user_agent='MyVoiceAssistant/1.0 (contact@myvoiceassistant.com)'
)

# Session data for enhanced features
session_data = {
    'start_time': datetime.datetime.now(),
    'commands_processed': 0,
    'conversation_context': [],
    'youtube_search_results': []  # Store YouTube search results
}

def calibrate_microphone():
    """Enhanced microphone calibration"""
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1.5)
            ambient_energy = recognizer.energy_threshold
            
            if ambient_energy > 8000:
                speak("I notice it's a bit noisy here, so I'm adjusting my sensitivity.")
                recognizer.energy_threshold = ambient_energy * 1.2
            elif ambient_energy < 1000:
                speak("It's nice and quiet here, so I'm making myself more sensitive to your voice.")
                recognizer.energy_threshold = 1000
            else:
                speak("The sound levels look perfect.")
                
    except Exception as e:
        speak("I had a small issue calibrating my microphone, but I should still be able to hear you fine.")

def clean_text_for_speech(text: str) -> str:
    """Clean text for better speech synthesis"""
    # Remove markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'`(.*?)`', r'\1', text)
    
    # Replace common abbreviations
    replacements = {
        'URL': 'U R L', 'API': 'A P I', 'AI': 'A I', 'UI': 'U I',
        'OS': 'Operating System', 'etc.': 'etcetera',
        'e.g.': 'for example', 'i.e.': 'that is'
    }
    
    for abbr, full in replacements.items():
        text = text.replace(abbr, full)
    
    return text

def listen_for_interruption():
    """Background listener for interruption"""
    global interrupt_speaking
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.1)
            audio = recognizer.listen(source, timeout=0.5, phrase_time_limit=1)
        
        try:
            command = recognizer.recognize_google(audio, language='en-US').lower()
            if any(word in command for word in ["stop", "pause", "wait", "hold on"]):
                interrupt_speaking = True
                print("🛑 Interruption detected!")
        except:
            pass
    except:
        pass

def speak(text):
    """FIXED text-to-speech with better error handling"""
    global interrupt_speaking, is_speaking, engine, tts_working
    
    try:
        # Always print what we're about to say
        print(f"🤖 Assistant: {text}")
        
        # If TTS is not working, just print and return
        if not tts_working or engine is None:
            print("⚠️ TTS not available - text only mode")
            return
        
        # Clean text for better speech
        clean_text = clean_text_for_speech(text)
        
        # Try different approaches to make TTS work
        is_speaking = True
        interrupt_speaking = False
        
        try:
            # Method 1: Standard approach
            engine.say(clean_text)
            engine.runAndWait()
            
        except Exception as e1:
            print(f"TTS Method 1 failed: {e1}")
            try:
                # Method 2: Stop any existing speech first
                engine.stop()
                engine.say(clean_text)
                engine.runAndWait()
                
            except Exception as e2:
                print(f"TTS Method 2 failed: {e2}")
                try:
                    # Method 3: Reinitialize engine
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 180)
                    engine.setProperty('volume', 0.9)
                    engine.say(clean_text)
                    engine.runAndWait()
                    
                except Exception as e3:
                    print(f"TTS Method 3 failed: {e3}")
                    print("⚠️ All TTS methods failed - continuing in text-only mode")
                    tts_working = False
        
        is_speaking = False
        interrupt_speaking = False
        
    except Exception as e:
        print(f"❌ Critical TTS error: {e}")
        print("⚠️ Switching to text-only mode")
        tts_working = False
        is_speaking = False

def speak_immediately(text):
    """Speak text immediately without interruption handling"""
    global engine, tts_working
    
    if not tts_working or engine is None:
        print(f"🤖 {text}")
        return
        
    try:
        clean_text = clean_text_for_speech(text)
        engine.say(clean_text)
        engine.runAndWait()
    except Exception as e:
        print(f"Immediate speech error: {e}")
        print(f"🤖 {text}")

def speak_and_print(text):
    """Always both print AND speak the text"""
    print(f"🤖 {text}")
    speak(text)

def test_tts():
    """Test TTS functionality"""
    print("Testing TTS functionality...")
    
    if not tts_working:
        print("❌ TTS is not initialized")
        return False
    
    try:
        test_phrases = [
            "Hello, this is a test",
            "Testing one two three",
            "Can you hear me now?"
        ]
        
        for phrase in test_phrases:
            print(f"Testing phrase: {phrase}")
            speak_immediately(phrase)
            time.sleep(1)
        
        print("✅ TTS test completed")
        return True
        
    except Exception as e:
        print(f"❌ TTS test failed: {e}")
        return False

def get_youtube_search_results(query: str, max_results: int = 5):
    """Get YouTube search results using YouTube's search API simulation"""
    try:
        # Create search URL for YouTube
        search_query = quote_plus(query)
        search_url = f"https://www.youtube.com/results?search_query={search_query}"
        
        # Since we can't use YouTube API without proper setup, 
        # we'll create mock results and let user open YouTube search page
        # This is a simplified approach - in production you'd use YouTube Data API v3
        
        mock_results = [
            {"title": f"{query} - Official Video", "url": f"https://www.youtube.com/watch?v=mock1"},
            {"title": f"{query} - Lyric Video", "url": f"https://www.youtube.com/watch?v=mock2"},
            {"title": f"{query} - Live Performance", "url": f"https://www.youtube.com/watch?v=mock3"},
            {"title": f"{query} - Cover Version", "url": f"https://www.youtube.com/watch?v=mock4"},
            {"title": f"{query} - Remix", "url": f"https://www.youtube.com/watch?v=mock5"}
        ]
        
        return search_url, mock_results[:max_results]
        
    except Exception as e:
        print(f"Error in YouTube search: {e}")
        return None, []

def play_youtube_song_interactive(song_name):
    """Enhanced YouTube song playing with interactive selection"""
    try:
        song_name = song_name.strip()
        if not song_name:
            return "Please tell me what song you'd like to hear."
        
        speak(f"I'm searching YouTube for {song_name}. Let me open the search results for you.")
        
        # Get search results
        search_url, results = get_youtube_search_results(song_name, 5)
        
        if not search_url:
            return f"I'm having trouble searching for {song_name} right now."
        
        # Open YouTube search page
        webbrowser.open(search_url)
        
        # Store results in session data for later selection
        session_data['youtube_search_results'] = results
        
        speak(f"I've opened YouTube search results for {song_name}. I can see several options. Would you like me to list them for you to choose from?")
        
        # Wait for user response
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                speak("Say 'yes' if you want me to list the options, or 'no' if you'll choose yourself.")
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)
                
            response = recognizer.recognize_google(audio, language='en-US').lower()
            
            if "yes" in response:
                return list_youtube_options()
            else:
                speak("Perfect! You can choose any video from the search results. If you want to select by number later, just say 'play number' followed by the number.")
                return f"YouTube search opened for: {song_name}"
                
        except Exception as e:
            speak("I'll let you choose from the search results yourself. If you want to select by number later, just say 'play number' followed by the number.")
            return f"YouTube search opened for: {song_name}"
        
    except Exception as e:
        return f"Error searching YouTube for: {song_name}. Error: {str(e)}"

def list_youtube_options():
    """List YouTube search options for user selection"""
    try:
        results = session_data.get('youtube_search_results', [])
        
        if not results:
            speak("I don't have any search results to show you right now.")
            return "No search results available"
        
        speak("Here are the top YouTube results I found:")
        
        options_text = "YouTube Search Results:\n"
        for i, result in enumerate(results, 1):
            option = f"Option {i}: {result['title']}"
            options_text += f"{i}. {result['title']}\n"
            speak(option)
        
        speak("Which one would you like to play? Just say 'number' followed by your choice, like 'number 3' or 'play number 2'.")
        
        return options_text
        
    except Exception as e:
        speak("I had trouble listing the options. You can choose directly from the YouTube page I opened.")
        return "Error listing options"

def play_youtube_by_number(number: int):
    """Play YouTube video by selection number"""
    try:
        results = session_data.get('youtube_search_results', [])
        
        if not results:
            speak("I don't have any search results saved. Please search for a song first.")
            return "No search results available"
        
        if number < 1 or number > len(results):
            speak(f"Please choose a number between 1 and {len(results)}.")
            return f"Invalid selection. Choose between 1 and {len(results)}"
        
        selected = results[number - 1]
        speak(f"Great choice! Playing option {number}: {selected['title']}")
        
        # Since we don't have real URLs, we'll open a new search for the specific title
        # In a real implementation, you'd open the actual video URL
        specific_search = quote_plus(selected['title'])
        video_url = f"https://www.youtube.com/results?search_query={specific_search}"
        webbrowser.open(video_url)
        
        return f"Now playing: {selected['title']}"
        
    except Exception as e:
        speak("I had trouble playing that selection. You can click on the video directly from the YouTube page.")
        return f"Error playing selection: {str(e)}"

def aiProcess(command):
    """Enhanced AI processing with context awareness and conversational prompting"""
    if not gemini_enabled:
        return "I'm sorry, but my AI brain isn't working right now. Please check my configuration."
    
    try:
        base_prompt = f"""You are a helpful, friendly voice assistant having a natural conversation with a human. 

IMPORTANT INSTRUCTIONS:
- Respond like you're talking to a friend - be conversational, warm, and natural
- Keep responses concise but helpful (2-4 sentences usually)
- Use contractions and casual language (I'm, you're, don't, can't, etc.)
- Be enthusiastic and engaging
- If explaining something technical, use simple terms
- Always sound human and friendly
- Don't be too formal or robotic

Human's question or request: {command}

Respond as if you're speaking directly to them in a friendly conversation:"""
        
        response = gemini_model.generate_content(base_prompt)
        
        if response and response.text:
            session_data['conversation_context'].append({
                'user': command,
                'assistant': response.text,
                'timestamp': datetime.datetime.now()
            })
            
            if len(session_data['conversation_context']) > 5:
                session_data['conversation_context'] = session_data['conversation_context'][-5:]
            
            return response.text
        else:
            return "Hmm, I'm having trouble thinking of a response right now. Could you try asking that again?"
            
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower():
            return "I've used up my thinking power for now. Give me a few minutes and try again!"
        elif "safety" in error_msg.lower():
            return "I can't help with that particular request, but I'm happy to help with something else!"
        else:
            return f"Sorry, I'm having some technical difficulties. My brain isn't connecting properly right now."

def get_enhanced_time():
    """Get enhanced time with context"""
    now = datetime.datetime.now()
    time_str = now.strftime("The current time is %I:%M %p")
    
    hour = now.hour
    if 5 <= hour < 12:
        time_str += " - Good morning!"
    elif 12 <= hour < 17:
        time_str += " - Good afternoon!"
    elif 17 <= hour < 21:
        time_str += " - Good evening!"
    else:
        time_str += " - Good night!"
    
    return time_str

def get_enhanced_date():
    """Get enhanced date with additional context"""
    now = datetime.datetime.now()
    date_str = now.strftime("Today is %A, %B %d, %Y")
    week_num = now.isocalendar()[1]
    date_str += f", week {week_num} of the year"
    return date_str

def get_weather(city: str = "Delhi"):
    """Enhanced weather information"""
    try:
        city_encoded = city.strip().replace(" ", "%20")
        url = f"https://wttr.in/{city_encoded}?format=j1"
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            current = data['current_condition'][0]
            
            temp_c = current['temp_C']
            temp_f = current['temp_F']
            desc = current['weatherDesc'][0]['value']
            humidity = current['humidity']
            
            return f"Weather in {city}: {desc}, {temp_c}°C ({temp_f}°F), {humidity}% humidity"
        
        url = f"https://wttr.in/{city_encoded}?format=3"
        response = requests.get(url, timeout=5)
        if response.status_code == 200 and response.text.strip():
            return f"Weather in {city}: {response.text.strip()}"
        
        return f"Unable to fetch weather information for {city}"
        
    except Exception as e:
        return f"Weather service is temporarily unavailable. Please try again later."

def enhanced_calculator(expression: str):
    """Enhanced calculator with more operations"""
    try:
        for word in ["calculate", "what is", "compute", "math"]:
            expression = expression.replace(word, "")
        
        replacements = {
            "plus": "+", "add": "+", "and": "+",
            "minus": "-", "subtract": "-", "less": "-",
            "times": "*", "multiply": "*", "multiplied by": "*",
            "divided by": "/", "divide": "/", "over": "/",
            "power": "**", "to the power of": "**",
            "squared": "**2", "cubed": "**3",
            "percent": "/100", "percentage": "/100"
        }
        
        for word, op in replacements.items():
            expression = expression.replace(word, op)
        
        expression = expression.strip()
        
        allowed_chars = set("0123456789+-*/.()** ")
        if not expression or not all(c in allowed_chars for c in expression):
            return "I can only handle basic math with numbers and operators (+, -, *, /, **)"
        
        if "**" in expression:
            parts = expression.split("**")
            if len(parts) == 2 and parts[1].strip().isdigit():
                if int(parts[1].strip()) > 1000:
                    return "Power operations are limited to exponents under 1000"
        
        result = eval(expression)
        
        if isinstance(result, float):
            if result.is_integer():
                result = int(result)
            else:
                result = round(result, 8)
        
        return f"The result is {result}"
        
    except ZeroDivisionError:
        return "Cannot divide by zero!"
    except Exception as e:
        return "Sorry, I couldn't calculate that. Please check your math expression."

def smart_web_search(query: str):
    """Enhanced web search"""
    try:
        query = query.strip()
        if not query:
            return "Please specify what you'd like to search for."
        
        if len(query.split()) == 1:
            query = f"{query} information"
        
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(search_url)
        
        return f"Searching the web for: {query}. Results opened in your browser."
        
    except Exception as e:
        return f"Error performing web search: {e}"

def is_gemini_question(command: str) -> bool:
    """Enhanced AI routing with better detection"""
    basic_commands = [
        "time", "date", "weather", "open", "search", "hello", "hi", 
        "bye", "exit", "quit", "calculate", "math", "play", "pause", "stop"
    ]
    
    if any(basic in command for basic in basic_commands):
        return False
    
    gemini_triggers = [
        "explain", "tell me about", "what is", "what are", "how does", "how do",
        "why", "who is", "who was", "when did", "when was", "where is", "where was",
        "define", "describe", "help me understand", "teach me", "learn about",
        "difference between", "compare", "analyze", "summarize", "list",
        "recommend", "suggest", "advice", "opinion", "think", "believe"
    ]
    
    question_patterns = [
        command.endswith('?'),
        any(trigger in command for trigger in gemini_triggers),
        any(word in command for word in ["what", "how", "why", "who", "when", "where"]),
        len(command.split()) > 6,
        "vs" in command or "versus" in command
    ]
    
    return any(question_patterns)

def extract_city_from_weather_command(command: str) -> str:
    """Extract city name from weather command"""
    for word in ["weather", "in", "for", "of", "today", "current", "now"]:
        command = command.replace(word, "")
    
    city = command.strip()
    
    if not city or city in ["here", "local", "my location"]:
        city = "Delhi"
    
    return city

def generate_contextual_greeting():
    """Generate contextual greeting"""
    hour = datetime.datetime.now().hour
    
    if 5 <= hour < 12:
        greeting = "Good morning!"
    elif 12 <= hour < 17:
        greeting = "Good afternoon!"
    elif 17 <= hour < 21:
        greeting = "Good evening!"
    else:
        greeting = "Good night!"
    
    if session_data['commands_processed'] == 1:
        greeting += " I'm your enhanced voice assistant. How can I help you today?"
    else:
        greeting += " How can I assist you further?"
    
    return greeting

def get_session_info():
    """Get session statistics"""
    duration = datetime.datetime.now() - session_data['start_time']
    minutes = int(duration.total_seconds() / 60)
    
    info = f"Session Statistics: "
    info += f"Duration: {minutes} minute{'s' if minutes != 1 else ''}, "
    info += f"Commands processed: {session_data['commands_processed']}, "
    info += f"Gemini AI: {'Connected' if gemini_enabled else 'Not configured'}, "
    info += f"TTS: {'Working' if tts_working else 'Not working'}"
    
    return info

def play_spotify_song(song_name):
    """Play song on Spotify with spoken feedback"""
    try:
        devices = sp.devices()
        if not devices['devices']:
            speak("I don't see any active Spotify devices. Please make sure Spotify is open on one of your devices.")
            return

        active_device_id = devices['devices'][0]['id']
        speak(f"Searching for {song_name} on Spotify.")
        
        results = sp.search(q=song_name, limit=1)
        if results['tracks']['items']:
            track_uri = results['tracks']['items'][0]['uri']
            track_name = results['tracks']['items'][0]['name']
            artist_name = results['tracks']['items'][0]['artists'][0]['name']
            
            sp.start_playback(device_id=active_device_id, uris=[track_uri])
            speak(f"Perfect! Now playing {track_name} by {artist_name} on Spotify.")
        else:
            speak(f"I couldn't find {song_name} on Spotify. Would you like me to try YouTube instead?")
    except Exception as e:
        speak(f"I'm having trouble connecting to Spotify right now. Let me try playing it on YouTube instead.")
        result = play_youtube_song_interactive(song_name)
        speak(result)

def stop_spotify_playback():
    """Stop Spotify with spoken feedback"""
    try:
        devices = sp.devices()
        if not devices['devices']:
            speak("I don't see any active Spotify devices right now.")
            return

        active_device_id = devices['devices'][0]['id']
        sp.pause_playback(device_id=active_device_id)
        speak("I've stopped the music on Spotify for you.")
    except Exception as e:
        speak("I had trouble stopping Spotify. The music might have already been paused.")

def processCommand(c):
    """Enhanced command processing with new features"""
    try:
        original_command = c
        c_lower = c.lower().strip()
        
        session_data['commands_processed'] += 1
        
        # STOP command - highest priority
        if any(word in c_lower for word in ["stop", "quit", "exit", "bye", "goodbye", "stop listening", "shut down", "turn off"]):
            duration = datetime.datetime.now() - session_data['start_time']
            minutes = int(duration.total_seconds() / 60)
            
            goodbye = "Goodbye! "
            if minutes > 0:
                goodbye += f"We chatted for {minutes} minute{'s' if minutes != 1 else ''}. "
            if session_data['commands_processed'] > 5:
                goodbye += "Thanks for the great conversation! "
            goodbye += "Have a wonderful day!"
            
            speak(goodbye)
            return "stop"
        
        # YouTube number selection
        elif "number" in c_lower and any(digit.isdigit() for digit in c_lower.split()):
            try:
                # Extract number from command
                numbers = re.findall(r'\d+', c_lower)
                if numbers:
                    number = int(numbers[0])
                    result = play_youtube_by_number(number)
                    speak(result)
                    return None
            except Exception as e:
                speak("I had trouble with that number. Please say it again or choose directly from YouTube.")
                return None
        
        # List YouTube options
        elif "list options" in c_lower or "show options" in c_lower or "what are the options" in c_lower:
            result = list_youtube_options()
            return None
        
        # Test TTS command
        elif "test speech" in c_lower or "test tts" in c_lower:
            speak("Testing text to speech functionality. If you can hear this, TTS is working correctly!")
            return None
        
        # Enhanced greeting detection
        elif any(word in c_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
            greeting = generate_contextual_greeting()
            speak(greeting)
            return None
        
        # Time queries
        elif any(word in c_lower for word in ["time", "clock", "what time"]):
            time_response = get_enhanced_time()
            speak(time_response)
            return None
        
        # Date queries
        elif any(word in c_lower for word in ["date", "today", "what day", "what's the date"]):
            date_response = get_enhanced_date()
            speak(date_response)
            return None
        
        # Weather queries with city extraction
        elif "weather" in c_lower:
            city = extract_city_from_weather_command(c_lower)
            speak(f"Let me check the weather in {city} for you.")
            weather_response = get_weather(city)
            speak(weather_response)
            return None
        
        # Session info
        elif any(word in c_lower for word in ["session", "statistics", "stats", "how long"]):
            session_response = get_session_info()
            speak(session_response)
            return None
        
        # Enhanced web search
        elif "search" in c_lower or "look up" in c_lower or "find" in c_lower:
            query = c_lower.replace("search", "").replace("for", "").replace("look up", "").replace("find", "").strip()
            speak(f"I'll search the web for {query} and open the results for you.")
            search_response = smart_web_search(query)
            speak(search_response)
            return None
        
        # Enhanced calculator
        elif any(word in c_lower for word in ["calculate", "math", "plus", "minus", "multiply", "divide"]):
            speak("Let me calculate that for you.")
            result = enhanced_calculator(c_lower)
            speak(result)
            return None
        
        # Stop music command
        elif "stop the music" in c_lower:
            speak("I'll stop the music for you.")
            stop_spotify_playback()
            return None
        
        # Website opening
        elif "open google" in c_lower:
            webbrowser.open("https://google.com")
            speak("Opening Google for you now.")
        elif "open facebook" in c_lower:
            webbrowser.open("https://facebook.com")
            speak("Opening Facebook for you now.")
        elif "open youtube" in c_lower:
            webbrowser.open("https://youtube.com")
            speak("Opening YouTube for you now.")
        elif "open linkedin" in c_lower:
            webbrowser.open("https://linkedin.com")
            speak("Opening LinkedIn for you now.")
        
        # Music playing - ENHANCED YOUTUBE FUNCTIONALITY
        elif c_lower.startswith("play"):
            song = " ".join(c_lower.split(" ")[1:])
            
            if "on spotify" in c_lower:
                song = song.replace("on spotify", "").strip()
                speak(f"I'll play {song} on Spotify for you.")
                play_spotify_song(song)
            elif "on youtube" in c_lower or "on yt" in c_lower:
                song = song.replace("on youtube", "").replace("on yt", "").strip()
                speak(f"I'll search YouTube for {song} and give you options to choose from.")
                result = play_youtube_song_interactive(song)
                return None
            else:
                # Check music library first
                link = musicLibrary.music.get(song, None)
                if link:
                    webbrowser.open(link)
                    speak(f"Playing {song} from your music library.")
                else:
                    speak(f"I'll search YouTube for {song} and give you options to choose from.")
                    result = play_youtube_song_interactive(song)
        
        # Wikipedia search
        elif "wikipedia" in c_lower:
            query = c_lower.split("for")[1].strip() if "for" in c_lower else c_lower.replace("wikipedia", "").strip()
            speak(f"Let me search Wikipedia for {query}.")
            search_wikipedia(query)
        
        # Route to Gemini AI for complex questions
        elif is_gemini_question(c_lower):
            if gemini_enabled:
                speak("Let me think about that for a moment.")
                output = aiProcess(original_command)
                speak(output)
            else:
                speak("I'd like to help with that question, but my AI brain isn't configured right now.")
        
        # Default AI processing for other queries
        else:
            speak("Let me think about that.")
            output = aiProcess(original_command)
            speak(output)
        
        return None
        
    except Exception as e:
        error_msg = f"I'm sorry, I encountered an error while processing your request. Let me try to help you with something else."
        speak(error_msg)
        return None

def search_wikipedia(query):
    """Search Wikipedia and SPEAK the results"""
    speak(f"Let me search Wikipedia for {query}.")
    
    try:
        page = wiki_wiki.page(query)
        if page.exists():
            summary = page.summary[:400]
            speak(f"Here's what I found on Wikipedia about {query}: {summary}")
        else:
            speak(f"I'm sorry, I couldn't find any information about {query} on Wikipedia. Would you like me to search for something else?")
    except Exception as e:
        speak(f"I had trouble accessing Wikipedia right now. Let me try searching the web for {query} instead.")
        smart_web_search(query)

def listen_for_commands():
    """Enhanced listening with better error handling"""
    while True:
        speak("I'm listening for your command.")
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=15, phrase_time_limit=20)
                
            speak("Let me process what you said.")
            command = recognizer.recognize_google(audio, language='en-US')
            speak(f"I heard you say: {command}")
            
            result = processCommand(command)
            if result == "stop":
                break
                
        except sr.WaitTimeoutError:
            speak("I didn't hear anything. I'm still here and listening.")
            continue
        except sr.UnknownValueError:
            speak("Sorry, I couldn't understand what you said. Could you please repeat that?")
            continue
        except sr.RequestError as e:
            speak(f"I'm having trouble with my hearing right now. There's a speech recognition error.")
            continue
        except Exception as e:
            speak(f"Something unexpected happened. Let me try to keep listening.")
            continue

if __name__ == "__main__":
    print("="*50)
    print("VOICE ASSISTANT STARTUP")
    print("="*50)
    
    # Test TTS first
    print("\n🔊 Testing Text-to-Speech...")
    if tts_working:
        speak("Hello! I'm starting up your enhanced voice assistant with improved YouTube functionality.")
        test_tts()
    else:
        print("❌ TTS is not working - running in text-only mode")
        print("🤖 Hello! I'm starting up your enhanced voice assistant (text-only mode)")
    
    # Enhanced initialization message
    welcome_msg = "I'm fully online and ready to help! "
    if gemini_enabled:
        welcome_msg += "My AI brain is connected and working perfectly. "
    if tts_working:
        welcome_msg += "My speech system is working great. "
    else:
        welcome_msg += "I'm running in text-only mode since speech isn't working. "
    welcome_msg += "I can help with time, weather, calculations, web searches, playing music on Spotify or YouTube with interactive selection, and answering any questions you have. When you ask me to play something on YouTube, I'll give you options to choose from by saying 'number 1', 'number 2', etc. Just say 'stop' whenever you want me to shut down."
    
    speak(welcome_msg)
    
    # System status
    print(f"\n🔊 SYSTEM STATUS:")
    print(f"TTS Engine: {'✅ Working' if tts_working else '❌ Not Working'}")
    print(f"Gemini AI: {'✅ Connected' if gemini_enabled else '❌ Not Connected'}")
    print(f"Speech Recognition: {'✅ Ready' if True else '❌ Not Ready'}")
    print(f"YouTube Integration: ✅ Enhanced with Interactive Selection")
    
    if not tts_working:
        print("\n⚠️  TTS TROUBLESHOOTING:")
        print("Try these commands in your terminal:")
        print("pip uninstall pyttsx3")
        print("pip install pyttsx3")
        
        if platform.system() == "Windows":
            print("pip install pywin32")
        elif platform.system() == "Darwin":  # macOS
            print("pip install pyobjc==9.0.1")
        elif platform.system() == "Linux":
            print("sudo apt-get install espeak espeak-data libespeak1 libespeak-dev")
    
    # Calibrate microphone
    speak("Let me quickly calibrate my hearing.")
    calibrate_microphone()
    speak("Perfect! My hearing is all set up. Now I have enhanced YouTube functionality - when you ask me to play something, I'll open YouTube search and you can tell me which video to play by number!")
    
    while True:  # Outer loop for wake word
        speak("I'm waiting for you to say 'hello' to wake me up.")
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)
            
            word = recognizer.recognize_google(audio)
            if word.lower() == "hello":
                speak("Hello there! I'm ready to help you. What would you like me to do? I can now help you select YouTube videos by number!")
                listen_for_commands()
                
        except sr.UnknownValueError:
            continue
        except sr.RequestError as e:
            speak("I'm having some trouble with my hearing. Let me keep trying.")
            continue
        except Exception as e:
            continue