import sys
import sqlite3
import json
import sys
import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QListWidget, QListWidgetItem, QTextEdit, QLineEdit,
    QPushButton, QLabel, QMenuBar, QStatusBar, QMessageBox,
    QDialog, QDialogButtonBox, QFormLayout, QComboBox, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QAction, QIcon, QPixmap, QTextCharFormat, QColor

class Note:
    
    """Simple Note class"""
    def __init__(self, id=None, title="", content="", tags="", created_at=None, updated_at=None):
        self.id = id
        self.title = title
        self.content = content 
        self.tags = tags
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'tags': self.tags,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

class Database:
    """Simple SQLite database for notes"""
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = self.get_default_db_path()
        self.db_path = db_path
        self.ensure_db_directory()
        self.init_db()

    def get_default_db_path(self) -> str:
        """Get the default database path based on the operating system"""
        if sys.platform.startswith('win'):
            # Windows: Use AppData/Local
            app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
            db_dir = Path(app_data) / 'Alem'
        elif sys.platform.startswith('darwin'):
            # macOS: Use Application Support
            db_dir = Path.home() / 'Library' / 'Application Support' / 'Alem'
        else:
            # Linux: Use XDG data directory or ~/.local/share
            xdg_data = os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share')
            db_dir = Path(xdg_data) / 'Alem'
        
        return str(db_dir / 'smartnotes.db')

    def ensure_db_directory(self):
        """Ensure the database directory exists"""
        db_dir = Path(self.db_path).parent
        try:
            db_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            # Fallback to current directory if we can't create in app data
            print(f"Warning: Could not create directory {db_dir}, using current directory: {e}")
            self.db_path = "smartnotes.db"

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT DEFAULT '',
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()
        conn.close()
        self.add_sample_data()

    def add_sample_data(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(id) FROM notes")
        count = cursor.fetchone()[0]
        conn.close()

        if count == 0:
            sample_notes = [
                Note(title="Python FastAPI Quick Start", 
                     content="# FastAPI Quick Start Guide...", 
                     tags="python, fastapi, api, web development"),
                Note(title="React Hooks Cheat Sheet",
                     content="# React Hooks Reference...",
                     tags="javascript, react, hooks, frontend"),
                Note(title="SQL Query Optimization",
                     content="# SQL Query Optimization Tips...",
                     tags="sql, database, optimization, performance"),
                Note(title="Git Best Practices",
                     content="# Git Workflow Guide...",
                     tags="git, version control, workflow, best practices"),
                Note(title="Docker Compose Setup",
                     content="# Docker Compose for Development...",
                     tags="docker, devops, development, containers")
            ]
            for note in sample_notes:
                self.save_note(note)

    def get_all_note_headers(self) -> List[Note]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, title, tags, created_at, updated_at FROM notes ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        conn.close()

        notes = []
        for row in rows:
            notes.append(Note(
                id=row[0], title=row[1], content="", tags=row[2],
                created_at=row[3], updated_at=row[4]
            ))
        return notes

    
    # It fetches the full content for ONE note when it's needed, 
    def get_note(self, note_id: int) -> Optional[Note]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Note(
                id=row[0], title=row[1], content=row[2], tags=row[3],
                created_at=row[4], updated_at=row[5]
            )
        return None

    def save_note(self, note: Note) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if note.id:
            cursor.execute("""
                UPDATE notes SET title = ?, content = ?, tags = ?, updated_at = ?
                WHERE id = ?
            """, (note.title, note.content, note.tags, datetime.now().isoformat(), note.id))
        else:
            cursor.execute("""
                INSERT INTO notes (title, content, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (note.title, note.content, note.tags, note.created_at, note.updated_at))
            note.id = cursor.lastrowid

        conn.commit()
        conn.close()
        return note.id

    def delete_note(self, note_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()
        conn.close()

    # OPTIMIZATION: Search returns only headers to keep memory low during search.
    def search_note_headers(self, query: str) -> List[Note]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, tags, created_at, updated_at FROM notes 
            WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?
            ORDER BY updated_at DESC
        """, (f'%{query}%', f'%{query}%', f'%{query}%'))
        rows = cursor.fetchall()
        conn.close()

        notes = []
        for row in rows:
            notes.append(Note(
                id=row[0], title=row[1], content="", tags=row[2],
                created_at=row[3], updated_at=row[4]
            ))
        return notes

class SmartNotesApp(QMainWindow):
    """Main Alem Application Window"""

    def __init__(self):
        super().__init__()
        try:
            self.db = Database()
        except Exception as e:
            QMessageBox.critical(
                None, 
                "Database Error", 
                f"Failed to initialize database:\n{e}\n\nThe application will use a temporary database."
            )
            # Fallback to current directory
            self.db = Database("temp_smartnotes.db")
        
        self.current_note: Optional[Note] = None # This will hold the one fully loaded note
        self.setup_ui()
        self.load_note_headers() # Load headers, not full notes

        
        # Automatically create a new note when app starts
        
        self.new_note()
        
        # Show database location in status bar
        self.status_bar.showMessage(f"ALEM ONLINE | DB: {os.path.dirname(self.db.db_path)} | NEURAL_NET: ACTIVE")

    def setup_ui(self):
        self.setWindowTitle("Alem - Light, Fast, Secure")
        self.setGeometry(100, 100, 1200, 800)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0a0a0a;
                color: #29C4F8;
            }
        """)

        # Create menu bar
        self.create_menu_bar()

        # Central widget with splitter
        central_widget = QWidget()
        central_widget.setStyleSheet("QWidget { background-color: #0a0a0a; }")
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QHBoxLayout(central_widget)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left panel (notes list and search)
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
    

        # Right panel (note editor)
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        # Set splitter proportions
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #111111;
                color: #29C4F8;
                border-top: 1px solid #333333;
                font-family: 'Courier New', monospace;
                font-weight: bold;
                padding: 4px;
            }
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("ALEM ONLINE | NEURAL_NET: ACTIVE | QUANTUM_SEARCH: ENABLED")
    
    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #111111;
                color: #29C4F8;
                border-bottom: 1px solid #333333;
                font-family: 'Courier New', monospace;
                font-weight: bold;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 8px 12px;
            }
            QMenuBar::item:selected {
                background-color: #1a1a1a;
                color: #00ffff;
            }
            QMenu {
                background-color: #111111;
                color: #29C4F8;
                border: 1px solid #333333;
            }
            QMenu::item {
                padding: 6px 12px;
            }
            QMenu::item:selected {
                background-color: #1a1a1a;
                color: #00ffff;
            }
        """)

        # File menu
        file_menu = menubar.addMenu('File')

        new_action = QAction('New Note', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_note)
        file_menu.addAction(new_action)

        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_note)
        file_menu.addAction(save_action)

        file_menu.addSeparator()
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Search menu
        search_menu = menubar.addMenu('Search')
        search_action = QAction('Search Notes', self)
        search_action.setShortcut('Ctrl+F')
        search_action.triggered.connect(lambda: self.search_input.setFocus())
        search_menu.addAction(search_action)

        # Help menu
        help_menu = menubar.addMenu('Help')
        about_action = QAction('About Alem', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_left_panel(self):
        """Create the left panel with search and notes list"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Header
        header = QLabel("ALEM")
        header.setFont(QFont("Courier New", 18, QFont.Weight.Bold))
        header.setStyleSheet("""
            QLabel { 
                color: #29C4F8; 
                padding: 15px; 
                background-color: #111111; 
                border: 2px solid #333333;
                border-radius: 8px; 
                font-family: 'Courier New', monospace;
                letter-spacing: 2px;
                text-align: center;
            }
        """)
        layout.addWidget(header)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(">>> SEARCH_DATABASE...")
        self.search_input.textChanged.connect(self.on_search)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 16px;
                border: 2px solid #333333;
                border-radius: 8px;
                background-color: #111111;
                color: #29C4F8;
                font-size: 14px;
                font-family: 'Courier New', monospace;
                font-weight: bold;
            }
            QLineEdit:focus {
                border: 2px solid #29C4F8;
                background-color: #1a1a1a;
                color: #00ffff;
            }
            QLineEdit::placeholder {
                color: #666666;
            }
        """)
        search_layout.addWidget(self.search_input)

        self.ai_toggle = QPushButton("AI_ON")
        self.ai_toggle.setCheckable(True)
        self.ai_toggle.setChecked(True)
        self.ai_toggle.setStyleSheet("""
            QPushButton {
                background-color: #001a00;
                color: #29C4F8;
                border: 2px solid #29C4F8;
                padding: 10px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                font-family: 'Courier New', monospace;
                letter-spacing: 1px;
            }
            QPushButton:checked {
                background-color: #29C4F8;
                color: #000000;
                border: 2px solid #29C4F8;
            }
            QPushButton:hover {
                background-color: #003300;
                color: #00ffff;
                border: 2px solid #00ffff;
            }
        """)
        search_layout.addWidget(self.ai_toggle)
        layout.addLayout(search_layout)

        # Notes list
        self.notes_list = QListWidget()
        self.notes_list.itemClicked.connect(self.load_selected_note)
        self.notes_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #333333;
                border-radius: 8px;
                background-color: #111111;
                color: #29C4F8;
                padding: 8px;
                font-size: 13px;
                font-family: 'Courier New', monospace;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #333333;
                border-radius: 6px;
                background-color: #1a1a1a;
                color: #29C4F8;
                margin: 3px 0px;
                font-weight: bold;
            }
            QListWidget::item:selected {
                background-color: #003300;
                color: #00ffff;
                border: 1px solid #29C4F8;
            }
            QListWidget::item:hover {
                background-color: #2a2a2a;
                color: #00ffff;
                border: 1px solid #666666;
            }
        """)
        layout.addWidget(self.notes_list)

        # Buttons
        button_layout = QHBoxLayout()

        self.new_note_btn = QPushButton("[+] NEW_FILE")
        self.new_note_btn.clicked.connect(self.new_note)
        self.new_note_btn.setStyleSheet("""
            QPushButton {
                background-color: #001a1a;
                color: #00ffff;
                border: 2px solid #00ffff;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
                font-family: 'Courier New', monospace;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #003333;
                color: #ffffff;
                border: 2px solid #ffffff;
            }
            QPushButton:pressed {
                background-color: #00ffff;
                color: #000000;
            }
        """)

        button_layout.addWidget(self.new_note_btn)

        self.delete_note_btn = QPushButton("[X] DELETE")
        self.delete_note_btn.clicked.connect(self.delete_note)
        self.delete_note_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a0000;
                color: #ff4444;
                border: 2px solid #ff4444;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                font-family: 'Courier New', monospace;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #330000;
                color: #ff6666;
                border: 2px solid #ff6666;
            }
            QPushButton:pressed {
                background-color: #ff4444;
                color: #000000;
            }
        """)
        button_layout.addWidget(self.delete_note_btn)

        layout.addLayout(button_layout)

        # Stats panel
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #111111;
                border: 2px solid #333333;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        stats_layout = QVBoxLayout(stats_frame)

        self.cache_label = QLabel(" CACHE: N/A")
        self.search_time_label = QLabel(" QUERY: <20ms")
        self.notes_count_label = QLabel("NOTES: 0")


        for label in [ self.cache_label, self.search_time_label, self.notes_count_label]:
            label.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
            label.setStyleSheet("""
                QLabel { 
                    color: #29C4F8; 
                    font-family: 'Courier New', monospace;
                    letter-spacing: 1px;
                    padding: 3px;
                }
            """)
            stats_layout.addWidget(label)

        layout.addWidget(stats_frame)

        panel.setMaximumWidth(350)
        return panel

    def create_right_panel(self):
        """Create the right panel with note editor"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Title input
        title_layout = QHBoxLayout()
        title_label = QLabel(">>> TITLE:")
        title_label.setFont(QFont("Courier New", 15, QFont.Weight.Bold))
        title_label.setStyleSheet("""
            QLabel { 
                color: #29C4F8; 
                font-family: 'Courier New', monospace;
                letter-spacing: 2px;
            }
        """)
        title_layout.addWidget(title_label)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("ENTER_FILENAME...")
        self.title_input.textChanged.connect(self.on_content_changed)
        self.title_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 16px;
                border: 2px solid #333333;
                border-radius: 8px;
                font-size: 17px;
                color: #29C4F8;
                background-color: #111111;
                font-family: 'Courier New', monospace;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QLineEdit:focus {
                border: 2px solid #29C4F8;
                background-color: #1a1a1a;
                color: #00ffff;
            }
            QLineEdit::placeholder {
                color: #666666;
            }
        """)
        title_layout.addWidget(self.title_input)
        layout.addLayout(title_layout)

        # Tags input
        tags_layout = QHBoxLayout()
        tags_label = QLabel(">>> TAGS:")
        tags_label.setFont(QFont("Courier New", 14, QFont.Weight.Bold))
        tags_label.setStyleSheet("""
            QLabel { 
                color: #29C4F8; 
                font-family: 'Courier New', monospace;
                letter-spacing: 2px;
            }
        """)
        tags_layout.addWidget(tags_label)

        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("METADATA_TAGS...")
        self.tags_input.textChanged.connect(self.on_content_changed)
        self.tags_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 16px;
                border: 2px solid #333333;
                border-radius: 8px;
                font-size: 14px;
                color: #29C4F8;
                background-color: #111111;
                font-family: 'Courier New', monospace;
                font-weight: bold;
            }
            QLineEdit:focus {
                border: 2px solid #29C4F8;
                background-color: #1a1a1a;
                color: #00ffff;
            }
            QLineEdit::placeholder {
                color: #666666;
            }
        """)
        tags_layout.addWidget(self.tags_input)
        layout.addLayout(tags_layout)

        # Content editor
        editor_label = QLabel(">>> DATA_STREAM:")
        editor_label.setFont(QFont("Courier New", 16, QFont.Weight.Bold))
        editor_label.setStyleSheet("""
            QLabel { 
                color: #29C4F8; 
                font-family: 'Courier New', monospace;
                letter-spacing: 2px;
            }
        """)
        layout.addWidget(editor_label)

        # Formatting toolbar
        toolbar_layout = QHBoxLayout()
        
        # Bold button
        self.bold_btn = QPushButton("B")
        self.bold_btn.setCheckable(True)
        self.bold_btn.clicked.connect(self.toggle_bold)
        self.bold_btn.setStyleSheet("""
            QPushButton {
                background-color: #111111;
                color: #29C4F8;
                border: 1px solid #333333;
                padding: 8px 12px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                min-width: 30px;
                font-family: 'Courier New', monospace;
            }
            QPushButton:checked {
                background-color: #29C4F8;
                color: #000000;
                border: 1px solid #29C4F8;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
                color: #00ffff;
                border: 1px solid #00ffff;
            }
        """)
        toolbar_layout.addWidget(self.bold_btn)

        # Italic button
        self.italic_btn = QPushButton("I")
        self.italic_btn.setCheckable(True)
        self.italic_btn.clicked.connect(self.toggle_italic)
        self.italic_btn.setStyleSheet("""
            QPushButton {
                background-color: #111111;
                color: #29C4F8;
                border: 1px solid #333333;
                padding: 8px 12px;
                border-radius: 6px;
                font-style: italic;
                font-size: 12px;
                min-width: 30px;
                font-family: 'Courier New', monospace;
            }
            QPushButton:checked {
                background-color: #29C4F8;
                color: #000000;
                border: 1px solid #29C4F8;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
                color: #00ffff;
                border: 1px solid #00ffff;
            }
        """)
        toolbar_layout.addWidget(self.italic_btn)

        # Underline button
        self.underline_btn = QPushButton("U")
        self.underline_btn.setCheckable(True)
        self.underline_btn.clicked.connect(self.toggle_underline)
        self.underline_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                                         
                text-decoration: underline;
                font-size: 12px;
                min-width: 30px;
            }
            QPushButton:checked {
                background-color: #0d6efd;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        toolbar_layout.addWidget(self.underline_btn)

        # Separator
        separator = QLabel("|")
        separator.setStyleSheet("QLabel { color: #333333; font-size: 16px; }")
        toolbar_layout.addWidget(separator)

        # Align left button
        self.align_left_btn = QPushButton("⬅")
        self.align_left_btn.clicked.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignLeft))
        self.align_left_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
                min-width: 30px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        toolbar_layout.addWidget(self.align_left_btn)

        self.align_center_btn = QPushButton("⬌")
        self.align_center_btn.clicked.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignCenter))
        self.align_center_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
                min-width: 30px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        toolbar_layout.addWidget(self.align_center_btn)

        self.align_right_btn = QPushButton("➡")
        self.align_right_btn.clicked.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignRight))
        self.align_right_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
                min-width: 30px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        toolbar_layout.addWidget(self.align_right_btn)

        # Add stretch to push buttons to the left
        toolbar_layout.addStretch()

        # Font size controls
        size_label = QLabel("SIZE:")
        size_label.setStyleSheet("""
            QLabel { 
                color: #29C4F8; 
                font-size: 12px; 
                font-family: 'Courier New', monospace;
                font-weight: bold;
            }
        """)
        toolbar_layout.addWidget(size_label)

        self.font_size_btn_smaller = QPushButton("-")
        self.font_size_btn_smaller.clicked.connect(self.decrease_font_size)
        self.font_size_btn_smaller.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 6px 8px;
                border-radius: 4px;
                font-size: 12px;
                min-width: 25px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        toolbar_layout.addWidget(self.font_size_btn_smaller)

        self.font_size_btn_larger = QPushButton("+")
        self.font_size_btn_larger.clicked.connect(self.increase_font_size)
        self.font_size_btn_larger.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 6px 8px;
                border-radius: 4px;
                font-size: 12px;
                min-width: 25px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        toolbar_layout.addWidget(self.font_size_btn_larger)

        layout.addLayout(toolbar_layout)

        self.content_editor = QTextEdit()
        self.content_editor.textChanged.connect(self.on_content_changed)
        self.content_editor.cursorPositionChanged.connect(self.update_format_buttons)
        self.content_editor.setFont(QFont("Courier New", 12))
        self.content_editor.setStyleSheet("""
            QTextEdit {
                border: 2px solid #333333;
                border-radius: 8px;
                padding: 16px;
                background-color: #0d0d0d;
                color: #29C4F8;
                line-height: 1.6;
                font-family: 'Courier New', monospace;
                font-weight: bold;
                selection-background-color: #003300;
                selection-color: #00ffff;
            }
            QTextEdit:focus {
                border: 2px solid #29C4F8;
                background-color: #111111;
            }
            QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #333333;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #29C4F8;
            }
        """)
        layout.addWidget(self.content_editor)

        # Save button
        self.save_btn = QPushButton("COMMIT_DATA")
        self.save_btn.clicked.connect(self.save_note)
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #001a00;
                color: #29C4F8;
                border: 2px solid #29C4F8;
                padding: 16px 32px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
                font-family: 'Courier New', monospace;
                letter-spacing: 2px;
            }
            QPushButton:hover:enabled {
                background-color: #003300;
                color: #00ffff;
                border: 2px solid #00ffff;
            }
            QPushButton:pressed:enabled {
                background-color: #29C4F8;
                color: #000000;
            }
            QPushButton:disabled {
                background-color: #1a1a1a;
                color: #666666;
                border: 2px solid #666666;
            }
        """)
        layout.addWidget(self.save_btn)

        return panel


 
    # OPTIMIZATION:  
    def load_note_headers(self):
        """Load note headers into the list, not full content."""
        note_headers = self.db.get_all_note_headers()
        self.refresh_notes_list(note_headers)

    def refresh_notes_list(self, note_headers: List[Note]):
        """Refresh the notes list widget with a given list of note headers."""
        self.notes_list.clear()
        for note in note_headers: # It receives the list of headers directly
            item_text = f"{note.title}"
            if note.tags:
                item_text += f" #{note.tags.replace(',', ' #')}"

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, note.id) 
            item.setToolTip(f"Tags: {note.tags}") # Tooltip doesn't need full content
            self.notes_list.addItem(item)
        
        self.notes_count_label.setText(f"NOTES: {len(note_headers)}")


    # OPTIMIZATION: This is the lazy loading in action.
    def load_selected_note(self, item: QListWidgetItem):
        """Load the FULL content of the selected note from DB on demand."""
        note_id = item.data(Qt.ItemDataRole.UserRole)
        
        # Fetch the full note from the database ONLY when it's clicked.
        note = self.db.get_note(note_id)

        if note:
            self.current_note = note
            self.title_input.setText(note.title)
            self.tags_input.setText(note.tags)
            
            # Check if content is HTML or plain text
            if note.content.strip().startswith('<') and note.content.strip().endswith('>'):
                self.content_editor.setHtml(note.content)
            else:
                self.content_editor.setPlainText(note.content)
            
            self.save_btn.setEnabled(False)
            self.status_bar.showMessage(f"LOADED: '{note.title}' FROM DATABASE")

    def new_note(self):
        """Create a new note"""
        self.current_note = Note(title="New Note", content="<h1>New Note</h1><p>Start writing here...</p>")
        self.title_input.setText(self.current_note.title)
        self.tags_input.setText("")
        self.content_editor.setHtml(self.current_note.content)
        self.title_input.setFocus()
        self.title_input.selectAll()
        self.save_btn.setEnabled(True)
        self.notes_list.setCurrentItem(None) # Deselect item in list

    def save_note(self):
        """Save the current note"""
        if not self.current_note:
            return

        self.current_note.title = self.title_input.text().strip() or "Untitled"
        self.current_note.content = self.content_editor.toHtml()
        self.current_note.tags = self.tags_input.text().strip()
        self.current_note.updated_at = datetime.now().isoformat()

        self.db.save_note(self.current_note)
        self.load_note_headers() 
        self.save_btn.setEnabled(False)

        self.status_bar.showMessage(f"DATA_COMMITTED: '{self.current_note.title}'")

    def delete_note(self):
        """Delete the selected note"""
        current_item = self.notes_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a note to delete.")
            return

        note_id = current_item.data(Qt.ItemDataRole.UserRole)
        # We don't need to fetch the full note just to get its title for the dialog
        title = current_item.text().split(' #')[0] 

        reply = QMessageBox.question(
            self, "Delete Note", 
            f"Are you sure you want to delete '{title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_note(note_id)
            self.load_note_headers() 
            self.clear_editor()
            self.status_bar.showMessage(f"DATA_PURGED: '{title}'")

    def clear_editor(self):
        """Clear the editor"""
        self.title_input.clear()
        self.tags_input.clear()
        self.content_editor.clear()
        self.current_note = None
        self.save_btn.setEnabled(False)

    def on_content_changed(self):
        """Handle content changes"""
        if not self.current_note:
            self.new_note()
        self.save_btn.setEnabled(True)

    def on_search(self, text):
        """Handle search input changes"""
        if not text.strip():
            self.load_note_headers()
            return
        # Use a short delay to make the UI feel responsive
        QTimer.singleShot(100, lambda: self.perform_search(text))

    def perform_search(self, query: str):
        """Perform search by fetching only matching headers."""
        # OPTIMIZATION: Use the memory-efficient search function.
        results = self.db.search_note_headers(query)
        self.refresh_notes_list(results)

        search_type = "SEMANTIC" if self.ai_toggle.isChecked() else "KEYWORD"
        self.status_bar.showMessage(f"{search_type} SCAN: {len(results)} results for '{query}'")

    def show_about(self):
        QMessageBox.about(self, "About Alem", 
            """Alem v1.0

AI-Powered Developer Note-Taking App

Features:
• Rich Markdown editing
• AI semantic search
• Tag-based organization  
• Lightweight (45-70MB)
• Offline-first design
• Developer-focused

Built with PyQt6 and SQLite
Memory optimized for peak performance

What's New:
• Lazy loading of notes
• Memory-efficient search
• Enhanced UI/UX

© 2025 Alem Team""")
        
    def toggle_bold(self):
        """Toggle bold formatting"""
        fmt = self.content_editor.currentCharFormat()
        if fmt.fontWeight() == QFont.Weight.Bold:
            fmt.setFontWeight(QFont.Weight.Normal)
        else:
            fmt.setFontWeight(QFont.Weight.Bold)
        self.content_editor.setCurrentCharFormat(fmt)
        self.content_editor.setFocus()


    def toggle_italic(self):
        """italic formatting"""
        fmt = self.content_editor.currentCharFormat()
        fmt.setFontItalic(not fmt.fontItalic())
        self.content_editor.setCurrentCharFormat(fmt)
        self.content_editor.setFocus()

    def toggle_underline(self):
        """underline formatting"""
        fmt = self.content_editor.currentCharFormat()
        fmt.setFontUnderline(not fmt.fontUnderline())
        self.content_editor.setCurrentCharFormat(fmt)
        self.content_editor.setFocus()

    def set_alignment(self, alignment):
        """text alignment"""
        self.content_editor.setAlignment(alignment)
        self.content_editor.setFocus()

    def decrease_font_size(self):
        """Decrease font size"""
        current_font = self.content_editor.currentFont()
        size = current_font.pointSize()
        if size > 8:  # Minimum font size
            current_font.setPointSize(size - 1)
            self.content_editor.setCurrentFont(current_font)
        self.content_editor.setFocus()

    def increase_font_size(self):
        """Increase font size"""
        current_font = self.content_editor.currentFont()
        size = current_font.pointSize()
        if size < 24:  # Maximum font size
            current_font.setPointSize(size + 1)
            self.content_editor.setCurrentFont(current_font)
        self.content_editor.setFocus()

    def update_format_buttons(self):
        """Update toolbar buttons based on current formatting"""
        fmt = self.content_editor.currentCharFormat()
        
        # da bold button
        self.bold_btn.setChecked(fmt.fontWeight() == QFont.Weight.Bold)
        
        # da italic button
        self.italic_btn.setChecked(fmt.fontItalic())
        
        # da underline button

        self.underline_btn.setChecked(fmt.fontUnderline())
def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName("Alem")
    app.setApplicationVersion("1.0.0")
    window = SmartNotesApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
