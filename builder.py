import sys
import os  
import markdown2
import urllib.request
import urllib.error
import urllib.parse
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QPushButton, QSplitter, QDialog, QLabel, QLineEdit, 
    QFrame, QMessageBox, QListWidget, QInputDialog, QListWidgetItem
)
from PySide6.QtCore import Qt, QUrl, QPoint, QPropertyAnimation, QEasingCurve, QTimer, QSize
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage
from PySide6.QtGui import QIcon, QFont, QPalette, QColor

GITHUB_DARK_CSS = """
<style>
    body { 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Tahoma", "Microsoft YaHei", "Arial", sans-serif;
        font-size: 16px; line-height: 1.6; color: #c9d1d9; background-color: #0d1117; padding: 24px; 
        max-width: 1012px; margin: 0 auto;
    }
    h1, h2, h3, h4, h5, h6 { margin-top: 24px; margin-bottom: 16px; font-weight: 600; line-height: 1.25; color: #c9d1d9; }
    h1 { font-size: 2em; border-bottom: 1px solid #21262d; padding-bottom: 0.3em; }
    h2 { font-size: 1.5em; border-bottom: 1px solid #21262d; padding-bottom: 0.3em; }
    p { margin-top: 0; margin-bottom: 16px; }
    code { 
        font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace; 
        background-color: rgba(110,118,129,0.4); padding: 0.2em 0.4em; border-radius: 6px; font-size: 85%; 
    }
    pre { background-color: #161b22; border-radius: 6px; padding: 16px; overflow: auto; border: 1px solid #30363d; margin-bottom: 16px; }
    pre code { background-color: transparent; padding: 0; margin: 0; font-size: 100%; color: inherit; border: none; }
    img { max-width: 100%; box-sizing: content-box; border-radius: 6px; cursor: pointer; }
    blockquote { padding: 0 1em; color: #8b949e; border-left: 0.25em solid #30363d; margin: 0 0 16px 0; }
    table { border-spacing: 0; border-collapse: collapse; width: 100%; margin-bottom: 16px; }
    table th, table td { padding: 6px 13px; border: 1px solid #30363d; }
    table tr:nth-child(2n) { background-color: #161b22; }
    a { color: #58a6ff; text-decoration: none; }
    a:hover { text-decoration: underline; }
    hr { height: 0.25em; padding: 0; margin: 24px 0; background-color: #30363d; border: 0; }
    
    /* Pygments Highlight Styles */
    .highlight .hll { background-color: #6e7681 }
    .highlight { background: #0d1117; color: #E6EDF3 }    
    .highlight .c { color: #8B949E; font-style: italic }
    .highlight .k { color: #FF7B72 }
    .highlight .s { color: #A5D6FF }
    .highlight .nf { color: #D2A8FF; font-weight: bold }
    .highlight .nb { color: #E6EDF3 }
    .highlight .nc { color: #F0883E; font-weight: bold }
    .highlight .nn { color: #FF7B72 }
    .highlight .nv { color: #79C0FF }
    .highlight .nt { color: #7EE787 }
    .highlight .kd { color: #FF7B72 }
    .highlight .kn { color: #FF7B72 }
    .highlight .o { color: #FF7B72; font-weight: bold }
    .highlight .p { color: #E6EDF3 }
    
    .markdown-alert { padding: 8px 16px; margin-bottom: 16px; border-left: 0.25em solid; border-radius: 0 6px 6px 0; }
    .markdown-alert-note { border-left-color: #2f81f7; background-color: rgba(47,129,247,0.1); }
    .markdown-alert-warning { border-left-color: #d29922; background-color: rgba(210,153,34,0.1); }
</style>
"""



class SuggestionPopup(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(400)
        self.setStyleSheet("""
            QListWidget {
                background-color: #1e1e20; 
                border: 1px solid #333336;
                border-radius: 8px; 
                color: #e5e5e7; 
                font-size: 14px;
                padding: 4px;
                outline: none;
            }
            QListWidget::item { 
                padding: 8px 12px; 
                border-radius: 4px;
                margin-bottom: 2px;
            }
            QListWidget::item:selected { 
                background-color: #333336; 
                color: #ffffff; 
            }
        """)
        self.hide()
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(150)
        
    def showEvent(self, event):
        self.setWindowOpacity(0)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()
        super().showEvent(event)

class SmartEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.popup = SuggestionPopup(self)
        self.popup.itemClicked.connect(self.insert_suggestion)
        
        self.data = {
            "📸 Screenshots": "## 📸 Screenshots\n| Preview 1 | Preview 2 |\n|---|---|\n| ![Img1](example/1.png) | ![Img2](example/2.png) |\n",
            "✨ Features": "## ✨ Features\n- 🚀 **High Performance:** Optimized core for maximum speed.\n- 🎨 **Modern UI:** Clean and intuitive minimal style.\n- 🔒 **Secure:** End-to-end data encryption.\n",
            "📝 Description": "## 📝 Description\nThis project is a powerful tool designed to streamline your workflow and enhance productivity by providing...\n",
            "🛠 Installation": "## 🛠 Installation\n1. **Clone the repo:**\n```bash\ngit clone https://github.com/user/repo.git\n```\n2. **Install dependencies:**\n```bash\npip install -r requirements.txt\n```\n",
            "🚀 Author": "### 👤 Author\nDeveloped by **Name** - [GitHub Profile](https://github.com/)\n",
            "🚨 WARNING": "> [!WARNING]\n> This software is for educational purposes only. Use it at your own risk!\n",
            "💡 Pro Note": "> [!NOTE]\n> Don't forget to star the repository if you find this tool useful! ⭐\n"
        }
        self.refresh_popup_items()

    def refresh_popup_items(self):
        self.popup.clear()
        for key in self.data.keys():
            self.popup.addItem(key)

    def save_custom_snippet(self):
        # الحصول على النص المظلل وتعديله
        selected_text = self.textCursor().selectedText()
        selected_text = selected_text.replace('\u2029', '\n') 
        
        if not selected_text.strip():
            QMessageBox.warning(self, "تنبيه", "قم بتظليل النص أولاً لحفظه كاختصار!")
            return
            
        name, ok = QInputDialog.getText(self, "حفظ اختصار جديد", "أدخل اسماً لهذا الاختصار:")
        if ok and name:
            custom_name = f"📌 {name}"
            self.data[custom_name] = selected_text
            self.refresh_popup_items()
            QMessageBox.information(self, "نجاح", f"تم حفظ الاختصار بنجاح! اضغط Tab في أي وقت لتجده.")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab:
            cursor_rect = self.cursorRect()
            pos = self.mapToGlobal(QPoint(cursor_rect.right() + 15, cursor_rect.bottom() + 10))
            self.popup.move(pos)
            self.popup.show()
            self.popup.setFocus()
            self.popup.setCurrentRow(0)
        elif self.popup.isVisible() and event.key() in (Qt.Key_Enter, Qt.Key_Return):
            self.insert_suggestion(self.popup.currentItem())
        elif self.popup.isVisible() and event.key() == Qt.Key_Escape:
            self.popup.hide()
            self.setFocus()
        else:
            super().keyPressEvent(event)

    def insert_suggestion(self, item):
        if item:
            self.insertPlainText(self.data[item.text()])
            self.popup.hide()
            self.setFocus()

class EmojiPicker(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setFixedWidth(250)
        self.setFixedHeight(300)
        self.setViewMode(QListWidget.IconMode)
        self.setGridSize(QSize(45, 45))
        self.setMovement(QListWidget.Static)
        self.setSpacing(2)
        
        self.setStyleSheet("""
            QListWidget {
                background-color: #1e1e20; border: 1px solid #333336;
                border-radius: 8px; color: #e5e5e7; outline: none; padding: 5px;
            }
            QListWidget::item { border-radius: 4px; }
            QListWidget::item:hover { background-color: #333336; }
        """)
        
        emojis = ["🚀", "✨", "📝", "🛠", "📸", "🚨", "💡", "📦", "🔥", "🎨", "🔒", "👤", "⭐", "✅", "❌", "🔗", "📖", "⚙️", "📱", "💻", "🌐", "⚡", "🌈", "🎉"]
        for e in emojis:
            item = QListWidgetItem(e)
            item.setTextAlignment(Qt.AlignCenter)
            item.setFont(QFont("Segoe UI Emoji", 18))
            self.addItem(item)
            
        self.hide()

    def show_at_cursor(self, editor):
        cursor_rect = editor.cursorRect()
        pos = editor.mapToGlobal(QPoint(cursor_rect.right() + 10, cursor_rect.bottom() + 10))
        self.move(pos)
        self.show()
        self.setFocus()

class SetupWizard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✨ Setup Wizard")
        self.setFixedSize(500, 480)
        self.setStyleSheet("""
            QDialog { background-color: #1a1a1c; color: white; }
            QLabel { font-size: 13px; color: #a1a1aa; margin-top: 5px; font-weight: 500; font-family:-apple-system; }
            QLineEdit { 
                background-color: #27272a; border: 1px solid #3f3f46; border-radius: 6px; 
                padding: 10px 12px; color: #f4f4f5; font-size: 14px; margin-bottom: 5px;
            }
            QLineEdit:focus { border: 1px solid #8b5cf6; background-color: #27272a; }
            QPushButton { 
                background-color: #8b5cf6; color: white; border-radius: 6px; 
                padding: 12px; font-weight: bold; font-size: 14px; border: none;
                margin-top: 15px; margin-bottom: 10px;
            }
            QPushButton:hover { background-color: #7c3aed; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(5)
        
        header = QLabel("Quick README Setup")
        header.setStyleSheet("font-size: 20px; color: #ffffff; margin-bottom: 15px; font-weight: bold; margin-top:0px;")
        layout.addWidget(header)

        self.inputs = {}
        fields = [("Project Name", "e.g. My Awesome App"), ("Description", "What it does..."), 
                  ("GitHub Username", "username"), ("Repository Name", "repo"), ("Install Command", "pip install ...")]

        for label_text, placeholder in fields:
            lbl = QLabel(label_text)
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            layout.addWidget(lbl)
            layout.addWidget(inp)
            self.inputs[label_text] = inp

        layout.addStretch()
        self.btn_finish = QPushButton("Create Masterpiece 🚀")
        self.btn_finish.clicked.connect(self.accept)
        layout.addWidget(self.btn_finish)

    def get_data(self):
        return {k: v.text() for k, v in self.inputs.items()}

class ReadmeEditor(QMainWindow):
    def __init__(self, workspace_dir=None):
        super().__init__()
        self.workspace_dir = os.path.abspath(workspace_dir or os.getcwd())
        
        self.setWindowTitle("Readme Builder")
        self.resize(1000, 750)
        
        # Set Window Icon
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.setStyleSheet("""
            QMainWindow { background-color: #131314; }
            QSplitter::handle { background-color: transparent; width: 0px; }
            QTextEdit {
                background-color: #131314; color: #e5e5e7;
                border: none; font-size: 15px; padding: 20px;
                font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
                line-height: 1.6;
            }
            QScrollBar:vertical {
                border: none; background: #131314; width: 6px; margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #3a3a3c; min-height: 30px; border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover { background: #5a5a5c; }
            QFrame#topBar {
                background-color: #1a1a1c; border-bottom: 1px solid #2c2c2e; padding: 0px;
            }
            QPushButton {
                background-color: #27272a; color: #a1a1aa; border: 1px solid #3f3f46;
                border-radius: 6px; padding: 6px 10px; font-size: 13px; font-weight: 500; font-family: -apple-system, sans-serif;
            }
            QPushButton:hover { background-color: #3f3f46; color: #ffffff; border-color: #52525b; }
            QPushButton#toolBtn { background-color: #1a1a1c; border-color: #2c2c2e; padding: 4px 8px; }
            QPushButton#primary { background-color: #8b5cf6; color: #ffffff; border: none; padding: 8px 16px; font-weight: bold; }
            QPushButton#primary:hover { background-color: #7c3aed; }
            QPushButton#actionBtn { background-color: #1e1e20; color: #58a6ff; border: 1px solid #30363d; padding: 8px 16px;}
            QPushButton#actionBtn:hover { background-color: #2c2c2e; border-color: #58a6ff; }
            QPushButton#saveSnippet { color: #facc15; border-color: #854d0e; }
            QPushButton#saveSnippet:hover { background-color: rgba(250, 204, 21, 0.1); }
        """)

        central = QWidget()
        central.setStyleSheet("background-color: #131314;")
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Horizontal)
        self.editor = SmartEditor()
        self.emoji_picker = EmojiPicker(self)
        self.emoji_picker.itemClicked.connect(self.insert_emoji)

        self.setup_topbar()
        
        # Debouncing
        self.render_timer = QTimer()
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self.update_preview)
        self.editor.textChanged.connect(lambda: self.render_timer.start(500))
        
        self.preview = QWebEngineView()
        self.page = QWebEnginePage(self.preview)
        self.preview.setPage(self.page)
        
        settings = self.preview.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.AutoLoadImages, True)
        
        self.preview.setStyleSheet("background-color: #0d1117;")
        
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        
        self.splitter.setSizes([600, 600])
        self.splitter.setHandleWidth(2)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #2c2c2e; }")
        self.main_layout.addWidget(self.splitter)

        self.set_default_template()

    def setup_topbar(self):
        topbar = QFrame()
        topbar.setObjectName("topBar")
        topbar.setFixedHeight(50)
        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(8)

        # Add Icon to Topbar
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        if os.path.exists(icon_path):
            icon_label = QLabel()
            pixmap = QIcon(icon_path).pixmap(24, 24)
            icon_label.setPixmap(pixmap)
            icon_label.setStyleSheet("margin-right: 5px;")
            layout.addWidget(icon_label)
        
        # App Title
        app_title = QLabel("README Builder")
        app_title.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 14px; margin-right: 15px;")
        layout.addWidget(app_title)

        # Markdown Tools Group
        tools_layout = QHBoxLayout()
        tools_layout.setSpacing(4)
        
        tools = [
            ("H1", "# "), ("H2", "## "), ("B", "**text**"), ("I", "*text*"),
            ("Quote", "> "), ("Strike", "~~text~~"), ("Code", "```python\n\n```"),
            ("Img", "![Alt](example/1.png)"), ("Table", "\n| H1 | H2 |\n|---|---|\n| C1 | C2 |\n")
        ]
        
        for name, code in tools:
            btn = QPushButton(name)
            btn.setObjectName("toolBtn")
            btn.setFixedWidth(50) if len(name) <= 2 else btn.setFixedWidth(65)
            btn.clicked.connect(lambda ch, c=code: self.editor.insertPlainText(c))
            tools_layout.addWidget(btn)
        
        layout.addLayout(tools_layout)

        sep = QFrame(); sep.setFrameShape(QFrame.VLine); sep.setFixedWidth(1); sep.setStyleSheet("background-color: #2c2c2e; margin: 10px 5px;"); layout.addWidget(sep)
        
        import_btn = QPushButton("⌘ Import")
        import_btn.clicked.connect(self.import_github_readme)
        layout.addWidget(import_btn)
        
        save_snippet_btn = QPushButton("💾 حفظ كاختصار")
        save_snippet_btn.setObjectName("saveSnippet")
        save_snippet_btn.clicked.connect(self.editor.save_custom_snippet)
        layout.addWidget(save_snippet_btn)

        emoji_btn = QPushButton("😀 Emojis")
        emoji_btn.clicked.connect(lambda: self.emoji_picker.show_at_cursor(self.editor))
        layout.addWidget(emoji_btn)

        toc_btn = QPushButton("📑 TOC")
        toc_btn.setToolTip("Generate Table of Contents")
        toc_btn.clicked.connect(self.generate_toc)
        layout.addWidget(toc_btn)

        layout.addStretch()

        wiz_btn = QPushButton("✨ Wizard")
        wiz_btn.setObjectName("primary")
        wiz_btn.clicked.connect(self.run_wizard)
        layout.addWidget(wiz_btn)
        
        save_btn = QPushButton("Save & Exit")
        save_btn.setObjectName("actionBtn")
        save_btn.clicked.connect(self.save_to_folder)
        layout.addWidget(save_btn)
        
        self.main_layout.addWidget(topbar)

    def update_preview(self):
        md = self.editor.toPlainText()
        # Enable pygments for offline syntax highlighting
        html = markdown2.markdown(md, extras=["fenced-code-blocks", "tables", "task_list", "strike", "code-friendly", "pygments"])
        
        replacements = {
            "> [!NOTE]": '<div class="markdown-alert markdown-alert-note"><span class="markdown-alert-title">Note</span>',
            "> [!WARNING]": '<div class="markdown-alert markdown-alert-warning"><span class="markdown-alert-title">Warning</span>'
        }
        for o, n in replacements.items(): 
            html = html.replace(o, n)
        
        base_url = QUrl.fromLocalFile(self.workspace_dir + os.sep)
        full_html = f"<!DOCTYPE html><html><head><meta charset='UTF-8'>{GITHUB_DARK_CSS}</head><body>{html}</body></html>"
        self.preview.setHtml(full_html, base_url)

    def run_wizard(self):
        wiz = SetupWizard(self)
        if wiz.exec() == QDialog.Accepted:
            d = wiz.get_data()
            project_name = d.get('Project Name') or 'Project'
            description = d.get('Description') or 'No description provided'
            install_cmd = d.get('Install Command') or 'pip install ...'
            content = f"# {project_name}\n\n## 📝 Description\n{description}\n\n## 🛠 Installation\n```bash\n{install_cmd}\n```\n\n## ✨ Features\n- [x] Feature one\n- [ ] Feature two\n"
            self.editor.setPlainText(content)

    def save_to_folder(self):
        filepath = os.path.join(self.workspace_dir, "README.md")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save:\n{str(e)}")

    def import_github_readme(self):
        url, ok = QInputDialog.getText(self, "Import README", "Enter GitHub Repo URL:")
        if ok and url:
            raw_url = url.strip()
            if "github.com" in raw_url and "raw.githubusercontent" not in raw_url:
                raw_url = raw_url.replace("github.com", "raw.githubusercontent.com")
                if "/blob/" in raw_url:
                    raw_url = raw_url.replace("/blob/", "/")
                else:
                    if not raw_url.endswith("/"): raw_url += "/"
                    raw_url += "main/README.md"
            try:
                req = urllib.request.Request(raw_url)
                try:
                    resp = urllib.request.urlopen(req)
                except urllib.error.HTTPError as e:
                    if e.code == 404 and "main" in raw_url:
                        raw_url = raw_url.replace("/main/", "/master/")
                        req = urllib.request.Request(raw_url)
                        resp = urllib.request.urlopen(req)
                    else:
                        raise e
                content = resp.read().decode('utf-8')
                self.editor.setPlainText(content)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not fetch README.\n{e}")

    def insert_emoji(self, item):
        self.editor.insertPlainText(item.text())
        self.emoji_picker.hide()
        self.editor.setFocus()

    def generate_toc(self):
        lines = self.editor.toPlainText().split('\n')
        toc = ["## 📋 Table of Contents"]
        found = False
        for line in lines:
            if line.startswith('#'):
                level = line.count('#', 0, line.find(' '))
                if level > 0:
                    title = line.strip('#').strip()
                    anchor = title.lower().replace(' ', '-').replace('.', '').replace(':', '')
                    indent = "  " * (level - 1)
                    toc.append(f"{indent}- [{title}](#{anchor})")
                    found = True
        
        if found:
            current_text = self.editor.toPlainText()
            self.editor.setPlainText("\n".join(toc) + "\n\n---\n\n" + current_text)
        else:
            QMessageBox.information(self, "TOC", "No headers found to generate TOC.")

    def set_default_template(self):
        template = ("# Project Name\n\n"
                    "## 📝 Description\nWrite a short and clear description here.\n\n"
                    "## 🛠 Installation\n```bash\n# Standard installation\npip install -r requirements.txt\n```\n\n"
                    "## ✨ Features\n- [x] Feature one\n- [x] Fast & Minimalistic\n\n"
                    "## 📸 Screenshots\n![Preview](example/1.png)\n")
        self.editor.setPlainText(template)

    # 2. دالة تحميل الملف المبدئي لتسريع التشغيل
    def load_initial_file(self, path):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.editor.setPlainText(f.read())
            except:
                pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set App Icon
    icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # استخدام ستايل النظام الأصلي بدلاً من Fusion
    # app.setStyle("Fusion") 
    
    workspace_dir = os.getcwd()
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        workspace_dir = os.path.abspath(sys.argv[1])
        
    window = ReadmeEditor(workspace_dir)
    
    # 2. تحميل الملف بعد فتح الواجهة بفترة قصيرة جداً (100ms) لمنع تجميد البرنامج عند الفتح
    readme_path = os.path.join(workspace_dir, "README.md")
    QTimer.singleShot(100, lambda: window.load_initial_file(readme_path))
            
    window.setWindowOpacity(0.0)
    window.show()
    
    window._startup_anim = QPropertyAnimation(window, b"windowOpacity")
    window._startup_anim.setDuration(300)
    window._startup_anim.setStartValue(0.0)
    window._startup_anim.setEndValue(1.0)
    window._startup_anim.setEasingCurve(QEasingCurve.OutCubic)
    window._startup_anim.start()
    
    sys.exit(app.exec())