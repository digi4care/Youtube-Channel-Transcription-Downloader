import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Set application information
    app.setApplicationName("YouTube Transcript Downloader")
    app.setApplicationVersion("1.0.0")
    
    # Set style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
