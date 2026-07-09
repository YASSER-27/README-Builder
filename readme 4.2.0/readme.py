import sys, os, re, json, html, time, urllib.request, urllib.error, urllib.parse, base64, subprocess, shutil
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
from PySide6.QtCore import Qt, QUrl, QTimer, QThread, QObject, Signal, QPoint, QSize, QRect, QRectF, QRunnable, QThreadPool, QProcess, QPropertyAnimation, QEasingCurve, QFileSystemWatcher, QByteArray
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtGui import (
    QAction, QFont, QColor, QSyntaxHighlighter, QTextCharFormat,
    QKeySequence, QIcon, QShortcut, QTextCursor, QPixmap, QImage,
    QTextDocument, QPainter, QBrush, QPen, QUndoCommand, QPalette, QLinearGradient, QPainterPath
)
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
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
    "bg":       "#161616",
    "panel":    "#161616",
    "border":   "#161616",
    "hover":    "#161616",
    "input":    "#161616",
    "text":     "#E8E8ED",
    "dim":      "#B3B3B3",
    "editor":   "#E8E8ED",
    "scroll":   "#161616",
    "accent":   "#4F8DFF",
    "accent2":  "#6AADFF",
    "code":     "#08080C",
    "chip":     "#161616",
    "chip_br":  "#161616",
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
    f"QMainWindow{{background:#161616;}}"
    f"QWidget{{background:#161616;color:{T['text']};}}"
    f"QDialog{{background:{T['panel']};color:{T['text']};}}"
    f"QTextEdit{{background:{T['bg']};color:{T['editor']};border:1px solid #28282c;border-radius:10px;"
    f"font-size:14px;padding:18px;font-family:ui-monospace,'SF Mono',Consolas,monospace;line-height:1.7;}}"
    f"QTextBrowser{{background:{T['bg']};color:#e6edf3;border:1px solid #28282c;border-radius:10px;padding:10px;}}"
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
    f"QTabBar::close-button:hover{{background:#161616;}}"
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
  border-spacing:0;border-collapse:collapse;
  margin-bottom:16px;max-width:100%;overflow:auto;
  width:auto;
}}
thead{{background:#161b22;}}
th{{
  padding:6px 13px;border:1px solid #30363d;font-weight:600;
  text-align:left;color:#c9d1d9;white-space:nowrap;
}}
td{{
  padding:6px 13px;border:1px solid #30363d;color:#c9d1d9;
}}
td img{{max-width:120px;height:auto;}}
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

/* Line numbers on preview to match editor */
#content{{counter-reset:preview-line;}}
#content>*{{counter-increment:preview-line;position:relative;padding-left:2.5em;}}
#content>*::before{{
  content:counter(preview-line);
  position:absolute;left:0;top:0;
  width:2em;text-align:right;
  color:#484f58;font-size:12px;line-height:inherit;
  font-family:'SF Mono',Consolas,monospace;
  padding-right:8px;border-right:1px solid #21262d;
  margin-right:8px;
}}

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
        self._max_threads = 5
        self.setOpenExternalLinks(True)
        self.setOpenLinks(True)

    def _limit_image_size(self, px):
        max_h = 500
        if px.height() > max_h:
            px = px.scaledToHeight(max_h, Qt.SmoothTransformation)
        if px.width() > 900:
            px = px.scaledToWidth(900, Qt.SmoothTransformation)
        return px

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
                        px = self._limit_image_size(QPixmap.fromImage(img))
                        self._img_cache[url_str] = px
                        return px
                except: pass
        if url_str.startswith(("http://", "https://")) and url_str not in self._pending:
            running = sum(1 for t, _ in self._threads if t.isRunning())
            if running >= self._max_threads:
                return QPixmap()
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
                else:
                    px = self._limit_image_size(px)
                if len(self._img_cache) > 200:
                    self._img_cache.clear()
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

        # Pre-process GitHub alerts BEFORE markdown conversion
        # Convert > [!NOTE] blocks into HTML divs so markdown2 doesn't mangle them
        alert_map = {
            'NOTE':      ('markdown-alert-note',      '📝 Note'),
            'WARNING':   ('markdown-alert-warning',   '⚠️ Warning'),
            'TIP':       ('markdown-alert-tip',       '💡 Tip'),
            'IMPORTANT': ('markdown-alert-important', '❗ Important'),
            'CAUTION':   ('markdown-alert-caution',   '🔴 Caution'),
        }
        def _replace_alerts(text):
            lines = text.split('\n')
            result = []
            i = 0
            while i < len(lines):
                line = lines[i]
                # Match > [!TYPE]
                m = re.match(r'^>\s*\[!(NOTE|WARNING|TIP|IMPORTANT|CAUTION)\]\s*$', line)
                if m:
                    alert_type = m.group(1)
                    css_cls, label = alert_map[alert_type]
                    # Collect all subsequent "> ..." lines as content
                    content_lines = []
                    i += 1
                    while i < len(lines):
                        cl = lines[i]
                        if cl.startswith('> '):
                            content_lines.append(cl[2:])
                            i += 1
                        elif cl.strip() == '>':
                            content_lines.append('')
                            i += 1
                        else:
                            break
                    content_html = '<br>'.join(content_lines)
                    result.append(f'<div class="markdown-alert {css_cls}"><b>{label}</b><br>{content_html}</div>')
                else:
                    result.append(line)
                    i += 1
            return '\n'.join(result)

        md_text = _replace_alerts(md_text)

        # Convert markdown to HTML with all extras
        html_out = markdown2.markdown(md_text,
            extras=["fenced-code-blocks", "tables", "task_list", "strike",
                     "code-friendly", "header-ids", "footnotes",
                     "numbering", "cuddled-lists"])

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

    def insertFromMimeData(self, source):
        if source.hasText():
            self.insertPlainText(source.text())


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
    # ── Alerts ──
    "Note Alert":       "> [!NOTE]\n> Add your note here.\n",
    "Warning Alert":    "> [!WARNING]\n> Add your warning here.\n",
    "Tip Alert":        "> [!TIP]\n> Pro tip: Read the full documentation first.\n",
    "Important Alert":  "> [!IMPORTANT]\n> Breaking changes in v2.0. See migration guide.\n",
    "Caution Alert":    "> [!CAUTION]\n> This operation is irreversible.\n",

    # ── Sections ──
    "Features":      "## Features\n- Performance: Lightning fast.\n- Modern UI: Clean minimal style.\n- Secure: End-to-end encryption.\n",
    "Installation":  "## Installation\n1. Clone:\n```bash\ngit clone https://github.com/user/repo.git\n```\n2. Install:\n```bash\npip install -r requirements.txt\n```\n",
    "Author":        "### Author\n**Your Name** - [GitHub](https://github.com/) - [LinkedIn](#)\n",
    "License MIT":   "## License\nThis project is licensed under the **MIT License** - see [LICENSE](LICENSE) for details.\n",
    "Contributing":  "## Contributing\n1. Fork the Project\n2. Create branch (`git checkout -b feature/X`)\n3. Commit (`git commit -m 'Add X'`)\n4. Push (`git push origin feature/X`)\n5. Open a Pull Request\n",
    "Roadmap":       "## Roadmap\n- [x] Initial release\n- [x] Core features\n- [ ] Version 2.0\n- [ ] Mobile support\n",
    "Usage":         "## Usage\n```python\nimport module\nmodule.run()\n```\n",
    "Screenshots":   "## Screenshots\n![Screenshot 1](screenshots/1.png)\n![Screenshot 2](screenshots/2.png)\n",
    "Changelog":     "## Changelog\n\n### [1.0.0] - 2024-01-01\n- Initial release\n",
    "API Reference": "## API\n### `function(args)`\nDescription here.\n\n**Parameters:**\n- `arg1` (type): Description\n- `arg2` (type): Description\n\n**Returns:**\ntype — Description\n",

    # ── Table of Contents ──
    "TOC Inline":    "[Features](#features) \u2022 [Installation](#installation) \u2022 [Usage](#usage) \u2022 [Configuration](#configuration) \u2022 [Contributing](#contributing)\n",
    "TOC List":      "- [Overview](#overview)\n- [Features](#features)\n- [Screenshots](#screenshots)\n- [Technology Stack](#technology-stack)\n- [Installation](#installation)\n- [Usage](#usage)\n- [Configuration](#configuration)\n- [Contributing](#contributing)\n- [License](#license)\n- [Author](#author)\n",
    "TOC Table":     "| Section | Description |\n|---------|-------------|\n| [Features](#features) | What it does |\n| [Installation](#installation) | How to install |\n| [Usage](#usage) | How to use |\n| [API](#api) | API reference |\n",

    # ── Layout ──
    "Left Align":    "<p align=\"left\">\n\n</p>\n",
    "Center":        "<p align=\"center\">\n\n</p>\n",
    "Center Image":  "<p align=\"center\">\n  <img src=\"image.png\" width=\"600\" alt=\"\">\n</p>\n",
    "Center Image + Title": '<p align="center">\n  <img src="icon.ico" width="150" alt="Logo">\n  <h1 align="center">Project Name</h1>\n</p>\n',

    # ── Language Badges ──
    "C# Badge":      '<img src="https://img.shields.io/badge/C%23-181818?style=for-the-badge&logo=c-sharp&logoColor=239120" />',
    "Python Badge":  '<img src="https://img.shields.io/badge/Python-181818?style=for-the-badge&logo=python&logoColor=3776AB" />',
    "JS Badge":      '<img src="https://img.shields.io/badge/JavaScript-181818?style=for-the-badge&logo=javascript&logoColor=F7DF1E" />',
    "TS Badge":      '<img src="https://img.shields.io/badge/TypeScript-181818?style=for-the-badge&logo=typescript&logoColor=3178C6" />',
    "Kotlin Badge":  '<img src="https://img.shields.io/badge/Kotlin-181818?style=for-the-badge&logo=kotlin&logoColor=7F52FF" />',
    "HTML Badge":    '<img src="https://img.shields.io/badge/HTML5-181818?style=for-the-badge&logo=html5&logoColor=E34F26" />',
    "CSS Badge":     '<img src="https://img.shields.io/badge/CSS3-181818?style=for-the-badge&logo=css3&logoColor=1572B6" />',
    "Rust Badge":    '<img src="https://img.shields.io/badge/Rust-181818?style=for-the-badge&logo=rust&logoColor=white" />',
    "Go Badge":      '<img src="https://img.shields.io/badge/Go-181818?style=for-the-badge&logo=go&logoColor=00ADD8" />',
    "C++ Badge":     '<img src="https://img.shields.io/badge/C%2B%2B-181818?style=for-the-badge&logo=c%2B%2B&logoColor=00599C" />',
    "Dart Badge":    '<img src="https://img.shields.io/badge/Dart-181818?style=for-the-badge&logo=dart&logoColor=0175C2" />',
    "Shell Badge":   '<img src="https://img.shields.io/badge/Shell-181818?style=for-the-badge&logo=gnu-bash&logoColor=4EAA25" />',
    "SQL Badge":     '<img src="https://img.shields.io/badge/SQL-181818?style=for-the-badge&logo=postgresql&logoColor=4169E1" />',

    # ── Meta Badges ──
    "Version Badge": '[![Version](https://img.shields.io/badge/version-1.0.0-FF5A5F.svg?style=for-the-badge)](https://github.com/user/repo)\n',
    "Platform Badge":'[![Platform](https://img.shields.io/badge/platform-Windows-0078D6.svg?style=for-the-badge)](https://github.com/user/repo)\n',
    "License Badge": '[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg?style=for-the-badge)](https://github.com/user/repo)\n',
    "Stars Badge":   '[![Stars](https://img.shields.io/github/stars/USER/REPO?style=social)](https://github.com/USER/REPO)\n',
    "Build Badge":   '[![Build](https://img.shields.io/github/actions/workflow/status/USER/REPO/ci.yml?style=for-the-badge)](https://github.com/USER/REPO/actions)\n',
    "Contributors Badge":'[![Contributors](https://img.shields.io/github/contributors/USER/REPO?style=for-the-badge)](https://github.com/USER/REPO/graphs/contributors)\n',

    # ── Arabic Support ──
    "Arabic Link":   '<a href="#\u0627\u0644\u0646\u0633\u062e\u0629-\u0627\u0644\u0639\u0631\u0628\u064a\u0629">\u0627\u0644\u0646\u0633\u062e\u0629 \u0627\u0644\u0639\u0631\u0628\u064a\u0629</a>\n',
    "Arabic Section":'<h2 id="\u0627\u0644\u0646\u0633\u062e\u0629-\u0627\u0644\u0639\u0631\u0628\u064a\u0629">\u0627\u0644\u0646\u0633\u062e\u0629 \u0627\u0644\u0639\u0631\u0628\u064a\u0629</h2>\n',
    "Arabic TOC":    "- [\u0627\u0644\u0645\u0642\u062f\u0645\u0629](#\u0627\u0644\u0645\u0642\u062f\u0645\u0629)\n- [\u0627\u0644\u0645\u0645\u064a\u0632\u0627\u062a](#\u0627\u0644\u0645\u0645\u064a\u0632\u0627\u062a)\n- [\u0627\u0644\u062a\u062b\u0628\u064a\u062a](#\u0627\u0644\u062a\u062b\u0628\u064a\u062a)\n- [\u0627\u0644\u0627\u0633\u062a\u062e\u062f\u0627\u0645](#\u0627\u0644\u0627\u0633\u062a\u062e\u062f\u0627\u0645)\n- [\u0627\u0644\u062a\u0631\u062e\u064a\u0635](#\u0627\u0644\u062a\u0631\u062e\u064a\u0635)\n",

    # ── Badges Row (combined) ──
    "Badges Row":    "[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#) [![Stars](https://img.shields.io/github/stars/USER/REPO?style=social)](#)\n",
}

BADGES = {
    # ── License ──
    "License MIT":   '<a href="https://github.com/YASSER-27/Bowow/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-lightgrey.svg?style=for-the-badge" alt="License"></a>',
    "License Apache":'<a href="#"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg?style=for-the-badge" alt="License"></a>',
    "License GPL":   '<a href="#"><img src="https://img.shields.io/badge/license-GPL%20v3-blue.svg?style=for-the-badge" alt="License"></a>',

    # ── Language ──
    "C# Badge":      '<img src="https://img.shields.io/badge/C%23-181818?style=for-the-badge&logo=c-sharp&logoColor=239120" />',
    "Python Badge":  '<img src="https://img.shields.io/badge/Python-181818?style=for-the-badge&logo=python&logoColor=3776AB" />',
    "JS Badge":      '<img src="https://img.shields.io/badge/JavaScript-181818?style=for-the-badge&logo=javascript&logoColor=F7DF1E" />',
    "TS Badge":      '<img src="https://img.shields.io/badge/TypeScript-181818?style=for-the-badge&logo=typescript&logoColor=3178C6" />',
    "Kotlin Badge":  '<img src="https://img.shields.io/badge/Kotlin-181818?style=for-the-badge&logo=kotlin&logoColor=7F52FF" />',
    "HTML5 Badge":   '<img src="https://img.shields.io/badge/HTML5-181818?style=for-the-badge&logo=html5&logoColor=E34F26" />',
    "CSS Badge":     '<img src="https://img.shields.io/badge/CSS3-181818?style=for-the-badge&logo=css3&logoColor=1572B6" />',
    "Rust Badge":    '<img src="https://img.shields.io/badge/Rust-181818?style=for-the-badge&logo=rust&logoColor=white" />',
    "Go Badge":      '<img src="https://img.shields.io/badge/Go-181818?style=for-the-badge&logo=go&logoColor=00ADD8" />',
    "C++ Badge":     '<img src="https://img.shields.io/badge/C%2B%2B-181818?style=for-the-badge&logo=c%2B%2B&logoColor=00599C" />',
    "Dart Badge":    '<img src="https://img.shields.io/badge/Dart-181818?style=for-the-badge&logo=dart&logoColor=0175C2" />',
    "Shell Badge":   '<img src="https://img.shields.io/badge/Shell-181818?style=for-the-badge&logo=gnu-bash&logoColor=4EAA25" />',
    "SQL Badge":     '<img src="https://img.shields.io/badge/SQL-181818?style=for-the-badge&logo=postgresql&logoColor=4169E1" />',
    "React Badge":   '<img src="https://img.shields.io/badge/React-18.2.0-61DAFB?style=for-the-badge&logo=react" />',

    # ── Version ──
    "Version Badge":  '<a href="https://github.com/yasser-27"><img src="https://img.shields.io/badge/version-1.0.0-FF5A5F.svg?style=for-the-badge" alt="Version"></a>',
    "Version Green":  '<img src="https://img.shields.io/badge/version-1.0.0-green?style=for-the-badge" />',
    "Stable Badge":   '<img src="https://img.shields.io/badge/version-stable-brightgreen" />',

    # ── Platform ──
    "Windows Badge":  '<a href="https://github.com/yasser-27"><img src="https://img.shields.io/badge/platform-Windows-0078D6.svg?style=for-the-badge" alt="Platform"></a>',
    "Platform Multi": '<img src="https://img.shields.io/badge/platform-Electron%20%7C%20Windows-lightgrey?style=for-the-badge" />',
    "Linux Badge":    '<img src="https://img.shields.io/badge/platform-Linux-FCC624?style=for-the-badge&logo=linux" />',
    "macOS Badge":    '<img src="https://img.shields.io/badge/platform-macOS-000000?style=for-the-badge&logo=apple" />',

    # ── Build / CI ──
    "Build Passing": '<img src="https://img.shields.io/github/actions/workflow/status/YASSER-27/Bowow/main.yml?style=for-the-badge" alt="Build Status" />',
    "Build Failing": '<img src="https://img.shields.io/badge/build-failing-red?style=for-the-badge" />',

    # ── Social ──
    "GitHub Stars":   '<a href="https://github.com/YASSER-27/Bowow"><img src="https://img.shields.io/github/stars/YASSER-27/Bowow?style=social" alt="Stars"></a>',
    "Forks Badge":    '<img src="https://img.shields.io/github/forks/YASSER-27/Bowow?style=social" alt="Forks" />',
    "Contributors":   '<img src="https://img.shields.io/github/contributors/YASSER-27/Bowow?style=for-the-badge" alt="Contributors" />',

    # ── Developer ──
    "Developer Badge":'<a href="https://github.com/yasser-27"><img src="https://img.shields.io/badge/developer-yasser--27-brightgreen.svg?style=for-the-badge" alt="Developer"></a>',

    # ── Download ──
    "Download Badge": '<p align="center"><a href="https://github.com/YASSER-27/Bowow/releases/latest"><img src="https://img.shields.io/badge/Bowow%20-%201.5.1-blue?style=for-the-badge&logo=github" alt="Download"></a></p>',

    # ── AI / Tech ──
    "XAI Badge":      '<img src="https://img.shields.io/badge/XAI-AI%20Chat-blue?style=for-the-badge&logo=artificial-intelligence" />',
    "Electron Badge": '<img src="https://img.shields.io/badge/Electron-25.0-47848F?style=for-the-badge&logo=electron" />',
    "Docker Badge":   '<img src="https://img.shields.io/badge/docker-ready-2496ED?style=for-the-badge&logo=docker" />',
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

# ── Badge Picker ──────────────────────────────────────────────────────────
class BadgeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Badges"); self.setFixedSize(480, 500)
        lay = QVBoxLayout(self); lay.setContentsMargins(14,12,14,12); lay.setSpacing(10)
        lay.addWidget(QLabel("Select a badge to insert:", styleSheet="font-weight:600;font-size:13px;"))
        self.list = QListWidget()
        self.list.setStyleSheet(
            f"QListWidget{{background:{T['bg']};border:1px solid {T['border']};border-radius:8px;outline:none;}}"
            f"QListWidget::item{{padding:6px 10px;border-radius:5px;font-size:11px;}}"
            f"QListWidget::item:selected{{background:{T['accent']};color:white;}}"
        )
        for k in BADGES:
            self.list.addItem(k)
        lay.addWidget(self.list)
        row = QHBoxLayout()
        row.addStretch()
        cancel = QPushButton("Cancel"); cancel.clicked.connect(self.reject); row.addWidget(cancel)
        insert = QPushButton("Insert")
        insert.setStyleSheet(f"background:{T['accent']};color:#F5F5F5;border:1px solid {T['border']};border-radius:7px;padding:8px 16px;font-weight:600;")
        insert.clicked.connect(self._insert); row.addWidget(insert)
        lay.addLayout(row)
        self.list.doubleClicked.connect(self._insert)

    def _insert(self):
        sel = self.list.currentItem()
        if sel and sel.text() in BADGES:
            tab = self.parent().tabs.currentWidget() if hasattr(self.parent(), 'tabs') else None
            if tab and hasattr(tab, 'editor'):
                tab.editor.insert_block(BADGES[sel.text()])
        self.accept()

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
                    colors = ["#FF6188", "#A9DC76", "#AB9DF2", "#FC9867", "#78DCE8", "#FDF9F3"]
                    color = QColor(colors[blk.blockNumber() % len(colors)])
                    line_w = min(30 + (blk.blockNumber() * 7) % 40, int(self.width()/scale)-8)
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

        self._saved_hash = hash(content) if content else hash("")
        self.editor = Editor(self.app)
        if content:
            self.editor.setPlainText(content)
        self.editor.textChanged.connect(self._on_change)
        self.canvas_data = self._load_canvas_data()

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


        self._worker = RenderWorker()
        self._render_thread = QThread()
        self._worker.moveToThread(self._render_thread)
        self._worker.finished.connect(self._on_html)
        self._render_thread.start()

        self._timer = QTimer(); self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._request_render)
        self.editor.textChanged.connect(lambda: self._timer.start(300))

    def _on_change(self):
        self.app.stats.refresh()
        current = hash(self.editor.toPlainText())
        dirty = current != self._saved_hash
        idx = self.app.tabs.indexOf(self)
        if idx >= 0:
            title = self.file_name
            if dirty:
                self.app.tabs.setTabText(idx, f"● {title}")
            else:
                self.app.tabs.setTabText(idx, title)

    def _request_render(self):
        if not self.editor.toPlainText().strip():
            self._show_empty_preview(); return
        self._worker.request(self.editor.toPlainText())
        QTimer.singleShot(0, self._worker.process)

    def _show_empty_preview(self):
        self._set_preview_html("")

    def _set_preview_html(self, body_html):
        css = preview_css()
        full = f"<!DOCTYPE html><html><head><meta charset='UTF-8'>{css}</head><body><div id='content'>{body_html}</div></body></html>"
        sb = self.preview.verticalScrollBar()
        old_pos = sb.value()
        self.preview.setHtml(full)
        if old_pos > 0 and sb.maximum() > 0:
            sb.setValue(min(old_pos, sb.maximum()))

    def _on_html(self, html_out):
        self._set_preview_html(html_out)

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

    def _load_canvas_data(self):
        canvas_filename = self.file_name
        if canvas_filename.endswith(".md"):
            canvas_filename = canvas_filename[:-3]
        canvas_filename += ".canvas.json"
        path = Path(self.workspace) / canvas_filename
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print("Error loading canvas sidecar:", e)
        return {"nodes": [], "conns": [], "notes": []}







import math as _math
import time as _time

# ── Canvas node ────────────────────────────────────────────────────────────
class _CNode:
    W, H = 210, 80
    def __init__(self, nid, name, x=60, y=60, preview=''):
        self.id      = nid
        self.name    = name
        self.x       = float(x)
        self.y       = float(y)
        self.preview = preview
    def to_dict(self):
        return {'id': self.id, 'name': self.name,
                'x': self.x, 'y': self.y, 'preview': self.preview}
    @staticmethod
    def from_dict(d):
        return _CNode(d['id'], d.get('name','Node'),
                      d.get('x', 60), d.get('y', 60),
                      d.get('preview',''))

class _CConn:
    def __init__(self, fr, to):
        self.from_id = fr; self.to_id = to
    def to_dict(self):
        return {'from': self.from_id, 'to': self.to_id}
    @staticmethod
    def from_dict(d):
        return _CConn(d['from'], d['to'])


# ── CanvasWidget — pure QPainter, NO WebEngine ──────────────────────────────
class CanvasWidget(QWidget):
    """Pan/zoom infinite canvas drawn entirely with QPainter."""

    def __init__(self, app_ref, parent=None):
        super().__init__(parent)
        self._app   = app_ref
        self.nodes: list[_CNode] = []
        self.conns: list[_CConn] = []
        self.cam_x  = 0.0
        self.cam_y  = 0.0
        self.zoom   = 1.0
        self.sel    = None   # selected node id
        self._drag  = None   # {'t':'n'|'c'|'conn', ...}
        self._hovered_node = None
        self._conn_source = None  # node id when dragging a connection
        self._conn_drag_pos = None  # (sx, sy) current drag pos
        self._conn_anchors = {}  # node_id -> list of (sx, sy, side)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.ClickFocus)
        self.setMinimumWidth(50)
        self.setStyleSheet(f"background:{T['bg']};")
        # Debounced persist timer
        self._persist_timer = QTimer()
        self._persist_timer.setSingleShot(True)
        self._persist_timer.setInterval(400)
        self._persist_timer.timeout.connect(self._do_persist)

    # ── coordinate helpers ─────────────────────────────────────────────────
    def _s2c(self, sx, sy):
        return (sx - self.cam_x) / self.zoom, (sy - self.cam_y) / self.zoom

    def _c2s(self, cx, cy):
        return cx * self.zoom + self.cam_x, cy * self.zoom + self.cam_y

    def _node_at(self, sx, sy):
        for n in reversed(self.nodes):
            nx, ny = self._c2s(n.x, n.y)
            if nx <= sx <= nx + n.W * self.zoom and ny <= sy <= ny + n.H * self.zoom:
                return n
        return None

    # ── data load ──────────────────────────────────────────────────────────
    def load(self, data: dict):
        self.nodes = [_CNode.from_dict(d) for d in data.get('nodes', [])]
        self.conns = [_CConn.from_dict(d) for d in data.get('conns', [])]
        self.sel = None
        # Center camera on nodes
        if self.nodes:
            xs = [n.x for n in self.nodes]
            ys = [n.y for n in self.nodes]
            cx = (min(xs) + max(xs)) / 2
            cy = (min(ys) + max(ys)) / 2
            sw = self.width() or 600
            sh = self.height() or 400
            bw = max(xs) - min(xs) + _CNode.W
            bh = max(ys) - min(ys) + _CNode.H
            zx = (sw - 40) / bw if bw > 0 else 1.0
            zy = (sh - 40) / bh if bh > 0 else 1.0
            self.zoom = min(1.0, min(zx, zy))
            self.cam_x = sw / 2 - cx * self.zoom
            self.cam_y = sh / 2 - cy * self.zoom
        else:
            self.cam_x = 0.0
            self.cam_y = 0.0
            self.zoom = 1.0
        self.update()

    # ── paint ──────────────────────────────────────────────────────────────
    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(T['bg']))

        # dot grid
        gs = max(6, 28 * self.zoom)
        ox = self.cam_x % gs; oy = self.cam_y % gs
        p.setPen(Qt.NoPen); p.setBrush(QColor('#202020'))
        x = ox
        while x < self.width():
            y = oy
            while y < self.height():
                p.drawEllipse(int(x)-1, int(y)-1, 2, 2)
                y += gs
            x += gs

        # connections
        for conn in self.conns:
            a = next((n for n in self.nodes if n.id == conn.from_id), None)
            b = next((n for n in self.nodes if n.id == conn.to_id), None)
            if not a or not b: continue
            ax, ay = self._c2s(a.x + _CNode.W/2, a.y + _CNode.H/2)
            bx, by = self._c2s(b.x + _CNode.W/2, b.y + _CNode.H/2)
            cp = max(30, abs(bx - ax) * 0.35)
            path = QPainterPath()
            path.moveTo(ax, ay)
            path.cubicTo(ax + cp, ay, bx - cp, by, bx, by)
            pen = QPen(QColor('#5B42F3'), 1.0)
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen); p.setOpacity(0.5)
            p.drawPath(path); p.setOpacity(1.0)

        # nodes
        self._conn_anchors = {}
        for node in self.nodes:
            sx, sy = self._c2s(node.x, node.y)
            nw = node.W * self.zoom
            nh = node.H * self.zoom
            th = 34 * self.zoom
            is_sel = node.id == self.sel
            is_hover = node.id == self._hovered_node

            # card bg
            rect = QRectF(sx, sy, nw, nh)
            bg = QLinearGradient(sx, sy, sx, sy + nh)
            bg.setColorAt(0, QColor('#242428'))
            bg.setColorAt(1, QColor('#1a1a1e'))
            p.setBrush(QBrush(bg))
            col = QColor('#00DDEB') if is_sel else QColor('#303030')
            p.setPen(QPen(col, 1.5 if is_sel else 1.0))
            p.drawRoundedRect(rect, 10, 10)

            # selection glow
            if is_sel:
                p.setPen(QPen(QColor(0, 221, 235, 45), 7))
                p.setBrush(Qt.NoBrush)
                p.drawRoundedRect(rect.adjusted(-3,-3,3,3), 13, 13)

            # title separator
            p.setPen(QPen(QColor('#2e2e2e'), 1))
            p.drawLine(int(sx), int(sy+th), int(sx+nw), int(sy+th))

            # title
            fs_t = max(7, int(11 * self.zoom))
            f = QFont('Segoe UI', fs_t); f.setWeight(QFont.DemiBold)
            p.setFont(f); p.setPen(QColor('#E8E8ED'))
            tr = QRectF(sx + 10*self.zoom, sy + 6*self.zoom,
                        nw - 20*self.zoom, th - 10*self.zoom)
            p.drawText(tr, Qt.AlignVCenter | Qt.AlignLeft,
                       p.fontMetrics().elidedText(node.name, Qt.ElideRight, int(tr.width())))

            # preview
            fs_p = max(6, int(9.5 * self.zoom))
            p.setFont(QFont('Segoe UI', fs_p))
            p.setPen(QColor('#666666'))
            pr = QRectF(sx + 10*self.zoom, sy + th + 5*self.zoom,
                        nw - 20*self.zoom, nh - th - 10*self.zoom)
            p.drawText(pr, Qt.AlignTop | Qt.AlignLeft | Qt.TextWordWrap,
                       node.preview or 'Empty...')

            # Connection anchors (only on hovered or selected nodes)
            if is_hover or is_sel or self._conn_source:
                anchor_radius = 6 * self.zoom
                anchor_positions = [
                    (sx + nw/2, sy, 'top'),
                    (sx + nw/2, sy + nh, 'bottom'),
                    (sx, sy + nh/2, 'left'),
                    (sx + nw, sy + nh/2, 'right'),
                ]
                anchors = []
                for ax, ay, side in anchor_positions:
                    p.setBrush(QColor('#00DDEB' if is_hover else '#4a4a4a'))
                    p.setPen(QPen(QColor('#00DDEB' if is_hover else '#666666'), 1))
                    p.drawEllipse(QRectF(ax - anchor_radius, ay - anchor_radius,
                                         anchor_radius * 2, anchor_radius * 2))
                    anchors.append((ax, ay, side))
                self._conn_anchors[node.id] = anchors

        # Draw temporary connection line while dragging
        if self._conn_source and self._conn_drag_pos:
            src_node = next((n for n in self.nodes if n.id == self._conn_source), None)
            if src_node:
                ax, ay = self._c2s(src_node.x + _CNode.W/2, src_node.y + _CNode.H/2)
                pen = QPen(QColor('#00DDEB'), 2.0, Qt.DashLine)
                pen.setCapStyle(Qt.RoundCap)
                p.setPen(pen)
                p.setOpacity(0.6)
                p.drawLine(int(ax), int(ay),
                           int(self._conn_drag_pos[0]), int(self._conn_drag_pos[1]))
                p.setOpacity(1.0)

        p.end()

    # ── mouse ──────────────────────────────────────────────────────────────
    def _anchor_at(self, sx, sy):
        """Check if click is on a connection anchor. Returns (node_id, side) or None."""
        for nid, anchors in self._conn_anchors.items():
            for ax, ay, side in anchors:
                r = 8 * self.zoom
                if abs(sx - ax) <= r and abs(sy - ay) <= r:
                    return nid, side
        return None

    def mousePressEvent(self, e):
        if e.button() != Qt.LeftButton: return
        # Stop scan debounce during drag to prevent canvas reload
        self._app._scan_debounce.stop()
        # Check if clicking on a connection anchor
        anchor = self._anchor_at(e.position().x(), e.position().y())
        if anchor:
            self._conn_source = anchor[0]
            self._conn_drag_pos = (e.position().x(), e.position().y())
            self._drag = {'t': 'conn'}
            self.update()
            return
        node = self._node_at(e.position().x(), e.position().y())
        if node:
            if (e.modifiers() & Qt.ShiftModifier) and self.sel and self.sel != node.id:
                if not any(c.from_id == self.sel and c.to_id == node.id for c in self.conns):
                    self.conns.append(_CConn(self.sel, node.id))
                    self._persist()
                self.sel = node.id; self.update(); return
            self.sel = node.id
            cx, cy = self._s2c(e.position().x(), e.position().y())
            self._drag = {'t':'n', 'id':node.id, 'ox':cx-node.x, 'oy':cy-node.y}
        else:
            self.sel = None
            self._drag = {'t':'c',
                          'sx': e.position().x() - self.cam_x,
                          'sy': e.position().y() - self.cam_y}
        self.update()

    def mouseMoveEvent(self, e):
        # Update hovered node for anchor display
        node = self._node_at(e.position().x(), e.position().y())
        self._hovered_node = node.id if node else None

        if not self._drag:
            self.update()
            return
        if self._drag['t'] == 'conn':
            self._conn_drag_pos = (e.position().x(), e.position().y())
            self.repaint()
            return
        elif self._drag['t'] == 'c':
            self.cam_x = e.position().x() - self._drag['sx']
            self.cam_y = e.position().y() - self._drag['sy']
            self.cam_x = max(-3000, min(3000, self.cam_x))
            self.cam_y = max(-3000, min(3000, self.cam_y))
        elif self._drag['t'] == 'n':
            cx, cy = self._s2c(e.position().x(), e.position().y())
            for n in self.nodes:
                if n.id == self._drag['id']:
                    n.x = cx - self._drag['ox']
                    n.y = cy - self._drag['oy']
                    break
            self.repaint()
            return
        self.update()

    def mouseReleaseEvent(self, e):
        if self._drag and self._drag['t'] == 'conn':
            # Check if released on another node's anchor
            anchor = self._anchor_at(e.position().x(), e.position().y())
            if anchor and anchor[0] != self._conn_source:
                target_id = anchor[0]
                if not any(c.from_id == self._conn_source and c.to_id == target_id for c in self.conns):
                    self.conns.append(_CConn(self._conn_source, target_id))
                    self._persist()
            self._conn_source = None
            self._conn_drag_pos = None
        elif self._drag and self._drag['t'] == 'n':
            self._persist()
        self._drag = None
        self.update()

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Delete, Qt.Key_Backspace) and self.sel:
            node = next((n for n in self.nodes if n.id == self.sel), None)
            if node:
                # Close open tab
                for i in range(self._app.tabs.count()):
                    tab = self._app.tabs.widget(i)
                    if tab and tab.file_name == node.id:
                        self._app._close_tab(i)
                        break
                self.nodes = [n for n in self.nodes if n.id != node.id]
                self.conns = [c for c in self.conns
                              if c.from_id != node.id and c.to_id != node.id]
                # Track as removed so it doesn't auto-reappear
                removed = set(self._app._global_canvas.get('removed', []))
                removed.add(node.id)
                self._app._global_canvas['removed'] = list(removed)
                self.sel = None
                self.update()
                self._persist()
                self._app._flash(f"Removed: {node.name}")
        super().keyPressEvent(e)

    def leaveEvent(self, e):
        self._hovered_node = None
        self.update()
        super().leaveEvent(e)

    def mouseDoubleClickEvent(self, e):
        """Double-click a node → switch to that README tab or open it."""
        node = self._node_at(e.position().x(), e.position().y())
        if not node: return
        app = self._app
        
        # Check if tab is already open
        for i in range(app.tabs.count()):
            tab = app.tabs.widget(i)
            if tab and tab.file_name == node.id:
                app.tabs.setCurrentIndex(i)
                app._flash(f"Switched to: {node.name}")
                return
                
        # Tab is not open. Try to open the file from workspace
        file_path = Path(app.workspace) / node.id
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                app._new_tab(content, node.id)
                app._flash(f"Opened: {node.name}")
            except Exception as e:
                app._flash(f"Failed to open file: {e}")
        else:
            # Create a new file/tab
            app._new_tab("", node.id)
            app._flash(f"Created new README: {node.name}")

    def wheelEvent(self, e):
        e.accept()
        if e.modifiers() & Qt.ControlModifier:
            mx, my = e.position().x(), e.position().y()
            f = 1.12 if e.angleDelta().y() > 0 else 0.89
            nz = max(0.15, min(2.5, self.zoom * f))
            self.cam_x = mx - (mx - self.cam_x) * (nz / self.zoom)
            self.cam_y = my - (my - self.cam_y) * (nz / self.zoom)
            self.zoom = nz
        else:
            self.cam_x -= e.angleDelta().x() / 3
            self.cam_y -= e.angleDelta().y() / 3
        # Clamp camera to prevent infinite scroll
        self.cam_x = max(-3000, min(3000, self.cam_x))
        self.cam_y = max(-3000, min(3000, self.cam_y))
        self._notify_zoom()
        self.update()

    def contextMenuEvent(self, e):
        node = self._node_at(e.pos().x(), e.pos().y())
        m = QMenu(self); m.setStyleSheet(MENU_STYLE())
        if node:
            ren = m.addAction('Rename')
            m.addSeparator()
            dlt = m.addAction('Delete')
            act = m.exec(e.globalPos())
            if act == ren:
                name, ok = QInputDialog.getText(self,'Rename','Name:', text=node.name)
                if ok and name.strip():
                    old_id = node.id
                    new_name = name.strip()
                    if not new_name.endswith('.md'):
                        new_id = new_name + '.md'
                    else:
                        new_id = new_name
                    # Sanitize: prevent path traversal
                    new_id = Path(new_id).name
                    
                    # Rename on disk if exists
                    old_path = Path(self._app.workspace) / old_id
                    new_path = Path(self._app.workspace) / new_id
                    if old_path.exists():
                        try:
                            old_path.rename(new_path)
                        except Exception as ex:
                            print("Rename error:", ex)
                    
                    # Rename currently open tab
                    for i in range(self._app.tabs.count()):
                        tab = self._app.tabs.widget(i)
                        if tab and tab.file_name == old_id:
                            tab.file_name = new_id
                            self._app.tabs.setTabText(i, new_id)
                    
                    # Update connections that reference old_id
                    for c in self.conns:
                        if c.from_id == old_id: c.from_id = new_id
                        if c.to_id == old_id: c.to_id = new_id
                    node.id = new_id
                    node.name = new_id
                    self.update()
                    self._persist()
                    self._app._flash(f"Renamed node to: {new_id}")
            elif act == dlt:
                # Ask user first before deleting file
                ret = QMessageBox.question(
                    self, 'Delete Node',
                    f"Do you want to delete the node '{node.name}' from the canvas?\n\n"
                    f"Click 'Yes' to also delete the file from your computer.",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                    QMessageBox.No
                )
                if ret == QMessageBox.Cancel:
                    return
                if ret == QMessageBox.Yes:
                    # Delete file from disk
                    file_path = Path(self._app.workspace) / node.id
                    if file_path.exists():
                        try:
                            file_path.unlink()
                            self._app._flash(f"Deleted file: {node.id}")
                        except Exception as ex:
                            self._app._flash(f"Failed to delete file: {ex}")
                            
                # Close open tab
                for i in range(self._app.tabs.count()):
                    tab = self._app.tabs.widget(i)
                    if tab and tab.file_name == node.id:
                        self._app._close_tab(i)
                        break
                        
                self.nodes = [n for n in self.nodes if n.id != node.id]
                self.conns = [c for c in self.conns
                              if c.from_id != node.id and c.to_id != node.id]
                # Track as removed so it doesn't auto-reappear
                removed = set(self._app._global_canvas.get('removed', []))
                removed.add(node.id)
                self._app._global_canvas['removed'] = list(removed)
                self.sel = None
                self.update(); self._persist()
        else:
            add = m.addAction('Add Node')
            act = m.exec(e.globalPos())
            if act == add:
                name, ok = QInputDialog.getText(self, 'Create New README', 'File name (e.g. README_new.md):')
                if ok and name.strip():
                    new_id = name.strip()
                    if not new_id.endswith('.md'):
                        new_id += '.md'
                    new_id = Path(new_id).name  # sanitize
                    cx, cy = self._s2c(e.pos().x(), e.pos().y())
                    node = _CNode(new_id, new_id, cx, cy)
                    self.nodes.append(node)
                    self.sel = new_id
                    
                    # Clear removed flag if re-adding
                    removed = set(self._app._global_canvas.get('removed', []))
                    removed.discard(new_id)
                    self._app._global_canvas['removed'] = list(removed)
                    # Create empty tab
                    self._app._new_tab("", new_id)
                    self.update()
                    self._persist()

    def _persist(self):
        self._persist_timer.start()

    def _do_persist(self):
        d = self._app.canvas_panel.get_data()
        self._app._global_canvas['nodes'] = d['nodes']
        self._app._global_canvas['conns'] = d['conns']
        self._app._save_global_canvas()

    def _notify_zoom(self):
        par = self.parent()
        if par and hasattr(par, '_update_zoom'):
            par._update_zoom(self.zoom)


# ── CanvasPanel — header bar + CanvasWidget ────────────────────────────────
class CanvasPanel(QWidget):
    def __init__(self, app_ref, parent=None):
        super().__init__(parent)
        self._app = app_ref
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # ── header ──
        hdr = QFrame()
        hdr.setFixedHeight(28)
        hdr.setStyleSheet(
            f'QFrame{{background:{T["panel"]};border-left:1px solid {T["border"]};'
            f'border-bottom:1px solid {T["border"]};}}'
        )
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(0, 0, 6, 0)
        hl.setSpacing(2)

        def _tbtn(lbl, fn):
            b = QToolButton(); b.setText(lbl)
            b.clicked.connect(fn)
            b.setStyleSheet(
                f'QToolButton{{background:transparent;color:{T["dim"]};border:none;'
                f'border-radius:4px;font-size:12px;padding:2px 4px;}}'
                f'QToolButton:hover{{background:{T["hover"]};color:{T["text"]};}}'
            )
            return b

        hl.addStretch()
        hl.addWidget(_tbtn('−', self._zoom_out))
        hl.addWidget(_tbtn('+', self._zoom_in))

        lay.addWidget(hdr)

        # ── canvas ──
        self.canvas = CanvasWidget(app_ref, self)
        lay.addWidget(self.canvas)

    def _zoom_in(self):
        self.canvas.zoom = min(2.5, self.canvas.zoom * 1.2)
        self.canvas.update()

    def _zoom_out(self):
        self.canvas.zoom = max(0.15, self.canvas.zoom / 1.2)
        self.canvas.update()

    def load(self, data: dict):
        self.canvas.load(data)

    def get_data(self):
        return {
            'nodes': [n.to_dict() for n in self.canvas.nodes],
            'conns': [c.to_dict() for c in self.canvas.conns],
        }

class App(QMainWindow):
    def __init__(self, workspace=None):
        super().__init__()
        self.workspace = os.path.abspath(workspace or os.getcwd())
        self.setWindowTitle("README Builder")
        self.resize(1300, 650)
        self.git_url = ""

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

        # Splitter to hold main area (tabs/stats) and rightbar (canvas)
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setStyleSheet(f"QSplitter::handle{{background:{T['border']};}}")
        self.main_splitter.setHandleWidth(2)
        root.addWidget(self.main_splitter)

        main = QWidget()
        ml = QVBoxLayout(main); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)
        self.main_splitter.addWidget(main)

        # Rightbar: pure-Qt canvas panel (no WebEngine – keeps app size small)
        self.canvas_panel = CanvasPanel(self)
        self.main_splitter.addWidget(self.canvas_panel)
        self.canvas_panel.hide()

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        ml.addWidget(self.tabs)
        
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
        QShortcut(QKeySequence("Ctrl+R"), self, self._toggle_canvas)

        # Smart shortcuts (AZERTY top row: &=1, é=2, "=3, '=4)
        QShortcut(QKeySequence("Alt+&"), self, lambda: self._smart_h("alt", 1))
        QShortcut(QKeySequence("Alt+é"), self, lambda: self._smart_h("alt", 2))
        QShortcut(QKeySequence('Alt+"'), self, lambda: self._smart_h("alt", 3))
        QShortcut(QKeySequence("F3"), self, lambda: self._smart_img())
        QShortcut(QKeySequence("F4"), self, lambda: self._smart_center_h1())
        QShortcut(QKeySequence("F5"), self, lambda: self._smart_align("left"))
        QShortcut(QKeySequence("F6"), self, lambda: self._smart_align("center"))
        QShortcut(QKeySequence("F7"), self, lambda: self._smart_align("right"))
        QShortcut(QKeySequence("F8"), self, lambda: self._smart_bold_list())
        QShortcut(QKeySequence("F9"), self, lambda: self._smart_note())
        QShortcut(QKeySequence("F10"), self, lambda: self._smart_code("bash"))
        QShortcut(QKeySequence("Ctrl+&"), self, lambda: self._smart_table(2))
        QShortcut(QKeySequence("Ctrl+é"), self, lambda: self._smart_table(3))
        QShortcut(QKeySequence('Ctrl+"'), self, lambda: self._smart_table(4))
        QShortcut(QKeySequence("Ctrl+'"), self, lambda: self._smart_table_aligned())

        self.user_snippets = self._load_snippets()
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # Global canvas — persisted in workspace/workspace.canvas.json
        self._global_canvas = {'nodes': [], 'conns': [], 'removed': []}
        self._load_global_canvas()

        # File system watcher for new .md files
        self._fs_watcher = QFileSystemWatcher()
        self._fs_watcher.addPath(self.workspace)
        self._fs_watcher.directoryChanged.connect(self._on_workspace_changed)
        self._scan_debounce = QTimer()
        self._scan_debounce.setSingleShot(True)
        self._scan_debounce.setInterval(500)
        self._scan_debounce.timeout.connect(self._sync_tabs_to_canvas)

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
            # Refresh global canvas when tab changes
            if self.canvas_panel.isVisible():
                QTimer.singleShot(60, self._load_active_tab_canvas)

    def _sync_ai_ctx_bar(self):
        pass

    def _on_workspace_changed(self, path):
        """Called when files in workspace change — rescan and update canvas."""
        self._scan_debounce.start()
        if self.canvas_panel.isVisible():
            QTimer.singleShot(600, self._refresh_canvas)

    def _toggle_canvas(self):
        """Show/hide the global canvas panel."""
        if self.canvas_panel.isVisible():
            self.canvas_panel.hide()
        else:
            self.canvas_panel.show()
            total = self.main_splitter.width()
            n = self.main_splitter.count()
            w = max(370, min(480, total // 3))
            sizes = [max(200, total - w)] + [0] * (n - 2) + [w]
            if n == 2:
                sizes = [total - w, w]
            self.main_splitter.setSizes(sizes)
            self._refresh_canvas()

    def _refresh_canvas(self):
        """Sync open README tabs as nodes, then push to the canvas widget."""
        if self.canvas_panel.canvas._drag is not None:
            return
        self._sync_tabs_to_canvas()
        self.canvas_panel.load(self._global_canvas)

    def _load_active_tab_canvas(self):
        """Called when tab changes — refresh canvas if visible."""
        if self.canvas_panel.isVisible():
            self._refresh_canvas()

    def _sync_tabs_to_canvas(self):
        """Ensure every .md file in the workspace has a node in the global canvas."""
        existing_ids = {n['id'] for n in self._global_canvas.get('nodes', [])}
        removed = set(self._global_canvas.get('removed', []))
        new_ids = []
        changed = False
        
        # Get all .md files in the workspace (skip removed)
        md_files = []
        try:
            for entry in os.scandir(self.workspace):
                if entry.is_file() and entry.name.lower().endswith('.md'):
                    if entry.name not in removed:
                        md_files.append(entry.name)
        except Exception:
            pass
        
        # Also include any currently open tabs (even if removed, re-add them)
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab and tab.file_name not in md_files:
                md_files.append(tab.file_name)
                removed.discard(tab.file_name)
                
        for file_name in md_files:
            if file_name not in existing_ids:
                col = len(existing_ids) % 4
                row = len(existing_ids) // 4
                x = 60 + col * 260
                y = 60 + row * 130
                
                # Extract preview: try heading first, then first non-empty line
                preview_text = ''
                file_path = Path(self.workspace) / file_name
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for line in f:
                                cleaned = line.strip()
                                if cleaned.startswith('#'):
                                    preview_text = cleaned.lstrip('#').strip()
                                    break
                                elif cleaned and not preview_text:
                                    preview_text = cleaned[:60]
                    except:
                        pass
                # Also check open tab for content if file is empty but tab has text
                if not preview_text:
                    for i in range(self.tabs.count()):
                        tab = self.tabs.widget(i)
                        if tab and tab.file_name == file_name:
                            content = tab.editor.toPlainText().strip()
                            if content:
                                first_line = content.split('\n')[0].strip()
                                preview_text = first_line.lstrip('#').strip()[:60]
                            break
                
                self._global_canvas.setdefault('nodes', []).append({
                    'id': file_name,
                    'name': file_name,
                    'x': x,
                    'y': y,
                    'preview': preview_text[:60] if preview_text else ''
                })
                existing_ids.add(file_name)
                new_ids.append(file_name)
                changed = True
        
        # Auto-connect all nodes in order (chain layout)
        existing_conns = {(c['from'], c['to']) for c in self._global_canvas.get('conns', [])}
        nodes = self._global_canvas.setdefault('nodes', [])
        node_ids = [n['id'] for n in nodes]
        for i in range(1, len(node_ids)):
            fr, to = node_ids[i-1], node_ids[i]
            if (fr, to) not in existing_conns and (to, fr) not in existing_conns:
                self._global_canvas.setdefault('conns', []).append({'from': fr, 'to': to})
                changed = True
                
        if changed:
            self._save_global_canvas()

    def _load_global_canvas(self):
        """Load global canvas from workspace/workspace.canvas.json."""
        path = Path(self.workspace) / 'workspace.canvas.json'
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self._global_canvas = json.load(f)
            except Exception as e:
                print('Canvas load error:', e)
                self._global_canvas = {'nodes': [], 'conns': []}

    def _save_global_canvas(self):
        """Persist global canvas → workspace/workspace.canvas.json."""
        path = Path(self.workspace) / 'workspace.canvas.json'
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self._global_canvas, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print('Canvas save error:', e)

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
            ("Images",   self._open_images,     "Ctrl+I"),
            ("Badge",    self._open_badges,      ""),
            ("Find",     lambda: (self.find_bar.show(), self.find_bar.find.setFocus()), "Ctrl+F"),
            ("Export",   self._export,          ""),
            ("Recent",   self._show_recent,     ""),
            ("Canvas",   self._toggle_canvas,   ""),
        ]
        for lbl, fn, sc in buttons:
            b = QToolButton(); b.setText(lbl); b.clicked.connect(fn)
            if sc: b.setToolTip(f"{lbl} ({sc})")
            lay.addWidget(b)
        
        lay.addStretch()
        credit = QLabel("Yasser-27")
        credit.setAlignment(Qt.AlignCenter)
        credit.setStyleSheet(f"color:{T['dim']};font-size:9px;background:transparent;padding:4px;")
        lay.addWidget(credit)
        return sb



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

    def _open_images(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        ImageDialog(tab.editor, self.workspace, self).exec()

    def _open_badges(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        d = BadgeDialog(self)
        if d.exec() == QDialog.Accepted: pass

    def _editor(self):
        tab = self.tabs.currentWidget()
        return tab.editor if tab and hasattr(tab, 'editor') else None

    def _smart_h(self, _, level):
        e = self._editor()
        if not e: return
        c = e.textCursor(); prefix = '#' * level + ' '
        if c.hasSelection():
            t = c.selectedText().replace('\u2029', '\n')
            c.insertText(prefix + t)
        else:
            c.movePosition(QTextCursor.StartOfLine)
            c.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
            t = c.selectedText().replace('\u2029', '\n')
            c.insertText(prefix + t)

    def _smart_align(self, where):
        e = self._editor()
        if not e: return
        c = e.textCursor()
        if c.hasSelection():
            t = c.selectedText().replace('\u2029', '\n')
            c.insertText(f'<p align="{where}">\n{t}\n</p>\n')
        else:
            c.movePosition(QTextCursor.StartOfLine)
            c.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
            t = c.selectedText().replace('\u2029', '\n')
            c.insertText(f'<p align="{where}">\n{t}\n</p>\n')

    def _smart_img(self):
        e = self._editor()
        if not e: return
        e.textCursor().insertText('<img src="" width="100" alt="Logo">')

    def _smart_center_h1(self):
        e = self._editor()
        if not e: return
        c = e.textCursor()
        if c.hasSelection():
            t = c.selectedText().replace('\u2029', '\n')
            c.insertText(f'<h1 align="center">{t}</h1>\n')
        else:
            c.movePosition(QTextCursor.StartOfLine)
            c.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
            t = c.selectedText().replace('\u2029', '\n')
            c.insertText(f'<h1 align="center">{t}</h1>\n')

    def _smart_bold_list(self):
        e = self._editor()
        if not e: return
        c = e.textCursor()
        if c.hasSelection():
            lines = c.selectedText().replace('\u2029', '\n').split('\n')
            c.insertText('\n'.join(f'- **{l}**' for l in lines))
        else:
            c.movePosition(QTextCursor.StartOfLine)
            c.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
            t = c.selectedText().replace('\u2029', '\n')
            c.insertText(f'- **{t}**')

    def _smart_note(self):
        e = self._editor()
        if not e: return
        c = e.textCursor()
        if c.hasSelection():
            t = c.selectedText().replace('\u2029', '\n')
            c.insertText(f'> [!NOTE]\n> {t}')
        else:
            c.insertText('> [!NOTE]\n> ')

    def _smart_code(self, lang):
        e = self._editor()
        if not e: return
        c = e.textCursor()
        if c.hasSelection():
            t = c.selectedText().replace('\u2029', '\n')
            c.insertText(f'```{lang}\n{t}\n```\n')
        else:
            c.insertText(f'```{lang}\n\n```\n')

    def _smart_table(self, cols):
        e = self._editor()
        if not e: return
        h = ' | '.join(f'Column {i+1}' for i in range(cols))
        s = ' | '.join('---' for _ in range(cols))
        r = ' | '.join('Cell' for _ in range(cols))
        e.textCursor().insertText(f'| {h} |\n| {s} |\n| {r} |\n')

    def _smart_table_aligned(self):
        e = self._editor()
        if not e: return
        e.textCursor().insertText('| Left | Center | Right |\n|:-----|:------:|------:|\n| L    |   C    |     R |\n')

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
        # Immediately sync to canvas
        self._sync_tabs_to_canvas()
        if self.canvas_panel.isVisible():
            self._refresh_canvas()
        return tab

    def _close_tab(self, idx):
        if self.tabs.count() > 1:
            tab = self.tabs.widget(idx)
            if tab:
                tab.stop()
                file_name = tab.file_name
            self.tabs.removeTab(idx)
            # Remove from canvas if visible
            if self.canvas_panel.isVisible() and tab:
                self._global_canvas['nodes'] = [
                    n for n in self._global_canvas.get('nodes', [])
                    if n['id'] != file_name
                ]
                self._global_canvas['conns'] = [
                    c for c in self._global_canvas.get('conns', [])
                    if c['from'] != file_name and c['to'] != file_name
                ]
                removed = set(self._global_canvas.get('removed', []))
                removed.add(file_name)
                self._global_canvas['removed'] = list(removed)
                self._save_global_canvas()
                self._refresh_canvas()

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
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
        snippets_dir = Path(base) / "README Builder"
        snippets_dir.mkdir(parents=True, exist_ok=True)
        return snippets_dir / "snippets.json"

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
        display_name = tab.file_name[:-3] if tab.file_name.endswith('.md') else tab.file_name
        dlg.setTextValue(display_name)
        if dlg.exec() == QInputDialog.Accepted:
            new_name = dlg.textValue().strip()
            if new_name:
                if "." not in new_name: new_name += ".md"
                new_name = Path(new_name).name  # sanitize
                # Rename canvas sidecar file if it exists
                old_canvas = tab.file_name[:-3] + '.canvas.json' if tab.file_name.endswith('.md') else tab.file_name + '.canvas.json'
                new_canvas = new_name[:-3] + '.canvas.json' if new_name.endswith('.md') else new_name + '.canvas.json'
                old_path = Path(self.workspace) / old_canvas
                new_path = Path(self.workspace) / new_canvas
                if old_path.exists():
                    try: old_path.rename(new_path)
                    except Exception as e: print('Canvas rename error:', e)
                tab.file_name = new_name; self.tabs.setTabText(idx, new_name)
                self._flash(f"Renamed: {new_name}")

    def _load_initial(self):
        # Defer tab creation slightly to let window paint first
        if self.tabs.count() == 0:
            QTimer.singleShot(50, lambda: self._new_tab("", "README.md"))

    def _export(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        p, _ = QFileDialog.getSaveFileName(self,"Export","README.md","Markdown (*.md);;HTML (*.html);;PDF (*.pdf)")
        if not p: return
        try:
            text = tab.editor.toPlainText()
            if p.endswith(".pdf"):
                css = preview_css()
                html = markdown2.markdown(text, extras=["fenced-code-blocks","tables","task_list"])
                full = f"<!DOCTYPE html><html><head><meta charset='UTF-8'>{css}</head><body>{html}</body></html>"
                doc = QTextDocument()
                doc.setHtml(full)
                printer = QPrinter()
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(p)
                printer.setPageSize(QPrinter.A4)
                printer.setPageMargins(20, 20, 20, 20, QPrinter.Millimeter)
                doc.print(printer)
            elif p.endswith(".html"):
                css = preview_css()
                html_out = markdown2.markdown(text, extras=["fenced-code-blocks","tables","task_list"])
                Path(p).write_text(f"<!DOCTYPE html><html><head><meta charset='UTF-8'>{css}</head><body>{html_out}</body></html>","utf-8")
            else:
                Path(p).write_text(f"<!-- README Builder | {datetime.now():%Y-%m-%d} -->\n\n{text}","utf-8")
            QMessageBox.information(self,"Exported",f"Saved:\n{p}")
        except Exception as e: QMessageBox.critical(self,"Error",str(e))

    def _save(self):
        tab = self.tabs.currentWidget()
        if not tab: return False
        try:
            text = tab.editor.toPlainText()
            (Path(self.workspace) / tab.file_name).write_text(text, "utf-8")
            tab._saved_hash = hash(text)
            idx = self.tabs.indexOf(tab)
            if idx >= 0:
                self.tabs.setTabText(idx, tab.file_name)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))
            return False

    def closeEvent(self, e):
        """Fast shutdown — terminate all threads promptly to avoid UI freeze."""
        # Stop file watcher
        self._scan_debounce.stop()
        try: self._fs_watcher.removePath(self.workspace)
        except: pass
        # Stop all document tabs
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab and hasattr(tab, "stop"):
                try: tab.stop()
                except: pass
        # Stop canvas persist timer
        try: self.canvas_panel.canvas._persist_timer.stop()
        except: pass

        # Let the event loop drain before exit
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
            # Check if registration is needed (missing or exe path changed)
            needs_register = False
            try:
                test_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\READMEBuilder.Markdown\shell\open\command")
                existing_cmd, _ = winreg.QueryValueEx(test_key, "")
                winreg.CloseKey(test_key)
                # Re-register if exe path changed
                if exe_path.lower() not in existing_cmd.lower():
                    needs_register = True
            except (FileNotFoundError, OSError):
                needs_register = True

            if needs_register:
                import ctypes
                ret = ctypes.windll.user32.MessageBoxW(
                    0,
                    "Allow README Builder to add context menu entries?\n\n"
                    "This adds:\n"
                    "\u2022 'Open with README Builder' for .md files\n"
                    "\u2022 'Create README here' in folder context menus\n"
                    "\u2022 File association for .md / .markdown",
                    "README Builder \u2014 Registry Setup",
                    4 | 32
                )
                if ret != 6:  # IDYES = 6
                    needs_register = False
            if needs_register:
                # Context menu: Open with README Builder (all files)
                k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\*\shell\Open with README Builder")
                winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, exe_path)
                winreg.SetValueEx(k, "Position", 0, winreg.REG_SZ, "Top")
                winreg.SetValueEx(winreg.CreateKey(k, "command"), "", 0, winreg.REG_SZ, f'{exe_str} "%1"')
                winreg.CloseKey(k)

                # Context menu: Create README here (folder)
                k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\Directory\shell\Create README here")
                winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, exe_path)
                winreg.SetValueEx(winreg.CreateKey(k, "command"), "", 0, winreg.REG_SZ, f'{exe_str} "%1"')
                winreg.CloseKey(k)

                # Context menu: Create README here (folder background)
                k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\Directory\Background\shell\Create README here")
                winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, exe_path)
                winreg.SetValueEx(winreg.CreateKey(k, "command"), "", 0, winreg.REG_SZ, f'{exe_str} "%V"')
                winreg.CloseKey(k)

                # File type: READMEBuilder.Markdown with icon + friendly name
                k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\READMEBuilder.Markdown")
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "Markdown Document")
                winreg.SetValueEx(k, "FriendlyTypeName", 0, winreg.REG_SZ, "Markdown Document")
                winreg.CloseKey(k)

                # DefaultIcon so .md files show the app icon
                k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\READMEBuilder.Markdown\DefaultIcon")
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, f"{exe_path},0")
                winreg.CloseKey(k)

                # Open command
                k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\READMEBuilder.Markdown\shell\open\command")
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, f'{exe_str} "%1"')
                winreg.CloseKey(k)

                # Associate .md extension
                k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.md")
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "READMEBuilder.Markdown")
                winreg.CloseKey(k)

                # Associate .markdown extension too
                k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.markdown")
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "READMEBuilder.Markdown")
                winreg.CloseKey(k)

                # Notify shell to refresh icons
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

    # Single-instance: try to send files to existing instance
    def _send_to_existing():
        sock = QLocalSocket()
        sock.connectToServer("READMEBuilder")
        if sock.waitForConnected(500):
            data = "\n".join(files_to_open).encode("utf-8")
            sock.write(QByteArray(data))
            sock.waitForBytesWritten(1000)
            sock.disconnectFromServer()
            return True
        return False

    if files_to_open and _send_to_existing():
        sys.exit(0)

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

    # Listen for files from new instances
    server = QLocalServer()
    server.removeServer("READMEBuilder")
    if server.listen("READMEBuilder"):
        def on_connection():
            conn = server.nextPendingConnection()
            if conn and conn.waitForReadyRead(2000):
                data = conn.readAll().data().decode("utf-8")
                for line in data.strip().split("\n"):
                    path = line.strip()
                    if os.path.exists(path):
                        try:
                            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()
                            window._new_tab(content, os.path.basename(path))
                        except: pass
            if conn: conn.disconnectFromServer()
        server.newConnection.connect(on_connection)

    sys.exit(app.exec())