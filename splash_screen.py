# splash_screen.py
import tkinter as tk
from tkinter import ttk

class SplashScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.geometry("500x300")
        self.root.configure(bg="#064E3B")
        
        # Center on screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 500) // 2
        y = (screen_height - 300) // 2
        self.root.geometry(f"500x300+{x}+{y}")
        
        # Content
        main_frame = tk.Frame(self.root, bg="#064E3B")
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        tk.Label(main_frame, text="CropPulse", 
                font=("Segoe UI", 36, "bold"),
                fg="white", bg="#064E3B").pack(pady=(30, 5))
        
        tk.Label(main_frame, text="AI-Powered Crop Disease Diagnostic Tool", 
                font=("Segoe UI", 12),
                fg="#A7F3D0", bg="#064E3B").pack()
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, length=300, mode='indeterminate')
        self.progress.pack(pady=30)
        self.progress.start(10)
        
        tk.Label(main_frame, text="Loading models...", 
                font=("Segoe UI", 9),
                fg="#86EFAC", bg="#064E3B").pack()
        
        self.root.after(2000, self.finish)
    
    def finish(self):
        self.progress.stop()
        self.root.destroy()

# Add to your app.py - modify the main block at the bottom
# Find: if __name__ == "__main__": and replace with: