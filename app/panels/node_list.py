"""Node list panel for selecting and adding nodes."""
from typing import Dict, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QMenu, QHeaderView,
    QAbstractItemView, QLabel, QLineEdit, QFrame
)
from PySide6.QtCore import Qt, Signal, QSize, QMimeData
from PySide6.QtGui import QIcon, QPixmap, QColor, QBrush, QFont, QPainter
from PySide6.QtGui import QDrag
import logging

from ..nodes.node_registry import NODE_REGISTRY, get_categories, get_node_info
from ..nodes.base_node import BaseNode

logger = logging.getLogger(__name__)


class DragTreeWidget(QTreeWidget):
    """Tree widget that supports drag operations."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDefaultDropAction(Qt.IgnoreAction)
    
    def startDrag(self, supportedActions):
        """Start drag operation."""
        item = self.currentItem()
        if not item:
            return
        
        node_type = item.data(0, Qt.UserRole)
        if not node_type:
            return  # It's a category
        
        # Create mime data
        mime_data = QMimeData()
        mime_data.setData("application/x-node-type", node_type.encode())
        
        # Create drag
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.CopyAction)


class NodeListPanel(QWidget):
    """Panel displaying available nodes organized by category."""
    
    node_selected = Signal(str)  # Emits node type
    node_add_requested = Signal(str)  # Emits node type (from context menu)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.node_items: Dict[str, QTreeWidgetItem] = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        header = QLabel("노드 목록")
        header.setFont(QFont("Segoe UI", 10, QFont.Bold))
        header.setStyleSheet("color: #333; padding-bottom: 4px;")
        layout.addWidget(header)
        
        search_frame = QFrame()
        search_layout = QVBoxLayout(search_frame)
        search_layout.setContentsMargins(0, 0, 0, 0)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("노드 검색...")
        self.search_box.textChanged.connect(self._filter_nodes)
        search_layout.addWidget(self.search_box)
        layout.addWidget(search_frame)
        
        # Create tree widget
        self.tree_widget = DragTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setIndentation(18)
        self.tree_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree_widget.setDragEnabled(True)
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self._on_context_menu)
        self.tree_widget.itemClicked.connect(self._on_item_clicked)
        self.tree_widget.setStyleSheet(
            """
            QTreeWidget { background: white; border: 1px solid #d0d0d0; }
            QTreeView::item { padding: 6px 8px; }
            QTreeView::item:selected { background: #f0f7ff; color: #000; }
            QTreeView::item:hover { background: #eef4ff; }
            """
        )
        
        # Populate tree
        self._populate_tree()
        
        layout.addWidget(self.tree_widget)
        self.setLayout(layout)
    
    def _populate_tree(self):
        """Populate tree with node categories and nodes."""
        # Get all categories
        categories = get_categories()
        
        for category in categories:
            category_item = QTreeWidgetItem()
            category_item.setText(0, category)
            category_item.setFont(0, QFont("Segoe UI", 9, QFont.Bold))
            category_item.setForeground(0, QBrush(QColor(50, 50, 80)))
            category_item.setFlags(category_item.flags() & ~Qt.ItemIsSelectable)
            self.tree_widget.addTopLevelItem(category_item)
            
            for node_type, node_class in NODE_REGISTRY.items():
                node_instance = node_class()
                if node_instance.category == category:
                    node_item = QTreeWidgetItem()
                    node_item.setText(0, node_instance.title)
                    node_item.setData(0, Qt.UserRole, node_type)
                    node_item.setFont(0, QFont("Segoe UI", 9))
                    
                    icon = QIcon(self._generate_icon(node_instance.title))
                    node_item.setIcon(0, icon)
                    
                    category_item.addChild(node_item)
                    self.node_items[node_type] = node_item
        
        # Expand all categories by default
        self.tree_widget.expandAll()
    
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Called when item is clicked."""
        node_type = item.data(0, Qt.UserRole)
        if node_type:
            self.node_selected.emit(node_type)
            logger.debug(f"Node selected: {node_type}")
    
    def _on_context_menu(self, position):
        """Show context menu."""
        item = self.tree_widget.itemAt(position)
        if not item:
            return
        
        node_type = item.data(0, Qt.UserRole)
        if not node_type:
            return
        
        menu = QMenu()
        add_action = menu.addAction("추가")
        
        action = menu.exec(self.tree_widget.mapToGlobal(position))
        
        if action == add_action:
            self.node_add_requested.emit(node_type)
            logger.info(f"Add requested for node: {node_type}")
    
    def _filter_nodes(self, text: str):
        """Filter the node list by text."""
        text = text.lower().strip()
        for node_type, item in self.node_items.items():
            visible = text in item.text(0).lower() or text in node_type.lower()
            item.setHidden(not visible)
            parent = item.parent()
            if parent:
                parent.setHidden(not any(not parent.child(i).isHidden() for i in range(parent.childCount())))

    def get_node_info(self, node_type: str) -> dict:
        """Get information about a node type."""
        return get_node_info(node_type)

    def _generate_icon(self, title: str) -> QPixmap:
        pixmap = QPixmap(24, 24)
        pixmap.fill(QColor(240, 240, 240))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(100, 150, 220))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 20, 20)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, title[0])
        painter.end()
        return pixmap
