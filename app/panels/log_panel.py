"""Log panel for displaying application logs."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, Signal, QDateTime, QObject
from PySide6.QtGui import QTextCursor, QFont
import logging


class LogSignalEmitter(QObject):
    """Signal emitter for logging."""
    log_signal = Signal(str)


class LogHandler(logging.Handler):
    """Custom logging handler that emits signals."""
    
    def __init__(self):
        super().__init__()
        self.emitter = LogSignalEmitter()
    
    def emit(self, record):
        """Emit log record."""
        msg = self.format(record)
        self.emitter.log_signal.emit(msg)


class LogPanel(QWidget):
    """Panel for displaying application logs."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_handler = LogHandler()
        self._setup_ui()
        self._setup_logging()
    
    def _setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout()
        
        # Log display
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Courier", 9))
        self.text_edit.setMaximumHeight(200)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        
        clear_button = QPushButton("로그 지우기")
        clear_button.clicked.connect(self._clear_logs)
        
        button_layout.addStretch()
        button_layout.addWidget(clear_button)
        
        layout.addWidget(self.text_edit)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect handler
        self.log_handler.emitter.log_signal.connect(self._add_log)
    
    def _setup_logging(self):
        """Setup logging."""
        # Configure the log handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        
        # Add handler to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)
        root_logger.setLevel(logging.DEBUG)
    
    def _add_log(self, message: str):
        """Add a log message."""
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_edit.setTextCursor(cursor)
        self.text_edit.insertPlainText(message + "\n")
        
        # Auto-scroll to bottom
        self.text_edit.verticalScrollBar().setValue(
            self.text_edit.verticalScrollBar().maximum()
        )
    
    def _clear_logs(self):
        """Clear all logs."""
        self.text_edit.clear()
    
    def log(self, level: str, message: str):
        """Log a message."""
        logger = logging.getLogger(__name__)
        if level.upper() == "DEBUG":
            logger.debug(message)
        elif level.upper() == "INFO":
            logger.info(message)
        elif level.upper() == "WARNING":
            logger.warning(message)
        elif level.upper() == "ERROR":
            logger.error(message)
        else:
            logger.info(message)
