import sys, os, re, json, html, urllib.request, urllib.error, urllib.parse, base64, subprocess, shutil
from pathlib import Path
from datetime import datetime

os.environ.setdefault("QT_FONT_DPI", "96")

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QFrame, QLabel, QLineEdit, QSplitter,
    QMessageBox, QFileDialog, QDialog, QScrollArea, QGridLayout,
    QListWidget, QListWidgetItem, QAbstractItemView, QToolButton,
    QCheckBox, QTabWidget, QInputDialog, QComboBox, QProgressBar,
    QButtonGroup, QRadioButton, QSizePolicy, QMenu, QTextBrowser,
    QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, QUrl, QTimer, QThread, QObject, Signal, QPoint, QSize, QRect, QRunnable, QThreadPool, QProcess, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import (
    QAction, QFont, QColor, QSyntaxHighlighter, QTextCharFormat,
    QKeySequence, QIcon, QShortcut, QTextCursor, QPixmap, QImage,
    QTextDocument, QPainter, QBrush, QPen, QUndoCommand, QPalette
)
import markdown2

# Pygments for syntax highlighting in preview
try:
    from pygments import highlight as pyg_highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer, TextLexer
    from pygments.formatters import HtmlFormatter
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# ── Theme (charcoal / deep dark) ──────────────────────────────────────────
T = {
    "bg":       "#151515",
    "panel":    "#151515",
    "border":   "#151515",
    "hover":    "#151515",
    "input":    "#151515",
    "text":     "#E8E8ED",
    "dim":      "#B3B3B3",
    "editor":   "#E8E8ED",
    "scroll":   "#151515",
    "accent":   "#4F8DFF",
    "accent2":  "#6AADFF",
    "code":     "#08080C",
    "chip":     "#151515",
    "chip_br":  "#151515",
    "syn_h":    "#79B8FF",
    "syn_b":    "#E6EDF3",
    "syn_i":    "#D2A8FF",
    "syn_c":    "#FF8B87",
    "syn_l":    "#D4D4DC",
    "syn_q":    "#7A7A8E",
    "syn_li":   "#E3A05C",
    "syn_img":  "#6BD09C",
    "syn_tag":  "#A3E798",
    "syn_chk":  "#E3C56D",
}

def apply_theme(app: QApplication, theme: str):
    """Apply theme colors to the application."""
    if theme == "dark":
        apply_dark_palette(app)
    # Apply global stylesheet
    app.setStyleSheet(GLOBAL_STYLE())

def apply_dark_palette(app: QApplication):
    """Force a fully dark system palette so every native widget is dark."""
    p = QPalette()
    bg      = QColor(T["bg"])
    panel   = QColor(T["panel"])
    text    = QColor(T["text"])
    dim     = QColor(T["dim"])
    accent  = QColor(T["accent"])
    border  = QColor(T["border"])
    inp     = QColor(T["input"])
    hover   = QColor(T["hover"])

    p.setColor(QPalette.Window,          bg)
    p.setColor(QPalette.WindowText,      text)
    p.setColor(QPalette.Base,            inp)
    p.setColor(QPalette.AlternateBase,   panel)
    p.setColor(QPalette.ToolTipBase,     panel)
    p.setColor(QPalette.ToolTipText,     text)
    p.setColor(QPalette.Text,            text)
    p.setColor(QPalette.Button,          hover)
    p.setColor(QPalette.ButtonText,      text)
    p.setColor(QPalette.BrightText,      QColor("#F5F5F5"))
    p.setColor(QPalette.Link,            accent)
    p.setColor(QPalette.Highlight,       accent)
    p.setColor(QPalette.HighlightedText, QColor("#F5F5F5"))
    p.setColor(QPalette.PlaceholderText, dim)
    p.setColor(QPalette.Mid,             border)
    p.setColor(QPalette.Dark,            panel)
    p.setColor(QPalette.Shadow,          QColor("#000000"))
    p.setColor(QPalette.Light,           hover)
    p.setColor(QPalette.Midlight,        border)

    # Disabled states
    p.setColor(QPalette.Disabled, QPalette.WindowText,  dim)
    p.setColor(QPalette.Disabled, QPalette.Text,         dim)
    p.setColor(QPalette.Disabled, QPalette.ButtonText,   dim)

    app.setPalette(p)

MENU_STYLE = lambda: (
    f"QMenu{{background:{T['panel']};border:1px solid {T['border']};border-radius:10px;"
    f"padding:5px;color:{T['text']};font-size:12px;}}"
    f"QMenu::item{{padding:8px 26px 8px 14px;border-radius:6px;margin:2px 4px;}}"
    f"QMenu::item:selected{{background:{T['input']};color:{T['accent2']};border:1px solid {T['border']};}}"
    f"QMenu::separator{{height:1px;background:{T['border']};margin:4px 10px;}}"
    f"QMenu::right-arrow{{width:8px;height:8px;}}"
)

BTN_STYLE = lambda: (
    f"QPushButton{{background:{T['hover']};color:{T['text']};border:1px solid {T['border']};"
    f"border-radius:8px;padding:8px 16px;font-size:12px;font-weight:600;}}"
    f"QPushButton:hover{{border-color:{T['accent']};background:{T['input']};}}"
    f"QPushButton#primary{{background:{T['accent']};border:1px solid {T['accent']};color:#F5F5F5;}}"
    f"QPushButton#primary:hover{{background:{T['accent2']};border-color:{T['accent2']};}}"
)

GLOBAL_STYLE = lambda: (
    f"QMainWindow{{background:{T['bg']};}}"
    f"QWidget{{background:{T['bg']};color:{T['text']};}}"
    f"QDialog{{background:{T['panel']};color:{T['text']};}}"
    f"QTextEdit{{background:{T['bg']};color:{T['editor']};border:none;"
    f"font-size:14px;padding:18px;font-family:ui-monospace,'SF Mono',Consolas,monospace;line-height:1.7;}}"
    f"QLineEdit{{background:{T['input']};color:{T['editor']};border:1px solid {T['border']};"
    f"border-radius:6px;padding:8px 12px;font-size:13px;}}"
    f"QLineEdit:focus{{border-color:{T['accent']};}}"
    f"QComboBox{{background:{T['input']};color:{T['editor']};border:1px solid {T['border']};"
    f"border-radius:6px;padding:6px 10px;selection-background-color:{T['accent']};}}"
    f"QComboBox::drop-down{{border:none;width:20px;background:transparent;}}"
    f"QComboBox QAbstractItemView{{background:{T['panel']};color:{T['text']};"
    f"border:1px solid {T['border']};selection-background-color:{T['accent']};"
    f"selection-color:#F5F5F5;outline:none;}}"
    f"QListWidget{{background:{T['input']};color:{T['text']};border:1px solid {T['border']};"
    f"border-radius:6px;outline:none;}}"
    f"QListWidget::item{{padding:9px;border-radius:5px;}}"
    f"QListWidget::item:selected{{background:{T['accent']};color:#F5F5F5;}}"
    f"QListWidget::item:hover:!selected{{background:{T['hover']};}}"
    f"QScrollBar:vertical{{border:none;background:{T['bg']};width:7px;}}"
    f"QScrollBar::handle:vertical{{background:{T['scroll']};border-radius:3px;min-height:24px;}}"
    f"QScrollBar::handle:vertical:hover{{background:{T['border']};}}"
    f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;background:none;}}"
    f"QScrollBar:horizontal{{border:none;background:{T['bg']};height:7px;}}"
    f"QScrollBar::handle:horizontal{{background:{T['scroll']};border-radius:3px;min-width:24px;}}"
    f"QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal{{width:0;background:none;}}"
    f"QMessageBox{{background:{T['panel']};color:{T['text']};}}"
    f"QMessageBox QLabel{{color:{T['text']};background:transparent;}}"
    f"QMessageBox QPushButton{{background:{T['hover']};color:{T['text']};border:1px solid {T['border']};"
    f"border-radius:6px;padding:6px 14px;min-width:60px;}}"
    f"QMessageBox QPushButton:hover{{border-color:{T['accent']};}}"
    f"QInputDialog{{background:{T['panel']};color:{T['text']};}}"
    f"QInputDialog QLabel{{color:{T['text']};background:transparent;}}"
    f"QFileDialog{{background:{T['panel']};color:{T['text']};}}"
    f"QFileDialog QWidget{{background:{T['panel']};color:{T['text']};}}"
    f"QTabWidget::pane{{border:none;background:{T['bg']};}}"
    f"QTabBar::tab{{background:transparent;color:{T['dim']};border:1px solid {T['border']};"
    f"border-bottom:none;border-top-left-radius:10px;border-top-right-radius:10px;"
    f"padding:8px 16px;margin-right:3px;font-size:11px;font-weight:600;min-width:100px;}}"
    f"QTabBar::tab:selected{{background:{T['input']};color:{T['text']};border-color:{T['border']};"
    f"border-bottom:2px solid {T['accent']};}}"
    f"QTabBar::tab:hover:!selected{{background:{T['hover']};color:{T['text']};}}"
    f"QTabBar::close-button{{background:transparent;border-radius:3px;margin-left:5px;}}"
    f"QTabBar::close-button:hover{{background:#151515;}}"
    f"QSplitter::handle{{background:{T['border']};}}"
    f"QToolButton{{background:transparent;color:{T['dim']};border:none;border-radius:8px;"
    f"padding:10px 4px;font-size:11px;font-weight:600;}}"
    f"QToolButton:hover{{background:{T['hover']};color:{T['text']};}}"
    f"QCheckBox{{color:{T['dim']};font-size:12px;background:transparent;}}"
    f"QCheckBox::indicator{{width:14px;height:14px;border:1px solid {T['border']};"
    f"border-radius:3px;background:{T['input']};}}"
    f"QCheckBox::indicator:checked{{background:{T['accent']};border-color:{T['accent']};}}"
    f"QLabel{{background:transparent;color:{T['text']};}}"
    f"QScrollArea{{border:none;background:transparent;}}"
    f"QToolTip{{background:{T['panel']};color:{T['text']};border:1px solid {T['border']};"
    f"border-radius:5px;padding:4px 8px;font-size:11px;}}"
)

# ── Pygments dark theme CSS for code blocks ────────────────────────────────
def _pygments_css():
    """Generate dark-theme CSS for Pygments syntax highlighting."""
    if not PYGMENTS_AVAILABLE:
        return ""
    try:
        formatter = HtmlFormatter(style='monokai', nowrap=False)
        css = formatter.get_style_defs('.highlight')
    except:
        css = ""
    return css

def _highlight_code(code, lang):
    """Highlight code with Pygments. Returns HTML string."""
    if not PYGMENTS_AVAILABLE:
        return f"<code>{html.escape(code)}</code>"
    try:
        lexer = get_lexer_by_name(lang, stripall=True)
    except:
        try:
            lexer = guess_lexer(code)
        except:
            lexer = TextLexer()
    formatter = HtmlFormatter(
        nowrap=False,
        style='monokai',
        noclasses=True,
        prestyles="margin:0;padding:0;background:transparent;",
    )
    return pyg_highlight(code, lexer, formatter)

# ── Preview CSS ────────────────────────────────────────────────────────────
def preview_css():
    pyg_css = _pygments_css()
    return f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
*{{box-sizing:border-box;}}
body{{
  font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;
  font-size:16px;line-height:1.7;color:#c9d1d9;background:{T['bg']};
  padding:32px 40px;max-width:980px;margin:0 auto;
}}
h1,h2,h3,h4,h5,h6{{
  font-weight:600;color:#c9d1d9;margin-top:24px;margin-bottom:16px;line-height:1.25;
}}
h1{{font-size:2em;border-bottom:1px solid #30363d;padding-bottom:.3em;}}
h2{{font-size:1.5em;border-bottom:1px solid #30363d;padding-bottom:.3em;}}
h3{{font-size:1.25em;}}
h4{{font-size:1em;}}
p{{margin-top:0;margin-bottom:16px;}}
a{{color:#58a6ff;text-decoration:none;}}
a:hover{{text-decoration:underline;color:#79c0ff;}}
strong{{font-weight:600;color:#c9d1d9;}}
em{{color:#c9d1d9;}}

/* Inline code */
code{{
  background:rgba(110,118,129,0.2);padding:.2em .4em;border-radius:6px;
  font-size:85%;font-family:'SF Mono',ui-monospace,Consolas,monospace;
  color:#c9d1d9;
}}

/* Code blocks */
pre{{
  background:#161b22;border:1px solid #30363d;border-radius:6px;
  padding:16px;overflow-x:auto;margin-bottom:16px;line-height:1.45;
  font-size:85%;
}}
pre code{{
  background:transparent;padding:0;border-radius:0;font-size:100%;
  color:#c9d1d9;white-space:pre;word-wrap:normal;
}}

/* Code block with language label */
.code-block-wrapper{{
  background:#161b22;border:1px solid #30363d;border-radius:6px;
  margin-bottom:16px;overflow:hidden;
}}
.code-block-header{{
  display:flex;align-items:center;justify-content:space-between;
  padding:8px 16px;border-bottom:1px solid #30363d;
  background:#161b22;
}}
.code-block-lang{{
  font-size:12px;color:#8b949e;font-family:'SF Mono',Consolas,monospace;
  font-weight:500;text-transform:lowercase;
}}
.code-block-wrapper pre{{
  border:none;border-radius:0;margin:0;
}}

/* Images */
img{{max-width:100%;height:auto;border-radius:6px;}}

/* Blockquotes */
blockquote{{
  padding:0 1em;color:#8b949e;border-left:.25em solid #30363d;
  margin:0 0 16px;
}}
blockquote p{{margin-bottom:0;}}

/* Tables - GitHub style */
table{{
  border-spacing:0;border-collapse:collapse;width:100%;
  margin-bottom:16px;display:block;max-width:100%;overflow:auto;
}}
thead{{background:#161b22;}}
th{{
  padding:6px 13px;border:1px solid #30363d;font-weight:600;
  text-align:left;color:#c9d1d9;
}}
td{{
  padding:6px 13px;border:1px solid #30363d;color:#c9d1d9;
}}
tr{{background:{T['bg']};border-top:1px solid #30363d;}}
tr:nth-child(2n){{background:#161b22;}}

/* Horizontal rules */
hr{{height:.25em;background:#30363d;border:0;margin:24px 0;border-radius:2px;}}

/* Lists */
ul,ol{{padding-left:2em;margin-bottom:16px;}}
li{{margin-top:.25em;}}
li+li{{margin-top:.25em;}}
ul ul,ol ol,ul ol,ol ul{{margin-top:0;margin-bottom:0;}}

/* Task lists */
.task-list-item{{list-style-type:none;}}
.task-list-item input{{margin:0 .2em .25em -1.6em;vertical-align:middle;}}

/* GitHub alerts */
.markdown-alert{{
  padding:8px 16px;margin-bottom:16px;border-left:.25em solid;
  border-radius:0 6px 6px 0;
}}
.markdown-alert-note{{border-left-color:#1f6feb;background:rgba(31,111,235,.08);}}
.markdown-alert-warning{{border-left-color:#d29922;background:rgba(210,153,34,.08);}}
.markdown-alert-tip{{border-left-color:#238636;background:rgba(35,134,54,.08);}}
.markdown-alert-important{{border-left-color:#8957e5;background:rgba(137,87,229,.08);}}
.markdown-alert-caution{{border-left-color:#da3633;background:rgba(218,54,51,.08);}}
.markdown-alert b{{display:block;margin-bottom:4px;}}

/* Details/Summary */
details{{
  background:rgba(110,118,129,0.05);border:1px solid #30363d;
  border-radius:6px;padding:8px 16px;margin-bottom:16px;
}}
summary{{cursor:pointer;font-weight:600;color:#58a6ff;}}

/* Keyboard */
kbd{{
  background:#161b22;border:1px solid #30363d;border-bottom:2px solid #30363d;
  border-radius:3px;padding:2px 6px;font-size:85%;
  font-family:'SF Mono',Consolas,monospace;color:#c9d1d9;
}}

/* Definition lists */
dt{{font-weight:600;margin-top:16px;}}
dd{{margin-left:16px;margin-bottom:16px;}}

/* Scrollbar */
::-webkit-scrollbar{{width:8px;height:8px;}}
::-webkit-scrollbar-track{{background:{T['bg']};}}
::-webkit-scrollbar-thumb{{background:#30363d;border-radius:10px;}}
::-webkit-scrollbar-thumb:hover{{background:#424a53;}}

{pyg_css}
</style>"""

# ── Syntax Highlighter ─────────────────────────────────────────────────────
class MDHighlighter(QSyntaxHighlighter):
    def __init__(self, doc):
        super().__init__(doc)
        def f(color, bold=False, italic=False):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            if bold:   fmt.setFontWeight(QFont.Bold)
            if italic: fmt.setFontItalic(True)
            return fmt
        self._rules = [
            (re.compile(r"^#{1,2} .+"),      f(T["syn_h"],  bold=True)),
            (re.compile(r"^#{3,} .+"),        f(T["syn_h"])),
            (re.compile(r"\*\*[^*]+\*\*"),    f(T["syn_b"],  bold=True)),
            (re.compile(r"\*[^*]+\*"),         f(T["syn_i"],  italic=True)),
            (re.compile(r"~~[^~]+~~"),         f(T["syn_q"])),
            (re.compile(r"`[^`]+`"),           f(T["syn_c"])),
            (re.compile(r"^```.*"),            f(T["syn_q"])),
            (re.compile(r"!\[.*?\]\(.*?\)"),   f(T["syn_img"])),
            (re.compile(r"\[.*?\]\(.*?\)"),    f(T["syn_l"])),
            (re.compile(r"^>.*"),              f(T["syn_q"],  italic=True)),
            (re.compile(r"^\s*[-*+] "),        f(T["syn_li"])),
            (re.compile(r"^\s*\d+\. "),        f(T["syn_li"])),
            (re.compile(r"<[^>]+>"),           f(T["syn_tag"])),
            (re.compile(r"\[[ xX]\]"),         f(T["syn_chk"])),
            (re.compile(r"\[!(NOTE|WARNING|TIP|IMPORTANT|CAUTION)\]"), f(T["syn_chk"], bold=True)),
            (re.compile(r"^\|.+\|"),           f(T["syn_b"])),
            (re.compile(r"---+"),              f(T["syn_q"])),
        ]

    def highlightBlock(self, text):
        for pat, fmt in self._rules:
            for m in pat.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)

# ── Line Number Area ───────────────────────────────────────────────────────
class LineNumbers(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
    def sizeHint(self): return QSize(self.editor._lnw(), 0)
    def paintEvent(self, e): self.editor._paint_ln(e)

# ── README Score ───────────────────────────────────────────────────────────
def readme_score(text):
    s = 0; tips = []
    if re.search(r"^# ", text, re.M): s += 20
    else: tips.append("Missing H1 title")
    if len(text) > 150: s += 15
    else: tips.append("Add more content")
    if re.search(r"##.*install", text, re.I): s += 15
    else: tips.append("Missing installation section")
    if re.search(r"##.*(usage|example|quick)", text, re.I): s += 15
    else: tips.append("Add usage examples")
    if re.search(r"shields\.io", text): s += 10
    else: tips.append("Add badges")
    if "```" in text: s += 10
    else: tips.append("Add code blocks")
    if re.search(r"##.*license", text, re.I): s += 10
    else: tips.append("Missing license section")
    if re.search(r"##.*contribut", text, re.I): s += 5
    return s, tips

# ── Preview Browser & Image Fetcher ────────────────────────────────────────
class _ImgFetcher(QObject):
    done = Signal(str, bytes)

    def __init__(self, url_str):
        super().__init__()
        self.url_str = url_str

    def run(self):
        try:
            req = urllib.request.Request(self.url_str, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = resp.read()
            self.done.emit(self.url_str, data)
        except:
            self.done.emit(self.url_str, b"")

class PreviewBrowser(QTextBrowser):
    def __init__(self, workspace_dir="", parent=None):
        super().__init__(parent)
        self.workspace_dir = workspace_dir
        self._img_cache   = {}
        self._pending     = set()
        self._threads     = []
        self.setOpenExternalLinks(True)
        self.setOpenLinks(True)

    def loadResource(self, resource_type, url):
        if resource_type != QTextDocument.ImageResource:
            return super().loadResource(resource_type, url)
        url_str = url.toString()
        if url_str in self._img_cache:
            return self._img_cache[url_str]
        candidates = []
        local = url.toLocalFile()
        if local: candidates.append(local)
        raw = url_str.replace("\\", "/").replace("%5C", "/").replace("%5c", "/")
        candidates.append(raw)
        candidates.append(raw.replace("/", os.sep))
        if self.workspace_dir:
            for p in [raw, raw.replace("/", os.sep)]:
                candidates.append(os.path.join(self.workspace_dir, p))
        seen = set()
        for path in candidates:
            if not path: continue
            path = os.path.normpath(path)
            if path in seen: continue
            seen.add(path)
            if os.path.isfile(path):
                try:
                    with open(path, "rb") as f: data = f.read()
                    img = QImage()
                    img.loadFromData(data)
                    if not img.isNull():
                        px = QPixmap.fromImage(img)
                        self._img_cache[url_str] = px
                        return px
                except: pass
        if url_str.startswith(("http://", "https://")) and url_str not in self._pending:
            self._pending.add(url_str)
            fetcher = _ImgFetcher(url_str)
            thread  = QThread()
            fetcher.moveToThread(thread)
            fetcher.done.connect(self._on_img_ready)
            thread.started.connect(fetcher.run)
            thread.start()
            self._threads.append((thread, fetcher))
        return QPixmap()

    def _on_img_ready(self, url_str: str, data: bytes):
        self._pending.discard(url_str)
        if data:
            img = QImage()
            img.loadFromData(data)
            if not img.isNull():
                px = QPixmap.fromImage(img)
                if px.height() < 40:
                    px = px.scaledToHeight(20, Qt.SmoothTransformation)
                self._img_cache[url_str] = px
                QTimer.singleShot(0, self._refresh_images)
        self._threads = [(t, w) for t, w in self._threads if t.isRunning()]

    def _refresh_images(self):
        sb = self.verticalScrollBar(); pos = sb.value()
        self.setHtml(self.toHtml())
        QTimer.singleShot(0, lambda: sb.setValue(pos))

    def shutdown_network_threads(self, wait_ms=800):
        for thread, _ in list(getattr(self, "_threads", [])):
            if thread.isRunning():
                thread.quit()
                if not thread.wait(wait_ms):
                    thread.terminate()
                    thread.wait(300)
        self._threads = []
        self._pending.clear()

# ── Render Worker ──────────────────────────────────────────────────────────
class RenderWorker(QObject):
    finished = Signal(str)
    def __init__(self):
        super().__init__()
        self._md = ""; self._dirty = False

    def request(self, md):
        self._md = md; self._dirty = True

    def process(self):
        if not self._dirty: return
        self._dirty = False
        md_text = self._md

        # Convert markdown to HTML with all extras
        html_out = markdown2.markdown(md_text,
            extras=["fenced-code-blocks", "tables", "task_list", "strike",
                     "code-friendly", "header-ids", "footnotes",
                     "numbering", "cuddled-lists"])

        # Process GitHub alerts
        for old, new in [
            ("> [!NOTE]",       '<div class="markdown-alert markdown-alert-note"><b>📝 Note</b><br>'),
            ("> [!WARNING]",    '<div class="markdown-alert markdown-alert-warning"><b>⚠️ Warning</b><br>'),
            ("> [!TIP]",        '<div class="markdown-alert markdown-alert-tip"><b>💡 Tip</b><br>'),
            ("> [!IMPORTANT]",  '<div class="markdown-alert markdown-alert-important"><b>❗ Important</b><br>'),
            ("> [!CAUTION]",    '<div class="markdown-alert markdown-alert-caution"><b>🔴 Caution</b><br>'),
        ]:
            html_out = html_out.replace(old, new)

        # Syntax highlighting for fenced code blocks
        if PYGMENTS_AVAILABLE:
            def _replace_code_block(m):
                full_match = m.group(0)
                # Try to extract language from class
                lang_match = re.search(r'class="([^"]*)"', full_match)
                lang = ""
                if lang_match:
                    cls = lang_match.group(1)
                    # Look for language- prefix or just the class name
                    for c in cls.split():
                        if c.startswith("language-"):
                            lang = c[9:]
                            break
                        elif c not in ("highlight", "codehilite"):
                            lang = c
                            break

                # Extract code content
                code_match = re.search(r'<code[^>]*>(.*?)</code>', full_match, re.DOTALL)
                if not code_match:
                    return full_match

                code = code_match.group(1)
                # Unescape HTML entities
                code = html.unescape(code)
                code = code.rstrip('\n')

                if lang:
                    highlighted = _highlight_code(code, lang)
                    header = (f'<div class="code-block-wrapper">'
                             f'<div class="code-block-header">'
                             f'<span class="code-block-lang">{html.escape(lang)}</span>'
                             f'</div>'
                             f'<pre style="background:#161b22;border:none;border-radius:0;margin:0;">{highlighted}</pre>'
                             f'</div>')
                    return header
                else:
                    return full_match

            html_out = re.sub(r'<pre><code[^>]*>.*?</code></pre>', _replace_code_block, html_out, flags=re.DOTALL)

        self.finished.emit(html_out)

# ── Smart Editor ───────────────────────────────────────────────────────────
class SnippetAddDialog(QDialog):
    def __init__(self, parent, text):
        super().__init__(parent); self.text = text
        self.setWindowTitle("Save Snippet"); self.setFixedSize(380, 420)
        lay = QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(15)
        lay.addWidget(QLabel("Snippet Name:"))
        self.name = QLineEdit(); self.name.setPlaceholderText("e.g., table-header")
        lay.addWidget(self.name)
        lay.addWidget(QLabel("Text Preview:"))
        self.preview = QTextEdit(); self.preview.setReadOnly(True); self.preview.setPlainText(text)
        self.preview.setStyleSheet(f"background:{T['input']};color:{T['dim']};border:none;border-radius:6px;font-family:monospace;font-size:11px;")
        lay.addWidget(self.preview)
        btns = QHBoxLayout(); lay.addLayout(btns); btns.addStretch()
        cancel = QPushButton("Cancel"); cancel.clicked.connect(self.reject); btns.addWidget(cancel)
        save = QPushButton("Save")
        save.setStyleSheet(f"background:{T['accent']};color:#F5F5F5;padding:8px 24px;border:1px solid {T['accent']};border-radius:6px;font-weight:600;")
        save.clicked.connect(self.accept); btns.addWidget(save)

class Editor(QTextEdit):
    def __init__(self, app=None):
        super().__init__()
        self.app = app
        self.highlighter = MDHighlighter(self.document())
        self._ln = LineNumbers(self)
        self.document().blockCountChanged.connect(self._update_lnw)
        self.textChanged.connect(self._update_lnw)
        self.verticalScrollBar().valueChanged.connect(self._ln.update)
        self.cursorPositionChanged.connect(self._highlight_line)

        QTimer.singleShot(50, self._update_lnw)

    def _trigger_ai(self, prompt=""):
        tab = self.parent()
        while tab and not isinstance(tab, DocTab):
            tab = tab.parent()
        if tab:
            tab.ai_panel.show()
            if prompt:
                tab.ai_panel.input.setText(prompt)
                tab.ai_panel.send_prompt()
            else:
                tab.ai_panel.input.setFocus()
            tab.ai_panel.update_position()

    def _lnw(self):
        return 20 + self.fontMetrics().horizontalAdvance("9") * max(len(str(self.document().blockCount())), 3)

    def _update_lnw(self):
        self.setViewportMargins(self._lnw(), 0, 0, 0)
    def resizeEvent(self, e):
        super().resizeEvent(e)
        cr = self.contentsRect()
        self._ln.setGeometry(QRect(cr.left(), cr.top(), self._lnw(), cr.height()))

    def _highlight_line(self):
        line_sel = QTextEdit.ExtraSelection()
        # Very subtle neutral highlight
        line_sel.format.setBackground(QColor(255, 255, 255, 8))
        line_sel.format.setProperty(QTextCharFormat.FullWidthSelection, True)
        line_sel.cursor = self.textCursor()
        line_sel.cursor.clearSelection()
        find_sels = []
        if self.app and getattr(self.app, "find_bar", None) and self.app.find_bar.isVisible():
            find_sels = self.app.find_bar.match_selections()
        self.setExtraSelections(find_sels + [line_sel])

    def _paint_ln(self, event):
        p = QPainter(self._ln)
        p.fillRect(event.rect(), QColor(T["input"]))
        block = self.document().begin(); bn = 0
        cur_bn = self.textCursor().blockNumber()
        while block.isValid():
            rect = self.document().documentLayout().blockBoundingRect(block)
            y = int(rect.top() - self.verticalScrollBar().value() + self.contentsMargins().top())
            if y > event.rect().bottom(): break
            if y + self.fontMetrics().height() >= event.rect().top():
                p.setPen(QColor(T['dim']))
                p.setFont(self.font())
                p.drawText(0, y, self._ln.width()-6, self.fontMetrics().height(), Qt.AlignRight, str(bn+1))
            block = block.next(); bn += 1

    def insert_md(self, pre, suf=""):
        cur = self.textCursor()
        if cur.hasSelection(): cur.insertText(f"{pre}{cur.selectedText()}{suf}")
        else:
            cur.insertText(f"{pre}{suf}")
            if suf: cur.setPosition(cur.position()-len(suf)); self.setTextCursor(cur)

    def insert_block(self, text):
        cur = self.textCursor()
        if not cur.hasSelection() and cur.columnNumber() != 0:
            cur.insertText("\n")
        cur.insertText(text + "\n")
        self.setTextCursor(cur)

    def contextMenuEvent(self, e):
        ms = MENU_STYLE()
        m = QMenu(self); m.setStyleSheet(ms)
        
        ai_menu = QMenu("✨ AI Assistant", m); ai_menu.setStyleSheet(ms)
        a_create = ai_menu.addAction("Create New README...")
        a_create.triggered.connect(self._ai_create_readme)
        ai_menu.addSeparator()
        a_improve = ai_menu.addAction("Improve Selection")
        a_improve.triggered.connect(lambda: self._trigger_ai("Improve and polish this text, make it professional."))
        trans_menu = QMenu("Translate to...", ai_menu); trans_menu.setStyleSheet(ms)
        for lang in ["Arabic", "English", "French", "Spanish", "German"]:
            a = trans_menu.addAction(lang)
            a.triggered.connect(lambda _, l=lang: self._trigger_ai(f"Translate this text to {l}."))
        ai_menu.addMenu(trans_menu)
        a_edit = ai_menu.addAction("Modify / Edit...")
        a_edit.triggered.connect(lambda: self._trigger_ai(""))
        m.addMenu(ai_menu)
        m.addSeparator()

        for lbl, fn in [("Undo", self.undo), ("Redo", self.redo)]:
            m.addAction(lbl).triggered.connect(fn)
        m.addSeparator()
        for lbl, fn in [("Cut", self.cut), ("Copy", self.copy), ("Paste", self.paste), ("Select All", self.selectAll)]:
            m.addAction(lbl).triggered.connect(fn)
        m.addSeparator()

        hdr = QMenu("# Headers", m); hdr.setStyleSheet(ms)
        for i in range(1, 7):
            hdr.addAction(f"{'#'*i}  H{i}").triggered.connect(lambda _, n=i: self.insert_block(f"{'#'*n} Heading {n}"))
        m.addMenu(hdr)

        fmt = QMenu("** Formatting", m); fmt.setStyleSheet(ms)
        for lbl, pre, suf in [
            ("**Bold**","**","**"),("_Italic_","*","*"),("~~Strikethrough~~","~~","~~"),
            ("`Inline Code`","`","`"),("==Highlight==","<mark>","</mark>"),
            ("^Superscript^","<sup>","</sup>"),("~Subscript~","<sub>","</sub>"),
        ]:
            fmt.addAction(lbl).triggered.connect(lambda _, p=pre, s=suf: self.insert_md(p, s))
        m.addMenu(fmt)

        code = QMenu("Code Blocks", m); code.setStyleSheet(ms)
        for lbl, txt in [
            ("Code Block","```\n\n```"),("Bash Block","```bash\n\n```"),
            ("Python Block","```python\n\n```"),("JavaScript Block","```javascript\n\n```"),
            ("JSON Block","```json\n\n```"),("YAML Block","```yaml\n\n```"),
            ("Diff Block","```diff\n+ added\n- removed\n```"),
        ]:
            code.addAction(lbl).triggered.connect(lambda _, t=txt: self.insert_block(t))
        m.addMenu(code)

        lst = QMenu("• Lists", m); lst.setStyleSheet(ms)
        for lbl, txt in [
            ("Unordered List","- Item 1\n- Item 2\n- Item 3"),
            ("Ordered List","1. Item 1\n2. Item 2\n3. Item 3"),
            ("Task List","- [x] Done\n- [ ] Todo\n- [ ] Future"),
            ("Nested List","- Parent\n  - Child\n  - Child\n- Parent"),
        ]:
            lst.addAction(lbl).triggered.connect(lambda _, t=txt: self.insert_block(t))
        m.addMenu(lst)

        tbl = QMenu("Tables", m); tbl.setStyleSheet(ms)
        for lbl, txt in [
            ("2 Columns","| Column 1 | Column 2 |\n|----------|----------|\n| Cell     | Cell     |"),
            ("3 Columns","| Column 1 | Column 2 | Column 3 |\n|----------|----------|----------|\n| Cell     | Cell     | Cell     |"),
            ("4 Columns","| Col 1 | Col 2 | Col 3 | Col 4 |\n|-------|-------|-------|-------|\n| Cell  | Cell  | Cell  | Cell  |"),
            ("Aligned Table","| Left | Center | Right |\n|:-----|:------:|------:|\n| L    |   C    |     R |"),
            ("API Endpoints","| Method | Endpoint | Description |\n|--------|----------|-------------|\n| `GET`  | `/items` | List all    |\n| `POST` | `/items` | Create new  |"),
        ]:
            tbl.addAction(lbl).triggered.connect(lambda _, t=txt: self.insert_block(t))
        m.addMenu(tbl)

        lnk = QMenu("Links & Images", m); lnk.setStyleSheet(ms)
        for lbl, txt in [
            ("Link","[link text](https://example.com)"),
            ("Link with Title",'[link text](https://example.com "Title")'),
            ("Image","![alt text](image.png)"),
            ("Image with Link","[![alt](image.png)](https://example.com)"),
            ("Reference Link","[text][ref]\n\n[ref]: https://example.com"),
            ("Footnote","Text[^1]\n\n[^1]: Footnote content."),
        ]:
            lnk.addAction(lbl).triggered.connect(lambda _, t=txt: self.insert_block(t))
        m.addMenu(lnk)

        bdg = QMenu("Badges", m); bdg.setStyleSheet(ms)
        for lbl, txt in [
            ("License MIT","[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)"),
            ("Build Passing","[![Build Status](https://img.shields.io/github/actions/workflow/status/USER/REPO/main.yml)](https://github.com/USER/REPO/actions)"),
            ("Stars","[![GitHub Stars](https://img.shields.io/github/stars/USER/REPO?style=social)](https://github.com/USER/REPO)"),
            ("Python 3.x","[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)"),
            ("Docker Ready","[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker)](https://hub.docker.com/)"),
            ("PRs Welcome","[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)"),
        ]:
            bdg.addAction(lbl).triggered.connect(lambda _, t=txt: self.insert_block(t))
        m.addMenu(bdg)

        alrt = QMenu("Alerts", m); alrt.setStyleSheet(ms)
        for lbl, txt in [
            ("Note","> [!NOTE]\n> Add your note here."),
            ("Warning","> [!WARNING]\n> Add your warning here."),
            ("Tip","> [!TIP]\n> Add your tip here."),
            ("Important","> [!IMPORTANT]\n> Add important info here."),
            ("Caution","> [!CAUTION]\n> Add caution here."),
            ("Blockquote","> Quoted text here."),
        ]:
            alrt.addAction(lbl).triggered.connect(lambda _, t=txt: self.insert_block(t))
        m.addMenu(alrt)

        gh = QMenu("GitHub Special", m); gh.setStyleSheet(ms)
        for lbl, txt in [
            ("Collapsible Section","<details>\n<summary>Click to expand</summary>\n\nContent here.\n\n</details>"),
            ("Mermaid Diagram","```mermaid\ngraph TD\n    A[Start] --> B{Decision}\n    B -->|Yes| C[Result]\n    B -->|No| D[End]\n```"),
            ("Keyboard Key","<kbd>Ctrl</kbd> + <kbd>C</kbd>"),
            ("Center Image",'<p align="center">\n  <img src="image.png" width="600" alt="alt text">\n</p>'),
            ("HTML Comment","<!-- comment here -->"),
        ]:
            gh.addAction(lbl).triggered.connect(lambda _, t=txt: self.insert_block(t))
        m.addMenu(gh)

        sec = QMenu("Sections", m); sec.setStyleSheet(ms)
        for lbl, txt in [
            ("Installation","## Installation\n```bash\ngit clone https://github.com/user/repo.git\ncd repo\npip install -r requirements.txt\n```"),
            ("Usage","## Usage\n```python\nimport module\nmodule.run()\n```"),
            ("Features","## Features\n- Fast and efficient\n- Easy to use\n- Highly configurable"),
            ("Contributing","## Contributing\n1. Fork the repo\n2. Create branch `git checkout -b feature/name`\n3. Commit `git commit -m 'Add feature'`\n4. Push `git push origin feature/name`\n5. Open a Pull Request"),
            ("License","## License\nThis project is licensed under the [MIT License](LICENSE)."),
            ("Changelog","## Changelog\n\n### [1.0.0] - 2024-01-01\n- Initial release"),
        ]:
            sec.addAction(lbl).triggered.connect(lambda _, t=txt: self.insert_block(t))
        m.addMenu(sec)
        m.addSeparator()

        m.addSeparator()
        if self.app and hasattr(self.app, "user_snippets") and self.app.user_snippets:
            snip_menu = QMenu("My Snippets", m); snip_menu.setStyleSheet(ms)
            for title, content in self.app.user_snippets.items():
                snip_menu.addAction(title).triggered.connect(lambda _, c=content: self.insert_block(c))
            m.addMenu(snip_menu)
        
        m.exec(e.globalPos())

    def _ai_create_readme(self):
        d = CreateReadmeDialog(self)
        if d.exec():
            data = d.get_data()
            prompt = f"Create a professional README. Project Name: {data['Project Name']}. Description: {data['Description']}. GitHub Profile: {data['GitHub Profile']}. Language: {data['Language']}."
            self._trigger_ai(prompt)

class FindBar(QFrame):
    def __init__(self, editor, parent=None):
        super().__init__(parent); self.editor = editor; self.setFixedHeight(46)
        self.setStyleSheet(
            f"QFrame{{background:{T['bg']};border-top:1px solid {T['border']};}}"
            f"QLineEdit{{background:{T['input']};color:{T['editor']};border:1px solid {T['border']};"
            f"border-radius:10px;padding:6px 11px;font-size:12px;}}"
            f"QLineEdit:focus{{border-color:{T['accent']};}}"
            f"QPushButton#findPill{{background:{T['chip']};color:{T['text']};border:1px solid {T['chip_br']};"
            f"border-radius:15px;min-width:32px;max-width:40px;min-height:30px;max-height:30px;padding:0;font-size:13px;font-weight:700;}}"
            f"QPushButton#findPill:hover{{border-color:{T['accent']};background:{T['hover']};}}"
            f"QPushButton#findWide{{background:{T['chip']};color:{T['text']};border:1px solid {T['chip_br']};"
            f"border-radius:15px;padding:6px 12px;min-height:30px;font-size:11px;font-weight:600;}}"
            f"QPushButton#findWide:hover{{border-color:{T['accent']};background:{T['hover']};}}"
            f"QCheckBox,QLabel{{color:{T['dim']};font-size:11px;background:transparent;}}"
        )
        lay = QHBoxLayout(self); lay.setContentsMargins(10,5,10,5); lay.setSpacing(7)
        self.find = QLineEdit(); self.find.setPlaceholderText("Search…"); self.find.setFixedWidth(200)
        self.find.textChanged.connect(self._hl); lay.addWidget(self.find)
        self.repl = QLineEdit(); self.repl.setPlaceholderText("Replace…"); self.repl.setFixedWidth(200)
        lay.addWidget(self.repl)
        self.case = QCheckBox("Aa"); lay.addWidget(self.case)
        self.lbl = QLabel(""); self.lbl.setTextFormat(Qt.RichText); lay.addWidget(self.lbl)
        for lbl, fn, wide in [("▲",self._prev,False),("▼",self._next,False),("Replace",self._repl1,True),("All",self._replAll,True)]:
            b = QPushButton(lbl); b.setObjectName("findWide" if wide else "findPill")
            b.clicked.connect(fn); lay.addWidget(b)
        lay.addStretch()
        x = QPushButton("✕"); x.setObjectName("findPill"); x.setFixedSize(30, 30)
        x.clicked.connect(self._close); lay.addWidget(x)
        self.find.returnPressed.connect(self._next)

    def _close(self):
        self.hide()
        if self.editor: self.editor._highlight_line(); self.editor.setFocus()

    def set_editor(self, editor):
        if self.editor:
            try: self.editor.textChanged.disconnect(self._hl)
            except: pass
        self.editor = editor
        if self.editor: self.editor.textChanged.connect(self._hl); self._hl()

    def _flags(self):
        f = QTextDocument.FindFlag(0)
        if self.case.isChecked(): f |= QTextDocument.FindCaseSensitively
        return f

    def match_selections(self):
        if not self.editor: return []
        t = self.find.text()
        if not t: return []
        extra = []
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#CA8A04"))
        fmt.setForeground(QColor("#FFFBEB"))
        fmt.setFontUnderline(True)
        doc = self.editor.document()
        fl = self._flags()
        c = doc.find(t, 0, fl)
        while not c.isNull():
            s = QTextEdit.ExtraSelection(); s.cursor = c; s.format = fmt
            extra.append(s); c = doc.find(t, c, fl)
        return extra

    def _hl(self):
        if not self.editor: return
        t = self.find.text()
        if not t: self.lbl.setText(""); self.editor._highlight_line(); return
        extra = self.match_selections(); ct = len(extra)
        col = "#4ADE80" if ct else "#F87171"
        self.lbl.setText(f'<span style="color:{col};font-weight:700;">{ct}</span> <span style="color:{T["dim"]};">match</span>')
        self.editor._highlight_line()

    def _next(self):
        if not self.editor: return
        t = self.find.text()
        if not t: return
        if not self.editor.find(t, self._flags()):
            cur = self.editor.textCursor(); cur.movePosition(QTextCursor.Start)
            self.editor.setTextCursor(cur); self.editor.find(t, self._flags())

    def _prev(self):
        if not self.editor: return
        t = self.find.text()
        if not t: return
        fl = self._flags() | QTextDocument.FindBackward
        if not self.editor.find(t, fl):
            cur = self.editor.textCursor(); cur.movePosition(QTextCursor.End)
            self.editor.setTextCursor(cur); self.editor.find(t, fl)

    def _repl1(self):
        if not self.editor: return
        cur = self.editor.textCursor()
        if cur.hasSelection(): cur.insertText(self.repl.text())
        self._next(); self._hl()

    def _replAll(self):
        if not self.editor: return
        text = self.editor.toPlainText(); t = self.find.text()
        if not t: return
        fl = 0 if self.case.isChecked() else re.IGNORECASE
        new = re.sub(re.escape(t), self.repl.text(), text, flags=fl)
        n = len(re.findall(re.escape(t), text, fl))
        self.editor.setPlainText(new)
        self.lbl.setText(f'<span style="color:#4ADE80">{n} replaced</span>')
        self.editor._highlight_line()

class StatsBar(QFrame):
    def __init__(self, editor, parent=None):
        super().__init__(parent); self.editor = editor; self.setFixedHeight(28)
        self.setStyleSheet(
            f"QFrame{{background:{T['bg']}; border-top:1px solid rgba(255,255,255,10);}}"
            f"QLabel{{font-size:10px; font-family:'Segoe UI', sans-serif; padding:0 6px; background:transparent; color:{T['dim']};}}"
        )
        lay = QHBoxLayout(self); lay.setContentsMargins(10,0,10,0); lay.setSpacing(0)
        self.lbls = {}
        for k in ["words","chars","lines","score"]:
            l = QLabel(); l.setTextFormat(Qt.RichText); self.lbls[k] = l; lay.addWidget(l)
            if k != "score": lay.addWidget(QLabel("·"))
        lay.addStretch()
        self.cursor_lbl = QLabel(); self.cursor_lbl.setTextFormat(Qt.RichText)
        lay.addWidget(self.cursor_lbl)
        if self.editor:
            self.editor.textChanged.connect(self.refresh)
            self.editor.cursorPositionChanged.connect(self.update_cursor)
            self.refresh()

    def set_editor(self, editor):
        if self.editor:
            try:
                self.editor.textChanged.disconnect(self.refresh)
                self.editor.cursorPositionChanged.disconnect(self.update_cursor)
            except: pass
        self.editor = editor
        if self.editor:
            self.editor.textChanged.connect(self.refresh)
            self.editor.cursorPositionChanged.connect(self.update_cursor)
            self.refresh()
        else:
            for l in self.lbls.values(): l.setText("")
            self.cursor_lbl.setText("")

    def _span(self, k, v, c=None):
        col = c or T["text"]
        return (f'<span style="color:{T["dim"]}">{k}:</span>'
                f' <span style="color:{col}">{v}</span>')

    def refresh(self):
        if not self.editor: return
        txt = self.editor.toPlainText()
        w = len(txt.split()) if txt.strip() else 0
        sc, _ = readme_score(txt)
        sc_c = "#4ADE80" if sc >= 80 else ("#FBBF24" if sc >= 50 else "#F87171")
        self.lbls["words"].setText(self._span("Words", f"{w:,}"))
        self.lbls["chars"].setText(self._span("Chars", f"{len(txt):,}"))
        self.lbls["lines"].setText(self._span("Lines", f"{txt.count(chr(10))+1:,}"))
        self.lbls["score"].setText(self._span("Score", f"{sc}/100", sc_c))

    def update_cursor(self):
        if not self.editor: return
        cur = self.editor.textCursor()
        self.cursor_lbl.setText(
            f'<span style="color:{T["dim"]}">Ln {cur.blockNumber()+1} Col {cur.columnNumber()+1}</span>')

# ── Templates ──────────────────────────────────────────────────────────────
TEMPLATES = {
    "Python Lib":
        "# {name}\n\n[![PyPI](https://img.shields.io/pypi/v/{slug}?style=flat-square)](https://pypi.org/project/{slug})\n"
        "[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](#)\n"
        "[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg?style=flat-square)](#)\n\n"
        "> Short description of what this library does.\n\n"
        "## Features\n- Fast and lightweight\n- Easy to configure\n- Well documented\n\n"
        "## Install\n```bash\npip install {slug}\n```\n\n"
        "## Quick Start\n```python\nimport {slug}\n\nresult = {slug}.run()\nprint(result)\n```\n\n"
        "## Contributing\n1. Fork → Branch → Commit → Push → PR\n\n"
        "## License\nMIT © [Author](#)\n",

    "Web App":
        "# {name}\n\n[![Demo](https://img.shields.io/badge/Live-Demo-blue?style=flat-square)](#)\n"
        "[![Build](https://img.shields.io/github/actions/workflow/status/user/{slug}/main.yml?style=flat-square)](#)\n\n"
        "> A modern web application built with [Framework].\n\n"
        "## Features\n- Beautiful UI\n- Fast performance\n- Fully responsive\n- Secure\n\n"
        "## Getting Started\n```bash\ngit clone https://github.com/user/{slug}.git\ncd {slug}\nnpm install\nnpm run dev\n```\n\n"
        "## License\nMIT\n",

    "CLI Tool":
        "# {name}\n\n[![npm](https://img.shields.io/npm/v/{slug}?style=flat-square)](#)\n\n"
        "> A powerful CLI tool for [purpose].\n\n"
        "## Install\n```bash\nnpm install -g {slug}\n```\n\n"
        "## Usage\n```bash\n{slug} [command] [options]\n```\n\n"
        "## Commands\n| Command | Description |\n|---------|-------------|\n| `init` | Initialize project |\n| `build` | Build the project |\n\n"
        "## License\nMIT\n",

    "REST API":
        "# {name}\n\n[![API](https://img.shields.io/badge/API-REST-green?style=flat-square)](#)\n\n"
        "> RESTful API for [purpose].\n\n"
        "## Base URL\n```\nhttps://api.example.com/v1\n```\n\n"
        "## Authentication\n```http\nAuthorization: Bearer <token>\n```\n\n"
        "## Endpoints\n| Method | Endpoint | Description |\n|--------|----------|-------------|\n"
        "| `GET` | `/items` | List all items |\n| `POST` | `/items` | Create new |\n\n"
        "## License\nMIT\n",

    "ML Project":
        "# {name}\n\n[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python)](#)\n\n"
        "## Abstract\n> Write your abstract here.\n\n"
        "## Results\n| Model | Accuracy | F1 |\n|-------|----------|----|\n"
        "| Ours | **95.2%** | **0.94** |\n| Baseline | 88.1% | 0.87 |\n\n"
        "## Requirements\n```bash\npip install -r requirements.txt\n```\n\n"
        "## Train\n```bash\npython train.py --config configs/default.yaml\n```\n\n"
        "## License\nMIT\n",

    "Docker":
        "# {name}\n\n[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker)](#)\n\n"
        "> Containerized [purpose].\n\n"
        "## Quick Start\n```bash\ndocker pull user/{slug}\ndocker run -d -p 8080:8080 user/{slug}\n```\n\n"
        "## License\nMIT\n",

    "React Component":
        "# {name}\n\n[![npm](https://img.shields.io/npm/v/{slug}?style=flat-square)](#)\n\n"
        "> A reusable React component for [purpose].\n\n"
        "## Install\n```bash\nnpm install {slug}\n```\n\n"
        "## Usage\n```jsx\nimport {{ {name} }} from '{slug}';\n\nfunction App() {{\n"
        "  return <{name} prop=\"value\" />;\n}}\n```\n\n"
        "## License\nMIT\n",

    "Minimal":
        "# {name}\n\n> Short description.\n\n"
        "## Install\n```bash\npip install {slug}\n```\n\n"
        "## Usage\n```python\nimport {slug}\n{slug}.run()\n```\n\n"
        "## License\nMIT\n",

    "Open Source":
        "# {name}\n\n[![Stars](https://img.shields.io/github/stars/user/{slug}?style=social)](#)\n"
        "[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](#)\n\n"
        "> {name} is an open-source project that [purpose].\n\n"
        "## Features\n- Feature one\n- Feature two\n- Feature three\n\n"
        "## Installation\n```bash\ngit clone https://github.com/user/{slug}.git\ncd {slug}\npip install -e .\n```\n\n"
        "## Contributing\nWe welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md).\n\n"
        "## License\nMIT © [Author](#) — see [LICENSE](LICENSE)\n",
}

SNIPPETS = {
    "Note Alert":    "> [!NOTE]\n> Add your note here.\n",
    "Warning Alert": "> [!WARNING]\n> Add your warning here.\n",
    "Tip Alert":     "> [!TIP]\n> Pro tip: Read the full documentation first.\n",
    "Important Alert":"> [!IMPORTANT]\n> Breaking changes in v2.0. See migration guide.\n",
    "Caution Alert": "> [!CAUTION]\n> This operation is irreversible.\n",
    "Features":      "## Features\n- Performance: Lightning fast.\n- Modern UI: Clean minimal style.\n- Secure: End-to-end encryption.\n",
    "Installation":  "## Installation\n1. Clone:\n```bash\ngit clone https://github.com/user/repo.git\n```\n2. Install:\n```bash\npip install -r requirements.txt\n```\n",
    "Author":        "### Author\n**Your Name** - [GitHub](https://github.com/) - [LinkedIn](#)\n",
    "License MIT":   "## License\nThis project is licensed under the **MIT License** - see [LICENSE](LICENSE) for details.\n",
    "Contributing":  "## Contributing\n1. Fork the Project\n2. Create branch (`git checkout -b feature/X`)\n3. Commit (`git commit -m 'Add X'`)\n4. Push (`git push origin feature/X`)\n5. Open a Pull Request\n",
    "Roadmap":       "## Roadmap\n- [x] Initial release\n- [x] Core features\n- [ ] Version 2.0\n- [ ] Mobile support\n",
    "Badges Row":    "[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#) [![Stars](https://img.shields.io/github/stars/USER/REPO?style=social)](#)\n",
}

# ── Template Picker ────────────────────────────────────────────────────────
class TemplatePicker(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.result_text = ""
        self.setWindowTitle("Templates"); self.setFixedSize(900, 560)
        lay = QVBoxLayout(self); lay.setContentsMargins(18,14,18,14); lay.setSpacing(10)
        lay.addWidget(QLabel("Quick Templates", styleSheet=f"font-size:16px;font-weight:600;color:{T['text']};"))
        row = QHBoxLayout()
        row.addWidget(QLabel("Project name:", styleSheet=f"color:{T['dim']};font-size:12px;min-width:90px;"))
        self.name = QLineEdit(); self.name.setPlaceholderText("My Awesome Project")
        self.name.textChanged.connect(self._update_preview)
        row.addWidget(self.name); lay.addLayout(row)

        body = QSplitter(Qt.Horizontal)
        left = QWidget()
        sa = QScrollArea(); sa.setWidgetResizable(True)
        sa.setStyleSheet(f"QScrollArea{{border:none;background:{T['bg']};}}")
        inner = QWidget(); inner.setStyleSheet(f"background:{T['bg']};")
        grid = QGridLayout(inner); grid.setSpacing(6); grid.setContentsMargins(2,2,2,2)
        self._sel = None; self._btns = []
        for i, k in enumerate(TEMPLATES):
            b = QPushButton(k); b.setCheckable(True); b.setFixedHeight(38)
            b.setStyleSheet(
                f"QPushButton{{background:{T['hover']};color:{T['text']};border:1px solid {T['border']};"
                f"border-radius:6px;font-size:11px;font-weight:600;}}"
                f"QPushButton:hover{{border-color:{T['accent']};}}"
                f"QPushButton:checked{{background:{T['accent']};color:#F5F5F5;border-color:{T['accent']};}}"
            )
            b.clicked.connect(lambda _, k=k, b=b: self._pick(k, b))
            grid.addWidget(b, i//3, i%3); self._btns.append(b)
        sa.setWidget(inner)
        ll = QVBoxLayout(left); ll.setContentsMargins(0,0,0,0); ll.addWidget(sa)
        body.addWidget(left)

        self._preview = QTextBrowser()
        self._preview.setOpenExternalLinks(False)
        self._preview.setStyleSheet(
            f"QTextBrowser{{background:{T['bg']};color:{T['text']};border:1px solid {T['border']};border-radius:8px;padding:10px;}}"
        )
        self._preview.document().setDefaultStyleSheet(preview_css())
        self._preview.setHtml(f"<p style='color:{T['dim']};text-align:center;margin-top:80px;'>Select a template to preview</p>")
        body.addWidget(self._preview)
        body.setSizes([380, 480])
        lay.addWidget(body, 1)

        row2 = QHBoxLayout()
        c = QPushButton("Cancel"); c.clicked.connect(self.reject); row2.addWidget(c)
        a = QPushButton("Apply")
        a.setStyleSheet(f"background:{T['accent']};color:#F5F5F5;border:1px solid {T['border']};border-radius:7px;padding:8px 16px;font-weight:600;")
        a.clicked.connect(self._apply); row2.addWidget(a)
        lay.addLayout(row2)

    def _pick(self, k, btn):
        self._sel = k
        for b in self._btns: b.setChecked(False)
        btn.setChecked(True); self._update_preview()

    def _update_preview(self):
        if not self._sel: return
        name = self.name.text().strip() or "My Project"
        slug = re.sub(r"[^a-z0-9-]", "-", name.lower()).strip("-")
        md = TEMPLATES[self._sel].replace("{name}", name).replace("{slug}", slug)
        html_out = markdown2.markdown(md, extras=["fenced-code-blocks","tables","task_list","strike"])
        self._preview.setHtml(html_out)

    def _apply(self):
        if not self._sel: QMessageBox.warning(self,"","Select a template first."); return
        name = self.name.text().strip() or "My Project"
        slug = re.sub(r"[^a-z0-9-]", "-", name.lower()).strip("-")
        self.result_text = TEMPLATES[self._sel].replace("{name}", name).replace("{slug}", slug)
        self.accept()

# ── Score Dialog ────────────────────────────────────────────────────────────
class ScoreDialog(QDialog):
    def __init__(self, score, tips, parent=None):
        super().__init__(parent)
        self.setWindowTitle("README Score"); self.setFixedSize(500, 520)
        lay = QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(15)
        lbl_top = QLabel("Current Score"); lbl_top.setAlignment(Qt.AlignCenter)
        lbl_top.setStyleSheet(f"color:{T['dim']};font-size:14px;")
        lay.addWidget(lbl_top)
        lbl_score = QLabel(f"{score}/100"); lbl_score.setAlignment(Qt.AlignCenter)
        lbl_score.setStyleSheet("font-size:48px;color:#dd8448;font-weight:bold;margin:10px 0;")
        lay.addWidget(lbl_score)
        stars = max(1, min(5, score // 20)) if score > 0 else 1
        if score >= 80: stars = 5
        star_lay = QHBoxLayout(); star_lay.setAlignment(Qt.AlignCenter)
        for i in range(5):
            lbl = QLabel("★" if i < stars else "☆")
            lbl.setStyleSheet("font-size:44px;color:#dd8448;" if i < stars else f"font-size:44px;color:{T['border']};")
            star_lay.addWidget(lbl)
        lay.addLayout(star_lay)
        if tips:
            tips_area = QScrollArea(); tips_area.setWidgetResizable(True)
            tips_area.setStyleSheet(f"QScrollArea{{border:1px solid {T['border']};border-radius:10px;background:{T['bg']};}}")
            tips_container = QWidget(); tips_container.setStyleSheet("background:transparent;")
            tips_lay = QVBoxLayout(tips_container); tips_lay.setContentsMargins(15,15,15,15); tips_lay.setSpacing(8)
            tips_lay.addWidget(QLabel(f"Suggestions:", styleSheet=f"color:{T['text']};font-weight:bold;font-size:14px;"))
            for t in tips:
                lbl = QLabel(f"• {t}"); lbl.setStyleSheet(f"color:{T['dim']};font-size:13px;")
                lbl.setWordWrap(True); tips_lay.addWidget(lbl)
            tips_lay.addStretch()
            tips_area.setWidget(tips_container); lay.addWidget(tips_area, 1)
        else:
            lay.addStretch()
        btn_lay = QHBoxLayout()
        auto_btn = QPushButton("Auto-Perfect (AI)")
        auto_btn.setStyleSheet(f"background:{T['accent2']};color:#F5F5F5;border:1px solid {T['border']};border-radius:7px;padding:10px 24px;font-weight:600;")
        def do_auto():
            if not parent or not hasattr(parent, "ai_panel"): return
            if not parent.ai_panel.isVisible(): parent._toggle_ai()
            parent.ai_panel.inp.setPlainText("Update this README to achieve a 100% score based on standard README sections.")
            self.accept()
            QTimer.singleShot(100, parent.ai_panel._send)
        auto_btn.clicked.connect(do_auto); btn_lay.addWidget(auto_btn); btn_lay.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(f"background:{T['accent']};color:#F5F5F5;border:1px solid {T['border']};border-radius:7px;padding:10px 24px;font-weight:600;")
        close_btn.clicked.connect(self.accept); btn_lay.addWidget(close_btn)
        lay.addLayout(btn_lay)

# ── Image Manager Dialog ───────────────────────────────────────────────────
class ImageDialog(QDialog):
    def __init__(self, editor, workspace_dir, parent=None):
        super().__init__(parent)
        self.editor = editor; self.workspace_dir = workspace_dir
        self.setWindowTitle("Project Images"); self.setFixedSize(450, 550)
        layout = QVBoxLayout(self); layout.setContentsMargins(15,15,15,15); layout.setSpacing(12)
        layout.addWidget(QLabel("Select images from project:", styleSheet=f"font-weight:600;color:{T['text']};"))
        self.img_list = QListWidget(); self.img_list.setSelectionMode(QAbstractItemView.MultiSelection)
        layout.addWidget(self.img_list)
        btns = QGridLayout(); btns.setSpacing(12)
        for txt, fn, pos in [("Table",lambda: self.insert_images("table"),(0,0)),("List",lambda: self.insert_images("list"),(0,1)),("Grid",lambda: self.insert_images("grid"),(1,0)),("Refresh",self.scan_images,(1,1))]:
            b = QPushButton(txt); b.clicked.connect(fn); btns.addWidget(b, *pos)
        layout.addLayout(btns)
        bot = QHBoxLayout(); bot.addStretch()
        cancel = QPushButton("Cancel"); cancel.clicked.connect(self.reject); bot.addWidget(cancel)
        layout.addLayout(bot)
        self.scan_images()

    def scan_images(self):
        self.img_list.clear()
        exts = {'.png','.jpg','.jpeg','.gif','.svg','.webp','.bmp'}
        try:
            ws = Path(self.workspace_dir)
            for p in ws.rglob("*"):
                if p.suffix.lower() in exts:
                    rel_p = "/".join(p.relative_to(ws).parts)
                    self.img_list.addItem(rel_p)
        except: pass

    def insert_images(self, style):
        selected = [item.text() for item in self.img_list.selectedItems()]
        if not selected: QMessageBox.information(self, "Selection Required", "Please select at least one image."); return
        code = ""
        if style == "table":
            code = "\n| Image | Image |\n|---|---|\n"
            for i in range(0, len(selected), 2):
                img1 = f"![{Path(selected[i]).stem}]({selected[i]})"
                img2 = f"![{Path(selected[i+1]).stem}]({selected[i+1]})" if i+1 < len(selected) else ""
                code += f"| {img1} | {img2} |\n"
            code += "\n"
        elif style == "list":
            code = "\n" + "\n".join([f"- ![{Path(img).stem}]({img})" for img in selected]) + "\n"
        elif style == "grid":
            code = "\n<div align='center'>\n\n"
            for img in selected: code += f"<img src='{img}' width='32%' style='margin:5px;' />\n"
            code += "\n</div>\n"
        if hasattr(self.editor, "insert_block"): self.editor.insert_block(code)
        else: self.editor.insertPlainText(code)
        self.accept()

def _unique_asset_roots(workspace_dir):
    roots = []; seen = set()
    # Priority: sys._MEIPASS (bundled), Workspace, Script Dir, CWD
    bundled = getattr(sys, '_MEIPASS', None)
    search = []
    if bundled: search.append(bundled)
    search.extend([workspace_dir, os.path.dirname(os.path.abspath(__file__)), os.getcwd()])
    
    for c in search:
        if not c: continue
        p = Path(c).resolve()
        if p not in seen: seen.add(p); roots.append(p)
    return roots

# ── Social Picker ─────────────────────────────────────────────────────────
class SocialPickerDialog(QDialog):
    def __init__(self, editor, workspace_dir, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.workspace_dir = os.path.abspath(workspace_dir or os.getcwd())
        self.setWindowTitle("Social Icons"); self.setMinimumSize(520, 420)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Click an icon to insert its SVG into the README."))
        grid_w = QWidget(); grid = QGridLayout(grid_w); grid.setSpacing(8)
        entries = []; seen_paths = set()
        for root in _unique_asset_roots(self.workspace_dir):
            soc = root / "social"
            if not soc.is_dir(): continue
            for p in sorted(soc.rglob("*.svg")):
                rp = str(Path(p).resolve())
                if rp in seen_paths: continue
                seen_paths.add(rp)
                try: rel = str(Path(p).relative_to(soc))
                except ValueError: rel = p.name
                entries.append((rp, rel.replace("\\", "/")))
        col = row = 0
        for path, rel in entries:
            btn = QToolButton()
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            btn.setIcon(QIcon(path)); btn.setIconSize(QSize(40, 40))
            btn.setText(Path(rel).parts[0] if "/" in rel else Path(rel).stem)
            btn.setFixedSize(110, 88)
            btn.clicked.connect(lambda _, p=path, r=rel: self._insert_svg(p, r))
            grid.addWidget(btn, row, col); col += 1
            if col >= 4: col = 0; row += 1
        if not entries: grid.addWidget(QLabel("No SVG found. Add a social/ folder with .svg files."), 0, 0)
        sa = QScrollArea(); sa.setWidgetResizable(True); sa.setWidget(grid_w)
        lay.addWidget(sa, 1)
        row_b = QHBoxLayout(); row_b.addStretch()
        close = QPushButton("Close"); close.clicked.connect(self.reject); row_b.addWidget(close)
        lay.addLayout(row_b)

    def _insert_svg(self, path, rel_hint):
        try: raw = Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError as e: QMessageBox.warning(self, "Read error", str(e)); return
        block = f"\n<!-- social: {rel_hint} -->\n<p align=\"left\">\n{raw.strip()}\n</p>\n\n"
        if hasattr(self.editor, "insert_block"): self.editor.insert_block(block)
        else: self.editor.insertPlainText(block)
        self.accept()


# ── Translate Dialog ───────────────────────────────────────────────────────
class TranslateDialog(QDialog):
    def __init__(self, text, parent=None):
        super().__init__(parent); self.text = text; self.result = ""
        self.setWindowTitle("Translate README"); self.setMinimumSize(680, 500)
        lay = QVBoxLayout(self); lay.setContentsMargins(18,16,18,16); lay.setSpacing(12)
        lay.addWidget(QLabel("Translate README", styleSheet="font-size:16px;font-weight:600;"))
        top = QHBoxLayout()
        top.addWidget(QLabel("Source:", styleSheet=f"color:{T['dim']};"))
        self.src_combo = QComboBox()
        for code, name in [("en","English"),("fr","French"),("es","Spanish"),("de","German"),("zh","Chinese"),("ja","Japanese"),("ar","Arabic"),("pt","Portuguese"),("ru","Russian"),("ko","Korean")]:
            self.src_combo.addItem(f"{name} ({code})", code)
        top.addWidget(self.src_combo)
        top.addWidget(QLabel("→ Target:", styleSheet=f"color:{T['dim']};"))
        self.tgt_combo = QComboBox()
        for code, name in [("fr","French"),("es","Spanish"),("de","German"),("zh","Chinese"),("ar","Arabic"),("en","English"),("it","Italian"),("ru","Russian"),("ko","Korean")]:
            self.tgt_combo.addItem(f"{name} ({code})", code)
        top.addWidget(self.tgt_combo)
        translate_btn = QPushButton("Translate")
        translate_btn.setStyleSheet(f"background:{T['accent']};color:#F5F5F5;border:1px solid {T['border']};border-radius:7px;padding:8px 20px;font-weight:600;")
        translate_btn.clicked.connect(self._translate); top.addWidget(translate_btn)
        top.addStretch(); lay.addLayout(top)
        split = QHBoxLayout(); lay.addLayout(split, 1)
        for lbl, attr, t in [("Source","src_edit",text),("Translation","tgt_edit","")]:
            col = QVBoxLayout(); col.addWidget(QLabel(lbl, styleSheet=f"font-size:11px;color:{T['dim']};font-weight:600;"))
            edit = QTextEdit(); edit.setPlainText(t)
            if lbl == "Source": edit.setReadOnly(True)
            setattr(self, attr, edit); col.addWidget(edit); split.addLayout(col)
        self.status = QLabel(""); self.status.setStyleSheet(f"color:{T['dim']};font-size:11px;")
        lay.addWidget(self.status)
        bot = QHBoxLayout(); bot.addWidget(self.status); bot.addStretch()
        cancel = QPushButton("Cancel"); cancel.clicked.connect(self.reject); bot.addWidget(cancel)
        apply = QPushButton("Apply Translation")
        apply.setStyleSheet(f"background:{T['accent']};color:#F5F5F5;border:1px solid {T['border']};border-radius:7px;padding:8px 16px;font-weight:600;")
        apply.clicked.connect(self._apply); bot.addWidget(apply); lay.addLayout(bot)

    def _translate(self):
        src = self.src_combo.currentData(); tgt = self.tgt_combo.currentData()
        text = self.src_edit.toPlainText().strip()
        if not text: return
        self.status.setText("Translating…"); QApplication.processEvents()
        paragraphs = text.split("\n\n"); translated = []
        for para in paragraphs:
            if not para.strip(): translated.append(""); continue
            if para.strip().startswith("```"): translated.append(para); continue
            try:
                q = urllib.parse.quote(para[:450])
                url = f"https://api.mymemory.translated.net/get?q={q}&langpair={src}|{tgt}"
                resp = urllib.request.urlopen(url, timeout=8)
                data = json.loads(resp.read().decode())
                translated.append(data["responseData"]["translatedText"] if data.get("responseStatus") == 200 else para)
            except: translated.append(para)
        self.tgt_edit.setPlainText("\n\n".join(translated))
        self.status.setText(f"Translation complete ({src} → {tgt})")

    def _apply(self):
        self.result = self.tgt_edit.toPlainText()
        if self.result: self.accept()

# ── Repair ─────────────────────────────────────────────────────────────────
def repair_markdown(text):
    lines = text.split("\n"); out = []; issues = []
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6})([^ #\n])", line)
        if m: line = m.group(1) + " " + line[len(m.group(1)):]; issues.append(f"Line {i+1}: Added space after heading")
        if "![" in line or "](" in line:
            def fix_path(m):
                pre, path, post = m.group(1), m.group(2), m.group(3)
                if "\\" in path: issues.append(f"Line {i+1}: Fixed backslash in path")
                return pre + path.replace("\\", "/") + post
            line = re.sub(r'(\!\[.*?\]\()([^)]+)(\))', fix_path, line)
            line = re.sub(r'(\[.*?\]\()([^)]+)(\))', fix_path, line)
        out.append(line)
    result = "\n".join(out)
    result2 = []
    lines2 = result.split("\n")
    for i, line in enumerate(lines2):
        if re.match(r"^#{1,6} ", line):
            if i > 0 and lines2[i-1].strip(): result2.append(""); issues.append("Added blank line before heading")
            result2.append(line)
            if i < len(lines2)-1 and lines2[i+1].strip() and not re.match(r"^#{1,6} ", lines2[i+1]): result2.append("")
        else: result2.append(line)
    result = "\n".join(result2)
    result = re.sub(r"\n{4,}", "\n\n\n", result)
    if result.count("```") % 2 != 0: result += "\n```"; issues.append("Closed unclosed code block")
    result = result.rstrip("\n") + "\n"
    return result, issues

class RepairDialog(QDialog):
    def __init__(self, text, parent=None):
        super().__init__(parent); self.text = text; self.result = ""
        self.setWindowTitle("Repair Markdown"); self.setMinimumSize(680, 500)
        lay = QVBoxLayout(self); lay.setContentsMargins(18,16,18,16); lay.setSpacing(12)
        lay.addWidget(QLabel("Repair Markdown", styleSheet="font-size:16px;font-weight:600;"))
        fixed, issues = repair_markdown(text); self._fixed = fixed
        if issues:
            issue_frame = QFrame()
            issue_frame.setStyleSheet(f"QFrame{{background:{T['panel']};border:1px solid {T['border']};border-radius:8px;}}")
            ifl = QVBoxLayout(issue_frame); ifl.setContentsMargins(10,8,10,8); ifl.setSpacing(4)
            ifl.addWidget(QLabel(f"Fixed {len(issues)} issue(s):", styleSheet="color:#4ADE80;font-weight:600;font-size:12px;"))
            for iss in issues[:10]: ifl.addWidget(QLabel(f"  • {iss}", styleSheet=f"color:{T['dim']};font-size:11px;"))
            lay.addWidget(issue_frame)
        else:
            lay.addWidget(QLabel("No issues found — your Markdown looks clean!", styleSheet="color:#4ADE80;font-size:13px;"))
        split = QHBoxLayout(); lay.addLayout(split, 1)
        for lbl, attr, t in [("Original","orig",text),("Repaired","repaired",fixed)]:
            col = QVBoxLayout(); col.addWidget(QLabel(lbl, styleSheet=f"font-size:11px;color:{T['dim']};font-weight:600;"))
            edit = QTextEdit(); edit.setPlainText(t); edit.setReadOnly(True)
            edit.setStyleSheet(f"background:{T['input']};color:{T['editor']};border:1px solid {T['border']};border-radius:6px;font-family:monospace;font-size:12px;")
            setattr(self, attr, edit); col.addWidget(edit); split.addLayout(col)
        bot = QHBoxLayout(); bot.addStretch()
        cancel = QPushButton("Cancel"); cancel.clicked.connect(self.reject); bot.addWidget(cancel)
        apply = QPushButton("Apply Repairs")
        apply.setStyleSheet(f"background:{T['accent']};color:#F5F5F5;border:1px solid {T['border']};border-radius:7px;padding:8px 16px;font-weight:600;")
        apply.clicked.connect(self._apply); bot.addWidget(apply); lay.addLayout(bot)

    def _apply(self): self.result = self._fixed; self.accept()

# ── Self Install (disabled on startup; kept for manual use) ────
def self_install():
    """Install to LocalAppData on first run; never re-copy if already at target."""
    if not getattr(sys, 'frozen', False):
        return
    current_exe = os.path.normpath(sys.executable)
    local_app = os.getenv('LOCALAPPDATA', '')
    if not local_app:
        return
    target_dir = os.path.join(local_app, 'Programs', 'READMEBuilder')
    target_exe = os.path.normpath(os.path.join(target_dir, 'READMEBuilder.exe'))

    # Already running from installed location — do nothing
    if current_exe == target_exe:
        return

    try:
        os.makedirs(target_dir, exist_ok=True)

        # If target exists and is locked (already running), just relaunch with args
        if os.path.exists(target_exe):
            try:
                os.rename(target_exe, target_exe + ".bak")
                os.remove(target_exe + ".bak")
            except PermissionError:
                # Installed version is running — relaunch it with the original file args
                args = [target_exe] + sys.argv[1:]
                subprocess.Popen(args)
                sys.exit(0)

        shutil.copy2(current_exe, target_exe)

        # Create desktop shortcut
        desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
        lnk_path = os.path.join(desktop, "README Builder.lnk")
        ps_cmd = (
            f'$s=(New-Object -ComObject WScript.Shell).CreateShortcut("{lnk_path}");'
            f'$s.TargetPath="{target_exe}";'
            f'$s.WorkingDirectory="{target_dir}";'
            f'$s.Description="README Builder Pro";'
            f'$s.Save()'
        )
        subprocess.run(
            ["powershell", "-WindowStyle", "Hidden", "-Command", ps_cmd],
            check=False,
            creationflags=0x08000000,
        )

        # ── Relaunch installed copy, preserving the file argument ──
        args = [target_exe] + sys.argv[1:]
        subprocess.Popen(args)
        sys.exit(0)
    except Exception:
        pass  # Silent failure — run from current location

# ── Context Menu Registration ──────────────────────────────────────────────
def auto_register_context_menu():
    if sys.platform != "win32": return
    try:
        import winreg
    except ImportError:
        return
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
    else:
        exe_path = os.path.abspath(sys.argv[0])
    exe_str = f'"{exe_path}"'

    # Register "Open with README Builder" for all files
    try:
        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\*\shell\Open with README Builder")
        winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, exe_path)
        winreg.SetValueEx(k, "Position", 0, winreg.REG_SZ, "Top")
        winreg.SetValueEx(winreg.CreateKey(k, "command"), "", 0, winreg.REG_SZ, f'{exe_str} "%1"')
        winreg.CloseKey(k)
    except Exception as e:
        print(f"Warning: Could not register file context menu: {e}")

    # Register folder context menu
    try:
        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\Directory\shell\Create README here")
        winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, exe_path)
        winreg.SetValueEx(winreg.CreateKey(k, "command"), "", 0, winreg.REG_SZ, f'{exe_str} "%1"')
        winreg.CloseKey(k)
    except Exception as e:
        print(f"Warning: Could not register folder context menu: {e}")

    # Register folder background context menu
    try:
        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\Directory\Background\shell\Create README here")
        winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, exe_path)
        winreg.SetValueEx(winreg.CreateKey(k, "command"), "", 0, winreg.REG_SZ, f'{exe_str} "%V"')
        winreg.CloseKey(k)
    except Exception as e:
        print(f"Warning: Could not register folder background context menu: {e}")

    # Register .md file association
    try:
        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\READMEBuilder.Markdown\shell\open\command")
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, f'{exe_str} "%1"')
        winreg.CloseKey(k)

        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.md")
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "READMEBuilder.Markdown")
        winreg.CloseKey(k)
    except Exception as e:
        print(f"Warning: Could not register .md file association: {e}")

    # Notify Windows Shell about the changes
    try:
        import ctypes
        SHCNE_ASSOCCHANGED = 0x08000000
        SHCNF_IDLIST = 0x0000
        ctypes.windll.shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)
    except Exception as e:
        print(f"Warning: Could not notify shell: {e}")

# ── Minimap ────────────────────────────────────────────────────────────────
class Minimap(QWidget):
    def __init__(self, target, parent=None):
        super().__init__(parent)
        self.target = target; self.setFixedWidth(60)
        self.peer = None; self._doc_h = 800
        self.target.verticalScrollBar().valueChanged.connect(self.update)
        try: self.target.textChanged.connect(self.update)
        except: pass
        self.setCursor(Qt.PointingHandCursor); self.setMouseTracking(True)

    def paintEvent(self, e):
        p = QPainter(self); p.fillRect(self.rect(), QColor(T["bg"]))
        h = self.height()
        eh = self.target.height()
        doc = self.target.document()
        if not doc: return
        th = doc.size().height()
        if th == 0 or eh == 0: return
        scale = h / max(th, eh); p.save(); p.scale(scale, scale)
        
        # Draw code-like colored lines
        is_preview = isinstance(self.target, QTextBrowser)
        blk = doc.begin()
        while blk.isValid():
            rect = doc.documentLayout().blockBoundingRect(blk)
            if rect.top() > th: break
            
            text = blk.text().strip()
            if text or is_preview: # For preview, we might have blocks that are just containers
                if is_preview:
                    # In preview, we use simpler heuristic or random-ish code colors to make it look like the editor
                    import random
                    random.seed(blk.blockNumber())
                    colors = ["#FF6188", "#A9DC76", "#AB9DF2", "#FC9867", "#78DCE8", "#FDF9F3"]
                    color = QColor(random.choice(colors))
                    line_w = min(random.randint(20, 60), int(self.width()/scale)-8)
                else:
                    # Monaco/Monokai-inspired vibrant colors for the editor
                    if text.startswith('#'): color = QColor("#FF6188")
                    elif text.startswith('```'): color = QColor("#A9DC76")
                    elif text.startswith(('- ', '* ', '1. ')): color = QColor("#AB9DF2")
                    elif '![' in text: color = QColor("#FC9867")
                    elif '[' in text: color = QColor("#78DCE8")
                    else: color = QColor("#FDF9F3")
                    line_w = min(len(text) * 1.5, int(self.width()/scale)-8)
                
                p.setPen(color)
                p.drawLine(4, int(rect.top()), 4 + int(line_w), int(rect.top()))
            
            blk = blk.next()
        p.restore()
        
        sb = self.target.verticalScrollBar()
        total = sb.maximum() + eh
        if total > 0:
            vy = (sb.value() / total) * h; vh = (eh / total) * h
            # Ghostly selection area - subtle white/grey
            p.setOpacity(0.05); p.fillRect(0, 0, self.width(), h, QColor(255, 255, 255, 20))
            p.setOpacity(0.12); p.fillRect(0, int(vy), self.width(), int(vh), QColor(255, 255, 255))
            p.setOpacity(0.3); p.setPen(QColor(255, 255, 255, 80)); p.drawRect(0, int(vy), self.width()-1, int(vh)-1)

    def _scroll(self, y, sync):
        h = max(self.height(), 1); y_frac = y / h
        sb = self.target.verticalScrollBar(); eh = self.target.viewport().height()
        if sb: sb.setValue(int(y_frac * (sb.maximum() + eh) - eh/2))
        if sync and self.peer:
            psb = self.peer.verticalScrollBar(); peh = self.peer.viewport().height()
            if psb: psb.setValue(int(y_frac * (psb.maximum() + peh) - peh/2))

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton: self._scroll(int(e.position().y()), bool(e.modifiers() & Qt.AltModifier))
    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.LeftButton: self._scroll(int(e.position().y()), bool(e.modifiers() & Qt.AltModifier))
    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton: self._scroll(int(e.position().y()), True)

# ── Document Tab ────────────────────────────────────────────────────────────
class DocTab(QWidget):
    def __init__(self, parent, content=None, workspace=None, title="README.md"):
        super().__init__(parent)
        self.app = parent
        self.workspace = os.path.abspath(workspace or os.getcwd())
        self.file_name = title
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        self.editor = Editor(self.app)
        self.editor.textChanged.connect(self._on_change)
        if content: self.editor.setPlainText(content)

        # Always use QTextBrowser (no WebEngine)
        self.preview = PreviewBrowser(self.workspace)
        self.preview.setOpenExternalLinks(True)
        self.preview.setContextMenuPolicy(Qt.NoContextMenu)
        self.preview.setStyleSheet(f"QTextBrowser{{background:{T['bg']};color:#e6edf3;border:none;padding:10px;}}")

        self.e_map = Minimap(self.editor)
        self.p_map = Minimap(self.preview)
        self.e_map.peer = self.preview; self.p_map.peer = self.editor

        self.split = QSplitter(Qt.Horizontal)
        self.split.addWidget(self.editor); self.split.addWidget(self.e_map)
        self.split.addWidget(self.preview); self.split.addWidget(self.p_map)
        self.split.setSizes([430, 50, 430, 50])
        self.split.setHandleWidth(2); self.split.setChildrenCollapsible(False)
        self.split.setStyleSheet(f"QSplitter::handle{{background:{T['border']};}}")
        lay.addWidget(self.split)

        self.ai_panel = NewAIPanel(self)
        self.ai_panel.show() # Show by default
        QTimer.singleShot(100, self.ai_panel.update_position)

        self._worker = RenderWorker()
        self._render_thread = QThread()
        self._worker.moveToThread(self._render_thread)
        self._worker.finished.connect(self._on_html)
        self._render_thread.start()

        self._timer = QTimer(); self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._request_render)
        self.editor.textChanged.connect(lambda: self._timer.start(300))

        # Sync editor scroll to preview scroll proportionally
        self.editor.verticalScrollBar().valueChanged.connect(self._sync_preview_scroll)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.ai_panel.update_position()

    def showEvent(self, e):
        super().showEvent(e)
        QTimer.singleShot(0, self.ai_panel.update_position)

    def _on_change(self): self.app.stats.refresh()

    def _sync_preview_scroll(self, editor_val):
        """Sync preview scroll position to match editor's relative position."""
        e_sb = self.editor.verticalScrollBar()
        p_sb = self.preview.verticalScrollBar()
        e_max = e_sb.maximum()
        p_max = p_sb.maximum()
        if e_max > 0 and p_max > 0:
            ratio = editor_val / e_max
            p_sb.blockSignals(True)
            p_sb.setValue(int(ratio * p_max))
            p_sb.blockSignals(False)

    def _request_render(self):
        if not self.editor.toPlainText().strip():
            self._show_empty_preview(); return
        self._worker.request(self.editor.toPlainText())
        QTimer.singleShot(0, self._worker.process)

    def _show_empty_preview(self):
        empty = (f"<!DOCTYPE html><html><head><meta charset='UTF-8'>"
                 f"<style>html,body{{margin:0;padding:0;height:100%;background:{T['bg']};}}</style>"
                 f"</head><body></body></html>")
        self.preview.setHtml(empty)

    def _on_html(self, html_out):
        css = preview_css()
        full = f"<!DOCTYPE html><html><head><meta charset='UTF-8'>{css}</head><body><div id='content'>{html_out}</div></body></html>"

        # Save scroll position
        sb = self.preview.verticalScrollBar()
        ratio = 0
        if sb.maximum() > 0:
            ratio = sb.value() / sb.maximum()

        self.preview.setUpdatesEnabled(False)
        self.preview.setHtml(full)
        
        def restore():
            if ratio > 0:
                sb.setValue(int(ratio * sb.maximum()))
            self.preview.setUpdatesEnabled(True)
            self.preview.update()
        QTimer.singleShot(1, restore)

    def stop(self):
        """Fast cleanup — terminate threads without long waits."""
        self._timer.stop()
        # Stop render thread
        if hasattr(self, '_render_thread') and self._render_thread.isRunning():
            self._render_thread.quit()
            if not self._render_thread.wait(400):
                self._render_thread.terminate()
                self._render_thread.wait(200)
        # Stop image fetcher threads
        if isinstance(self.preview, PreviewBrowser):
            self.preview.shutdown_network_threads(wait_ms=400)


# ── AI Logic (Llama Server) ────────────────────────────────────────────────
class LlamaServer(QObject):
    status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        self.process = None
        self.is_running = False
        
        self.server_path = resource_path(os.path.join("server", "llama-server.exe"))
        self.model_path = resource_path(os.path.join("models", "qwen2.5-0.5b.gguf"))

    def start(self):
        if self.process and self.process.state() == QProcess.Running:
            return True
            
        if not os.path.exists(self.server_path):
            self.error_occurred.emit(f"Server not found: {self.server_path}")
            return False
            
        if not os.path.exists(self.model_path):
            self.error_occurred.emit(f"Model not found: {self.model_path}")
            return False

        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        
        # Command to start llama-server
        args = [
            "-m", self.model_path,
            "--port", "8080",
            "-c", "2048",
            "--n-gpu-layers", "0" 
        ]
        
        self.status_changed.emit("Starting AI Server...")
        self.process.start(self.server_path, args)
        
        if not self.process.waitForStarted(5000):
            self.error_occurred.emit("Failed to start AI server process.")
            return False
            
        self.is_running = True
        self.status_changed.emit("AI Server Running")
        return True

    def stop(self):
        if self.process and self.process.state() == QProcess.Running:
            self.process.kill()
            self.process.waitForFinished(500)
            self.is_running = False

class LlamaWorker(QObject):
    finished = Signal(str)
    chunk = Signal(str)
    error = Signal(str)

    def __init__(self, prompt, context=""):
        super().__init__()
        self.prompt = prompt
        self.context = context
        self._abort = False

    def abort(self):
        self._abort = True

    def run(self):
        try:
            url = "http://localhost:8080/completion"
            # Simplified prompt for small models
            role_hint = "You are a professional assistant."
            if "Selected Text:" in self.context:
                role_hint += " Focus specifically on the 'Selected Text' provided."
                
            full_prompt = (
                f"<|im_start|>system\n"
                f"{role_hint} Respond ONLY with direct markdown. NO emojis. NO chat. NO repetition.\n"
                f"<|im_end|>\n"
                f"<|im_start|>user\n"
                f"Context:\n{self.context}\n\nTask: {self.prompt}\n"
                f"<|im_end|>\n"
                f"<|im_start|>assistant\n"
            )
            
            data = json.dumps({
                "prompt": full_prompt,
                "n_predict": 600,
                "stream": True,
                "stop": ["<|im_end|>", "<|im_start|>", "User:", "Assistant:", "😊"],
                "temperature": 0.1,
                "repeat_penalty": 1.2,
                "top_p": 0.9,
                "presence_penalty": 0.2
            }).encode("utf-8")
            
            req = urllib.request.Request(url, data=data, method="POST")
            req.add_header("Content-Type", "application/json")
            
            full_response = ""
            with urllib.request.urlopen(req, timeout=120) as response:
                for line in response:
                    if self._abort: break
                    if not line.strip(): continue
                    
                    line_str = line.decode("utf-8")
                    if line_str.startswith("data: "):
                        try:
                            obj = json.loads(line_str[6:])
                            token = obj.get("content", "")
                            if token:
                                full_response += token
                                self.chunk.emit(token)
                            if obj.get("stop"): break
                        except: pass
            
            if not self._abort:
                self.finished.emit(full_response.strip())
        except Exception as e:
            if not self._abort:
                self.error.emit(str(e))

# ── New AI Panel Components ───────────────────────────────────────────────
class ResponseBlock(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedWidth(650)
        self.setMinimumHeight(240)
        self.setMaximumHeight(480)
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(24, 24, 24, 235), 
                    stop:1 rgba(15, 15, 15, 245));
                border: 1px solid rgba(255, 255, 255, 15);
                border-radius: 18px;
            }}
        """)
        
        # Add glow effect
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(40)
        self.shadow.setColor(QColor(0, 0, 0, 200))
        self.shadow.setOffset(0, 10)
        self.setGraphicsEffect(self.shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.loader = QLabel("Wait a moment .")
        self.loader.setStyleSheet(f"""
            QLabel {{
                background: rgba(255, 255, 255, 10);
                border: 1px solid rgba(255, 255, 255, 15);
                border-radius: 12px;
                color: {T['text']};
                font-size: 12px;
                padding: 6px 15px;
            }}
        """)
        self.loader.setAlignment(Qt.AlignCenter)
        
        loader_lay = QHBoxLayout()
        loader_lay.addStretch()
        loader_lay.addWidget(self.loader)
        loader_lay.addStretch()
        layout.addLayout(loader_lay)
        self.loader.hide()

        self.load_timer = QTimer()
        self.load_timer.timeout.connect(self._animate_loader)
        self._dot_count = 0
        
        self.browser = QTextBrowser()
        self.browser.setStyleSheet(f"border: none; background: transparent; color: {T['text']}; font-size: 13.5px;")
        self.browser.document().setDefaultStyleSheet(preview_css().replace("16px", "14px"))
        layout.addWidget(self.browser)
        
        self.actions = QHBoxLayout()
        self.copy_btn = QPushButton("Copy")
        self.insert_btn = QPushButton("Insert")
        self.close_btn = QPushButton("✕")
        
        for btn in [self.copy_btn, self.insert_btn, self.close_btn]:
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(32)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255, 255, 255, 12);
                    border: 1px solid rgba(255, 255, 255, 15);
                    border-radius: 6px;
                    color: {T['text']};
                    font-size: 11px;
                    padding: 0 12px;
                }}
                QPushButton:hover {{
                    background: rgba(255, 255, 255, 22);
                }}
            """)
        
        self.insert_btn.setStyleSheet(self.copy_btn.styleSheet())
        
        self.actions.addWidget(self.close_btn)
        self.actions.addStretch()
        self.actions.addWidget(self.copy_btn)
        self.actions.addWidget(self.insert_btn)
        layout.addLayout(self.actions)
        
        self.close_btn.clicked.connect(self.hide)
        self.copy_btn.clicked.connect(self._copy)
        self.insert_btn.clicked.connect(self._insert)
        
        self.content = ""
        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setDuration(400)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def _animate_loader(self):
        self._dot_count = (self._dot_count + 1) % 4
        self.loader.setText("Wait a moment " + "." * self._dot_count)

    def set_content(self, md):
        if md:
            self.loader.hide()
            self.load_timer.stop()
        self.content = md
        self._refresh()

    def add_chunk(self, chunk):
        if not self.content:
            self.loader.hide()
            self.load_timer.stop()
        self.content += chunk
        self._refresh()

    def _refresh(self):
        html_out = markdown2.markdown(self.content, extras=["fenced-code-blocks", "tables", "task_list"])
        self.browser.setHtml(html_out)
        self.browser.verticalScrollBar().setValue(self.browser.verticalScrollBar().maximum())

    def _copy(self):
        QApplication.clipboard().setText(self.content)
        
    def _insert(self):
        tab = self.window().tabs.currentWidget()
        if tab and hasattr(tab, "editor"):
            tab.editor.insert_block(self.content)
        self.hide()

    def show_animated(self, start_pos, end_pos):
        self._anim.setStartValue(start_pos)
        self._anim.setEndValue(end_pos)
        self.loader.show()
        self.load_timer.start(400)
        self.show()
        self._anim.start()

class NewAIPanel(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.app = parent.app
        self.server = self.app.ai_server
        self._thread = None
        self._worker = None
        
        self.setFixedWidth(400)
        self.setFixedHeight(50)
        
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(30, 30, 30, 240), 
                    stop:1 rgba(15, 15, 15, 250));
                border: 1px solid rgba(255, 255, 255, 25);
                border-radius: 25px;
            }}
        """)
        
        # Glow for the input bar
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(25)
        self.shadow.setColor(QColor(0, 0, 0, 150))
        self.shadow.setOffset(0, 4)
        self.setGraphicsEffect(self.shadow)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 5, 5, 5)
        layout.setSpacing(8)
        
        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask AI...")
        self.input.setStyleSheet(f"border:none; background:transparent; color:{T['text']}; font-size:13px;")
        self.input.returnPressed.connect(self.send_prompt)
        layout.addWidget(self.input, 1)
        
        self.send_btn = QPushButton("Ask")
        self.send_btn.setFixedSize(60, 36)
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {T['accent']};
                border: none;
                border-radius: 18px;
                color: white;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {T['accent2']};
            }}
        """)
        self.send_btn.clicked.connect(self.handle_btn)
        layout.addWidget(self.send_btn)
        
        self.response_block = ResponseBlock(parent)
        self.response_block.hide()

    def handle_btn(self):
        if self.send_btn.text() == "Stop":
            self.stop_generation()
        else:
            self.send_prompt()

    def stop_generation(self):
        if self._worker:
            self._worker.abort()
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Ask")
        self.input.setPlaceholderText("Ask AI...")
        if self._thread:
            self._thread.quit()

    def update_position(self):
        p = self.parent()
        if not p: return
        w, h = self.width(), self.height()
        pw, ph = p.width(), p.height()
        if pw < 100 or ph < 100: return # Parent not ready
        
        # Center at the bottom of the parent (DocTab)
        self.move((pw - w) // 2, ph - h - 20)
        
        if self.response_block.isVisible():
            rw, rh = self.response_block.width(), self.response_block.height()
            # Position above input
            target_pos = QPoint((p.width() - rw) // 2, p.height() - h - rh - 30)
            if self.response_block.pos() != target_pos and self.response_block._anim.state() != QPropertyAnimation.Running:
                self.response_block.move(target_pos)

    def send_prompt(self):
        prompt = self.input.text().strip()
        if not prompt: return
        
        if not self.server.is_running:
            if not self.server.start():
                QMessageBox.critical(self, "Server Error", "Could not start AI server.")
                return
        
        self.input.clear()
        self.input.setPlaceholderText("Thinking...")
        self.input.setEnabled(False)
        self.send_btn.setEnabled(False)
        
        tab = self.parent()
        context = ""
        if hasattr(tab, "editor"):
            text = tab.editor.toPlainText()
            sel = tab.editor.textCursor().selectedText().replace("\u2029", "\n")
            context = f"Full Document:\n{text}\n\nSelected Text:\n{sel}" if sel else text
            
        self._worker = LlamaWorker(prompt, context)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        
        self._worker.chunk.connect(self.response_block.add_chunk)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._thread.started.connect(self._worker.run)
        
        self.send_btn.setText("Stop")
        self.send_btn.setEnabled(True)
        
        self._thread.start()
        
        self.response_block.set_content("")
        self.response_block.show()
        
        # Rising animation
        start_y = self.y()
        end_y = self.y() - self.response_block.height() - 10
        start_pos = QPoint((self.parent().width() - self.response_block.width()) // 2, start_y)
        end_pos = QPoint((self.parent().width() - self.response_block.width()) // 2, end_y)
        self.response_block.show_animated(start_pos, end_pos)


    def _on_finished(self, text):
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Ask")
        self.input.setPlaceholderText("Ask AI...")
        self.response_block.set_content(text)
        self.update_position()
        if self._thread: self._thread.quit()

    def _on_error(self, err):
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Ask")
        self.input.setPlaceholderText("Ask AI...")
        self.response_block.hide()
        if "timeout" not in str(err).lower():
            QMessageBox.warning(self, "AI Error", err)
        if self._thread: self._thread.quit()


# ── Create README Dialog ───────────────────────────────────────────────────
class CreateReadmeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create README")
        self.setFixedWidth(400)
        self.setStyleSheet(f"background:{T['bg']}; color:{T['text']};")
        
        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        
        self.inputs = {}
        fields = [
            ("Project Name", "e.g. My Awesome Project"),
            ("Description", "What does it do?"),
            ("GitHub Profile", "https://github.com/your-username"),
            ("Language", "e.g. Python, JavaScript, etc.")
        ]
        
        for label, placeholder in fields:
            lay.addWidget(QLabel(label))
            le = QLineEdit()
            le.setPlaceholderText(placeholder)
            le.setStyleSheet(f"background:{T['input']}; border:1px solid {T['border']}; border-radius:6px; padding:8px;")
            self.inputs[label] = le
            lay.addWidget(le)
            
        btn_lay = QHBoxLayout()
        self.cancel = QPushButton("Cancel")
        self.create = QPushButton("Create")
        for btn in [self.cancel, self.create]:
            btn.setFixedHeight(35)
            btn.setCursor(Qt.PointingHandCursor)
            
        self.create.setStyleSheet(f"background:{T['accent']}; border:none; border-radius:6px; font-weight:bold; color:white;")
        self.cancel.setStyleSheet(f"background:{T['hover']}; border:none; border-radius:6px; color:white;")
        
        btn_lay.addWidget(self.cancel)
        btn_lay.addWidget(self.create)
        lay.addLayout(btn_lay)
        
        self.create.clicked.connect(self.accept)
        self.cancel.clicked.connect(self.reject)

    def get_data(self):
        return {k: v.text().strip() for k, v in self.inputs.items()}

# ── Main Window ────────────────────────────────────────────────────────────
class App(QMainWindow):
    def __init__(self, workspace=None):
        super().__init__()
        self.workspace = os.path.abspath(workspace or os.getcwd())
        self.setWindowTitle("README Builder")
        self.resize(1200, 650)
        self.git_url = ""
        self.ai_server = LlamaServer()
        self.ai_server.status_changed.connect(self._on_server_status)

        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        for icon_name in ["icon.ico", "icon.png"]:
            icon_path = resource_path(icon_name)
            if os.path.exists(icon_path):
                ic = QIcon(icon_path)
                if not ic.isNull():
                    self.setWindowIcon(ic)
                break

        central = QWidget(); self.setCentralWidget(central)
        root = QHBoxLayout(central); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        root.addWidget(self._make_sidebar())

        main = QWidget()
        ml = QVBoxLayout(main); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)
        root.addWidget(main)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        ml.addWidget(self.tabs)
        
        QShortcut(QKeySequence("F3"), self).activated.connect(self._toggle_ai)

        self.find_bar = FindBar(None, self); self.find_bar.hide()
        ml.addWidget(self.find_bar)

        self._status = QLabel("", self); self._status.setAlignment(Qt.AlignCenter); self._status.setFixedSize(140, 36)
        self._status.setStyleSheet(f"background:{T['accent']};color:#F5F5F5;border-radius:8px;font-weight:600;font-size:12px;")
        self._status.hide()

        self.stats = StatsBar(None, self)
        ml.addWidget(self.stats)

        QShortcut(QKeySequence("Ctrl+N"), self, self._new_tab)
        QShortcut(QKeySequence("Ctrl+W"), self, lambda: self._close_tab(self.tabs.currentIndex()))
        QShortcut(QKeySequence("Ctrl+S"), self, self._quick_save)
        QShortcut(QKeySequence("F1"), self, self._add_snippet)
        QShortcut(QKeySequence("F2"), self, self._rename_tab)
        QShortcut(QKeySequence("Ctrl+F"), self, self._open_find)
        QShortcut(QKeySequence("Ctrl+H"), self, self._open_replace)
        QShortcut(QKeySequence("Ctrl+T"), self, self._open_templates)
        QShortcut(QKeySequence("Ctrl+I"), self, self._open_images)

        self.user_snippets = self._load_snippets()
        self.tabs.currentChanged.connect(self._on_tab_changed)
        QTimer.singleShot(80, self._load_initial)

    def _on_tab_changed(self, idx):
        prev = getattr(self, "_ctx_editor", None)
        if prev:
            try: prev.textChanged.disconnect(self._sync_ai_ctx_bar)
            except: pass
        self._ctx_editor = None
        tab = self.tabs.widget(idx)
        if tab:
            self.stats.editor = tab.editor; self.stats.refresh()
            self.find_bar.editor = tab.editor; self.find_bar._hl()
            self._ctx_editor = tab.editor
            tab.editor.textChanged.connect(self._sync_ai_ctx_bar)
            tab.ai_panel.update_position()

    def _sync_ai_ctx_bar(self):
        pass

    def _open_find(self):
        tab = self.tabs.currentWidget()
        if tab: self.find_bar.editor = tab.editor; self.find_bar.show(); self.find_bar.find.setFocus()

    def _open_replace(self):
        tab = self.tabs.currentWidget()
        if tab: self.find_bar.editor = tab.editor; self.find_bar.show(); self.find_bar.repl.setFocus()

    def _make_sidebar(self):
        sb = QFrame(); sb.setFixedWidth(80)
        sb.setStyleSheet(f"QFrame{{background:{T['panel']};border-right:1px solid {T['border']};}}")
        lay = QVBoxLayout(sb); lay.setContentsMargins(6,10,6,10); lay.setSpacing(6)
        buttons = [
            ("Template", self._open_templates, "Ctrl+T"),
            ("Snippet",  self._open_snippets,  ""),
            ("Import",   self._import_gh,       ""),
            ("TOC",      self._gen_toc,         ""),
            ("Score",    self._show_score,      ""),
            ("Images",   self._open_images,     "Ctrl+I"),
            ("Social",   self._open_social,     ""),
            ("Translate",self._translate,       ""),
            ("Repair",   self._repair,          ""),
            ("Find",     lambda: (self.find_bar.show(), self.find_bar.find.setFocus()), "Ctrl+F"),
            ("Export",   self._export,          ""),
            ("Recent",   self._show_recent,     ""),
        ]
        for lbl, fn, sc in buttons:
            b = QToolButton(); b.setText(lbl); b.clicked.connect(fn)
            if sc: b.setToolTip(f"{lbl} ({sc})")
            lay.addWidget(b)
        
        lay.addSpacing(12)
        server_lbl = QLabel("AI Server F3")
        server_lbl.setAlignment(Qt.AlignCenter)
        server_lbl.setStyleSheet(f"color:{T['dim']}; font-size:10px; font-weight:bold; margin-top:5px;")
        lay.addWidget(server_lbl)
        
        self.ai_toggle = QPushButton("OFF")
        self.ai_toggle.setCheckable(True)
        self.ai_toggle.setFixedSize(64, 26)
        self.ai_toggle.setCursor(Qt.PointingHandCursor)
        self.ai_toggle.setStyleSheet(self._get_toggle_style(False))
        self.ai_toggle.clicked.connect(self._toggle_server)
        lay.addWidget(self.ai_toggle, 0, Qt.AlignCenter)
        
        lay.addStretch()
        credit = QLabel("Yasser-27")
        credit.setAlignment(Qt.AlignCenter)
        credit.setStyleSheet(f"color:{T['dim']};font-size:9px;background:transparent;padding:4px;")
        lay.addWidget(credit)
        return sb

    def _get_toggle_style(self, on):
        bg = T['accent'] if on else "rgba(255,255,255,10)"
        color = "white" if on else T['dim']
        border = T['accent'] if on else "rgba(255,255,255,15)"
        return f"""
            QPushButton {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 13px;
                color: {color};
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {T['accent2'] if on else "rgba(255,255,255,15)"};
            }}
        """

    def _toggle_server(self):
        if self.ai_toggle.isChecked():
            if self.ai_server.start():
                self.ai_toggle.setText("ON")
                self.ai_toggle.setStyleSheet(self._get_toggle_style(True))
                self._flash("AI Server Started", "#4ADE80")
            else:
                self.ai_toggle.setChecked(False)
                self.ai_toggle.setText("OFF")
                self.ai_toggle.setStyleSheet(self._get_toggle_style(False))
        else:
            self.ai_server.stop()
            self.ai_toggle.setText("OFF")
            self.ai_toggle.setStyleSheet(self._get_toggle_style(False))
            self._flash("AI Server Stopped")

    def _on_server_status(self, status):
        is_on = "Running" in status
        if self.ai_toggle.isChecked() != is_on:
            self.ai_toggle.blockSignals(True)
            self.ai_toggle.setChecked(is_on)
            self.ai_toggle.setText("ON" if is_on else "OFF")
            self.ai_toggle.setStyleSheet(self._get_toggle_style(is_on))
            self.ai_toggle.blockSignals(False)

    def _toggle_ai(self):
        tab = self.tabs.currentWidget()
        if tab and isinstance(tab, DocTab):
            v = not tab.ai_panel.isVisible()
            tab.ai_panel.setVisible(v)
            if v:
                tab.ai_panel.input.setFocus()
                tab.ai_panel.update_position()

    def _show_recent(self):
        d = QDialog(self); d.setWindowTitle("Recent Files"); d.setFixedSize(400, 450)
        lay = QVBoxLayout(d); lay.setContentsMargins(16,14,16,14); lay.setSpacing(10)
        lay.addWidget(QLabel("Recently Modified Markdown Files:", styleSheet="font-weight:bold;font-size:13px;"))
        lw = QListWidget()
        files = []
        for root, dirs, fns in os.walk(self.workspace):
            for fn in fns:
                if fn.endswith('.md'):
                    p = os.path.join(root, fn)
                    try: files.append((os.stat(p).st_mtime, p))
                    except: pass
        files.sort(reverse=True)
        for _, p in files[:15]:
            i = QListWidgetItem(os.path.basename(p)); i.setData(Qt.UserRole, p); lw.addItem(i)
        lay.addWidget(lw)
        b = QPushButton("Open Selected")
        b.setStyleSheet(f"background:{T['accent']};color:#F5F5F5;border:1px solid {T['border']};border-radius:7px;padding:9px;font-weight:600;")
        def _op():
            it = lw.currentItem()
            if it:
                path = it.data(Qt.UserRole)
                try:
                    with open(path, "r", encoding="utf-8") as f: content = f.read()
                    self._new_tab(content, os.path.basename(path)); d.accept()
                except Exception as e: QMessageBox.warning(self, "Error", str(e))
        b.clicked.connect(_op); lw.itemDoubleClicked.connect(_op); lay.addWidget(b)
        d.exec()

    def _flash(self, msg, color=None):
        self._status.setText(msg)
        col = color or T['accent']
        self._status.setStyleSheet(f"background:{col};color:#F5F5F5;border-radius:8px;font-weight:600;font-size:12px;")
        self._status.move(self.width()//2-70, self.height()-54)
        self._status.show(); QTimer.singleShot(1800, self._status.hide)

    def _quick_save(self):
        if self._save(): self._flash("Saved ✓")

    def _open_templates(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        d = TemplatePicker(self)
        if d.exec() == QDialog.Accepted and d.result_text: tab.editor.setPlainText(d.result_text)

    def _gen_toc(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        lines = tab.editor.toPlainText().split("\n"); toc = ["## Table of Contents"]; found = False
        for line in lines:
            if line.startswith("#"):
                lv = len(line) - len(line.lstrip("#"))
                title = line.strip("#").strip()
                anchor = re.sub(r"[^a-z0-9-]","",title.lower().replace(" ","-"))
                toc.append("  "*(lv-1) + f"- [{title}](#{anchor})"); found = True
        if found: tab.editor.setPlainText("\n".join(toc)+"\n\n\n"+tab.editor.toPlainText())
        else: QMessageBox.information(self,"TOC","No headings found.")

    def _open_snippets(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        dlg = QDialog(self); dlg.setWindowTitle("Snippets"); dlg.setFixedSize(340, 380)
        lay = QVBoxLayout(dlg); lay.setContentsMargins(16,14,16,14); lay.setSpacing(10)
        lw = QListWidget()
        lw.setStyleSheet(f"QListWidget{{background:{T['bg']};border:1px solid {T['border']};border-radius:8px;outline:none;}}"
                         f"QListWidget::item{{padding:8px;border-radius:5px;}}"
                         f"QListWidget::item:selected{{background:{T['accent']};color:white;}}")
        for k in SNIPPETS: lw.addItem(k)
        lay.addWidget(lw)
        def insert():
            sel = lw.currentItem()
            if sel: tab.editor.insert_block(SNIPPETS[sel.text()]); dlg.accept()
        b = QPushButton("Insert")
        b.setStyleSheet(f"background:{T['accent']};color:#F5F5F5;border:1px solid {T['border']};border-radius:7px;padding:9px;font-weight:600;")
        b.clicked.connect(insert); lay.addWidget(b)
        dlg.exec()

    def _import_gh(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        d = QDialog(self); d.setWindowTitle("Import from GitHub"); d.setFixedSize(420, 160)
        lay = QVBoxLayout(d); lay.setContentsMargins(18,14,18,14); lay.setSpacing(10)
        lay.addWidget(QLabel("GitHub repo URL:"))
        inp = QLineEdit(); inp.setPlaceholderText("https://github.com/user/repo"); lay.addWidget(inp)
        row = QHBoxLayout()
        cancel = QPushButton("Cancel"); cancel.clicked.connect(d.reject); row.addWidget(cancel)
        confirm = QPushButton("Import")
        confirm.setStyleSheet(f"background:{T['accent']};color:#F5F5F5;border:1px solid {T['border']};border-radius:7px;padding:8px 16px;font-weight:600;")
        confirm.clicked.connect(d.accept); row.addWidget(confirm); lay.addLayout(row)
        if d.exec() != QDialog.Accepted: return
        raw = inp.text().strip()
        if not raw: return
        self.git_url = raw
        target = raw
        if "github.com" in raw and "raw.githubusercontent" not in raw:
            target = raw.replace("github.com","raw.githubusercontent.com").rstrip("/") + "/main/README.md"
        try:
            try: resp = urllib.request.urlopen(urllib.request.Request(target))
            except urllib.error.HTTPError as e:
                if e.code == 404 and "/main/" in target:
                    target = target.replace("/main/","/master/"); resp = urllib.request.urlopen(urllib.request.Request(target))
                else: raise
            tab.editor.setPlainText(resp.read().decode("utf-8"))
        except Exception as e: QMessageBox.warning(self,"Error",str(e))

    def _show_score(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        sc, tips = readme_score(tab.editor.toPlainText())
        ScoreDialog(sc, tips, self).exec()

    def _open_images(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        ImageDialog(tab.editor, self.workspace, self).exec()

    def _open_social(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        SocialPickerDialog(tab.editor, self.workspace, self).exec()

    def _translate(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        d = TranslateDialog(tab.editor.toPlainText(), self)
        if d.exec() == QDialog.Accepted and d.result:
            tab.editor.setPlainText(d.result); self._flash("Translation applied!")

    def _repair(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        d = RepairDialog(tab.editor.toPlainText(), self)
        if d.exec() == QDialog.Accepted and d.result:
            tab.editor.setPlainText(d.result); self._flash("Repairs applied ✓", "#4ADE80")

    def _new_tab(self, content=None, title=None):
        if not title:
            existing = [self.tabs.widget(i).file_name for i in range(self.tabs.count())]
            if "README.md" not in existing: title = "README.md"
            else:
                i = 2
                while f"README_{i}.md" in existing: i += 1
                title = f"README_{i}.md"
        tab = DocTab(self, content, self.workspace, title)
        idx = self.tabs.addTab(tab, title)
        self.tabs.setCurrentIndex(idx)
        # Defer initial render to not block UI
        QTimer.singleShot(100, tab._request_render)
        return tab

    def _close_tab(self, idx):
        if self.tabs.count() > 1:
            tab = self.tabs.widget(idx)
            if tab: tab.stop()
            self.tabs.removeTab(idx)

    def _add_snippet(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        text = tab.editor.textCursor().selectedText().replace("\u2029", "\n")
        if not text: self._flash("Select text first!"); return
        dlg = SnippetAddDialog(self, text)
        if dlg.exec() == QDialog.Accepted:
            name = dlg.name.text().strip()
            if name: self.user_snippets[name] = text; self._save_snippets(); self._flash(f"Saved '{name}'!")

    def _get_snippet_path(self):
        if getattr(sys, 'frozen', False): base = os.path.dirname(sys.executable)
        else: base = os.path.dirname(os.path.abspath(__file__))
        return Path(base) / "snippets.json"

    def _load_snippets(self):
        p = self._get_snippet_path()
        if p.exists():
            try: return json.loads(p.read_text("utf-8"))
            except: pass
        return {}

    def _save_snippets(self):
        try: self._get_snippet_path().write_text(json.dumps(self.user_snippets, indent=4), "utf-8")
        except: pass

    def _rename_tab(self):
        idx = self.tabs.currentIndex(); tab = self.tabs.widget(idx)
        if not tab: return
        dlg = QInputDialog(self); dlg.setWindowTitle("Rename Tab"); dlg.setLabelText("New name:")
        dlg.setTextValue(tab.file_name)
        if dlg.exec() == QInputDialog.Accepted:
            new_name = dlg.textValue().strip()
            if new_name:
                if "." not in new_name: new_name += ".md"
                tab.file_name = new_name; self.tabs.setTabText(idx, new_name)
                self._flash(f"Renamed: {new_name}")

    def _load_initial(self):
        # Defer tab creation slightly to let window paint first
        if self.tabs.count() == 0:
            QTimer.singleShot(50, lambda: self._new_tab("", "README.md"))

    def _export(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        p, _ = QFileDialog.getSaveFileName(self,"Export","README.md","Markdown (*.md);;HTML (*.html)")
        if not p: return
        try:
            if p.endswith(".html"):
                css = preview_css()
                html_out = markdown2.markdown(tab.editor.toPlainText(), extras=["fenced-code-blocks","tables","task_list"])
                Path(p).write_text(f"<!DOCTYPE html><html><head><meta charset='UTF-8'>{css}</head><body>{html_out}</body></html>","utf-8")
            else:
                Path(p).write_text(f"<!-- README Builder | {datetime.now():%Y-%m-%d} -->\n\n{tab.editor.toPlainText()}","utf-8")
            QMessageBox.information(self,"Exported",f"Saved:\n{p}")
        except Exception as e: QMessageBox.critical(self,"Error",str(e))

    def _save(self):
        tab = self.tabs.currentWidget()
        if not tab: return False
        try:
            (Path(self.workspace) / tab.file_name).write_text(tab.editor.toPlainText(), "utf-8")
            return True
        except Exception as e: QMessageBox.critical(self,"Error",str(e)); return False

    def closeEvent(self, e):
        """Fast shutdown — terminate all threads promptly to avoid UI freeze."""
        # 1. Stop all document tabs and AI processes
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab and isinstance(tab, DocTab):
                try:
                    tab.ai_panel.server.stop()
                except: pass
            if tab and hasattr(tab, "stop"):
                try: tab.stop()
                except: pass

        # 2. Let the event loop drain before exit
        QApplication.processEvents()
        e.accept()

# ── Entry Point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Register context menu FIRST (fast, no blocking)
    # This MUST happen before QApplication for fastest startup
    if sys.platform == "win32":
        try:
            import winreg
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
            else:
                exe_path = os.path.abspath(sys.argv[0])
            exe_str = f'"{exe_path}"'
            # Only register if not already done (check command key)
            try:
                test_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\*\shell\Open with README Builder\command")
                winreg.CloseKey(test_key)
            except FileNotFoundError:
                # Not registered yet, do it now
                k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\*\shell\Open with README Builder")
                winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, exe_path)
                winreg.SetValueEx(k, "Position", 0, winreg.REG_SZ, "Top")
                winreg.SetValueEx(winreg.CreateKey(k, "command"), "", 0, winreg.REG_SZ, f'{exe_str} "%1"')
                winreg.CloseKey(k)

                k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\Directory\shell\Create README here")
                winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, exe_path)
                winreg.SetValueEx(winreg.CreateKey(k, "command"), "", 0, winreg.REG_SZ, f'{exe_str} "%1"')
                winreg.CloseKey(k)

                k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\Directory\Background\shell\Create README here")
                winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, exe_path)
                winreg.SetValueEx(winreg.CreateKey(k, "command"), "", 0, winreg.REG_SZ, f'{exe_str} "%V"')
                winreg.CloseKey(k)

                k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\READMEBuilder.Markdown\shell\open\command")
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, f'{exe_str} "%1"')
                winreg.CloseKey(k)

                k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.md")
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "READMEBuilder.Markdown")
                winreg.CloseKey(k)

                # Notify shell (fast, non-blocking)
                import ctypes
                ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
        except Exception:
            pass  # Silently ignore registry errors

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Apply initial dark theme and stylesheet
    apply_theme(app, "dark")

    ws = os.getcwd()
    files_to_open = []
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if not arg: continue
            p = os.path.abspath(arg)
            if os.path.isdir(p):
                for fn in sorted(os.listdir(p)):
                    if fn.lower().endswith('.md'):
                        files_to_open.append(os.path.join(p, fn))
                if not files_to_open:
                    ws = p
            elif os.path.isfile(p):
                files_to_open.append(p)
                if not files_to_open:
                    ws = os.path.dirname(p)
        if files_to_open:
            ws = os.path.dirname(files_to_open[0])

    # Show window ASAP
    window = App(ws)
    window.show()

    # Open files AFTER window is visible (non-blocking)
    if files_to_open:
        for path in files_to_open:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    window._new_tab(content, os.path.basename(path))
                except: pass

    # Defer context menu re-registration (lightweight, runs later)
    QTimer.singleShot(2000, auto_register_context_menu)

    sys.exit(app.exec())