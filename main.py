import sys
import os  
import markdown2
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QPushButton, QSplitter, QDialog, QLabel, QLineEdit, 
    QFrame, QMessageBox, QListWidget
)
from PySide6.QtCore import Qt, QUrl, QPoint
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QIcon, QFont, QColor, QPalette, QTextCursor

# --- 1. إعدادات التصميم (CSS) لمحاكاة GitHub ---
GITHUB_CSS = """
<style>
    body { 
        font-family: -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans",Helvetica,Arial,sans-serif;
        font-size: 16px; line-height: 1.5; color: #24292f; background-color: #ffffff; padding: 32px; 
    }
    h1, h2, h3 { margin-top: 24px; margin-bottom: 16px; font-weight: 600; line-height: 1.25; }
    h1 { font-size: 2em; border-bottom: 1px solid #d0d7de; padding-bottom: 0.3em; }
    h2 { font-size: 1.5em; border-bottom: 1px solid #d0d7de; padding-bottom: 0.3em; }
    p { margin-top: 0; margin-bottom: 10px; }
    code { 
        font-family: ui-monospace,SFMono-Regular,SF Mono,Menlo,Consolas,Liberation Mono,monospace; 
        background-color: rgba(175,184,193,0.2); padding: 0.2em 0.4em; border-radius: 6px; font-size: 85%; 
    }
    pre { background-color: #f6f8fa; border-radius: 6px; padding: 16px; overflow: auto; }
    img { max-width: 100%; box-sizing: content-box; border-radius: 4px; background-color: white; }
    blockquote { padding: 0 1em; color: #57606a; border-left: 0.25em solid #d0d7de; margin: 0 0 16px 0; }
    table { border-spacing: 0; border-collapse: collapse; width: 100%; margin-bottom: 16px; }
    table th, table td { padding: 6px 13px; border: 1px solid #d0d7de; }
    table tr:nth-child(2n) { background-color: #f6f8fa; }
    a { color: #0969da; text-decoration: none; }
    
    .markdown-alert { padding: 8px 16px; margin-bottom: 16px; border-left: 0.25em solid; border-radius: 0 6px 6px 0; }
    .markdown-alert-note { border-left-color: #0969da; background-color: #f0f7ff; }
    .markdown-alert-warning { border-left-color: #9a6700; background-color: #fff8c5; }
    .markdown-alert-tip { border-left-color: #1a7f37; background-color: #dafbe1; }
    .markdown-alert-caution { border-left-color: #cf222e; background-color: #ffebe9; }
    .markdown-alert-title { font-weight: bold; display: block; margin-bottom: 4px; }
</style>
"""

# --- 2. نظام مساعد الكتابة (Tab Completion) ---
class SuggestionPopup(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setFixedWidth(450)
        self.setStyleSheet("""
            QListWidget {
                background-color: #252526; border: 2px solid #0078d4;
                border-radius: 8px; color: #ffffff; font-size: 15px;
            }
            QListWidget::item { padding: 12px; border-bottom: 1px solid #3e3e42; }
            QListWidget::item:selected { background-color: #0078d4; color: white; }
        """)
        self.hide()

class SmartEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.popup = SuggestionPopup(self)
        self.popup.itemClicked.connect(self.insert_suggestion)
        
        # الكلمات والجمل الاحترافية
        self.data = {
            "📸 Screenshots": "## 📸 Screenshots\n| Preview 1 | Preview 2 |\n|---|---|\n| ![Img1](url) | ![Img2](url) |\n",
            "✨ Features": "## ✨ Features\n- 🚀 **High Performance:** Optimized core for maximum speed.\n- 🎨 **Modern UI:** Clean and intuitive Windows 11 style.\n- 🔒 **Secure:** End-to-end data encryption.\n",
            "📝 Description": "## 📝 Description\nThis project is a powerful tool designed to streamline your workflow and enhance productivity by providing...\n",
            "🛠 Installation": "## 🛠 Installation\n1. **Clone the repo:**\n```bash\ngit clone [https://github.com/user/repo.git](https://github.com/user/repo.git)\n```\n2. **Install dependencies:**\n```bash\npip install -r requirements.txt\n```\n",
            "🚀 yasser27": "### 👤 Author\nDeveloped by **yasser27** - [GitHub Profile](https://github.com/YASSER-27)\n",
            "🚨 WARNING": "> [!WARNING]\n> This software is for educational purposes only. Use it at your own risk!\n",
            "💡 Pro Note": "> [!NOTE]\n> Don't forget to star the repository if you find this tool useful! ⭐\n",
            "🏁 Conclusion": "## 🏁 Conclusion\nWe hope this tool makes your life easier. For support, please open an issue.\n",
            "📖 Usage Guide": "## 📖 Usage\nTo run the application, use the following command:\n```python\npython main.py\n```\n"
        }
        
        for key in self.data.keys():
            self.popup.addItem(key)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab:
            cursor_rect = self.cursorRect()
            pos = self.mapToGlobal(QPoint(cursor_rect.right() + 10, cursor_rect.bottom() + 10))
            self.popup.move(pos)
            self.popup.show()
            self.popup.setFocus()
        elif self.popup.isVisible() and event.key() in (Qt.Key_Enter, Qt.Key_Return):
            self.insert_suggestion(self.popup.currentItem())
        else:
            super().keyPressEvent(event)
            self.popup.hide()

    def insert_suggestion(self, item):
        if item:
            self.insertPlainText(self.data[item.text()])
            self.popup.hide()
            self.setFocus()

# --- 3. نافذة المساعد (Wizard) ---
class SetupWizard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🚀 Project Setup Wizard")
        self.setFixedSize(550, 600)
        self.setStyleSheet("""
            QDialog { background-color: #202020; color: white; }
            QLabel { font-size: 14px; color: #dddddd; margin-top: 10px; font-weight: bold; }
            QLineEdit { 
                background-color: #2d2d30; border: 1px solid #3e3e42; border-radius: 6px; 
                padding: 12px; color: white; font-size: 14px; 
            }
            QLineEdit:focus { border: 1px solid #0078d4; }
            QPushButton { 
                background-color: #0078d4; color: white; border-radius: 6px; 
                padding: 12px; font-weight: bold; font-size: 14px; border: none;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        header = QLabel("Create Your Professional README")
        header.setStyleSheet("font-size: 22px; color: #ffffff; margin-bottom: 20px;")
        layout.addWidget(header)

        self.inputs = {}
        fields = [("Project Name", "e.g. Super App"), ("Description", "What it does..."), 
                  ("GitHub Username", "username"), ("Repository Name", "repo"), ("Install Command", "pip install...")]

        for label_text, placeholder in fields:
            lbl = QLabel(label_text)
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            layout.addWidget(lbl)
            layout.addWidget(inp)
            self.inputs[label_text] = inp

        layout.addStretch()
        self.btn_finish = QPushButton("✨ Generate README")
        self.btn_finish.clicked.connect(self.accept)
        layout.addWidget(self.btn_finish)

    def get_data(self):
        return {k: v.text() for k, v in self.inputs.items()}

# --- 4. التطبيق الرئيسي ---
class ReadmeEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GitHub README Builder")
        self.resize(1000, 650)
        # --- 🟢 إضافة الأيقونة هنا 🟢 ---
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png") # تأكد من وجود ملف icon.png
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QSplitter::handle { background-color: #3e3e42; width: 2px; }
            QPushButton {
                background-color: #333333; color: #ffffff; border: 1px solid #3e3e42;
                border-radius: 6px; padding: 8px 16px; font-size: 13px; font-weight: 500;
            }
            QPushButton:hover { background-color: #3e3e42; border-color: #0078d4; }
            QPushButton#primary { background-color: #0078d4; border: none; }
            QPushButton#success { background-color: #238636; border: none; }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)
        self.main_layout.setContentsMargins(15, 15, 15, 15)

        # Toolbar
        self.setup_toolbar()

        # Splitter
        self.splitter = QSplitter(Qt.Horizontal)
        self.editor = SmartEditor() # استخدام المحرر الذكي الجديد
        self.editor.textChanged.connect(self.update_preview)
        
        self.preview = QWebEngineView()
        self.preview.setStyleSheet("background-color: white; border-radius: 8px;")
        
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        self.main_layout.addWidget(self.splitter)

        self.set_default_template()

    def setup_toolbar(self):
        toolbar = QHBoxLayout()
        for name, code in [("H1", "# "), ("H2", "## "), ("Bold", "**text**"), ("Code", "```\n\n```")]:
            btn = QPushButton(name)
            btn.clicked.connect(lambda ch, c=code: self.editor.insertPlainText(c))
            toolbar.addWidget(btn)

        sep = QFrame(); sep.setFrameShape(QFrame.VLine); sep.setStyleSheet("color: #555;"); toolbar.addWidget(sep)

        for name, code in [("ℹ️ Note", "> [!NOTE]\n> "), ("⚠️ Warning", "> [!WARNING]\n> ")]:
            btn = QPushButton(name); btn.clicked.connect(lambda ch, c=code: self.editor.insertPlainText(c)); toolbar.addWidget(btn)

        toolbar.addStretch()
        
        wiz_btn = QPushButton("🪄 Wizard"); wiz_btn.setObjectName("primary"); wiz_btn.clicked.connect(self.run_wizard); toolbar.addWidget(wiz_btn)
        copy_btn = QPushButton("📋 Copy All"); copy_btn.setObjectName("success"); copy_btn.clicked.connect(self.copy_to_clipboard); toolbar.addWidget(copy_btn)
        
        self.main_layout.addLayout(toolbar)

    def update_preview(self):
        md = self.editor.toPlainText()
        html = markdown2.markdown(md, extras=["fenced-code-blocks", "tables", "task_list"])
        replacements = {"> [!NOTE]": '<div class="markdown-alert markdown-alert-note"><span class="markdown-alert-title">Note</span>',
                        "> [!WARNING]": '<div class="markdown-alert markdown-alert-warning"><span class="markdown-alert-title">Warning</span>'}
        for o, n in replacements.items(): html = html.replace(o, n)
        self.preview.setHtml(f"<html><head>{GITHUB_CSS}</head><body>{html}</body></html>")

    def run_wizard(self):
        wiz = SetupWizard(self)
        if wiz.exec() == QDialog.Accepted:
            d = wiz.get_data()
            enc_name = d['Project Name'].replace(" ", "%20")
            header = f"![Header](https://capsule-render.vercel.app/api?type=waving&height=250&color=gradient&text={enc_name}&fontSize=50&animation=fadeIn)\n\n"
            content = header + f"# 🚀 {d['Project Name']}\n\n## 📝 Description\n{d['Description']}\n\n## 🛠 Installation\n```bash\n{d['Install Command']}\n```"
            self.editor.setPlainText(content)

    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.editor.toPlainText())
        QMessageBox.information(self, "Success", "Markdown Copied! 📋")

    def set_default_template(self):
        template = ("# 🚀 Project Name\n\n![Banner](https://img.shields.io/badge/Maintained%3F-yes-green.svg)\n\n"
                    "## 📝 Description\nWrite a short and clear description here.\n\n"
                    "## 🛠 Installation\n```bash\ngit clone [https://github.com/user/repo.git](https://github.com/user/repo.git)\ncd repo\npip install -r requirements.txt\n```\n\n"
                    "## ✨ Features\n- [x] Feature one\n- [x] Live Preview\n\n"
                    "## 📸 Screenshots\n![Preview](https://via.placeholder.com/600x300.png?text=Your+App+Screenshot)\n\n"
                    "## 🤝 Contributing\nFeel free to dive in! [Open an issue](link) or submit PRs.")
        self.editor.setPlainText(template)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    font = QFont("Segoe UI", 10); app.setFont(font)
    window = ReadmeEditor(); window.show()
    sys.exit(app.exec())