"""Attribute panel for displaying node properties."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFormLayout, QGroupBox
from PySide6.QtCore import Signal
import logging

from ..nodes.base_node import BaseNode

logger = logging.getLogger(__name__)


class AttributePanel(QWidget):
    """Panel for displaying selected node attributes."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_node = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title_label = QLabel("Node Attributes")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title_label)
        
        # Form layout for attributes
        self.form_layout = QFormLayout()
        
        # Create labels for attributes
        self.title_label = QLabel("None")
        self.category_label = QLabel("None")
        self.id_label = QLabel("None")
        self.position_label = QLabel("None")
        self.input_ports_label = QLabel("None")
        self.output_ports_label = QLabel("None")
        
        self.form_layout.addRow("Title:", self.title_label)
        self.form_layout.addRow("Category:", self.category_label)
        self.form_layout.addRow("ID:", self.id_label)
        self.form_layout.addRow("Position:", self.position_label)
        self.form_layout.addRow("Input Ports:", self.input_ports_label)
        self.form_layout.addRow("Output Ports:", self.output_ports_label)
        
        # Group box for attributes
        group_box = QGroupBox()
        group_box.setLayout(self.form_layout)
        layout.addWidget(group_box)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def update_node(self, node: BaseNode = None):
        """Update the panel with node information."""
        self.current_node = node
        if node is None:
            self.title_label.setText("None")
            self.category_label.setText("None")
            self.id_label.setText("None")
            self.position_label.setText("None")
            self.input_ports_label.setText("None")
            self.output_ports_label.setText("None")
        else:
            self.title_label.setText(node.title)
            self.category_label.setText(node.category)
            self.id_label.setText(str(node.node_id))
            self.position_label.setText(f"({node.x:.1f}, {node.y:.1f})")
            self.input_ports_label.setText(str(len(node.input_ports)))
            self.output_ports_label.setText(str(len(node.output_ports)))