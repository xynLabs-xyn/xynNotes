import sys
import json
import os
import shutil
from appdirs import user_data_dir
import base64
from PyQt6.QtCore import Qt, QPoint, QEvent, QByteArray, QBuffer, QIODevice, QRectF
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTextEdit, QLineEdit, QLabel, QDialog, QMenu, QScrollArea,
    QGraphicsView, QGraphicsScene
)
from PyQt6.QtGui import QKeySequence, QShortcut, QMouseEvent, QPixmap, QAction, QPainter, QPen, QColor, QWheelEvent

# Determine the user data directory for your application.
DATA_DIR = user_data_dir("xynNotes", "xynLabs")
os.makedirs(DATA_DIR, exist_ok=True)
# The file where the notes will be stored.
NOTES_PATH = os.path.join(DATA_DIR, "notes.json")

# ---------------------------
# Title Bar
# ---------------------------
class TitleBar(QWidget):
    def __init__(self, parent=None, title="xynNotes"):
        super().__init__(parent)
        self.parent = parent
        self.startPos = QPoint(0, 0)
        self.moving = False
        self.setFixedHeight(30)
        self.setStyleSheet("background-color: #444; color: white;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        
        self.titleLabel = QLabel(title)
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.titleLabel.setStyleSheet("padding: 0 10px;")
        layout.addWidget(self.titleLabel)
        
        layout.addStretch()

        self.minimizeButton = QLabel("_")
        self.minimizeButton.setFixedWidth(20)
        self.minimizeButton.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.minimizeButton.setStyleSheet("QLabel:hover { background-color: blue; }")
        layout.addWidget(self.minimizeButton)
        self.minimizeButton.mousePressEvent = self.minimizeClicked
        
        self.closeButton = QLabel("X")
        self.closeButton.setFixedWidth(20)
        self.closeButton.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.closeButton.setStyleSheet("QLabel:hover { background-color: #c00; }")
        layout.addWidget(self.closeButton)
        self.closeButton.mousePressEvent = self.closeClicked

    def minimizeClicked(self, event):
        if self.parent:
            self.parent.showMinimized()

    def closeClicked(self, event):
        if self.parent:
            self.parent.close()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.startPos = event.globalPosition().toPoint()
            self.moving = True

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.moving and self.parent:
            delta = event.globalPosition().toPoint() - self.startPos
            self.parent.move(self.parent.pos() + delta)
            self.startPos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.moving = False

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if self.parent:
            if self.parent.isMaximized():
                self.parent.showNormal()
            else:
                self.parent.showMaximized()

# ---------------------------
# Prompt for Popups
# ---------------------------
class PromptTitleBar(QWidget):
    def __init__(self, parent=None, title="Prompt"):
        super().__init__(parent)
        self.parent = parent
        self.startPos = QPoint(0, 0)
        self.moving = False
        self.setFixedHeight(30)
        self.setStyleSheet("background-color: #444; color: white;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        
        self.titleLabel = QLabel(title)
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.titleLabel.setStyleSheet("padding: 0 10px;")
        layout.addWidget(self.titleLabel)
        
        layout.addStretch()
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.startPos = event.globalPosition().toPoint()
            self.moving = True

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.moving and self.parent:
            delta = event.globalPosition().toPoint() - self.startPos
            self.parent.move(self.parent.pos() + delta)
            self.startPos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.moving = False

# ---------------------------
# Close Prompt (for unsaved changes)
# ---------------------------
class ClosePromptDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setModal(True)
        self.setMinimumWidth(300)
        self.choice = None  # Will store either "quit" or "save"
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.titleBar = PromptTitleBar(self, title="Unsaved Changes")
        main_layout.addWidget(self.titleBar)
        
        content_widget = QWidget(self)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        prompt_label = QLabel("Type 'quit' to exit without saving or 'save' to save all changes and exit:")
        prompt_label.setWordWrap(True)
        content_layout.addWidget(prompt_label)
        self.line_edit = QLineEdit(self)
        content_layout.addWidget(self.line_edit)
        main_layout.addWidget(content_widget)
        
        QShortcut(QKeySequence("Return"), self, activated=self.processInput)
        QShortcut(QKeySequence("Escape"), self, activated=self.reject)
    
    def processInput(self):
        text = self.line_edit.text().strip().lower()
        if text in ("quit", "save"):
            self.choice = text
            self.accept()

# ---------------------------
# Custom Information Dialog (for confirmations)
# ---------------------------
class CustomInfoDialog(QDialog):
    def __init__(self, parent=None, title="Confirmation", message=""):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setModal(True)
        self.setMinimumWidth(250)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.titleBar = PromptTitleBar(self, title=title)
        main_layout.addWidget(self.titleBar)
        
        content_widget = QWidget(self)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        self.label = QLabel(message, self)
        self.label.setWordWrap(True)
        content_layout.addWidget(self.label)
        main_layout.addWidget(content_widget)
        
        QShortcut(QKeySequence("Return"), self, activated=self.accept)
        QShortcut(QKeySequence("Escape"), self, activated=self.reject)

# ---------------------------
# Export Dialog allows specifying the extension to be used
# ---------------------------
class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setModal(True)
        self.setFixedSize(300, 100)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.titleBar = PromptTitleBar(self, title="Export Note")
        main_layout.addWidget(self.titleBar)
        
        content_widget = QWidget(self)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        self.line_edit = QLineEdit(self)
        self.line_edit.setPlaceholderText("Enter file extension (e.g., lua, json, txt)")
        content_layout.addWidget(self.line_edit)
        main_layout.addWidget(content_widget)
        
        self.line_edit.returnPressed.connect(self.accept)
    
    def getExtension(self):
        return self.line_edit.text().strip()

class Note:
    def __init__(self, title, content, images=None, deleted=False):
        self.title = title
        self.content = content
        self.images = images if images is not None else []
        self.deleted = deleted

# ---------------------------
# Note Viewer (Read-Only)
# ---------------------------
class ZoomableImageView(QGraphicsView):
    def __init__(self, main_window=None, parent=None, show_border=True):
        super().__init__(parent)
        self.main_window = main_window
        self.show_border = show_border
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._pixmap_item = None
        self._original_pixmap = None
        self._zoom = 1.0
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.viewport().setStyleSheet("")

    def clearImage(self):
        self._scene.clear()

    def setImage(self, pixmap):
        self._original_pixmap = pixmap
        self._scene.clear()
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(QRectF(pixmap.rect()))
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom = 1.0

    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        self._zoom *= zoom_factor
        self.scale(zoom_factor, zoom_factor)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Paste):
            self.pasteImage()
            event.accept()
        else:
            super().keyPressEvent(event)

    def pasteImage(self):
        clipboard = QApplication.clipboard()
        image = clipboard.image()
        if not image.isNull():
            pixmap = QPixmap.fromImage(image)
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            pixmap.save(buffer, "PNG")
            base64_str = buffer.data().toBase64().data().decode()
            if self.main_window and hasattr(self.main_window, "addImageToCurrentNote"):
                self.main_window.addImageToCurrentNote(base64_str)
            self.setImage(pixmap)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self.show_border:
            self.viewport().setStyleSheet("border: 1px solid orange;")

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if self.show_border:
            self.viewport().setStyleSheet("")
        
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.hasFocus():
            painter = QPainter(self)
            pen = QPen(QColor("orange"))
            pen.setWidth(1)
            painter.setPen(pen)
            rect = self.rect().adjusted(0, 0, -1, -1)
            painter.drawRect(rect)

class NoteViewer(QMainWindow):
    def __init__(self, note):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.resize(1024, 768)
        
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        self.setCentralWidget(main_widget)
        
        self.titleBar = TitleBar(self, title=note.title)
        main_layout.addWidget(self.titleBar)
        
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)
        
        # Read-only text
        self.textEdit = QTextEdit()
        self.textEdit.setPlainText(note.content)
        self.textEdit.setReadOnly(True)
        self.textEdit.setStyleSheet("QTextEdit::viewport { padding: 5px; }")
        content_layout.addWidget(self.textEdit, 1)
        
        self.imageViewer = ZoomableImageView(show_border=False)
        if note.images:
            ba = QByteArray.fromBase64(note.images[0].encode())
            pixmap = QPixmap()
            pixmap.loadFromData(ba)
            self.imageViewer.setImage(pixmap)
        content_layout.addWidget(self.imageViewer, 1)
        
        QShortcut(QKeySequence("Ctrl+W"), self, activated=self.close)
    
    def showEvent(self, event):
        # Center the window on the primary screen.
        screen = QApplication.primaryScreen()
        screen_geom = screen.availableGeometry()
        self.move(screen_geom.center() - self.rect().center())
        super().showEvent(event)

# ---------------------------
# Main Application Window
# ---------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(800, 600)
        
        self.notes = []
        self.current_note_index = None
        self.unsaved_changes = False  # Tracks unsaved changes.
        self.viewers = []
        self.init_ui()

    def showEvent(self, event):
        self.imageViewer.setFixedWidth(self.note_list_widget.width())
        super().showEvent(event)

    def resizeEvent(self, event):
        self.imageViewer.setFixedWidth(self.note_list_widget.width())
        super().resizeEvent(event)
  
    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(main_widget)
        
        self.titleBar = TitleBar(self, title="xynNotes")
        main_layout.addWidget(self.titleBar)
        
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.addWidget(content_widget)
        
        # Left column: Note List
        left_column = QVBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.textChanged.connect(self.search_notes)
        left_column.addWidget(self.search_input)
        
        self.note_list_widget = QListWidget()
        self.note_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.note_list_widget.customContextMenuRequested.connect(self.on_note_list_context_menu)
        self.note_list_widget.setStyleSheet("""
            QListWidget:focus { border: 1px solid orange; }
            QListWidget::viewport { padding: 5px; }
        """)
        self.note_list_widget.clicked.connect(self.load_selected_note)
        self.note_list_widget.currentItemChanged.connect(self.load_selected_note)
        self.note_list_widget.itemActivated.connect(self.open_viewer)
        left_column.addWidget(self.note_list_widget)
        content_layout.addLayout(left_column, 1)
        
        # Right column: Image List
        right_column = QVBoxLayout()
        self.note_title = QLineEdit()
        self.note_title.setPlaceholderText("Title")
        right_column.addWidget(self.note_title)

        editor_layout = QHBoxLayout()
        self.note_content = QTextEdit()
        self.note_content.setStyleSheet("""
            QTextEdit:focus { border: 1px solid orange; }
            QTextEdit::viewport { padding: 5px; }
        """)
        editor_layout.addWidget(self.note_content, stretch=3)

        self.imageViewer = ZoomableImageView(self) # show_border defaults to True
        self.imageViewer.setFixedWidth(self.note_list_widget.width())
        editor_layout.addWidget(self.imageViewer, stretch=0)

        right_column.addLayout(editor_layout)
        content_layout.addLayout(right_column, 2)
        
        # Hotkeys
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.new_note)
        QShortcut(QKeySequence("Delete"), self, activated=self.delete_note)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_note)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=lambda: self.search_input.setFocus())
        QShortcut(QKeySequence("Ctrl+Up"), self, activated=self.navigate_up)
        QShortcut(QKeySequence("Ctrl+Down"), self, activated=self.navigate_down)
        QShortcut(QKeySequence("Ctrl+C"), self.note_list_widget, activated=self.open_context_menu_for_current_item)
        
        self.note_title.installEventFilter(self)
        self.note_content.installEventFilter(self)
        
        self.load_notes()
    
        def resizeEvent(self, event):
            self.imagesTab.setFixedWidth(self.note_list_widget.width())
            super().resizeEvent(event)

    
    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Tab:
                self.focusNextChild()
                return True
            elif event.key() == Qt.Key.Key_Backtab:
                self.focusPreviousChild()
                return True
        return super().eventFilter(source, event)
    
    def update_current_note_from_editor(self):
        title = self.note_title.text().strip()
        content = self.note_content.toPlainText().strip()
        if title == "" and content == "":
            return
        if self.current_note_index is not None and 0 <= self.current_note_index < len(self.notes):
            note = self.notes[self.current_note_index]
            if getattr(note, "deleted", False):
                self.current_note_index = None
                return
            if note.title != title or note.content != content:
                note.title = title
                note.content = content
                self.unsaved_changes = True
                self.update_note_list()
        else:
            if title or content:
                new_note = Note(title, content)
                self.notes.append(new_note)
                self.current_note_index = len(self.notes) - 1
                self.unsaved_changes = True
                self.update_note_list()
    
    def addImageToCurrentNote(self, base64_str):
        if self.current_note_index is None:
            new_note = Note("", "", images=[base64_str])
            self.notes.append(new_note)
            self.current_note_index = len(self.notes) - 1
            self.unsaved_changes = True
            self.update_note_list()
        else:
            note = self.notes[self.current_note_index]
            note.images.append(base64_str)
            self.unsaved_changes = True
    
    def new_note(self):
        self.update_current_note_from_editor()
        self.note_title.clear()
        self.note_content.clear()
        self.imageViewer.clearImage()  # Clear the zoomable image viewer
        self.imageViewer.setFixedWidth(self.note_list_widget.width())
        self.current_note_index = None
        self.note_list_widget.clearSelection()
        self.note_title.setFocus()
    
    def load_selected_note(self, current=None, previous=None):
        self.update_current_note_from_editor()
        if current is None:
            items = self.note_list_widget.selectedItems()
            if not items:
                self.imageViewer.clearImage()
                self.imageViewer.setFixedWidth(self.note_list_widget.width())
                return
            current = items[0]
        try:
            index = current.data(Qt.ItemDataRole.UserRole)
        except RuntimeError:
            self.imageViewer.clearImage()
            self.imageViewer.setFixedWidth(self.note_list_widget.width())
            return
        if index is None or not (0 <= index < len(self.notes)):
            self.imageViewer.clearImage()
            self.imageViewer.setFixedWidth(self.note_list_widget.width())
            return
        note = self.notes[index]
        self.current_note_index = index
        self.note_title.setText(note.title)
        self.note_content.setText(note.content)
        self.imageViewer.clearImage()
        self.imageViewer.setFixedWidth(self.note_list_widget.width())
        if note.images:
            ba = QByteArray.fromBase64(note.images[0].encode())
            pixmap = QPixmap()
            pixmap.loadFromData(ba)
            self.imageViewer.setImage(pixmap)
    
    def save_note(self):
        title = self.note_title.text().strip()
        content = self.note_content.toPlainText().strip()
        if title == "" and content == "":
            self.current_note_index = None
            self.unsaved_changes = False
            self.save_notes_to_file()  # This will remove deleted notes.
            return
        if title == "":
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Input Error", "Missing a title")
            return
        if self.current_note_index is None:
            note = Note(title, content)
            self.notes.append(note)
            self.current_note_index = len(self.notes) - 1
        else:
            if getattr(self.notes[self.current_note_index], "deleted", False):
                note = Note(title, content)
                self.notes.append(note)
                self.current_note_index = len(self.notes) - 1
            else:
                self.notes[self.current_note_index].title = title
                self.notes[self.current_note_index].content = content
        self.unsaved_changes = False
        self.update_note_list()
        self.save_notes_to_file()
    
    def delete_note(self):
        items = self.note_list_widget.selectedItems()
        if not items:
            return
        item = items[0]
        index = item.data(Qt.ItemDataRole.UserRole)
        if index is None or index < 0 or index >= len(self.notes):
            return
        self.notes[index].deleted = True
        self.unsaved_changes = True
        if self.current_note_index == index:
            self.current_note_index = None
            self.note_title.clear()
            self.note_content.clear()
            self.imageViewer.clearImage()
        self.update_note_list()
    
    def update_note_list(self):
        self.note_list_widget.clear()
        for i, note in enumerate(self.notes):
            item = QListWidgetItem(note.title)
            item.setData(Qt.ItemDataRole.UserRole, i)
            # If the note is flagged as deleted, show it in red.
            if getattr(note, "deleted", False):
                item.setForeground(QColor("red"))
            self.note_list_widget.addItem(item)

    def search_notes(self):
        self.update_current_note_from_editor()
        query = self.search_input.text().lower()
        self.note_list_widget.clear()
        for i, note in enumerate(self.notes):
            if query in note.title.lower() or query in note.content.lower():
                item = QListWidgetItem(note.title)
                item.setData(Qt.ItemDataRole.UserRole, i)
                self.note_list_widget.addItem(item)
    
    def load_notes(self):
        if not os.path.exists(NOTES_PATH):
            try:
                bundled_notes = os.path.join(sys._MEIPASS, "resources", "notes.json")
            except Exception:
                bundled_notes = os.path.join(os.path.dirname(__file__), "resources", "notes.json")
            if os.path.exists(bundled_notes):
                shutil.copy(bundled_notes, NOTES_PATH)
            else:
                # Create an empty notes file.
                with open(NOTES_PATH, "w", encoding="utf-8") as f:
                    json.dump([], f)
        # Load the notes from NOTES_PATH.
        try:
            with open(NOTES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.notes = [Note(item["title"], item["content"], item.get("images", [])) for item in data]
                self.update_note_list()
        except Exception as e:
            print("Error loading notes:", e)
            self.notes = []
    
    def save_notes_to_file(self):
        # Permanently remove all notes that are flagged as deleted.
        self.notes = [note for note in self.notes if not getattr(note, "deleted", False)]
        data = [{"title": note.title, "content": note.content, "images": note.images} for note in self.notes]
        try:
            with open(NOTES_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.unsaved_changes = False
            self.update_note_list()
        except Exception as e:
            print("Error saving notes:", e)
    
    def open_viewer(self, item):
        index = item.data(Qt.ItemDataRole.UserRole)
        note = self.notes[index]
        viewer = NoteViewer(note)
        viewer.show()
        self.viewers.append(viewer)
    
    def navigate_up(self):
        self.update_current_note_from_editor()
        self.note_list_widget.setFocus()
        count = self.note_list_widget.count()
        if count == 0:
            return
        row = self.note_list_widget.currentRow()
        if row == -1:
            self.note_list_widget.setCurrentRow(0)
        elif row > 0:
            self.note_list_widget.setCurrentRow(row - 1)
    
    def navigate_down(self):
        self.update_current_note_from_editor()
        self.note_list_widget.setFocus()
        count = self.note_list_widget.count()
        if count == 0:
            return
        row = self.note_list_widget.currentRow()
        if row == -1:
            self.note_list_widget.setCurrentRow(0)
        elif row < count - 1:
            self.note_list_widget.setCurrentRow(row + 1)
    
    # Context menu for note list.
    def on_note_list_context_menu(self, pos):
        item = self.note_list_widget.itemAt(pos)
        if not item:
            return
        menu = QMenu(self.note_list_widget)
        export_action = menu.addAction("Export")
        edit_action = menu.addAction("Edit")
        dupe_action = menu.addAction("Dupe")
        
        export_action.triggered.connect(lambda: self.export_note(item))
        edit_action.triggered.connect(lambda: self.edit_note(item))
        dupe_action.triggered.connect(lambda: self.dupe_note(item))
        
        menu.exec(self.note_list_widget.mapToGlobal(pos))
    
    def open_context_menu_for_current_item(self):
        item = self.note_list_widget.currentItem()
        if item:
            rect = self.note_list_widget.visualItemRect(item)
            pos_global = self.note_list_widget.viewport().mapToGlobal(rect.center())
            pos_local = self.note_list_widget.mapFromGlobal(pos_global)
            self.on_note_list_context_menu(pos_local)
    
    def export_note(self, item):
        self.update_current_note_from_editor()
        index = item.data(Qt.ItemDataRole.UserRole)
        note = self.notes[index]
        dlg = ExportDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            ext = dlg.getExtension()
            if ext:
                filename = f"{note.title}.{ext}"
                try:
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(note.content)
                    confirm = CustomInfoDialog(self, title="Export Confirmation", message=f"Note exported as {filename}")
                    confirm.exec()
                except Exception as e:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.warning(self, "Export Error", f"Failed to export note: {e}")
    
    def edit_note(self, item):
        self.note_list_widget.setCurrentItem(item)
        self.load_selected_note(item)
        self.note_content.setFocus()
    
    def dupe_note(self, item):
        self.update_current_note_from_editor()
        index = item.data(Qt.ItemDataRole.UserRole)
        orig = self.notes[index]
        dup_title = f"Copy - {orig.title}"
        dup_note = Note(dup_title, orig.content, orig.images.copy())
        self.notes.append(dup_note)
        self.update_note_list()
        dlg = CustomInfoDialog(self, title="Dupe Confirmation", message=f"Note duplicated as '{dup_title}'")
        dlg.exec()
    
    def closeEvent(self, event):
        self.update_current_note_from_editor()
        if self.unsaved_changes:
            dlg = ClosePromptDialog(self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                if dlg.choice == "save":
                    self.save_notes_to_file()
                    event.accept()
                elif dlg.choice == "quit":
                    event.accept()
                else:
                    event.ignore()
            else:
                event.ignore()
        else:
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
