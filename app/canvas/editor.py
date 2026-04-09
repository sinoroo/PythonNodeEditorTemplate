"""Canvas/Editor widget for node-based editing."""
from typing import Dict, Optional, Tuple
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsLineItem
from PySide6.QtCore import Qt, QMimeData, QPoint, QSize, QPointF, QRectF
from PySide6.QtGui import QColor, QPen, QBrush, QFont, QDrag, QPixmap, QPainter
from PySide6.QtCore import Signal
import logging

from ..nodes.base_node import BaseNode
from ..nodes.node_registry import create_node, NODE_REGISTRY
from ..commands.undo_redo import Command, CommandStack
from .node_item import NodeItemGraphics, ConnectionItem, PortItem

logger = logging.getLogger(__name__)

class CanvasGraphicsView(QGraphicsView):
    """Custom graphics view with keyboard support and drop handling."""
    
    def __init__(self, editor, scene):
        super().__init__(scene)
        self.editor = editor
        self.setAcceptDrops(True)
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Delete:
            for item in self.scene().selectedItems():
                if isinstance(item, NodeItemGraphics):
                    command = RemoveNodeCommand(self.editor, item.node)
                    self.editor.command_stack.execute(command)
        else:
            super().keyPressEvent(event)

    def dragEnterEvent(self, event):
        """Accept drag enter on the view."""
        if event.mimeData().hasFormat("application/x-node-type"):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        """Accept drag move on the view."""
        if event.mimeData().hasFormat("application/x-node-type"):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        """Handle node drops onto the view."""
        if event.mimeData().hasFormat("application/x-node-type"):
            node_type = bytes(event.mimeData().data("application/x-node-type")).decode()
            scene_pos = self.mapToScene(event.position().toPoint()) if hasattr(event, 'position') else self.mapToScene(event.pos())
            try:
                node = create_node(node_type)
                node.x = scene_pos.x()
                node.y = scene_pos.y()
                self.editor.add_node(node, node.x, node.y)
                logger.info(f"Node dropped at ({node.x}, {node.y}): {node.title}")
                event.acceptProposedAction()
            except Exception as e:
                logger.error(f"Failed to add node on drop: {e}")
                event.ignore()
        else:
            super().dropEvent(event)


class AddNodeCommand(Command):
    """Command to add a node to the canvas."""
    
    def __init__(self, canvas, node: BaseNode, description: str = ""):
        super().__init__(description or f"Add {node.title}")
        self.canvas = canvas
        self.node = node
        self.node_item = None
    
    def execute(self):
        self.node_item = self.canvas._add_node(self.node)
        logger.info(f"Added node: {self.node.title}")
    
    def undo(self):
        if self.node_item:
            self.canvas._remove_node(self.node)
            logger.info(f"Removed node: {self.node.title}")


class RemoveNodeCommand(Command):
    """Command to remove a node from the canvas."""
    
    def __init__(self, canvas, node: BaseNode, description: str = ""):
        super().__init__(description or f"Remove {node.title}")
        self.canvas = canvas
        self.node = node
        self.node_data = node.to_dict()
    
    def execute(self):
        self.canvas._remove_node(self.node)
        logger.info(f"Removed node: {self.node.title}")
    
    def undo(self):
        # Recreate node
        new_node = create_node(self._get_node_type())
        new_node.node_id = self.node.node_id
        self.canvas._add_node(new_node)
        logger.info(f"Restored node: {self.node.title}")
    
    def _get_node_type(self):
        for node_type, node_class in NODE_REGISTRY.items():
            instance = node_class()
            if instance.title == self.node.title:
                return node_type
        return "DataSource"


class ConnectNodesCommand(Command):
    """Command to connect two nodes."""
    
    def __init__(self, canvas, source_node: BaseNode, source_port: str, 
                 target_node: BaseNode, target_port: str, description: str = ""):
        super().__init__(description or f"Connect {source_node.title} to {target_node.title}")
        self.canvas = canvas
        self.source_node = source_node
        self.source_port = source_port
        self.target_node = target_node
        self.target_port = target_port
        self.connection_item = None
    
    def execute(self):
        self.source_node.connect_output(self.source_port, self.target_node.node_id, self.target_port)
        self.target_node.connect_input(self.target_port, self.source_node.node_id, self.source_port)
        self.connection_item = self.canvas._create_connection_item(
            self.source_node, self.source_port, self.target_node, self.target_port)
        logger.info(f"Connected {self.source_node.title}.{self.source_port} -> {self.target_node.title}.{self.target_port}")
    
    def undo(self):
        self.source_node.disconnect_output(self.source_port, self.target_node.node_id, self.target_port)
        self.target_node.disconnect_input(self.target_port)
        if self.connection_item is not None:
            self.canvas._remove_connection_item(self.connection_item)
            self.connection_item = None
        logger.info(f"Disconnected {self.source_node.title}.{self.source_port} from {self.target_node.title}.{self.target_port}")


class CanvasEditor(QWidget):
    """Node-based canvas editor."""
    
    node_added = Signal(BaseNode)
    node_removed = Signal(BaseNode)
    nodes_connected = Signal(BaseNode, str, BaseNode, str)
    action_logged = Signal(str)
    node_selected = Signal(object)  # BaseNode or None
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.nodes: Dict[int, BaseNode] = {}
        self.command_stack = CommandStack()
        self.command_stack.register_callback(self._on_command_stack_changed)
        self.active_port_drag = None
        
        self._setup_ui()
        self._setup_scene()
    
    def _setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create graphics scene
        self.graphics_scene = QGraphicsScene()
        self.graphics_scene.setBackgroundBrush(QBrush(QColor(245, 245, 245)))
        self.graphics_scene.selectionChanged.connect(self._on_selection_changed)
        
        # Create graphics view
        self.graphics_view = CanvasGraphicsView(self, self.graphics_scene)
        self.graphics_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.graphics_view.customContextMenuRequested.connect(self._on_canvas_context_menu)
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        self.graphics_view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.graphics_view.setDragMode(QGraphicsView.RubberBandDrag)
        self.graphics_view.setStyleSheet("background: #f5f5f5; border: none;")
        
        layout.addWidget(self.graphics_view)
        self.setLayout(layout)
        
        # Track selected node items
        self.selected_node_items = []
    
    def _setup_scene(self):
        """Setup canvas scene."""
        # Grid
        pen = QPen(QColor(100, 100, 100))
        pen.setWidth(0)
        
        # Draw grid
        for i in range(-500, 1000, 50):
            self.graphics_scene.addLine(i, -500, i, 1000, pen)
            self.graphics_scene.addLine(-500, i, 1000, i, pen)
    
    def _on_selection_changed(self):
        """Handle selection changes."""
        selected_items = self.graphics_scene.selectedItems()
        selected_nodes = [item.node for item in selected_items if isinstance(item, NodeItemGraphics)]
        if selected_nodes:
            self.node_selected.emit(selected_nodes[0])  # Emit first selected node
        else:
            self.node_selected.emit(None)
    
    def add_node(self, node: BaseNode, x: float = 0, y: float = 0):
        """Add node via command."""
        node.x = x
        node.y = y
        command = AddNodeCommand(self, node)
        self.command_stack.execute(command)
    
    def _add_node(self, node: BaseNode) -> Optional[object]:
        """Internal method to add node to scene."""
        self.nodes[node.node_id] = node
        
        # Create node item
        node_item = self._create_node_item(node)
        self.graphics_scene.addItem(node_item)
        
        self.node_added.emit(node)
        self.action_logged.emit(f"Node added: {node.title} (ID: {node.node_id})")
        
        return node_item
    
    def _create_node_item(self, node: BaseNode) -> object:
        """Create a visual node item."""
        node_item = NodeItemGraphics(node, editor=self)
        node_item.node = node
        return node_item
    
    def _create_connection_item(self, source_node: BaseNode, source_port: str,
                                target_node: BaseNode, target_port: str):
        source_item = self._find_node_item(source_node)
        target_item = self._find_node_item(target_node)
        if source_item is None or target_item is None:
            return None
        connection_item = ConnectionItem(source_item, source_port, target_item, target_port)
        self.graphics_scene.addItem(connection_item)
        return connection_item

    def _remove_connection_item(self, connection_item):
        self.graphics_scene.removeItem(connection_item)

    def _find_node_item(self, node: BaseNode):
        for item in self.graphics_scene.items():
            if hasattr(item, 'node') and item.node.node_id == node.node_id:
                return item
        return None

    def _remove_node(self, node: BaseNode):
        """Internal method to remove node from scene."""
        if node.node_id in self.nodes:
            del self.nodes[node.node_id]

        # Remove any connections involving this node
        for item in list(self.graphics_scene.items()):
            if isinstance(item, ConnectionItem) and (
                item.source_node.node.node_id == node.node_id or
                item.target_node.node.node_id == node.node_id
            ):
                self.graphics_scene.removeItem(item)

        # Remove the node item itself
        for item in list(self.graphics_scene.items()):
            if hasattr(item, 'node') and item.node.node_id == node.node_id:
                self.graphics_scene.removeItem(item)

        self.node_removed.emit(node)
        self.action_logged.emit(f"Node removed: {node.title} (ID: {node.node_id})")

    def start_port_drag(self, source_port_item):
        self.active_port_drag = {
            'source_port': source_port_item,
            'preview': QGraphicsLineItem(),
            'highlighted': None
        }
        self.active_port_drag['preview'].setPen(QPen(QColor(80, 80, 180), 2, Qt.DashLine))
        self.graphics_scene.addItem(self.active_port_drag['preview'])

    def update_port_drag(self, position: QPointF):
        if not self.active_port_drag:
            return
        source_port_item = self.active_port_drag['source_port']
        source_node_item = source_port_item.parentItem()
        if source_node_item is None:
            return
        source_center = source_node_item.get_port_center(source_port_item.port_name)
        self.active_port_drag['preview'].setLine(
            source_center.x(), source_center.y(), position.x(), position.y()
        )
        target_port_item = self._find_port_item_at_position(position, port_type='input')
        self._update_highlighted_port(target_port_item)

    def finish_port_drag(self, source_port_item, end_position: QPointF):
        if not self.active_port_drag:
            return
        preview = self.active_port_drag.get('preview')
        if preview is not None:
            self.graphics_scene.removeItem(preview)
        self._update_highlighted_port(None)
        target_port_item = self._find_port_item_at_position(end_position, port_type='input')
        self.active_port_drag = None
        if target_port_item is None:
            return
        source_node_item = source_port_item.parentItem()
        target_node_item = target_port_item.parentItem()
        if source_node_item is None or target_node_item is None:
            return
        if not self._can_connect(
            source_node_item.node,
            source_port_item.port_name,
            target_node_item.node,
            target_port_item.port_name
        ):
            logger.info(
                f"Invalid connection: {source_node_item.node.title}.{source_port_item.port_name} -> "
                f"{target_node_item.node.title}.{target_port_item.port_name}"
            )
            return
        self.connect_nodes(
            source_node_item.node,
            source_port_item.port_name,
            target_node_item.node,
            target_port_item.port_name
        )

    def _find_port_item_at_position(self, position: QPointF, port_type: str = None):
        search_area = QRectF(position.x() - 16, position.y() - 16, 32, 32)
        for item in self.graphics_scene.items(search_area, Qt.IntersectsItemShape):
            if isinstance(item, PortItem):
                if port_type is None or item.port_type == port_type:
                    return item
        return None

    def _update_highlighted_port(self, port_item):
        if not self.active_port_drag:
            return
        current = self.active_port_drag.get('highlighted')
        if current is port_item:
            return
        if current is not None:
            current.set_highlight(False)
        if port_item is not None:
            port_item.set_highlight(True)
        self.active_port_drag['highlighted'] = port_item

    def _can_connect(self, source_node: BaseNode, source_port: str,
                     target_node: BaseNode, target_port: str) -> bool:
        if source_node.node_id == target_node.node_id:
            return False
        if source_port not in source_node.output_ports:
            return False
        if target_port not in target_node.input_ports:
            return False
        if target_port in target_node.input_connections:
            return False
        return True

    def connect_nodes(self, source_node: BaseNode, source_port: str,
                     target_node: BaseNode, target_port: str):
        """Connect two nodes via command."""
        command = ConnectNodesCommand(self, source_node, source_port, target_node, target_port)
        self.command_stack.execute(command)
        self.nodes_connected.emit(source_node, source_port, target_node, target_port)
    
    def undo(self):
        """Undo last action."""
        self.command_stack.undo()
    
    def redo(self):
        """Redo last undone action."""
        self.command_stack.redo()
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return self.command_stack.can_undo()
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return self.command_stack.can_redo()
    
    def get_all_nodes(self) -> list:
        """Get all nodes in the canvas."""
        return list(self.nodes.values())
    
    def _on_command_stack_changed(self):
        """Called when command stack changes."""
        pass
    
    def _on_canvas_context_menu(self, position):
        """Show context menu on canvas."""
        from PySide6.QtWidgets import QMenu
        
        # Get item at position
        item = self.graphics_view.itemAt(position)
        if not item or not isinstance(item, NodeItemGraphics):
            return
        
        node = item.node
        
        menu = QMenu()
        delete_action = menu.addAction("삭제")
        
        action = menu.exec(self.graphics_view.mapToGlobal(position))
        
        if action == delete_action:
            command = RemoveNodeCommand(self, node)
            self.command_stack.execute(command)
    
    def clear(self):
        """Clear the canvas."""
        self.nodes.clear()
        self.graphics_scene.clear()
        self._setup_scene()
        self.action_logged.emit("Canvas cleared")
    
    def zoom_in(self):
        """Zoom in by 10% centered on the view center."""
        self.graphics_view.scale(1.1, 1.1)
        self.action_logged.emit("Zoomed in")
    
    def zoom_out(self):
        """Zoom out by 10% centered on the view center."""
        self.graphics_view.scale(0.9, 0.9)
        self.action_logged.emit("Zoomed out")
    
    def fit_to_view(self):
        """Fit all nodes in the view."""
        if self.nodes:
            # Get bounding rect of all node items
            items = [item for item in self.graphics_scene.items() if isinstance(item, NodeItemGraphics)]
            if items:
                bounding_rect = items[0].sceneBoundingRect()
                for item in items[1:]:
                    bounding_rect = bounding_rect.united(item.sceneBoundingRect())
                
                # Add some padding
                padding = 50
                bounding_rect.adjust(-padding, -padding, padding, padding)
                
                # Fit in view
                self.graphics_view.fitInView(bounding_rect, Qt.KeepAspectRatio)
                self.action_logged.emit("Fitted to view")
        else:
            # If no nodes, reset to default zoom
            self.graphics_view.resetTransform()
            self.action_logged.emit("Reset view")
    
    def get_all_nodes(self):
        """Get all nodes in the canvas."""
        return list(self.nodes.values())
    
    def get_all_connections(self):
        """Get all connections in the canvas."""
        connections = []
        for node in self.nodes.values():
            for port_name, connections_list in node.output_connections.items():
                for target_node_id, target_port_name in connections_list:
                    connections.append({
                        'source_node_id': node.node_id,
                        'source_port': port_name,
                        'target_node_id': target_node_id,
                        'target_port': target_port_name
                    })
        return connections
    
    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasFormat("application/x-node-type"):
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        """Handle drag move event."""
        if event.mimeData().hasFormat("application/x-node-type"):
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle drop event."""
        if event.mimeData().hasFormat("application/x-node-type"):
            node_type = event.mimeData().data("application/x-node-type").decode()
            
            # Get drop position
            pos = event.position()
            
            try:
                node = create_node(node_type)
                node.x = pos.x()
                node.y = pos.y()
                self.add_node(node, node.x, node.y)
                logger.info(f"Node dropped at ({node.x}, {node.y}): {node.title}")
                event.acceptProposedAction()
            except Exception as e:
                logger.error(f"Failed to add node on drop: {e}")
                event.ignore()
