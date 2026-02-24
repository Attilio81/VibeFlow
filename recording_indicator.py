import tkinter as tk
from tkinter import font as tkfont
from plyer import notification
import threading
try:
    import win32gui
    import win32con
    HAS_WIN32 = True
except:
    HAS_WIN32 = False
    print("Warning: pywin32 not available, focus restoration disabled")

class RecordingIndicator:
    def __init__(self):
        """Initialize with pre-created window for better threading support."""
        self.window = None
        self.is_showing = False
        self.animation_running = False
        self.use_notifications = False  # Fallback to Windows notifications
        self.stop_recording = False  # Flag for manual stop
        self.saved_window_handle = None  # Save active window
        
        # Try to initialize Tkinter window
        try:
            self._init_window()
        except Exception as e:
            print(f"Tkinter overlay not available: {e}")
            print("Using Windows notifications instead.")
            self.use_notifications = True
    
    def _init_window(self):
        """Pre-initialize the Tkinter window with modern waveform design."""
        self.window = tk.Tk()
        self.window.title("VibeFlow")
        
        # Window configuration
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.window.attributes('-alpha', 0.95)
        self.window.attributes('-toolwindow', True)  # Don't show in taskbar
        # Note: NOT using -disabled so buttons are clickable
        
        # Size and position
        width = 280
        height = 140
        screen_width = self.window.winfo_screenwidth()
        x = screen_width - width - 20
        y = 20
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Dark background
        self.window.configure(bg='#1a1a1a')
        
        # Top bar with buttons
        top_frame = tk.Frame(self.window, bg='#1a1a1a', height=40)
        top_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        # Stop button (X) on the left
        self.stop_button = tk.Button(
            top_frame,
            text='✕',
            font=("Segoe UI", 16, "bold"),
            bg='#2a2a2a',
            fg='white',
            activebackground='#ff4444',
            activeforeground='white',
            relief=tk.FLAT,
            cursor='hand2',
            command=self._on_stop_clicked,
            width=2,
            height=1,
            bd=0
        )
        self.stop_button.pack(side=tk.LEFT)
        
        # Confirm button (✓) on the right
        self.confirm_button = tk.Button(
            top_frame,
            text='✓',
            font=("Segoe UI", 16, "bold"),
            bg='#2a2a2a',
            fg='white',
            activebackground='#44ff44',
            activeforeground='white',
            relief=tk.FLAT,
            cursor='hand2',
            command=self._on_confirm_clicked,
            width=2,
            height=1,
            bd=0
        )
        self.confirm_button.pack(side=tk.RIGHT)
        
        # Waveform canvas in the center
        self.canvas = tk.Canvas(self.window, bg='#1a1a1a', highlightthickness=0, height=60)
        self.canvas.pack(fill=tk.BOTH, padx=20, pady=10)
        
        # Create waveform bars
        self.waveform_bars = []
        num_bars = 15
        bar_width = 6
        spacing = 4
        canvas_width = 240  # approx canvas width
        total_bars_width = num_bars * bar_width + (num_bars - 1) * spacing
        start_x = (canvas_width - total_bars_width) // 2
        
        for i in range(num_bars):
            x = start_x + i * (bar_width + spacing)
            # Create bars with varying initial heights
            bar = self.canvas.create_rectangle(
                x, 30, x + bar_width, 30,
                fill='white',
                outline=''
            )
            self.waveform_bars.append(bar)
        
        # Bottom bar with language icon
        bottom_frame = tk.Frame(self.window, bg='#1a1a1a', height=30)
        bottom_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Language/globe icon
        self.label = tk.Label(
            bottom_frame,
            text='🌐',
            font=("Segoe UI", 14),
            bg='#1a1a1a',
            fg='white'
        )
        self.label.pack(side=tk.LEFT)
        
        # Start hidden
        self.window.withdraw()
    
    def _on_stop_clicked(self):
        """Handle stop button click."""
        print("Stop button clicked - ending recording")
        self.stop_recording = True
        self.stop_button.config(bg='#666666', state='disabled')
        
        # Restore focus to original window immediately
        if HAS_WIN32 and self.saved_window_handle:
            try:
                win32gui.SetForegroundWindow(self.saved_window_handle)
                print(f"Focus restored to window: {self.saved_window_handle}")
            except Exception as e:
                print(f"Could not restore focus: {e}")
    
    def _on_confirm_clicked(self):
        """Handle confirm button click (same as stop for now)."""
        self._on_stop_clicked()
    
    def show(self):
        """Show the recording indicator."""
        if self.use_notifications:
            self._show_notification("Recording", "🎤 Listening... (press hotkey again to stop)")
            return
            
        if self.is_showing or not self.window:
            return
        
        # Save the currently active window BEFORE showing overlay
        if HAS_WIN32:
            try:
                self.saved_window_handle = win32gui.GetForegroundWindow()
                window_title = win32gui.GetWindowText(self.saved_window_handle)
                print(f"Saved focus from window: {window_title} (handle: {self.saved_window_handle})")
            except Exception as e:
                print(f"Could not save window handle: {e}")
                self.saved_window_handle = None
            
        self.is_showing = True
        self.stop_recording = False  # Reset stop flag
        try:
            self.label.config(text='�')
            self.stop_button.config(bg='#2a2a2a', state='normal')
            self.confirm_button.config(bg='#2a2a2a', state='normal')
            self.window.deiconify()
            self.window.lift()
            # Don't steal focus - let user's app keep focus
            
            # Start waveform animation
            self.animation_running = True
            self._animate_waveform()
        except Exception as e:
            print(f"Error showing overlay: {e}")
            self.use_notifications = True
            self._show_notification("Recording", "🎤 Listening...")
    
    def hide(self):
        """Hide the recording indicator."""
        if self.use_notifications:
            return
            
        if not self.is_showing:
            return
            
        self.is_showing = False
        self.animation_running = False
        try:
            if self.window:
                self.window.withdraw()
        except:
            pass
    
    def _animate_waveform(self):
        """Animate waveform bars with random heights."""
        if not self.animation_running or not self.window or not self.is_showing:
            return
        
        try:
            import random
            
            # Update each bar with random height
            for bar in self.waveform_bars:
                height = random.randint(5, 50)
                coords = self.canvas.coords(bar)
                x1, _, x2, _ = coords
                center_y = 30
                self.canvas.coords(bar, x1, center_y - height//2, x2, center_y + height//2)
            
            # Continue animation
            self.window.after(80, self._animate_waveform)
        except:
            pass
    
    def update_status(self, status_text):
        """Update status indicator."""
        if self.use_notifications:
            messages = {
                "processing": ("Processing", "⚙️ Transcribing..."),
                "success": ("Success", "✓ Done!"),
                "error": ("Error", "✗ Failed")
            }
            title, msg = messages.get(status_text, ("VibeFlow", "Working..."))
            self._show_notification(title, msg)
            return
        
        if not self.window:
            return
            
        try:
            if status_text == "processing":
                self.label.config(text='⚙️')
                # Change bars to orange
                for bar in self.waveform_bars:
                    self.canvas.itemconfig(bar, fill='#ffa500')
                self.animation_running = False
            elif status_text == "success":
                self.label.config(text='✓')
                # Change bars to green
                for bar in self.waveform_bars:
                    self.canvas.itemconfig(bar, fill='#00ff00')
                self.animation_running = False
                self.window.after(1200, self.hide)
            elif status_text == "error":
                self.label.config(text='✗')
                # Change bars to red
                for bar in self.waveform_bars:
                    self.canvas.itemconfig(bar, fill='#ff3333')
                self.animation_running = False
                self.window.after(2000, self.hide)
        except Exception as e:
            print(f"Error updating status: {e}")
    
    def _show_notification(self, title, message):
        """Fallback to Windows notifications."""
        try:
            notification.notify(
                title=title,
                message=message,
                app_name='VibeFlow',
                timeout=2
            )
        except:
            pass
