





import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from new1 import speak, listen_for_commands, listen_for_typed_commands, processCommand, set_gui_callback

class VoiceAssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Assistant")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        
        # Register GUI callback
        set_gui_callback(self.append_to_display)
        
        # Configure style
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", background="#2196F3")
        style.configure("TFrame", background="#f0f0f0")
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Voice Assistant", font=("Helvetica", 24, "bold"))
        title_label.pack(pady=10)
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = ttk.Label(status_frame, text="Status: Ready", font=("Helvetica", 12))
        self.status_label.pack(side=tk.LEFT)
        
        # Command display area
        self.command_display = scrolledtext.ScrolledText(main_frame, height=15, width=70, font=("Helvetica", 12))
        self.command_display.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        # Voice command button
        self.voice_button = ttk.Button(button_frame, text="Start Voice Command", command=self.start_voice_command)
        self.voice_button.pack(side=tk.LEFT, padx=5)
        
        # Type command button
        self.type_button = ttk.Button(button_frame, text="Type Command", command=self.start_typed_command)
        self.type_button.pack(side=tk.LEFT, padx=5)
        
        # Exit button
        self.exit_button = ttk.Button(button_frame, text="Exit", command=self.exit_app)
        self.exit_button.pack(side=tk.LEFT, padx=5)
        
        # Command entry
        self.command_entry = ttk.Entry(main_frame, width=50, font=("Helvetica", 12))
        self.command_entry.pack(pady=10)
        self.command_entry.bind("<Return>", self.process_typed_command)
        
        # Initialize variables
        self.is_listening = False
        self.voice_thread = None
        self.type_thread = None

    def update_status(self, message):
        self.status_label.config(text=f"Status: {message}")
        self.root.update()

    def append_to_display(self, text):
        self.command_display.insert(tk.END, f"{text}\n")
        self.command_display.see(tk.END)
        self.root.update()

    def start_voice_command(self):
        if not self.is_listening:
            self.is_listening = True
            self.voice_button.config(text="Stop Voice Command")
            self.update_status("Listening for voice commands...")
            self.voice_thread = threading.Thread(target=self.run_voice_command)
            self.voice_thread.daemon = True
            self.voice_thread.start()
        else:
            self.is_listening = False
            self.voice_button.config(text="Start Voice Command")
            self.update_status("Ready")

    def run_voice_command(self):
        self.append_to_display("Voice command mode activated. Say 'hello' to start.")
        listen_for_commands()

    def start_typed_command(self):
        self.update_status("Ready for typed commands")
        self.append_to_display("Type your commands below and press Enter")

    def process_typed_command(self, event):
        command = self.command_entry.get()
        if command:
            self.append_to_display(f"You: {command}")
            self.command_entry.delete(0, tk.END)
            result = processCommand(command)
            if result:
                self.append_to_display(f"Assistant: {result}")

    def exit_app(self):
        self.is_listening = False
        self.root.quit()

def main():
    root = tk.Tk()
    app = VoiceAssistantGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 