import sys
import os 
import markdown2
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QPushButton, QSplitter, QDialog, QLabel, QLineEdit, 
    QFrame, QMessageBox, QListWidget, QTextBrowser
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QIcon, QFont, QTextCursor, QColor

# إعداد لضمان ظهور الأيقونة في شريط المهام على ويندوز
try:
    from ctypes import windll
    windll.shell32.SetCurrentProcessExplicitAppUserModelID('yasser.readme.lite.pro')
except:
    pass

# --- 1. إعدادات التصميم (CSS) لعارض النصوص الخفيف ---
GITHUB_CSS = """
<style>
    body { 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; 
        font-size: 16px; line-height: 1.5; color: #1f2328; background-color: #ffffff; padding: 30px; 
    }
    h1 { font-size: 2em; border-bottom: 1px solid #d8dee4; padding-bottom: 0.3em; margin-top: 24px; color: #1f2328; }
    h2 { font-size: 1.5em; border-bottom: 1px solid #d8dee4; padding-bottom: 0.3em; margin-top: 24px; color: #1f2328; }
    h3 { font-size: 1.25em; margin-top: 24px; color: #1f2328; }
    p { margin-top: 0; margin-bottom: 16px; }
    
    /* تنسيق الكود - محاكاة جيتهاب */
    code { 
        background-color: rgba(175, 184, 193, 0.2); padding: 0.2em 0.4em; 
        border-radius: 6px; font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, monospace; 
        font-size: 85%; 
    }
    pre { 
        background-color: #f6f8fa; padding: 16px; border-radius: 6px; 
        border: 1px solid #d0d7de; overflow: auto; line-height: 1.45;
    }
    pre code { background-color: transparent; padding: 0; font-size: 100%; }

    /* الاقتباسات */
    blockquote { 
        border-left: 0.25em solid #d0d7de; padding: 0 1em; color: #636c76; margin: 0 0 16px 0; 
    }

    /* الجداول */
    table { border-collapse: collapse; width: 100%; margin-bottom: 16px; border-spacing: 0; }
    table th, table td { border: 1px solid #d0d7de; padding: 6px 13px; }
    table th { font-weight: 600; background-color: #f6f8fa; }
    table tr { background-color: #ffffff; border-top: 1px solid #d8dee4; }
    table tr:nth-child(2n) { background-color: #f6f8fa; }

    /* التنبيهات الاحترافية (GitHub Alerts) */
    .alert { padding: 12px 16px; border-radius: 6px; margin-bottom: 16px; border-left: 4px solid; font-size: 14px; }
    .note { background-color: #f0f7ff; border-color: #0969da; color: #0969da; }
    .warning { background-color: #fff8c5; border-color: #9a6700; color: #9a6700; }
    
    a { color: #0969da; text-decoration: none; }
    a:hover { text-decoration: underline; }
    
    img { max-width: 100%; border-radius: 6px; }
</style>
"""

# --- 2. نظام مساعد الكتابة الذكي (Tab Completion) ---
class SuggestionPopup(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setFixedWidth(450)
        self.setStyleSheet("""
            QListWidget {
                background-color: #252526; border: 2px solid #0078d4;
                border-radius: 10px; color: #ffffff; font-size: 15px; outline: none;
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
        
        # بنك النصوص الاحترافية
        self.data = {
            "📸 Screenshots": "## 📸 Screenshots\n\n| Main Interface | Feature Preview |\n| :---: | :---: |\n| ![App](https://via.placeholder.com/400x250) | ![Feature](https://via.placeholder.com/400x250) |\n",
            "✨ Features": "## ✨ Features\n\n- 🚀 **High Performance:** Optimized for speed and low memory usage.\n- 🎨 **Modern Design:** Built with the latest UI/UX principles.\n- 🔒 **Secure:** Data privacy and security by default.\n- 🛠 **Open Source:** Fully customizable and community-driven.\n",
            "📝 Description": "## 📝 Description\n\n> This project is a professional tool designed to solve [Problem Name]. It offers a seamless experience for users looking to [Goal] with minimal effort.\n",
            "🛠 Installation": "## 🛠 Installation\n\n### Step 1: Clone\n```bash\ngit clone [https://github.com/user/repo.git](https://github.com/user/repo.git)\n```\n### Step 2: Install\n```bash\ncd repo\npip install -r requirements.txt\n```\n### Step 3: Run\n```bash\npython main.py\n```\n",
            "🚀 yasser27": "### 👤 Developer\n\nBuilt with ❤️ by **[yasser27](https://github.com/YASSER-27)**.\n*Feel free to reach out for collaborations!*\n",
            "🚨 WARNING": "> [!WARNING]\n> **Critical:** Always make a backup of your configuration before upgrading to a new version to prevent data loss.\n",
            "💡 Pro Note": "> [!NOTE]\n> You can enable 'Expert Mode' in the settings menu to access advanced developer tools.\n",
            "🤝 Contributing": "## 🤝 Contributing\n\nContributions are welcome! If you have any ideas or find a bug, please open an issue or submit a pull request.\n",
            "📜 License": "## 📜 License\n\nDistributed under the **MIT License**. See `LICENSE` for more information.\n"
        }
        for key in self.data.keys():
            self.popup.addItem(key)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab:
            cursor_rect = self.cursorRect()
            pos = self.mapToGlobal(QPoint(cursor_rect.right() + 15, cursor_rect.bottom() + 15))
            self.popup.move(pos)
            self.popup.show()
            self.popup.setFocus()
        elif self.popup.isVisible() and event.key() in (Qt.Key_Enter, Qt.Key_Return):
            self.insert_suggestion(self.popup.currentItem())
        elif self.popup.isVisible() and event.key() == Qt.Key_Escape:
            self.popup.hide()
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
        self.setFixedSize(500, 550)
        self.setStyleSheet("""
            QDialog { background-color: #1a1a1a; color: white; }
            QLabel { font-size: 14px; color: #bbb; margin-top: 10px; font-weight: bold; }
            QLineEdit { 
                background-color: #252526; border: 1px solid #333; border-radius: 6px; 
                padding: 10px; color: white; font-size: 14px; 
            }
            QPushButton { 
                background-color: #0078d4; color: white; border-radius: 6px; 
                padding: 12px; font-weight: bold; border: none; margin-top: 20px;
            }
            QPushButton:hover { background-color: #005a9e; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        
        header = QLabel("Quick README Generator")
        header.setStyleSheet("font-size: 20px; color: white; margin-bottom: 15px;")
        layout.addWidget(header)

        self.inputs = {}
        fields = [("Project Name", "e.g. My App"), ("Short Description", "A brief intro..."), 
                  ("Author Name", "yasser27"), ("Installation", "pip install ...")]

        for label_text, placeholder in fields:
            layout.addWidget(QLabel(label_text))
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            layout.addWidget(inp)
            self.inputs[label_text] = inp

        layout.addStretch()
        self.btn_finish = QPushButton("✨ Generate Template")
        self.btn_finish.clicked.connect(self.accept)
        layout.addWidget(self.btn_finish)

    def get_data(self):
        return {k: v.text() for k, v in self.inputs.items()}

# --- 4. التطبيق الرئيسي ---
class ReadmeEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("README Builder")
        self.resize(1000, 600)
        
        # --- إعداد الأيقونة ---
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            QApplication.setWindowIcon(QIcon(icon_path))

        self.setStyleSheet("""
            QMainWindow { background-color: #1a1a1a; }
            QSplitter::handle { background-color: #333; width: 2px; }
            QPushButton {
                background-color: #2d2d2d; color: #ddd; border: 1px solid #444;
                border-radius: 6px; padding: 8px 15px; font-size: 13px;
            }
            QPushButton:hover { background-color: #3d3d3d; border-color: #0078d4; }
            QPushButton#primary { background-color: #0078d4; border: none; font-weight: bold; }
            QPushButton#success { background-color: #238636; border: none; font-weight: bold; }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)

        # Toolbar
        self.setup_toolbar()

        # Workspace
        self.splitter = QSplitter(Qt.Horizontal)
        self.editor = SmartEditor()
        self.editor.textChanged.connect(self.update_preview)
        
        self.preview = QTextBrowser() # عارض خفيف بدلاً من المتصفح الثقيل
        self.preview.setOpenExternalLinks(True)
        self.preview.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #333;")
        
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        self.main_layout.addWidget(self.splitter)

        self.set_default_template()

    def setup_toolbar(self):
        toolbar = QHBoxLayout()
        tools = [("H1", "# "), ("H2", "## "), ("Bold", "**"), ("Code", "```\n"), ("Link", "[]()")]
        for name, code in tools:
            btn = QPushButton(name)
            btn.clicked.connect(lambda ch, c=code: self.editor.insertPlainText(c))
            toolbar.addWidget(btn)

        toolbar.addStretch()
        
        wiz_btn = QPushButton("🪄 Wizard"); wiz_btn.setObjectName("primary")
        wiz_btn.clicked.connect(self.run_wizard); toolbar.addWidget(wiz_btn)
        
        copy_btn = QPushButton("📋 Copy All"); copy_btn.setObjectName("success")
        copy_btn.clicked.connect(self.copy_to_clipboard); toolbar.addWidget(copy_btn)
        
        self.main_layout.addLayout(toolbar)

    def update_preview(self):
        md = self.editor.toPlainText()
        # تحويل الماركدوان إلى HTML
        html = markdown2.markdown(md, extras=["fenced-code-blocks", "tables", "task_list", "admonitions"])
        
        # معالجة الـ Alerts يدوياً لتناسب QTextBrowser
        html = html.replace("> [!NOTE]", '<div class="alert note"><b>ℹ️ Note:</b>')
        html = html.replace("> [!WARNING]", '<div class="alert warning"><b>⚠️ Warning:</b>')
        
        full_html = f"<html><head>{GITHUB_CSS}</head><body>{html}</body></html>"
        self.preview.setHtml(full_html)

    def run_wizard(self):
        wiz = SetupWizard(self)
        if wiz.exec() == QDialog.Accepted:
            d = wiz.get_data()
            content = f"# 🚀 {d['Project Name']}\n\n{d['Short Description']}\n\n## 🛠 Installation\n```bash\n{d['Installation']}\n```\n\n### 👤 Author\nDeveloped by **{d['Author Name']}**"
            self.editor.setPlainText(content)

    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.editor.toPlainText())
        QMessageBox.information(self, "Success", "README Markdown Copied to Clipboard!")

    def set_default_template(self):
        template = ("# 🚀 Project Title\n\n![Status](https://img.shields.io/badge/Status-Active-brightgreen)\n\n"
                    "## 📝 Description\nYour project description goes here. Make it catchy!\n\n"
                    "## ✨ Features\n- [x] Feature one\n- [x] Light & Fast\n\n"
                    "## 🛠 Installation\n```bash\npip install my-awesome-tool\n```\n\n"
                    "--- \n*Generated using Yasser's Builder*")
        self.editor.setPlainText(template)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # تحسين الخطوط للنافذة
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = ReadmeEditor()
    window.show()
    sys.exit(app.exec())