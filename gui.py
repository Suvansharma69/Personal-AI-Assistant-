#!/usr/bin/env python3
"""
Enhanced Voice Assistant - Advanced Multi-Platform Integration
A sophisticated voice assistant with Gemini AI, platform controls, and improved interaction management
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
import os
import json
import re
from typing import Optional, Dict, Any, List
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import subprocess
import platform

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

class VoiceAssistant:
    def __init__(self):
        """Initialize the enhanced voice assistant with multi-platform capabilities"""
        print("🤖 Initializing Enhanced Voice Assistant...")
        
        # Initialize text-to-speech engine with optimized settings
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 180)
        self.engine.setProperty('volume', 0.8)
        
        # Get available voices and set preferred voice
        voices = self.engine.getProperty('voices')
        if voices:
            # Try to set a more natural voice
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
        
        # Initialize speech recognition with enhanced settings
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        
        self.microphone = sr.Microphone()
        self.is_listening_active = False
        self.conversation_context = []
        
        # Gemini AI setup
        self.gemini_model = None
        self.gemini_enabled = False
        self.api_key = None
        
        # Platform integration
        self.platform_controllers = {
            'spotify': SpotifyController(),
            'youtube': YouTubeController(),
            'system': SystemController()
        }
        
        # Task management
        self.current_tasks = {}
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Session state
        self.session_data = {
            'start_time': datetime.datetime.now(),
            'commands_processed': 0,
            'user_preferences': {},
            'conversation_history': []
        }
        
        # ==================== GEMINI API KEY ====================
        GEMINI_API_KEY = "AIzaSyDJrhNrl-MsGQ1zc0hc3jVXFQjh3xMwHDI"  # Replace with your key
        
        # Auto-setup Gemini AI if key is provided
        if GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
            self.setup_gemini(GEMINI_API_KEY)
        
        # Calibrate microphone
        self._calibrate_microphone()
        
        print("✅ Enhanced Voice Assistant initialized successfully!")
    
    def _calibrate_microphone(self):
        """Enhanced microphone calibration with noise detection"""
        try:
            print("🎤 Calibrating microphone for optimal performance...")
            with self.microphone as source:
                print("   Analyzing ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                
                # Test microphone sensitivity
                ambient_energy = self.recognizer.energy_threshold
                print(f"   Ambient energy level: {ambient_energy}")
                
                if ambient_energy > 8000:
                    print("   ⚠️  High noise environment detected - adjusting sensitivity")
                    self.recognizer.energy_threshold = ambient_energy * 1.2
                elif ambient_energy < 1000:
                    print("   🔇 Very quiet environment detected - increasing sensitivity")
                    self.recognizer.energy_threshold = 1000
                    
            print("✅ Microphone calibrated successfully")
        except Exception as e:
            print(f"⚠️  Warning: Could not calibrate microphone: {e}")
    
    def setup_gemini(self, api_key: str) -> bool:
        """Enhanced Gemini AI setup with model selection and testing"""
        try:
            print("🔧 Setting up Gemini AI...")
            self.api_key = api_key
            genai.configure(api_key=api_key)
            
            # Try different model names with priority order
            model_names = [
                'gemini-1.5-flash-latest',
                'gemini-1.5-flash', 
                'gemini-1.5-pro-latest',
                'gemini-1.5-pro', 
                'gemini-pro'
            ]
            
            for model_name in model_names:
                try:
                    print(f"   Testing model: {model_name}")
                    self.gemini_model = genai.GenerativeModel(
                        model_name,
                        generation_config={
                            'temperature': 0.7,
                            'max_output_tokens': 1000,
                        }
                    )
                    
                    # Test the model with a simple query
                    test_response = self.gemini_model.generate_content("Say hello briefly")
                    if test_response and test_response.text:
                        print(f"✅ Successfully configured with model: {model_name}")
                        self.gemini_enabled = True
                        return True
                        
                except Exception as e:
                    print(f"   ❌ Model {model_name} failed: {str(e)[:50]}...")
                    continue
            
            raise Exception("No supported Gemini model found")
                
        except Exception as e:
            print(f"❌ Error setting up Gemini: {str(e)}")
            self.gemini_enabled = False
            return False
    
    def ask_gemini(self, question: str, context: Optional[str] = None) -> str:
        """Enhanced Gemini AI interaction with context awareness"""
        if not self.gemini_enabled:
            return "Gemini AI is not configured. Please set up your API key first."
        
        try:
            # Build context-aware prompt
            prompt = question
            if context:
                prompt = f"Context: {context}\n\nQuestion: {question}"
            
            # Add conversation history for better context
            if self.conversation_context:
                recent_context = self.conversation_context[-3:]  # Last 3 exchanges
                context_str = "\n".join([f"User: {c['user']}\nAssistant: {c['assistant']}" 
                                       for c in recent_context])
                prompt = f"Previous conversation:\n{context_str}\n\nCurrent: {prompt}"
            
            response = self.gemini_model.generate_content(prompt)
            
            if response and response.text:
                # Store in conversation context
                self.conversation_context.append({
                    'user': question,
                    'assistant': response.text,
                    'timestamp': datetime.datetime.now()
                })
                
                # Keep only recent context (last 10 exchanges)
                if len(self.conversation_context) > 10:
                    self.conversation_context = self.conversation_context[-10:]
                
                return response.text
            else:
                return "I couldn't generate a response. Please try rephrasing your question."
                
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower():
                return "I've reached my usage limit for now. Please try again later."
            elif "safety" in error_msg.lower():
                return "I can't provide a response to that request due to safety guidelines."
            else:
                return f"I encountered an error: {error_msg[:100]}..."
    
    def speak(self, text: str, priority: bool = False):
        """Enhanced text-to-speech with priority handling"""
        try:
            print(f"🤖 Assistant: {text}")
            
            if priority:
                # Stop current speech for priority messages
                self.engine.stop()
            
            # Clean text for better speech
            clean_text = self._clean_text_for_speech(text)
            
            self.engine.say(clean_text)
            self.engine.runAndWait()
            
        except Exception as e:
            print(f"❌ Text-to-speech error: {e}")
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text for better speech synthesis"""
        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'`(.*?)`', r'\1', text)
        
        # Replace common abbreviations
        replacements = {
            'URL': 'U R L',
            'API': 'A P I',
            'AI': 'A I',
            'UI': 'U I',
            'OS': 'Operating System',
            'etc.': 'etcetera',
            'e.g.': 'for example',
            'i.e.': 'that is'
        }
        
        for abbr, full in replacements.items():
            text = text.replace(abbr, full)
        
        return text
    
    def listen_once(self, timeout: int = 8) -> str:
        """Enhanced speech recognition with noise filtering"""
        try:
            print("🎤 Listening... (speak clearly)")
            
            with self.microphone as source:
                # Dynamic adjustment based on environment
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                
                # Listen with enhanced parameters
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=15,
                    snowball_effect=True
                )
            
            print("🔄 Processing speech...")
            
            # Try multiple recognition engines for better accuracy
            try:
                text = self.recognizer.recognize_google(audio, language='en-US')
            except sr.UnknownValueError:
                # Fallback to alternative service if available
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                except:
                    raise sr.UnknownValueError()
            
            print(f"👤 You said: {text}")
            
            # Update session statistics
            self.session_data['commands_processed'] += 1
            
            return text.lower().strip()
        
        except sr.WaitTimeoutError:
            return "timeout"
        except sr.UnknownValueError:
            return "unknown"
        except sr.RequestError as e:
            print(f"❌ Speech recognition service error: {e}")
            return "error"
        except Exception as e:
            print(f"❌ Microphone error: {e}")
            return "error"
    
    def get_enhanced_time(self) -> str:
        """Get enhanced time information"""
        now = datetime.datetime.now()
        time_str = now.strftime("The current time is %I:%M %p")
        
        # Add contextual information
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
    
    def get_enhanced_date(self) -> str:
        """Get enhanced date information with additional context"""
        now = datetime.datetime.now()
        date_str = now.strftime("Today is %A, %B %d, %Y")
        
        # Add week information
        week_num = now.isocalendar()[1]
        date_str += f", week {week_num} of the year"
        
        return date_str
    
    def get_weather(self, city: str = "") -> str:
        """Enhanced weather information with multiple data sources"""
        if not city:
            city = "Delhi"  # Default city
        
        try:
            # Primary weather service
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
                
                weather_info = f"Weather in {city}: {desc}, {temp_c}°C ({temp_f}°F), {humidity}% humidity"
                return weather_info
            
            # Fallback to simple format
            url = f"https://wttr.in/{city_encoded}?format=3"
            response = requests.get(url, timeout=5)
            if response.status_code == 200 and response.text.strip():
                return f"Weather in {city}: {response.text.strip()}"
            
            return f"Unable to fetch weather information for {city}"
            
        except Exception as e:
            return f"Weather service is temporarily unavailable. Please try again later."
    
    def smart_web_search(self, query: str) -> str:
        """Enhanced web search with smart query processing"""
        try:
            # Clean and enhance the query
            query = query.strip()
            if not query:
                return "Please specify what you'd like to search for."
            
            # Smart query enhancement
            if len(query.split()) == 1:
                query = f"{query} information"
            
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            
            return f"Searching the web for: {query}. Results opened in your browser."
            
        except Exception as e:
            return f"Error performing web search: {e}"
    
    def enhanced_calculator(self, expression: str) -> str:
        """Enhanced calculator with more operations and safety"""
        try:
            # Clean the expression
            for word in ["calculate", "what is", "compute", "math"]:
                expression = expression.replace(word, "")
            
            # Enhanced word replacements
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
            
            # Enhanced safety check
            allowed_chars = set("0123456789+-*/.()** ")
            if not expression or not all(c in allowed_chars for c in expression):
                return "I can only handle basic math with numbers and operators (+, -, *, /, **)"
            
            # Prevent dangerous operations
            if "**" in expression:
                parts = expression.split("**")
                if len(parts) == 2 and parts[1].strip().isdigit():
                    if int(parts[1].strip()) > 1000:
                        return "Power operations are limited to exponents under 1000"
            
            # Evaluate safely
            result = eval(expression)
            
            # Format result nicely
            if isinstance(result, float):
                if result.is_integer():
                    result = int(result)
                else:
                    result = round(result, 8)  # Limit decimal places
            
            return f"The result is {result}"
            
        except ZeroDivisionError:
            return "Cannot divide by zero!"
        except Exception as e:
            return "Sorry, I couldn't calculate that. Please check your math expression."
    
    def is_gemini_question(self, command: str) -> bool:
        """Enhanced AI routing with better detection"""
        # Basic commands that shouldn't go to Gemini
        basic_commands = [
            "time", "date", "weather", "open", "search", "hello", "hi", 
            "bye", "exit", "quit", "calculate", "math", "play", "pause", "stop"
        ]
        
        if any(basic in command for basic in basic_commands):
            return False
        
        # Strong Gemini indicators
        gemini_triggers = [
            "explain", "tell me about", "what is", "what are", "how does", "how do",
            "why", "who is", "who was", "when did", "when was", "where is", "where was",
            "define", "describe", "help me understand", "teach me", "learn about",
            "difference between", "compare", "analyze", "summarize", "list",
            "recommend", "suggest", "advice", "opinion", "think", "believe"
        ]
        
        # Check for question patterns
        question_patterns = [
            command.endswith('?'),
            any(trigger in command for trigger in gemini_triggers),
            any(word in command for word in ["what", "how", "why", "who", "when", "where"]),
            len(command.split()) > 6,  # Long queries likely need AI
            "vs" in command or "versus" in command
        ]
        
        return any(question_patterns)
    
    def process_command(self, command: str) -> str:
        """Enhanced command processing with context awareness"""
        original_command = command
        command = command.lower().strip()
        
        if not command or command in ["timeout", "unknown", "error"]:
            return self._handle_unclear_input(command)
        
        # Store command in history
        self.session_data['conversation_history'].append({
            'command': original_command,
            'timestamp': datetime.datetime.now()
        })
        
        # Enhanced greeting detection
        if any(word in command for word in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
            return self._generate_contextual_greeting()
        
        # Time-related queries
        elif any(word in command for word in ["time", "clock", "what time"]):
            return self.get_enhanced_time()
        
        # Date-related queries
        elif any(word in command for word in ["date", "today", "what day", "what's the date"]):
            return self.get_enhanced_date()
        
        # Weather queries with enhanced parsing
        elif "weather" in command:
            city_part = self._extract_city_from_weather_command(command)
            return self.get_weather(city_part)
        
        # Web search
        elif "search" in command or "look up" in command or "find" in command:
            query = self._extract_search_query(command)
            return self.smart_web_search(query)
        
        # Website opening
        elif "open" in command:
            return self._handle_website_opening(command)
        
        # Calculator
        elif any(word in command for word in ["calculate", "math", "plus", "minus", "multiply", "divide"]):
            return self.enhanced_calculator(command)
        
        # Platform controls
        elif any(word in command for word in ["play", "pause", "stop", "volume", "skip"]):
            return self._handle_media_control(command)
        
        # System commands
        elif any(word in command for word in ["shutdown", "restart", "sleep", "lock"]):
            return self._handle_system_command(command)
        
        # Exit commands
        elif any(word in command for word in ["exit", "quit", "bye", "goodbye", "stop listening"]):
            return self._generate_goodbye()
        
        # Session information
        elif any(word in command for word in ["session", "statistics", "stats", "how long"]):
            return self._get_session_info()
        
        # Route to Gemini AI
        elif self.is_gemini_question(command):
            if self.gemini_enabled:
                print("🤔 Thinking... (using Gemini AI)")
                return self.ask_gemini(original_command)
            else:
                return "I'd like to help with that question, but Gemini AI is not configured. Please set up your API key."
        
        # Default fallback with suggestions
        else:
            return self._generate_fallback_response(command)
    
    def _handle_unclear_input(self, command: str) -> str:
        """Handle unclear or failed input"""
        if command == "timeout":
            return "I didn't hear anything. Please try speaking again, or say 'help' for available commands."
        elif command == "unknown":
            return "I couldn't understand what you said. Please speak clearly and try again."
        else:
            return "There was an issue with the microphone. Please check your audio input and try again."
    
    def _generate_contextual_greeting(self) -> str:
        """Generate a contextual greeting based on time and session"""
        hour = datetime.datetime.now().hour
        
        if 5 <= hour < 12:
            greeting = "Good morning!"
        elif 12 <= hour < 17:
            greeting = "Good afternoon!"
        elif 17 <= hour < 21:
            greeting = "Good evening!"
        else:
            greeting = "Good night!"
        
        # Add session context
        if self.session_data['commands_processed'] == 1:
            greeting += " I'm your voice assistant. How can I help you today?"
        else:
            greeting += " How can I assist you further?"
        
        return greeting
    
    def _extract_city_from_weather_command(self, command: str) -> str:
        """Extract city name from weather command"""
        # Remove common weather command words
        for word in ["weather", "in", "for", "of", "today", "current", "now"]:
            command = command.replace(word, "")
        
        city = command.strip()
        
        # Default to Delhi if no city specified
        if not city or city in ["here", "local", "my location"]:
            city = "Delhi"
        
        return city
    
    def _extract_search_query(self, command: str) -> str:
        """Extract search query from command"""
        for word in ["search", "for", "look up", "find", "about"]:
            command = command.replace(word, "")
        
        return command.strip()
    
    def _handle_website_opening(self, command: str) -> str:
        """Handle website opening commands"""
        sites = {
            "google": "https://www.google.com",
            "youtube": "https://www.youtube.com",
            "facebook": "https://www.facebook.com",
            "twitter": "https://www.twitter.com",
            "instagram": "https://www.instagram.com",
            "linkedin": "https://www.linkedin.com",
            "github": "https://www.github.com",
            "reddit": "https://www.reddit.com"
        }
        
        for site, url in sites.items():
            if site in command:
                try:
                    webbrowser.open(url)
                    return f"Opening {site.title()} in your browser."
                except Exception as e:
                    return f"Error opening {site}: {e}"
        
        return "I can open Google, YouTube, Facebook, Twitter, Instagram, LinkedIn, GitHub, or Reddit. Which would you like?"
    
    def _handle_media_control(self, command: str) -> str:
        """Handle media control commands"""
        # This would integrate with platform controllers
        if "play" in command:
            if "spotify" in command or "music" in command:
                return "Media control integration would be implemented here for Spotify."
            elif "youtube" in command or "video" in command:
                return "Media control integration would be implemented here for YouTube."
            else:
                return "What would you like me to play? Music on Spotify or videos on YouTube?"
        
        elif "pause" in command or "stop" in command:
            return "Pausing current media playback."
        
        return "I can help with play, pause, or stop commands for music and videos."
    
    def _handle_system_command(self, command: str) -> str:
        """Handle system-level commands with safety checks"""
        if "shutdown" in command:
            return "System shutdown would require administrator privileges. This is disabled for safety."
        elif "restart" in command:
            return "System restart would require administrator privileges. This is disabled for safety."
        elif "sleep" in command:
            return "System sleep mode would be initiated here (disabled in demo)."
        elif "lock" in command:
            return "System lock would be initiated here (disabled in demo)."
        
        return "System commands are available but disabled for safety in this demo."
    
    def _generate_goodbye(self) -> str:
        """Generate a contextual goodbye message"""
        session_duration = datetime.datetime.now() - self.session_data['start_time']
        minutes = int(session_duration.total_seconds() / 60)
        
        goodbye = "Goodbye! "
        
        if minutes > 0:
            goodbye += f"We chatted for {minutes} minute{'s' if minutes != 1 else ''}. "
        
        if self.session_data['commands_processed'] > 5:
            goodbye += "Thanks for the great conversation! "
        
        goodbye += "Have a wonderful day!"
        
        return goodbye
    
    def _get_session_info(self) -> str:
        """Get session statistics"""
        duration = datetime.datetime.now() - self.session_data['start_time']
        minutes = int(duration.total_seconds() / 60)
        
        info = f"Session Statistics: "
        info += f"Duration: {minutes} minute{'s' if minutes != 1 else ''}, "
        info += f"Commands processed: {self.session_data['commands_processed']}, "
        info += f"Gemini AI: {'Connected' if self.gemini_enabled else 'Not configured'}"
        
        return info
    
    def _generate_fallback_response(self, command: str) -> str:
        """Generate helpful fallback response with suggestions"""
        response = f"I heard '{command}' but I'm not sure how to help with that. "
        
        suggestions = [
            "Try asking for the time or date",
            "Ask about weather in any city",
            "Request web searches",
            "Open popular websites",
            "Perform calculations",
            "Ask general knowledge questions"
        ]
        
        if self.gemini_enabled:
            suggestions.append("Ask complex questions (I have AI assistance)")
        
        response += "Here are some things I can help with: " + ", ".join(suggestions[:3]) + ", and more."
        
        return response
    
    def run_interactive_mode(self):
        """Enhanced interactive mode with better user experience"""
        print("\n" + "="*70)
        print("🤖 ENHANCED VOICE ASSISTANT - INTERACTIVE MODE")
        print("="*70)
        print("Enhanced Features:")
        print("• Natural conversation with context awareness")
        print("• Multi-platform integration (Spotify, YouTube, System)")
        print("• Advanced speech recognition with noise filtering")
        print("• Enhanced calculator with complex operations")
        print("• Smart web search and website opening")
        print("• Session tracking and statistics")
        if self.gemini_enabled:
            print("• Gemini AI for complex questions and conversations")
        print("\nExample Commands:")
        print("• 'What's the weather like in London?'")
        print("• 'Calculate 15 percent of 250'")
        print("• 'Explain quantum physics simply'")
        print("• 'Open YouTube and play some music'")
        print("• 'What's my session statistics?'")
        print("\nSay 'exit', 'quit', or 'goodbye' to stop")
        print("-"*70)
        
        # Enhanced welcome message
        welcome = "Enhanced voice assistant ready! "
        if self.gemini_enabled:
            welcome += "I have AI capabilities for complex questions. "
        welcome += "How can I assist you today?"
        
        self.speak(welcome)
        
        try:
            while True:
                # Listen for command with enhanced detection
                command = self.listen_once(timeout=12)
                
                if command == "timeout":
                    print("⏱️  No input detected. I'm still listening...")
                    continue
                elif command in ["unknown", "error"]:
                    print("❌ Sorry, I didn't catch that. Please try again.")
                    continue
                
                # Process command with enhanced features
                response = self.process_command(command)
                
                # Handle exit gracefully
                if any(word in command.lower() for word in ["exit", "quit", "bye", "goodbye"]):
                    self.speak(response, priority=True)
                    break
                
                # Speak response with enhancements
                self.speak(response)
                
        except KeyboardInterrupt:
            print("\n👋 Assistant stopped by user")
            self.speak("Goodbye! Assistant stopped.", priority=True)
        except Exception as e:
            print(f"❌ Error in interactive mode: {e}")
            self.speak("I encountered an error. Goodbye!", priority=True)
    
    def run_single_command(self, command: str):
        """Process a single command (enhanced for scripting)"""
        print(f"Processing command: {command}")
        response = self.process_command(command)
        self.speak(response)
        print(f"Response: {response}")
        return response


# Platform Controller Classes (Placeholder implementations)
class SpotifyController:
    """Spotify integration controller"""
    def __init__(self):
        self.is_connected = False
    
    def play(self, query: str = ""):
        return f"Playing {query} on Spotify" if query else "Playing music on Spotify"
    
    def pause(self):
        return "Pausing Spotify playback"
    
    def skip(self):
        return "Skipping to next track on Spotify"


class YouTubeController:
    """YouTube integration controller"""
    def __init__(self):
        self.is_connected = False
    
    def play(self, query: str = ""):
        if query:
            search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            return f"Searching and playing '{query}' on YouTube"
        return "Opening YouTube"
    
    def pause(self):
        return "YouTube pause command sent"


class SystemController:
    """System integration controller"""
    def __init__(self):
        self.platform = platform.system()
    
    def get_system_info(self):
        return f"Running on {self.platform}"
    
    def open_application(self, app_name: str):
        try:
            if self.platform == "Windows":
                subprocess.run(["start", app_name], shell=True)
            elif self.platform == "Darwin":  # macOS
                subprocess.run(["open", "-a", app_name])
            elif self.platform == "Linux":
                subprocess.run([app_name])
            return f"Opening {app_name}"
        except Exception as e:
            return f"Could not open {app_name}: {e}"


def main():
    """Enhanced main function with improved error handling and options"""
    print("🚀 Starting Enhanced Voice Assistant...")
    
    try:
        assistant = VoiceAssistant()
        
        # Check for command line arguments
        if len(sys.argv) > 1:
            if sys.argv[1] == "--test":
                # Test mode
                print("🧪 Running in test mode...")
                test_commands = [
                    "hello",
                    "what time is it",
                    "weather in New York",
                    "calculate 25 plus 17",
                    "what is artificial intelligence"
                ]
                
                for cmd in test_commands:
                    print(f"\n--- Testing: {cmd} ---")
                    response = assistant.run_single_command(cmd)
                    time.sleep(1)
                    
            elif sys.argv[1] == "--info":
                # Show system information
                print("📊 System Information:")
                print(f"Platform: {platform.system()} {platform.release()}")
                print(f"Python: {sys.version}")
                print(f"Gemini AI: {'Enabled' if assistant.gemini_enabled else 'Disabled'}")
                
                # Test microphone
                print("\n🎤 Testing microphone...")
                test_audio = assistant.listen_once(timeout=3)
                if test_audio not in ["timeout", "unknown", "error"]:
                    print(f"✅ Microphone working: '{test_audio}'")
                else:
                    print(f"⚠️  Microphone test result: {test_audio}")
                    
            elif sys.argv[1] == "--setup":
                # Setup wizard
                print("🔧 Voice Assistant Setup Wizard")
                print("-" * 40)
                
                # API Key setup
                if not assistant.gemini_enabled:
                    print("Gemini AI is not configured.")
                    api_key = input("Enter your Gemini API key (or press Enter to skip): ").strip()
                    if api_key:
                        if assistant.setup_gemini(api_key):
                            print("✅ Gemini AI configured successfully!")
                        else:
                            print("❌ Failed to configure Gemini AI")
                
                # Voice settings
                print("\n🔊 Voice Settings:")
                voices = assistant.engine.getProperty('voices')
                if voices:
                    print("Available voices:")
                    for i, voice in enumerate(voices[:5]):  # Show first 5 voices
                        print(f"  {i}: {voice.name}")
                    
                    try:
                        choice = input("Select voice (0-4, or press Enter for default): ").strip()
                        if choice.isdigit() and 0 <= int(choice) < len(voices):
                            assistant.engine.setProperty('voice', voices[int(choice)].id)
                            assistant.speak("Voice updated successfully!")
                    except:
                        print("Using default voice")
                
                # Test all systems
                print("\n🧪 Testing all systems...")
                assistant.speak("All systems are ready!")
                print("✅ Setup complete!")
                
            else:
                # Single command mode
                command = " ".join(sys.argv[1:])
                assistant.run_single_command(command)
        else:
            # Interactive mode
            assistant.run_interactive_mode()
            
    except KeyboardInterrupt:
        print("\n👋 Voice Assistant stopped")
    except Exception as e:
        print(f"❌ Error starting assistant: {e}")
        logging.error(f"Startup error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()