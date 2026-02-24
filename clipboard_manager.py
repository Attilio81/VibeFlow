import pyperclip
import time
import win32clipboard
import win32con

class ClipboardManager:
    def __init__(self):
        pass

    def paste_text(self, text: str):
        """
        Backs up the clipboard, sets the new text, simulates CTRL+V using Windows API,
        and restores the clipboard.
        """
        print(f"Pasting text: {text[:50]}..." if len(text) > 50 else f"Pasting text: {text}")
        
        # Backup original clipboard
        try:
            original_clipboard = pyperclip.paste()
        except:
            original_clipboard = ""
        
        # Set new text in clipboard using Windows API
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32con.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
        except Exception as e:
            print(f"Clipboard error: {e}")
            # Fallback to pyperclip
            pyperclip.copy(text)
        
        # Longer wait for clipboard to be ready
        time.sleep(0.5)
        
        # Use keyboard module for paste
        import keyboard
        keyboard.send('ctrl+v')
        
        print("Paste command sent")
        
        # Wait before restoring
        time.sleep(0.5)
        
        # Restore original clipboard
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(original_clipboard, win32con.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
        except:
            pyperclip.copy(original_clipboard)
        
        print("Paste complete")
