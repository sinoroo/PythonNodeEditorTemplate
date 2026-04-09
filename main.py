"""Main entry point for the application."""
import sys
import logging
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main function."""
    logger.info("Starting Orange Canvas Node Editor")
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Orange Canvas Node Editor")
    app.setApplicationVersion("1.0.0")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    logger.info("Application window shown")
    
    # Event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
