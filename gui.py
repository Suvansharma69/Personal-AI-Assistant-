import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import os
import subprocess
import requests
import json
import google.generativeai as genai
from typing import Optional

class VoiceAssistant:
    def __init__(self):
        # Initialize text-to-speech engine
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 200)
        self.engine.setProperty('volume', 0.9)
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # GUI callback for displaying messages
        self.gui_callback = None
        self.is_listening_active = False
        
        # Gemini AI setup
        self.gemini_model = None
        self.gemini_enabled = False
        self.api_key = None
        self.setup_error = None  # Track setup errors
        
        # ==================== PASTE YOUR GEMINI API KEY HERE ====================
        # Replace "YOUR_GEMINI_API_KEY_HERE" with your actual Gemini API key
        GEMINI_API_KEY = "AIzaSyDJrhNrl-MsGQ1zc0hc3jVXFQjh3xMwHDI"
        
        # Auto-setup Gemini AI on initialization
        if GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
            self.setup_gemini(GEMINI_API_KEY)
        
        # Calibrate microphone for ambient noise
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
        except Exception as e:
            print(f"Warning: Could not calibrate microphone: {e}")
    
    def setup_gemini(self, api_key: str) -> bool:
        """Setup Gemini AI with API key"""
        try:
            self.api_key = api_key
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
            
            # Test the connection with a simple query
            test_response = self.gemini_model.generate_content("Say 'Hello' in one word.")
            if test_response and test_response.text:
                self.gemini_enabled = True
                self.setup_error = None
                if self.gui_callback:
                    self.gui_callback("✓ Gemini AI successfully configured and tested!")
                return True
            else:
                raise Exception("Failed to get response from Gemini")
                
        except Exception as e:
            error_msg = f"Error setting up Gemini: {str(e)}"
            self.setup_error = error_msg
            if self.gui_callback:
                self.gui_callback(f"❌ {error_msg}")
            self.gemini_enabled = False
            return False
    
    def ask_gemini(self, question: str) -> str:
        """Ask Gemini AI a question"""
        if not self.gemini_enabled:
            if self.setup_error:
                return f"Gemini AI is not available: {self.setup_error}"
            return "Gemini AI is not configured. Please set up your API key first."
        
        try:
            # Generate response using Gemini
            response = self.gemini_model.generate_content(question)
            
            if response and response.text:
                return response.text
            else:
                return "I couldn't generate a response for that question."
                
        except Exception as e:
            return f"Error communicating with Gemini: {str(e)}"
    
    def set_gui_callback(self, callback):
        """Set callback function for GUI updates"""
        self.gui_callback = callback
    
    def speak(self, text):
        """Convert text to speech"""
        try:
            self.engine.say(text)
            self.engine.runAndWait()
            if self.gui_callback:
                self.gui_callback(f"Assistant: {text}")
        except Exception as e:
            print(f"Error in text-to-speech: {e}")
    
    def listen_for_speech(self, timeout=5):
        """Listen for speech and return recognized text"""
        try:
            if self.gui_callback:
                self.gui_callback("Listening...")
            
            # Use microphone without nested context managers
            audio = self.recognizer.listen(self.microphone, timeout=timeout, phrase_time_limit=5)
            
            if self.gui_callback:
                self.gui_callback("Processing speech...")
            
            # Use Google Speech Recognition
            text = self.recognizer.recognize_google(audio)
            return text.lower()
        
        except sr.WaitTimeoutError:
            return "timeout"
        except sr.UnknownValueError:
            return "unknown"
        except sr.RequestError as e:
            if self.gui_callback:
                self.gui_callback(f"Speech recognition error: {e}")
            return "error"
        except Exception as e:
            if self.gui_callback:
                self.gui_callback(f"Microphone error: {e}")
            return "error"
    
    def get_current_time(self):
        """Get current time"""
        now = datetime.datetime.now()
        return now.strftime("The current time is %I:%M %p")
    
    def get_current_date(self):
        """Get current date"""
        now = datetime.datetime.now()
        return now.strftime("Today is %A, %B %d, %Y")
    
    def open_website(self, url):
        """Open website in default browser"""
        try:
            webbrowser.open(url)
            return f"Opening {url}"
        except Exception as e:
            return f"Error opening website: {e}"
    
    def search_web(self, query):
        """Search web using default browser"""
        try:
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            return f"Searching for: {query}"
        except Exception as e:
            return f"Error searching web: {e}"
    
    def get_weather(self, city=""):
        """Get weather information (requires API key for full functionality)"""
        if not city:
            return "Please specify a city for weather information"
        
        # This is a basic implementation - you'd need to add your weather API key
        try:
            # Using a free weather API (replace with your preferred service)
            url = f"https://wttr.in/{city}?format=3"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return f"Weather: {response.text.strip()}"
            else:
                return "Unable to fetch weather information"
        except Exception as e:
            return f"Weather service unavailable: {e}"
    
    def is_gemini_question(self, command):
        """Check if the command should be handled by Gemini AI"""
        # Keywords that indicate a Gemini AI question
        gemini_triggers = [
            "ask gemini", "gemini", "ai question", "artificial intelligence",
            "explain", "tell me about", "what is", "how does", "why", 
            "who is", "when did", "where is", "define", "describe",
            "help me understand", "can you explain", "what are"
        ]
        
        # Check for basic commands that shouldn't go to Gemini
        basic_commands = [
            "time", "date", "weather", "open", "search", "calculate",
            "hello", "hi", "hey", "bye", "exit", "quit"
        ]
        
        # If it's a basic command, don't use Gemini
        for basic in basic_commands:
            if basic in command:
                return False
        
        # If it contains Gemini triggers or is a question-like format
        for trigger in gemini_triggers:
            if trigger in command:
                return True
        
        # Check if it looks like a question (ends with ?, contains question words)
        if command.endswith('?') or any(word in command for word in ["what", "how", "why", "who", "when", "where"]):
            return True
        
        # If the command is longer and doesn't match basic patterns, likely a Gemini question
        if len(command.split()) > 5:
            return True
            
        return False
    
    def process_command(self, command):
        """Process and execute commands"""
        command = command.lower().strip()
        
        if not command:
            return "I didn't hear anything. Please try again."
        
        # Check if this should be handled by Gemini AI
        if self.is_gemini_question(command):
            if self.gemini_enabled:
                if self.gui_callback:
                    self.gui_callback("Thinking... (using Gemini AI)")
                return self.ask_gemini(command)
            else:
                return "I'd like to help with that question, but Gemini AI is not configured. Please set up your API key first."
        
        # Greeting commands
        if any(word in command for word in ["hello", "hi", "hey"]):
            return "Hello! How can I help you today? I can handle basic commands or answer complex questions using Gemini AI."
        
        # Time commands
        elif any(word in command for word in ["time", "clock"]):
            return self.get_current_time()
        
        # Date commands
        elif any(word in command for word in ["date", "today"]):
            return self.get_current_date()
        
        # Weather commands
        elif "weather" in command:
            city = command.replace("weather", "").replace("in", "").strip()
            return self.get_weather(city)
        
        # Web search commands
        elif "search" in command:
            query = command.replace("search", "").replace("for", "").strip()
            return self.search_web(query)
        
        # Website opening commands
        elif "open" in command and any(site in command for site in ["google", "youtube", "facebook", "twitter"]):
            if "google" in command:
                return self.open_website("https://www.google.com")
            elif "youtube" in command:
                return self.open_website("https://www.youtube.com")
            elif "facebook" in command:
                return self.open_website("https://www.facebook.com")
            elif "twitter" in command:
                return self.open_website("https://www.twitter.com")
        
        # Calculator commands
        elif any(word in command for word in ["calculate", "math", "plus", "minus", "multiply", "divide"]):
            return self.calculate(command)
        
        # System commands
        elif "shutdown" in command or "restart" in command:
            return "I cannot perform system shutdown/restart operations for security reasons."
        
        # Exit commands
        elif any(word in command for word in ["exit", "quit", "bye", "goodbye"]):
            return "Goodbye! Have a great day!"
        
        # If none of the basic commands match, try Gemini AI as fallback
        elif self.gemini_enabled:
            if self.gui_callback:
                self.gui_callback("Using Gemini AI to understand your request...")
            return self.ask_gemini(command)
        
        # Default response when Gemini is not available
        else:
            return f"I heard: '{command}' but I'm not sure how to help with that. Try asking for time, date, weather, web search, or set up Gemini AI for more complex questions."
    
    def calculate(self, command):
        """Simple calculator functionality"""
        try:
            # Remove common words
            command = command.replace("calculate", "").replace("what is", "").strip()
            
            # Replace words with operators
            command = command.replace("plus", "+").replace("add", "+")
            command = command.replace("minus", "-").replace("subtract", "-")
            command = command.replace("times", "*").replace("multiply", "*")
            command = command.replace("divided by", "/").replace("divide", "/")
            
            # Evaluate the expression (basic safety check)
            if all(c in "0123456789+-*/.() " for c in command):
                result = eval(command)
                return f"The result is {result}"
            else:
                return "Sorry, I can only handle basic math operations"
        except Exception as e:
            return "Sorry, I couldn't calculate that. Please check your math expression."
    
    def listen_for_commands(self):
        """Main listening loop for voice commands"""
        if self.is_listening_active:
            return
        
        self.is_listening_active = True
        greeting = "Voice assistant activated. Say hello to start."
        if self.gemini_enabled:
            greeting += " Gemini AI is ready for complex questions."
        self.speak(greeting)
        
        try:
            # Open microphone context once for the entire session
            with self.microphone as source:
                # Adjust for ambient noise at the beginning
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                while self.is_listening_active:
                    try:
                        if self.gui_callback:
                            self.gui_callback("Listening...")
                        
                        # Listen for audio without timeout to avoid constant timeouts
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                        
                        if self.gui_callback:
                            self.gui_callback("Processing speech...")
                        
                        # Use Google Speech Recognition
                        command = self.recognizer.recognize_google(audio).lower()
                        
                        if self.gui_callback:
                            self.gui_callback(f"You said: {command}")
                        
                        # Process the command
                        response = self.process_command(command)
                        
                        # Exit conditions
                        if any(word in command for word in ["exit", "quit", "bye", "goodbye"]):
                            self.speak(response)
                            break
                        
                        # Speak the response
                        self.speak(response)
                        
                    except sr.WaitTimeoutError:
                        # Just continue listening, no need to report timeout
                        continue
                    except sr.UnknownValueError:
                        if self.gui_callback:
                            self.gui_callback("Sorry, I didn't understand that. Please speak clearly.")
                        continue
                    except sr.RequestError as e:
                        if self.gui_callback:
                            self.gui_callback(f"Speech recognition error: {e}")
                        continue
                    except Exception as e:
                        if self.gui_callback:
                            self.gui_callback(f"Error processing command: {e}")
                        continue
                        
        except Exception as e:
            error_msg = f"Error initializing microphone: {e}"
            if self.gui_callback:
                self.gui_callback(error_msg)
            print(error_msg)
        finally:
            self.is_listening_active = False

class VoiceAssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Assistant with Gemini AI")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f0f0")
        
        # Initialize the voice assistant
        self.assistant = VoiceAssistant()
        self.assistant.set_gui_callback(self.append_to_display)
        
        # Configure style
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", background="#2196F3")
        style.configure("TFrame", background="#f0f0f0")
        style.configure("GeminiButton.TButton", padding=6, relief="flat", background="#4CAF50")
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Voice Assistant with Gemini AI", font=("Helvetica", 24, "bold"))
        title_label.pack(pady=10)
        
        # Gemini setup frame
        gemini_frame = ttk.LabelFrame(main_frame, text="Gemini AI Configuration", padding="10")
        gemini_frame.pack(fill=tk.X, pady=10)
        
        # API key entry
        ttk.Label(gemini_frame, text="Gemini API Key:").pack(side=tk.LEFT, padx=5)
        self.api_key_entry = ttk.Entry(gemini_frame, width=40, show="*")
        self.api_key_entry.pack(side=tk.LEFT, padx=5)
        
        # Pre-fill the API key if it was auto-configured
        if self.assistant.api_key:
            self.api_key_entry.insert(0, self.assistant.api_key)
        
        self.setup_button = ttk.Button(gemini_frame, text="Setup Gemini", 
                                     command=self.setup_gemini_ai, style="GeminiButton.TButton")
        self.setup_button.pack(side=tk.LEFT, padx=5)
        
        self.gemini_status = ttk.Label(gemini_frame, text="Status: Not configured", foreground="red")
        self.gemini_status.pack(side=tk.LEFT, padx=10)
        
        # Update status based on initial setup
        self.update_gemini_status()
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = ttk.Label(status_frame, text="Status: Ready", font=("Helvetica", 12))
        self.status_label.pack(side=tk.LEFT)
        
        # Command display area
        self.command_display = scrolledtext.ScrolledText(main_frame, height=15, width=80, font=("Helvetica", 12))
        self.command_display.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Add welcome message
        self.append_to_display("Welcome to Voice Assistant with Gemini AI!")
        self.append_to_display("Basic commands: 'Hello', 'What time is it?', 'What's the date?', 'Search for Python'")
        self.append_to_display("AI commands: 'Explain quantum physics', 'What is machine learning?', 'Tell me about space exploration'")
        
        if self.assistant.gemini_enabled:
            self.append_to_display("✓ Gemini AI is ready and connected!")
        else:
            self.append_to_display("Set up your Gemini API key above to enable AI-powered responses!")
            if self.assistant.setup_error:
                self.append_to_display(f"Auto-setup failed: {self.assistant.setup_error}")
        
        self.append_to_display("-" * 70)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        # Voice command button
        self.voice_button = ttk.Button(button_frame, text="Start Voice Command", command=self.start_voice_command)
        self.voice_button.pack(side=tk.LEFT, padx=5)
        
        # Type command button
        self.type_button = ttk.Button(button_frame, text="Type Command", command=self.start_typed_command)
        self.type_button.pack(side=tk.LEFT, padx=5)
        
        # Clear display button
        self.clear_button = ttk.Button(button_frame, text="Clear Display", command=self.clear_display)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # Exit button
        self.exit_button = ttk.Button(button_frame, text="Exit", command=self.exit_app)
        self.exit_button.pack(side=tk.LEFT, padx=5)
        
        # Command entry
        self.command_entry = ttk.Entry(main_frame, width=60, font=("Helvetica", 12))
        self.command_entry.pack(pady=10)
        self.command_entry.bind("<Return>", self.process_typed_command)
        
        # Initialize variables
        self.is_listening = False
        self.voice_thread = None

    def update_gemini_status(self):
        """Update the Gemini status display"""
        if self.assistant.gemini_enabled:
            self.gemini_status.config(text="Status: Connected ✓", foreground="green")
            self.update_status("Ready - Gemini AI enabled")
        else:
            if self.assistant.setup_error:
                self.gemini_status.config(text="Status: Connection failed ❌", foreground="red")
            else:
                self.gemini_status.config(text="Status: Not configured", foreground="red")
            self.update_status("Ready")

    def setup_gemini_ai(self):
        """Setup Gemini AI with the provided API key"""
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter a valid Gemini API key")
            return
        
        self.update_status("Setting up Gemini AI...")
        self.gemini_status.config(text="Status: Connecting...", foreground="orange")
        
        def setup_in_thread():
            success = self.assistant.setup_gemini(api_key)
            # Use root.after to update GUI from thread
            self.root.after(0, lambda: self.update_gemini_status())
            if success:
                self.root.after(0, lambda: self.append_to_display("You can now ask complex questions and get AI-powered responses."))
        
        thread = threading.Thread(target=setup_in_thread)
        thread.daemon = True
        thread.start()

    def update_status(self, message):
        """Update status label"""
        self.status_label.config(text=f"Status: {message}")
        self.root.update()

    def append_to_display(self, text):
        """Add text to the display area"""
        self.command_display.insert(tk.END, f"{text}\n")
        self.command_display.see(tk.END)
        self.root.update()

    def clear_display(self):
        """Clear the display area"""
        self.command_display.delete(1.0, tk.END)

    def start_voice_command(self):
        """Start or stop voice command listening"""
        if not self.is_listening:
            self.is_listening = True
            self.voice_button.config(text="Stop Voice Command")
            self.update_status("Starting voice commands...")
            self.voice_thread = threading.Thread(target=self.run_voice_command)
            self.voice_thread.daemon = True
            self.voice_thread.start()
        else:
            self.is_listening = False
            self.assistant.is_listening_active = False  # Stop the assistant's listening loop
            self.voice_button.config(text="Start Voice Command")
            self.update_status("Stopping voice commands...")
            # Give a moment for the thread to finish
            self.root.after(1000, lambda: self.update_status("Ready"))

    def run_voice_command(self):
        """Run voice command in separate thread"""
        try:
            self.assistant.listen_for_commands()
        except Exception as e:
            self.append_to_display(f"Voice command error: {e}")
        finally:
            self.is_listening = False
            self.voice_button.config(text="Start Voice Command")
            self.update_status("Ready")

    def start_typed_command(self):
        """Activate typed command mode"""
        self.update_status("Ready for typed commands")
        self.append_to_display("Type your commands below and press Enter")
        self.command_entry.focus()

    def process_typed_command(self, event):
        """Process typed command"""
        command = self.command_entry.get()
        if command:
            self.append_to_display(f"You: {command}")
            self.command_entry.delete(0, tk.END)
            
            # Process command in separate thread to avoid GUI freezing
            def process_in_thread():
                try:
                    result = self.assistant.process_command(command)
                    if result:
                        self.root.after(0, lambda: self.append_to_display(f"Assistant: {result}"))
                except Exception as e:
                    self.root.after(0, lambda: self.append_to_display(f"Error: {e}"))
            
            thread = threading.Thread(target=process_in_thread)
            thread.daemon = True
            thread.start()

    def exit_app(self):
        """Exit the application"""
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.is_listening = False
            self.root.quit()

def main():
    """Main function to run the application"""
    try:
        root = tk.Tk()
        app = VoiceAssistantGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        messagebox.showerror("Error", f"Failed to start application: {e}")

if __name__ == "__main__":
    main()