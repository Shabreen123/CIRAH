"""
Convenience helper to launch the academic manuscript in the default web browser
for 1-click 'Save as PDF'.
"""
import os
import webbrowser

HTML_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "CIRAH_Journal_Paper.html"))

if __name__ == "__main__":
    print(f"Opening manuscript in default browser: {HTML_FILE}")
    webbrowser.open(f"file:///{HTML_FILE}")
    print("In your browser, click '🖨️ Save as PDF / Print' (or press Ctrl + P) -> Destination: 'Save as PDF' -> Save!")
