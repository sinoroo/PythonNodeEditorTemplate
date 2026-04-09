"""Advanced canvas features and utilities."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSpinBox, QCheckBox, QPushButton, QDialog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from ..nodes.base_node import BaseNode


class NodePropertiesDialog(QDialog):
    """Dialog for editing node properties."""
    
    def __init__(self, node: BaseNode, parent=None):
        super().__init__(parent)
        self.node = node
        self.setWindowTitle(f"Properties - {node.title}")
        self.setGeometry(100, 100, 300, 200)
        
        # Create layout
        layout = QVBoxLayout()
        
        # Title
        layout.addWidget(QLabel(f"Node: {node.title}"))
        layout.addWidget(QLabel(f"ID: {node.node_id}"))
        layout.addWidget(QLabel(f"Category: {node.category}"))
        
        # Position
        layout.addWidget(QLabel("Position:"))
        
        x_layout = QVBoxLayout()
        x_label = QLabel("X:")
        x_spin = QSpinBox()
        x_spin.setValue(int(node.x))
        x_layout.addWidget(x_label)
        x_layout.addWidget(x_spin)
        
        y_layout = QVBoxLayout()
        y_label = QLabel("Y:")
        y_spin = QSpinBox()
        y_spin.setValue(int(node.y))
        y_layout.addWidget(y_label)
        y_layout.addWidget(y_spin)
        
        layout.addLayout(x_layout)
        layout.addLayout(y_layout)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)
        self.x_spin = x_spin
        self.y_spin = y_spin
    
    def get_position(self):
        """Get updated position."""
        return (self.x_spin.value(), self.y_spin.value())
