# =============================================================================
# new1_gemini.py - Fixed Gemini API integration with correct model names
# =============================================================================

import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
from datetime import datetime
import requests
import json
import threading

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyDJrhNrl-MsGQ1zc0hc3jVXFQjh3xMwHDI"
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the model with the correct model name
try:
    # Try the new model names first
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
    except:
        try:
            model = genai.GenerativeModel('models/gemini-1.5-flash')
        except:
            # Fallback to basic model
            model = genai.GenerativeModel('gemini-1.0-pro')

# Initialize speech recognition and text-to-speech
recognizer = sr.Recognizer()
microphone = sr.Microphone()
engine = pyttsx3.init()

# Enhanced TTS settings for better voice quality
try:
    voices = engine.getProperty('voices')
    if voices:
        engine.setProperty('voice', voices[0].id)  # Use first available voice
    engine.setProperty('rate', 180)  # Slightly faster speech rate
    engine.setProperty('volume', 0.9)  # High volume
except:
    pass  # Continue even if voice settings fail

# GUI callback function
gui_callback = None

def set_gui_callback(callback):
    global gui_callback
    gui_callback = callback

def log_message(message):
    """Send message to GUI if callback is available"""
    if gui_callback:
        gui_callback(message)
    else:
        print(message)

def speak(text):
    """Convert text to speech with enhanced error handling"""
    try:
        log_message(f"Assistant: {text}")
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        log_message(f"Error in speech synthesis: {e}")

def listen_for_speech():
    """Listen for speech input with improved noise handling"""
    try:
        log_message("Listening...")
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            recognizer.energy_threshold = 300  # Adjust for better noise filtering
        
        with microphone as source:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)
        
        command = recognizer.recognize_google(audio).lower()
        log_message(f"You said: {command}")
        return command
    except sr.WaitTimeoutError:
        log_message("Listening timeout")
        return None
    except sr.UnknownValueError:
        log_message("Could not understand audio")
        return None
    except sr.RequestError as e:
        log_message(f"Error with speech recognition service: {e}")
        return None

def list_available_models():
    """List available Gemini models for debugging"""
    try:
        models = genai.list_models()
        print("Available models:")
        for model in models:
            print(f"- {model.name}")
        return models
    except Exception as e:
        print(f"Error listing models: {e}")
        return []

def get_gemini_response(user_input):
    """Get enhanced response from Gemini API with better error handling"""
    try:
        # Enhanced prompt for better conversational AI
        prompt = f"""You are an intelligent, helpful, and friendly voice assistant named Gemini Assistant. 

Key instructions:
- Respond naturally and conversationally
- Keep responses concise but informative (ideal for text-to-speech)
- Be helpful, accurate, and engaging
- If you don't know something, say so honestly
- Provide practical and actionable information when possible

User request: {user_input}

Assistant response:"""
        
        response = model.generate_content(prompt)
        return response.text.strip()
    
    except Exception as e:
        log_message(f"Error with Gemini API: {e}")
        # Try to get available models for debugging
        if "not found" in str(e).lower() or "404" in str(e):
            log_message("Checking available models...")
            available_models = list_available_models()
        return "I apologize, but I'm experiencing connectivity issues with my AI system. Please try again in a moment."

def processCommand(command):
    """Process user command with enhanced logic and Gemini integration"""
    try:
        if not command:
            return "I didn't catch that. Could you please repeat your request?"
        
        command = command.lower().strip()
        
        # Handle basic commands locally for faster response
        if "hello" in command or "hi" in command or "hey" in command:
            return "Hello! I'm your Gemini-powered voice assistant. How can I help you today?"
        
        elif "time" in command and "what" in command:
            current_time = datetime.now().strftime("%I:%M %p")
            return f"The current time is {current_time}"
        
        elif "date" in command and ("what" in command or "today" in command):
            current_date = datetime.now().strftime("%B %d, %Y")
            return f"Today's date is {current_date}"
        
        elif "goodbye" in command or "bye" in command or "see you" in command:
            return "Goodbye! It was great helping you today. Have a wonderful time!"
        
        elif "stop" in command or "exit" in command or "quit" in command:
            return "Stopping the assistant now. Thank you for using Gemini Assistant!"
        
        elif "who are you" in command or "what are you" in command:
            return "I'm Gemini Assistant, an AI-powered voice assistant created using Google's Gemini AI technology. I'm here to help answer questions, provide information, and assist with various tasks!"
        
        elif "list models" in command or "show models" in command:
            # Debug command to show available models
            models = list_available_models()
            return f"I found {len(models)} available models. Check the console for the full list."
        
        else:
            # For all other commands, use enhanced Gemini API
            log_message("Processing with Gemini AI...")
            response = get_gemini_response(command)
            return response
    
    except Exception as e:
        log_message(f"Error processing command: {e}")
        return "I encountered an unexpected error while processing your request. Please try again."

def listen_for_commands():
    """Enhanced main loop for voice commands"""
    log_message("🎤 Gemini Voice Assistant activated! Say 'hello' to start our conversation.")
    
    conversation_active = False
    
    while True:
        try:
            command = listen_for_speech()
            if command:
                # Check for exit commands
                if any(word in command.lower() for word in ["stop listening", "exit", "quit assistant"]):
                    speak("Thank you for using Gemini Assistant. Goodbye!")
                    break
                
                # Activate conversation mode
                if not conversation_active and any(word in command.lower() for word in ["hello", "hi", "hey"]):
                    conversation_active = True
                
                if conversation_active or any(word in command.lower() for word in ["hello", "hi", "hey"]):
                    response = processCommand(command)
                    if response:
                        speak(response)
                else:
                    log_message("Say 'hello' to activate the assistant.")
            
        except KeyboardInterrupt:
            log_message("Voice command loop interrupted by user")
            break
        except Exception as e:
            log_message(f"Error in command loop: {e}")

def listen_for_typed_commands():
    """Enhanced typed command handler"""
    log_message("💬 Gemini Text Assistant ready! Type your commands below.")
    
    while True:
        try:
            command = input("\nYou: ")
            if command.lower() in ['exit', 'quit', 'stop', 'bye']:
                print("Assistant: Goodbye!")
                break
            
            response = processCommand(command)
            if response:
                print(f"Assistant: {response}")
        
        except KeyboardInterrupt:
            print("\nAssistant: Goodbye!")
            break
        except Exception as e:
            log_message(f"Error in typed command loop: {e}")

# Enhanced test function
if __name__ == "__main__":
    print("🚀 Testing Enhanced Gemini Integration...")
    print("=" * 50)
    
    # First, list available models
    print("🔍 Checking available Gemini models...")
    available_models = list_available_models()
    print("=" * 50)
    
    test_commands = [
        "Hello",
        "What is artificial intelligence?",
        "What time is it?",
        "Tell me a fun fact about space"
    ]
    
    for cmd in test_commands:
        print(f"\nTest Command: {cmd}")
        response = processCommand(cmd)
        print(f"Response: {response}")
        print("-" * 30)
