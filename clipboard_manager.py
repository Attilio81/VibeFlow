import pyperclip
import time
import threading
import logging
import win32clipboard
import win32con

logger = logging.getLogger("vibeflow")


class ClipboardManager:
    def __init__(self):
        pass

    def _restore_clipboard(self, original: str, delay: float = 1.5) -> None:
        """Restore the original clipboard contents after a delay.

        Runs in a background thread so paste_text() returns immediately
        without blocking the main pipeline.  The delay gives the target
        application enough time to read the clipboard before we overwrite it.
        """
        def _do_restore():
            time.sleep(delay)
            try:
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(original, win32con.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
            except Exception:
                try:
                    pyperclip.copy(original)
                except Exception:
                    pass
            logger.debug("Clipboard restored to original content")

        threading.Thread(target=_do_restore, daemon=True).start()

    def paste_text(self, text: str) -> None:
        """Back up the clipboard, inject text, send Ctrl+V, then restore asynchronously."""
        logger.info(f"Pasting text: {text[:50]}..." if len(text) > 50 else f"Pasting text: {text}")

        # Back up original clipboard
        try:
            original_clipboard = pyperclip.paste()
        except Exception:
            original_clipboard = ""

        # Write new text to clipboard using Windows API
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32con.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
        except Exception as e:
            logger.warning(f"win32clipboard error, falling back to pyperclip: {e}")
            pyperclip.copy(text)

        # Small wait to make sure the clipboard is fully populated before paste
        time.sleep(0.2)

        import keyboard
        keyboard.send('ctrl+v')
        logger.info("Paste command sent")

        # Restore original clipboard in background after a safe delay
        self._restore_clipboard(original_clipboard, delay=1.5)
