#!/usr/bin/env python3
"""
Optimized Voice Assistant - Command Line Interface
A lightweight voice assistant with Gemini AI integration
"""

import threading
import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import requests
import google.generativeai as genai
import time
import sys
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.WARNING)

class VoiceAssistant:
    def __init__(self):
        """Initialize the voice assistant with optimized settings"""
        print("🤖 Initializing Voice Assistant...")
        
        # Initialize text-to-speech engine with optimized settings
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 180)  # Slightly faster speech
        self.engine.setProperty('volume', 0.8)
        
        # Initialize speech recognition with optimized settings
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 4000  # Adjust based on environment
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8  # Shorter pause detection
        
        self.microphone = sr.Microphone()
        self.is_listening_active = False
        
        # Gemini AI setup
        self.gemini_model = None
        self.gemini_enabled = False
        self.api_key = None
        
        # ==================== GEMINI API KEY ====================
        GEMINI_API_KEY = "AIzaSyCjF8tEq2C2NwnEnJXfh1ECol8L6nJ3nIc"
        
        # Auto-setup Gemini AI if key is provided
        if GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
            self.setup_gemini(GEMINI_API_KEY)
        
        # Calibrate microphone once during initialization
        self._calibrate_microphone()
        
        print("✅ Voice Assistant initialized successfully!")
    
    def _calibrate_microphone(self):
        """Calibrate microphone for ambient noise (optimized)"""
        try:
            print("🎤 Calibrating microphone...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("✅ Microphone calibrated")
        except Exception as e:
            print(f"⚠️  Warning: Could not calibrate microphone: {e}")
    
    def setup_gemini(self, api_key: str) -> bool:
        """Setup Gemini AI with API key"""
        try:
            print("🔧 Setting up Gemini AI...")
            self.api_key = api_key
            genai.configure(api_key=api_key)
            # Try different model names that are currently supported
            model_names = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
            
            for model_name in model_names:
                try:
                    self.gemini_model = genai.GenerativeModel(model_name)
                    # Test the model
                    test_response = self.gemini_model.generate_content("Hello")
                    if test_response and test_response.text:
                        print(f"✅ Using model: {model_name}")
                        break
                except Exception as e:
                    print(f"⚠️  Model {model_name} failed: {e}")
                    continue
            else:
                raise Exception("No supported Gemini model found")
            
            # Quick connection test
            test_response = self.gemini_model.generate_content("Hello")
            if test_response and test_response.text:
                self.gemini_enabled = True
                print("✅ Gemini AI configured successfully!")
                return True
            else:
                raise Exception("No response from Gemini")
                
        except Exception as e:
            print(f"❌ Error setting up Gemini: {str(e)}")
            self.gemini_enabled = False
            return False
    
    def ask_gemini(self, question: str) -> str:
        """Ask Gemini AI a question with error handling"""
        if not self.gemini_enabled:
            return "Gemini AI is not configured. Please set up your API key first."
        
        try:
            response = self.gemini_model.generate_content(question)
            return response.text if response and response.text else "I couldn't generate a response."
        except Exception as e:
            return f"Error communicating with Gemini: {str(e)}"
    
    def speak(self, text: str):
        """Convert text to speech with optimization"""
        try:
            print(f"🤖 Assistant: {text}")
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"❌ Text-to-speech error: {e}")
    
    def listen_once(self, timeout: int = 5) -> str:
        """Listen for a single command with timeout"""
        try:
            print("🎤 Listening...")
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            
            print("🔄 Processing speech...")
            text = self.recognizer.recognize_google(audio)
            print(f"👤 You said: {text}")
            return text.lower()
        
        except sr.WaitTimeoutError:
            return "timeout"
        except sr.UnknownValueError:
            return "unknown"
        except sr.RequestError as e:
            print(f"❌ Speech recognition error: {e}")
            return "error"
        except Exception as e:
            print(f"❌ Microphone error: {e}")
            return "error"
    
    def get_current_time(self) -> str:
        """Get current time"""
        return datetime.datetime.now().strftime("The current time is %I:%M %p")
    
    def get_current_date(self) -> str:
        """Get current date"""
        return datetime.datetime.now().strftime("Today is %A, %B %d, %Y")
    
    def open_website(self, url: str) -> str:
        """Open website in default browser"""
        try:
            webbrowser.open(url)
            return f"Opening {url}"
        except Exception as e:
            return f"Error opening website: {e}"
    
    def search_web(self, query: str) -> str:
        """Search web using default browser"""
        try:
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            return f"Searching for: {query}"
        except Exception as e:
            return f"Error searching web: {e}"
    
    def get_weather(self, city: str = "") -> str:
        """Get weather information using free API with better error handling"""
        if not city:
            return "Please specify a city for weather information"
        
        try:
            # Clean up the city name
            city = city.strip().replace(" ", "%20")
            url = f"https://wttr.in/{city}?format=3"
            response = requests.get(url, timeout=10)
            if response.status_code == 200 and response.text.strip():
                return f"Weather: {response.text.strip()}"
            else:
                # Fallback - try a different format
                url = f"https://wttr.in/{city}?format=1"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    return f"Weather: {response.text.strip()}"
                return f"Unable to fetch weather for {city.replace('%20', ' ')}"
        except Exception as e:
            return f"Weather service temporarily unavailable. Please try again later."
    
    def is_gemini_question(self, command: str) -> bool:
        """Determine if command should be handled by Gemini AI"""
        # Basic commands that shouldn't go to Gemini
        basic_commands = ["time", "date", "weather", "open", "search", "hello", "hi", "bye", "exit", "quit"]
        
        if any(basic in command for basic in basic_commands):
            return False
        
        # Gemini triggers
        gemini_triggers = [
            "explain", "tell me about", "what is", "how does", "why", "who is", 
            "when did", "where is", "define", "describe", "help me understand"
        ]
        
        return (any(trigger in command for trigger in gemini_triggers) or 
                command.endswith('?') or 
                any(word in command for word in ["what", "how", "why", "who", "when", "where"]) or
                len(command.split()) > 5)
    
    def calculate(self, command: str) -> str:
        """Simple calculator with safety checks"""
        try:
            # Clean the command
            for word in ["calculate", "what is", "compute"]:
                command = command.replace(word, "")
            
            # Replace words with operators
            replacements = {
                "plus": "+", "add": "+", "minus": "-", "subtract": "-",
                "times": "*", "multiply": "*", "divided by": "/", "divide": "/"
            }
            
            for word, op in replacements.items():
                command = command.replace(word, op)
            
            command = command.strip()
            
            # Safety check - only allow safe characters
            if all(c in "0123456789+-*/.() " for c in command) and command:
                result = eval(command)
                return f"The result is {result}"
            else:
                return "Sorry, I can only handle basic math operations with numbers and +, -, *, /"
        except Exception:
            return "Sorry, I couldn't calculate that. Please check your math expression."
    
    def process_command(self, command: str) -> str:
        """Process and execute commands with optimized routing"""
        command = command.lower().strip()
        
        if not command or command in ["timeout", "unknown", "error"]:
            return "I didn't understand that. Please try again."
        
        # Quick routing for common commands
        if any(word in command for word in ["hello", "hi", "hey"]):
            return "Hello! How can I help you today?"
        
        elif any(word in command for word in ["time", "clock"]):
            return self.get_current_time()
        
        elif any(word in command for word in ["date", "today"]):
            return self.get_current_date()
        
        elif "weather" in command:
            # Better parsing for weather commands
            city_part = command.replace("weather", "").replace("in", "").replace("of", "").replace("today", "").strip()
            # Handle common phrases
            if not city_part or city_part in ["", "here", "current", "local"]:
                city_part = "Delhi"  # Default to Delhi for India
            return self.get_weather(city_part)
        
        elif "search" in command:
            query = command.replace("search", "").replace("for", "").strip()
            return self.search_web(query)
        
        elif "open" in command:
            if "google" in command:
                return self.open_website("https://www.google.com")
            elif "youtube" in command:
                return self.open_website("https://www.youtube.com")
            elif "facebook" in command:
                return self.open_website("https://www.facebook.com")
            elif "twitter" in command:
                return self.open_website("https://www.twitter.com")
        
        elif any(word in command for word in ["calculate", "math", "plus", "minus", "multiply", "divide"]):
            return self.calculate(command)
        
        elif any(word in command for word in ["exit", "quit", "bye", "goodbye"]):
            return "Goodbye! Have a great day!"
        
        # Check if it should go to Gemini
        elif self.is_gemini_question(command):
            if self.gemini_enabled:
                print("🤔 Thinking... (using Gemini AI)")
                return self.ask_gemini(command)
            else:
                return "I'd like to help with that question, but Gemini AI is not configured."
        
        # Default fallback
        else:
            return f"I heard '{command}' but I'm not sure how to help with that. Try asking for time, date, weather, or web search."
    
    def run_interactive_mode(self):
        """Run the assistant in interactive mode"""
        print("\n" + "="*60)
        print("🤖 VOICE ASSISTANT - INTERACTIVE MODE")
        print("="*60)
        print("Commands you can try:")
        print("• 'What time is it?' or 'time'")
        print("• 'What's the date?' or 'date'")
        print("• 'Weather in London'")
        print("• 'Search for Python programming'")
        print("• 'Open Google/YouTube/Facebook/Twitter'")
        print("• 'Calculate 15 plus 25'")
        if self.gemini_enabled:
            print("• 'Explain quantum physics' (Gemini AI)")
            print("• 'What is machine learning?' (Gemini AI)")
        print("• 'Exit' or 'quit' to stop")
        print("-"*60)
        
        # Welcome message
        welcome = "Voice assistant ready!"
        if self.gemini_enabled:
            welcome += " Gemini AI is connected for complex questions."
        self.speak(welcome)
        
        try:
            while True:
                # Listen for command
                command = self.listen_once(timeout=10)
                
                if command == "timeout":
                    print("⏱️  No input detected. Say something or type 'quit' to exit.")
                    continue
                elif command in ["unknown", "error"]:
                    print("❌ Sorry, I didn't catch that. Please try again.")
                    continue
                
                # Process command
                response = self.process_command(command)
                
                # Handle exit
                if any(word in command for word in ["exit", "quit", "bye", "goodbye"]):
                    self.speak(response)
                    break
                
                # Speak response
                self.speak(response)
                
        except KeyboardInterrupt:
            print("\n👋 Assistant stopped by user")
        except Exception as e:
            print(f"❌ Error in interactive mode: {e}")
    
    def run_single_command(self, command: str):
        """Process a single command (useful for scripting)"""
        response = self.process_command(command)
        self.speak(response)
        return response


def main():
    """Main function with command line interface"""
    print("🚀 Starting Voice Assistant...")
    
    try:
        assistant = VoiceAssistant()
        
        # Check for command line arguments
        if len(sys.argv) > 1:
            # Single command mode
            command = " ".join(sys.argv[1:])
            print(f"Processing command: {command}")
            assistant.run_single_command(command)
        else:
            # Interactive mode
            assistant.run_interactive_mode()
            
    except KeyboardInterrupt:
        print("\n👋 Voice Assistant stopped")
    except Exception as e:
        print(f"❌ Error starting assistant: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
    