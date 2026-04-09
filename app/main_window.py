"""Main application window."""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QDockWidget, QMessageBox, QFileDialog, QApplication, QLabel, QTabWidget, QStyle
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QAction, QKeySequence, QPixmap, QPainter, QFont
import logging
import json
from pathlib import Path

from .canvas.editor import CanvasEditor, ConnectNodesCommand
from .panels.node_list import NodeListPanel
from .panels.log_panel import LogPanel
from .panels.attribute_panel import AttributePanel
from .nodes.node_registry import create_node

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Orange Canvas - Node Editor")
        self.setWindowIcon(QIcon())
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget with tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        self.setCentralWidget(self.tab_widget)
        
        # Track editors and their file paths
        self.editors = []
        self.file_paths = []
        self.dirty_flags = []  # Track if each tab has unsaved changes
        
        # For attribute panel connections
        self.current_editor_connection = None
        
        # Create first editor tab
        self._create_new_tab("Untitled")
        
        # Create log panel
        self.log_panel = LogPanel()
        log_dock = QDockWidget("Log", self)
        log_dock.setWidget(self.log_panel)
        log_dock.setMinimumHeight(150)
        self.addDockWidget(Qt.BottomDockWidgetArea, log_dock)
        
        # Create node list panel
        self.node_list = NodeListPanel()
        node_list_dock = QDockWidget("Node List", self)
        node_list_dock.setWidget(self.node_list)
        node_list_dock.setMinimumWidth(200)
        self.addDockWidget(Qt.LeftDockWidgetArea, node_list_dock)
        
        # Create attribute panel
        self.attribute_panel = AttributePanel()
        attribute_dock = QDockWidget("Attributes", self)
        attribute_dock.setWidget(self.attribute_panel)
        attribute_dock.setMinimumWidth(200)
        self.addDockWidget(Qt.RightDockWidgetArea, attribute_dock)
        
        # Setup tool bar first (needed for menu actions)
        self._setup_tool_bar()
        # Setup menu bar
        self._setup_menu_bar()
        
        # Connect signals
        self._connect_signals()
        
        # Setup status bar
        self.statusBar().showMessage("Ready")
        
        logger.info("Application started")
    
    def _create_new_tab(self, title="Untitled"):
        """Create a new editor tab."""
        editor = CanvasEditor()
        self.editors.append(editor)
        self.file_paths.append(None)  # No file path initially
        self.dirty_flags.append(False)  # Initially clean
        
        tab_index = self.tab_widget.addTab(editor, title)
        self.tab_widget.setCurrentIndex(tab_index)
        
        # Connect editor signals
        editor.action_logged.connect(self._log_action)
        editor.node_added.connect(self._on_node_added_to_canvas)
        editor.node_removed.connect(self._on_node_removed_from_canvas)
        editor.nodes_connected.connect(self._on_nodes_connected)
        
        # Register callback for undo/redo state updates
        editor.command_stack.register_callback(self._update_undo_redo)
        
        return editor
    
    def _get_current_editor(self):
        """Get the currently active editor."""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0 and current_index < len(self.editors):
            return self.editors[current_index]
        return None
    
    def _close_tab(self, index):
        """Close a tab."""
        if index >= 0 and index < len(self.editors):
            # Check if there are unsaved changes
            if self.dirty_flags[index]:
                reply = QMessageBox.question(
                    self, "탭 닫기",
                    "저장되지 않은 변경사항이 있습니다. 계속하시겠습니까?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # Remove tab and editor
            editor = self.editors[index]
            # Disconnect signals to prevent errors
            try:
                editor.graphics_scene.selectionChanged.disconnect(editor._on_selection_changed)
            except:
                pass  # Already disconnected
            self.tab_widget.removeTab(index)
            del self.editors[index]
            del self.file_paths[index]
            del self.dirty_flags[index]
    
    def _setup_menu_bar(self):
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("파일 (&F)")
        
        new_tab_action = QAction("새 탭 (&N)", self)
        new_tab_action.setShortcut(QKeySequence.New)
        new_tab_action.triggered.connect(self._on_new_tab)
        file_menu.addAction(new_tab_action)
        
        new_canvas_action = QAction("새 캔버스 (&W)", self)
        new_canvas_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        new_canvas_action.triggered.connect(self._on_new_canvas)
        file_menu.addAction(new_canvas_action)
        
        file_menu.addSeparator()
        
        open_action = QAction("열기 (&O)", self)
        
        open_action = QAction("열기 (&O)", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)
        
        save_action = QAction("저장 (&S)", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("종료 (&X)", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("편집 (&E)")
        
        undo_action = QAction("실행 취소 (&U)", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self._on_undo)
        edit_menu.addAction(undo_action)
        self.menu_undo_action = undo_action
        
        redo_action = QAction("다시 실행 (&Y)", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(self._on_redo)
        edit_menu.addAction(redo_action)
        self.menu_redo_action = redo_action
        
        edit_menu.addSeparator()
        
        clear_action = QAction("캔버스 지우기 (&C)", self)
        clear_action.triggered.connect(self._on_clear)
        edit_menu.addAction(clear_action)
        
        # View menu
        view_menu = menubar.addMenu("보기 (&V)")
        
        view_menu.addAction(self.zoom_in_action)
        view_menu.addAction(self.zoom_out_action)
        view_menu.addAction(self.fit_view_action)
        
        # Help menu
        help_menu = menubar.addMenu("도움말 (&H)")
        
        about_action = QAction("정보 (&A)", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def _create_text_icon(self, text, size=20):
        """Create an icon with text."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
        painter.end()
        return QIcon(pixmap)
    
    def _setup_tool_bar(self):
        """Setup top toolbar."""
        toolbar = self.addToolBar("Main")
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setMovable(False)
        
        self.new_tab_action = QAction(self.style().standardIcon(QStyle.SP_FileDialogNewFolder), "새 탭", self)
        self.new_tab_action.triggered.connect(self._on_new_tab)
        toolbar.addAction(self.new_tab_action)
        
        self.open_action = QAction(self.style().standardIcon(QStyle.SP_DirOpenIcon), "열기", self)
        self.open_action.triggered.connect(self._on_open)
        toolbar.addAction(self.open_action)
        
        self.save_action = QAction(self.style().standardIcon(QStyle.SP_DialogSaveButton), "저장", self)
        self.save_action.triggered.connect(self._on_save)
        toolbar.addAction(self.save_action)
        
        toolbar.addSeparator()
        
        self.toolbar_undo_action = QAction(self.style().standardIcon(QStyle.SP_ArrowLeft), "실행 취소", self)
        self.toolbar_undo_action.setShortcut(QKeySequence.Undo)
        self.toolbar_undo_action.triggered.connect(self._on_undo)
        toolbar.addAction(self.toolbar_undo_action)
        
        self.toolbar_redo_action = QAction(self.style().standardIcon(QStyle.SP_ArrowRight), "다시 실행", self)
        self.toolbar_redo_action.setShortcut(QKeySequence.Redo)
        self.toolbar_redo_action.triggered.connect(self._on_redo)
        toolbar.addAction(self.toolbar_redo_action)
        
        toolbar.addSeparator()
        
        self.clear_action = QAction(self._create_text_icon("🗑️"), "캔버스 지우기", self)
        self.clear_action.triggered.connect(self._on_clear)
        toolbar.addAction(self.clear_action)
        
        toolbar.addSeparator()
        
        self.zoom_in_action = QAction(self._create_text_icon("+"), "확대", self)
        self.zoom_in_action.setShortcut(QKeySequence("Ctrl++"))
        self.zoom_in_action.triggered.connect(self._on_zoom_in)
        toolbar.addAction(self.zoom_in_action)
        
        self.zoom_out_action = QAction(self._create_text_icon("-"), "축소", self)
        self.zoom_out_action.setShortcut(QKeySequence("Ctrl+-"))
        self.zoom_out_action.triggered.connect(self._on_zoom_out)
        toolbar.addAction(self.zoom_out_action)
        
        self.fit_view_action = QAction(self.style().standardIcon(QStyle.SP_BrowserReload), "맞추기", self)
        self.fit_view_action.setShortcut(QKeySequence("Ctrl+="))
        self.fit_view_action.triggered.connect(self._on_fit_view)
        toolbar.addAction(self.fit_view_action)
    
    def _connect_signals(self):
        """Connect signals."""
        # Node list signals
        self.node_list.node_selected.connect(self._on_node_selected)
        self.node_list.node_add_requested.connect(self._on_node_add_requested)
        
        # Tab widget signals
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # Update undo/redo menu when tab changes
        self._update_undo_redo()
        self._update_attribute_panel_connection()
    
    def _update_undo_redo(self):
        """Update undo/redo menu state."""
        editor = self._get_current_editor()
        if editor:
            # Update toolbar actions (simple enable/disable)
            self.toolbar_undo_action.setEnabled(editor.can_undo())
            self.toolbar_redo_action.setEnabled(editor.can_redo())
            
            # Update menu actions (with descriptions)
            undo_text = editor.command_stack.get_undo_description()
            redo_text = editor.command_stack.get_redo_description()
            
            self.menu_undo_action.setEnabled(editor.can_undo())
            self.menu_redo_action.setEnabled(editor.can_redo())
            # Keep menu text simple (no descriptions)
        else:
            # Disable all actions
            self.toolbar_undo_action.setEnabled(False)
            self.toolbar_redo_action.setEnabled(False)
            self.menu_undo_action.setEnabled(False)
            self.menu_redo_action.setEnabled(False)
            # Keep menu text as initially set
    
    def _update_attribute_panel_connection(self):
        """Update the connection between current editor and attribute panel."""
        # Disconnect previous connection
        if self.current_editor_connection is not None:
            self.current_editor_connection[0].node_selected.disconnect(self.current_editor_connection[1])
            self.current_editor_connection = None
        
        # Connect current editor
        editor = self._get_current_editor()
        if editor:
            editor.node_selected.connect(self.attribute_panel.update_node)
            self.current_editor_connection = (editor, self.attribute_panel.update_node)
            # Update with current selection
            selected_items = editor.graphics_scene.selectedItems()
            selected_nodes = [item.node for item in selected_items if hasattr(item, 'node')]
            if selected_nodes:
                self.attribute_panel.update_node(selected_nodes[0])
            else:
                self.attribute_panel.update_node(None)
    
    def _on_tab_changed(self, index):
        """Called when active tab changes."""
        self._update_undo_redo()
        self._update_attribute_panel_connection()
    
    def _on_new_tab(self):
        """Create a new tab."""
        self._create_new_tab("Untitled")
    
    def _on_new_canvas(self):
        """Create a new canvas (clear current tab)."""
        editor = self._get_current_editor()
        if editor:
            editor.clear()
            current_index = self.tab_widget.currentIndex()
            self.file_paths[current_index] = None
            self.tab_widget.setTabText(current_index, "Untitled")
    
    def _on_node_selected(self, node_type: str):
        """Called when node is selected in list."""
        logger.debug(f"Node type selected: {node_type}")
        self.statusBar().showMessage(f"Selected: {node_type}")
    
    def _on_node_add_requested(self, node_type: str):
        """Called when user requests to add a node."""
        editor = self._get_current_editor()
        if editor:
            try:
                node = create_node(node_type)
                node.x = 100
                node.y = 100
                editor.add_node(node, node.x, node.y)
                logger.info(f"Node added via context menu: {node.title}")
            except Exception as e:
                logger.error(f"Failed to add node: {e}")
                QMessageBox.critical(self, "Error", f"노드를 추가할 수 없습니다: {e}")
    
    def _on_node_added_to_canvas(self, node):
        """Called when node is added to canvas."""
        self.statusBar().showMessage(f"Node added: {node.title}")
        # Mark current tab as dirty
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            self.dirty_flags[current_index] = True
    
    def _on_node_removed_from_canvas(self, node):
        """Called when node is removed from canvas."""
        self.statusBar().showMessage(f"Node removed: {node.title}")
        # Mark current tab as dirty
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            self.dirty_flags[current_index] = True
    
    def _on_nodes_connected(self, source_node, source_port, target_node, target_port):
        """Called when nodes are connected."""
        self.statusBar().showMessage(f"Connected: {source_node.title}.{source_port} -> {target_node.title}.{target_port}")
        # Mark current tab as dirty
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            self.dirty_flags[current_index] = True
    
    def _log_action(self, message: str):
        """Log action message."""
        self.log_panel.log("INFO", message)
    
    def _on_new(self):
        """New canvas."""
        reply = QMessageBox.question(
            self, "New Canvas",
            "Create new canvas? Current work will be lost.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.editor.clear()
            logger.info("New canvas created")
    
    def _on_open(self):
        """Open canvas file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Canvas", "", "Canvas Files (*.canvas);;All Files (*)"
        )
        if file_path:
            try:
                self._load_canvas(file_path)
                logger.info(f"Canvas loaded: {file_path}")
            except Exception as e:
                logger.error(f"Failed to load canvas: {e}")
                QMessageBox.critical(self, "Error", f"캔버스를 열 수 없습니다: {e}")
    
    def _on_save(self):
        """Save canvas file."""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            file_path = self.file_paths[current_index]
            if not file_path:
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Save Canvas", "", "Canvas Files (*.canvas);;All Files (*)"
                )
            
            if file_path:
                try:
                    self._save_canvas(file_path, current_index)
                    self.file_paths[current_index] = file_path
                    # Update tab title
                    tab_name = Path(file_path).stem
                    self.tab_widget.setTabText(current_index, tab_name)
                    # Mark as clean
                    self.dirty_flags[current_index] = False
                    logger.info(f"Canvas saved: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to save canvas: {e}")
                    QMessageBox.critical(self, "Error", f"캔버스를 저장할 수 없습니다: {e}")
    
    def _on_undo(self):
        """Undo action."""
        editor = self._get_current_editor()
        if editor:
            editor.undo()
            self._update_undo_redo()
    
    def _on_redo(self):
        """Redo action."""
        editor = self._get_current_editor()
        if editor:
            editor.redo()
            self._update_undo_redo()
    
    def _on_clear(self):
        """Clear canvas."""
        editor = self._get_current_editor()
        if editor:
            reply = QMessageBox.question(
                self, "Clear Canvas",
                "Clear the canvas? This cannot be undone.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                editor.clear()
                # Mark current tab as dirty
                current_index = self.tab_widget.currentIndex()
                if current_index >= 0:
                    self.dirty_flags[current_index] = True
                logger.info("Canvas cleared")
    
    def _on_reset_view(self):
        """Reset view."""
        editor = self._get_current_editor()
        if editor:
            editor.graphics_view.fitInView(
                editor.graphics_scene.itemsBoundingRect(),
                Qt.KeepAspectRatio
            )
    
    def _on_zoom_in(self):
        """Handle zoom in action."""
        editor = self._get_current_editor()
        if editor:
            editor.zoom_in()
    
    def _on_zoom_out(self):
        """Handle zoom out action."""
        editor = self._get_current_editor()
        if editor:
            editor.zoom_out()
    
    def _on_fit_view(self):
        """Handle fit to view action."""
        editor = self._get_current_editor()
        if editor:
            editor.fit_to_view()
    
    def _on_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "정보",
            "Orange Canvas - Node Editor\n\n"
            "버전: 1.0.0\n"
            "PySide6 기반의 노드 에디터\n\n"
            "© 2026"
        )
    
    def _save_canvas(self, file_path: str, editor_index: int):
        """Save canvas to file."""
        editor = self.editors[editor_index]
        nodes_data = []
        for node in editor.get_all_nodes():
            nodes_data.append(node.to_dict())
        
        connections_data = editor.get_all_connections()
        
        data = {
            'version': '1.0',
            'nodes': nodes_data,
            'connections': connections_data
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_canvas(self, file_path: str):
        """Load canvas from file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Create new tab
        tab_name = Path(file_path).stem
        editor = self._create_new_tab(tab_name)
        self.file_paths[-1] = file_path  # Set file path for the new tab
        
        # Clear the new editor (it should be empty anyway)
        editor.clear()
        
        # Recreate nodes
        for node_data in data.get('nodes', []):
            # Find node type by title
            node = self._create_node_from_data(node_data)
            if node:
                editor._add_node(node)
        
        # Recreate connections
        for connection_data in data.get('connections', []):
            source_node_id = connection_data['source_node_id']
            source_port = connection_data['source_port']
            target_node_id = connection_data['target_node_id']
            target_port = connection_data['target_port']
            
            if source_node_id in editor.nodes and target_node_id in editor.nodes:
                source_node = editor.nodes[source_node_id]
                target_node = editor.nodes[target_node_id]
                
                # Create connection
                command = ConnectNodesCommand(
                    editor, source_node, source_port, target_node, target_port
                )
                command.execute()
    
    def _create_node_from_data(self, node_data: dict):
        """Create node from saved data."""
        from .nodes.node_registry import NODE_REGISTRY
        
        title = node_data.get('title')
        for node_type, node_class in NODE_REGISTRY.items():
            instance = node_class()
            if instance.title == title:
                node = node_class(node_data.get('node_id'))
                node.x = node_data.get('x', 0)
                node.y = node_data.get('y', 0)
                return node
        
        return None
    
    def closeEvent(self, event):
        """Handle application close event."""
        # Check if any tabs have unsaved changes
        for i, dirty in enumerate(self.dirty_flags):
            if dirty:
                reply = QMessageBox.question(
                    self, "종료 확인",
                    "저장되지 않은 변경사항이 있습니다. 정말로 종료하시겠습니까?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    event.ignore()
                    return
                break
        
        event.accept()
