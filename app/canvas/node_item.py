"""Canvas node item visualization."""
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem, QGraphicsPolygonItem, QGraphicsLineItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QPen, QBrush, QFont, QPainter, QPolygonF, QPainterPath


class PortItem(QGraphicsItem):
    """Visual representation of a port."""
    
    PORT_SIZE = 20
    
    def __init__(self, port_name: str, port_type: str, parent=None):
        super().__init__(parent)
        self.port_name = port_name
        self.port_type = port_type  # "input" or "output"
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setZValue(2)
        self.is_hovered = False
        self.is_highlighted = False
        self.is_dragging = False

    def boundingRect(self):
        return QRectF(0, 0, self.PORT_SIZE, self.PORT_SIZE)

    def shape(self):
        path = QPainterPath()
        path.addEllipse(self.boundingRect())
        return path

    def paint(self, painter: QPainter, option, widget):
        if self.is_highlighted:
            color = QColor(120, 210, 120)
        elif self.is_hovered:
            color = QColor(100, 150, 255)
        else:
            color = QColor(100, 100, 200)
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawEllipse(0, 0, self.PORT_SIZE, self.PORT_SIZE)

    def set_highlight(self, value: bool):
        if self.is_highlighted != value:
            self.is_highlighted = value
            self.update()

    def hoverEnterEvent(self, event):
        self.is_hovered = True
        self.update()

    def hoverLeaveEvent(self, event):
        self.is_hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.port_type == "output":
            self.is_dragging = True
            self.grabMouse()
            event.accept()
            view = self.scene().views()[0] if self.scene().views() else None
            if view and hasattr(view, 'editor'):
                view.editor.start_port_drag(self)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            view = self.scene().views()[0] if self.scene().views() else None
            if view and hasattr(view, 'editor'):
                view.editor.update_port_drag(event.scenePos())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_dragging:
            self.is_dragging = False
            self.ungrabMouse()
            event.accept()
            view = self.scene().views()[0] if self.scene().views() else None
            if view and hasattr(view, 'editor'):
                view.editor.finish_port_drag(self, event.scenePos())
        else:
            super().mouseReleaseEvent(event)


class NodeItemGraphics(QGraphicsItem):
    """Visual representation of a node on the canvas."""
    
    NODE_WIDTH = 150
    NODE_HEIGHT = 100
    PORT_SPACING = 20
    
    def __init__(self, node, editor=None, parent=None):
        super().__init__(parent)
        self.node = node
        self.editor = editor
        self.is_selected = False
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setPos(node.x, node.y)
        
        self.port_items = {}
        self._create_port_items()

    def get_port_center(self, port_name: str) -> QPointF:
        port_item = self.port_items.get(port_name)
        if port_item is None:
            return self.mapToScene(QPointF(self.NODE_WIDTH / 2, self.NODE_HEIGHT / 2))
        return self.mapToScene(port_item.pos() + QPointF(port_item.PORT_SIZE / 2, port_item.PORT_SIZE / 2))
    
    def _create_port_items(self):
        """Create visual port items."""
        # Input ports
        y_offset = 20 + PortItem.PORT_SIZE
        for i, (port_name, port) in enumerate(self.node.input_ports.items()):
            port_item = PortItem(port_name, "input", self)
            port_item.setPos(-PortItem.PORT_SIZE, y_offset)
            self.port_items[port_name] = port_item
            y_offset += self.PORT_SPACING
        
        # Output ports
        y_offset = 20 + PortItem.PORT_SIZE
        for i, (port_name, port) in enumerate(self.node.output_ports.items()):
            port_item = PortItem(port_name, "output", self)
            port_item.setPos(self.NODE_WIDTH, y_offset)
            self.port_items[port_name] = port_item
            y_offset += self.PORT_SPACING
    
    def boundingRect(self):
        return QRectF(0, 0, self.NODE_WIDTH, self.NODE_HEIGHT)
    
    def paint(self, painter: QPainter, option, widget):
        # Draw rounded background
        bg_color = QColor(255, 255, 255) if not self.is_selected else QColor(235, 245, 255)
        border_color = QColor(140, 160, 190) if not self.is_selected else QColor(80, 120, 180)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 2))
        painter.drawRoundedRect(0, 0, self.NODE_WIDTH, self.NODE_HEIGHT, 10, 10)
        
        # Header bar
        header_color = QColor(100, 140, 200) if not self.is_selected else QColor(80, 120, 190)
        painter.setBrush(QBrush(header_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.NODE_WIDTH, 28, 10, 10)
        painter.drawRect(0, 14, self.NODE_WIDTH, 14)
        
        # Draw title
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.setPen(QColor(255, 255, 255))
        title_rect = QRectF(10, 5, self.NODE_WIDTH - 20, 18)
        painter.drawText(title_rect, Qt.AlignVCenter | Qt.AlignLeft, self.node.title)
        
        # Draw separator line
        painter.setPen(QPen(QColor(210, 210, 210), 1))
        painter.drawLine(10, 34, self.NODE_WIDTH - 10, 34)
        
        # Draw port labels
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QColor(60, 60, 60))
        y_pos = 45
        
        for port_name in self.node.input_ports.keys():
            painter.drawText(18, y_pos, port_name)
            y_pos += self.PORT_SPACING
        
        y_pos = 45
        for port_name in self.node.output_ports.keys():
            rect = QRectF(self.NODE_WIDTH - 70, y_pos - 4, 60, 14)
            painter.drawText(rect, Qt.AlignRight | Qt.AlignVCenter, port_name)
            y_pos += self.PORT_SPACING
    
    def itemChange(self, change, value):
        # Update node position
        if change == QGraphicsItem.ItemPositionChange:
            self.node.x = value.x()
            self.node.y = value.y()
            scene = self.scene()
            if scene is not None:
                for item in scene.items():
                    if isinstance(item, ConnectionItem) and (item.source_node == self or item.target_node == self):
                        item.prepareGeometryChange()
                        item.update()
        return super().itemChange(change, value)
    
    def mousePressEvent(self, event):
        self.is_selected = True
        self.update()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        # Emit signal to show node properties dialog
        pass


class ConnectionItem(QGraphicsItem):
    """Visual representation of a connection between nodes."""
    
    def __init__(self, source_node: NodeItemGraphics, source_port: str,
                 target_node: NodeItemGraphics, target_port: str, parent=None):
        super().__init__(parent)
        self.source_node = source_node
        self.source_port = source_port
        self.target_node = target_node
        self.target_port = target_port
        self.setZValue(-1)

    def boundingRect(self):
        source_pos = self.source_node.get_port_center(self.source_port)
        target_pos = self.target_node.get_port_center(self.target_port)
        
        # Calculate control points for bezier curve
        dx = abs(target_pos.x() - source_pos.x())
        cp_offset = max(dx * 0.4, 50)  # Minimum curve radius
        
        cp1 = QPointF(source_pos.x() + cp_offset, source_pos.y())
        cp2 = QPointF(target_pos.x() - cp_offset, target_pos.y())
        
        # Create path to get bounding rect
        path = QPainterPath()
        path.moveTo(source_pos)
        path.cubicTo(cp1, cp2, target_pos)
        
        return path.boundingRect().adjusted(-10, -10, 10, 10)

    def paint(self, painter: QPainter, option, widget):
        color = QColor(100, 100, 100)
        painter.setPen(QPen(color, 2))

        source_pos = self.source_node.get_port_center(self.source_port)
        target_pos = self.target_node.get_port_center(self.target_port)
        
        # Calculate control points for smooth bezier curve
        dx = abs(target_pos.x() - source_pos.x())
        cp_offset = max(dx * 0.4, 50)  # Minimum curve radius
        
        cp1 = QPointF(source_pos.x() + cp_offset, source_pos.y())
        cp2 = QPointF(target_pos.x() - cp_offset, target_pos.y())
        
        # Draw bezier curve
        path = QPainterPath()
        path.moveTo(source_pos)
        path.cubicTo(cp1, cp2, target_pos)
        painter.drawPath(path)
        
        # Draw arrow at target end
        arrow_size = 8
        angle = 0.5  # Arrow angle in radians
        
        # Calculate direction at target end
        direction = target_pos - cp2
        if direction.manhattanLength() > 0:
            direction = direction / direction.manhattanLength()
        else:
            direction = QPointF(0, -1)  # Default upward direction
        
        # Arrow points
        arrow_p1 = target_pos - arrow_size * QPointF(
            direction.x() * 0.866 - direction.y() * 0.5,
            direction.x() * 0.5 + direction.y() * 0.866
        )
        arrow_p2 = target_pos - arrow_size * QPointF(
            direction.x() * 0.866 + direction.y() * 0.5,
            -direction.x() * 0.5 + direction.y() * 0.866
        )
        
        # Draw arrow
        arrow_path = QPainterPath()
        arrow_path.moveTo(target_pos)
        arrow_path.lineTo(arrow_p1)
        arrow_path.lineTo(arrow_p2)
        arrow_path.closeSubpath()
        painter.setBrush(QBrush(color))
        painter.drawPath(arrow_path)
