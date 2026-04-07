import sys, os, re, json, urllib.request, urllib.error, urllib.parse, base64, subprocess, shutil
from pathlib import Path
from datetime import datetime

os.environ["QT_FONT_DPI"] = "115"

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QFrame, QLabel, QLineEdit, QSplitter,
    QMessageBox, QFileDialog, QDialog, QScrollArea, QGridLayout,
    QListWidget, QListWidgetItem, QAbstractItemView, QToolButton,
    QCheckBox, QTabWidget, QInputDialog, QComboBox, QProgressBar,
    QButtonGroup, QRadioButton, QSizePolicy, QMenu, QTextBrowser
)
from PySide6.QtCore import Qt, QUrl, QTimer, QThread, QObject, Signal, QPoint, QSize, QRect, QRunnable, QThreadPool
from PySide6.QtGui import (
    QFont, QColor, QPainter, QPen, QSyntaxHighlighter, QTextCharFormat,
    QTextDocument, QTextCursor, QIcon, QKeySequence, QShortcut, QAction,
    QPixmap
)
import markdown2

# ── Theme ──────────────────────────────────────────────────────────────────
T = {
    "bg":      "#1C1C1C", "panel":  "#141414", "border": "#2A2A2A",
    "hover":   "#222222", "input":  "#181818", "text":   "#D4D4D4",
    "dim":     "#6B6B6B", "editor": "#E8E8E8", "scroll": "#3A3A3A",
    "accent":  "#58A6FF", "accent2":"#1F6FEB", "code":   "#141414",
    "syn_h":   "#79C0FF", "syn_b":  "#E6EDF3", "syn_i":  "#CBA6F7",
    "syn_c":   "#FF7B72", "syn_l":  "#58A6FF", "syn_q":  "#888888",
    "syn_li":  "#F0883E", "syn_img":"#4ADE80", "syn_tag":"#7EE787",
    "syn_chk": "#FBBF24",
}

MENU_STYLE = lambda: (
    f"QMenu{{background:{T['panel']};border:1px solid {T['border']};border-radius:8px;"
    f"padding:4px;color:{T['text']};font-size:12px;}}"
    f"QMenu::item{{padding:7px 24px 7px 12px;border-radius:5px;margin:1px 3px;}}"
    f"QMenu::item:selected{{background:{T['accent']};color:#fff;}}"
    f"QMenu::separator{{height:1px;background:{T['border']};margin:3px 8px;}}"
    f"QMenu::right-arrow{{width:8px;height:8px;}}"
)

BTN_STYLE = lambda: (
    f"QPushButton{{background:{T['hover']};color:{T['text']};border:1px solid {T['border']};"
    f"border-radius:7px;padding:8px 16px;font-size:12px;font-weight:600;}}"
    f"QPushButton:hover{{border-color:{T['accent']};}}"
    f"QPushButton#primary{{background:{T['accent']};border:none;color:#fff;}}"
    f"QPushButton#primary:hover{{background:{T['accent2']};}}"
)

# ── Preview CSS ────────────────────────────────────────────────────────────
def preview_css():
    return f"""<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:16px;
  line-height:1.6;color:{T['text']};background:{T['bg']};padding:24px;max-width:900px;margin:0 auto;}}
h1,h2,h3,h4{{font-weight:600;color:{T['text']};margin:24px 0 12px;}}
h1{{font-size:2em;border-bottom:1px solid {T['border']};padding-bottom:.3em;}}
h2{{font-size:1.5em;border-bottom:1px solid {T['border']};padding-bottom:.3em;}}
p{{margin:0 0 14px;}}
code{{background:rgba(110,118,129,.35);padding:.2em .4em;border-radius:6px;font-size:85%;
  font-family:ui-monospace,Consolas,monospace;}}
pre{{background:{T['code']};border:1px solid {T['border']};border-radius:8px;padding:16px;
  overflow:auto;margin-bottom:16px;}}
pre code{{background:transparent;padding:0;}}
img{{max-width:100%;border-radius:6px;}}
blockquote{{padding:0 1em;color:{T['dim']};border-left:.25em solid {T['border']};margin:0 0 14px;}}
table{{border-spacing:0;border-collapse:collapse;width:100%;margin-bottom:16px;}}
th,td{{padding:6px 13px;border:1px solid {T['border']};}}
tr:nth-child(2n){{background:{T['code']};}}
hr{{height:.25em;background:{T['border']};border:0;margin:20px 0;}}
a{{color:{T['accent']};text-decoration:none;}}
a:hover{{text-decoration:underline;}}
.markdown-alert{{padding:8px 16px;margin-bottom:16px;border-left:.25em solid;border-radius:0 6px 6px 0;}}
.markdown-alert-note{{border-left-color:#2f81f7;background:rgba(47,129,247,.08);}}
.markdown-alert-warning{{border-left-color:#d29922;background:rgba(210,153,34,.08);}}
.markdown-alert-tip{{border-left-color:#3fb950;background:rgba(63,185,80,.08);}}
.markdown-alert-important{{border-left-color:#8957e5;background:rgba(137,87,229,.08);}}
.markdown-alert-caution{{border-left-color:#f85149;background:rgba(248,81,73,.08);}}
details{{background:{T['hover']};border:1px solid {T['border']};border-radius:6px;padding:8px 16px;margin-bottom:12px;}}
summary{{cursor:pointer;color:{T['accent']};font-weight:600;}}
@keyframes skeleton {{ 0%,100% {{opacity:.4}} 50% {{opacity:1}} }}
.skeleton-wrapper{{display:flex;flex-direction:column;gap:15px;width:100%;animation:skeleton 1.5s ease infinite;margin-top:20px;}}
.skeleton-line{{height:16px;border-radius:4px;background:#2a2a2a;}}
.skeleton-line.title-line{{height:24px;margin-bottom:10px;}}
.w-100{{width:100%}}.w-80{{width:80%}}.w-60{{width:60%}}.w-40{{width:40%}}
::-webkit-scrollbar{{width:8px;}}
::-webkit-scrollbar-track{{background:{T['bg']};}}
::-webkit-scrollbar-thumb{{background:{T['border']};border-radius:10px;}}
</style>"""

# ── Syntax Highlighter ─────────────────────────────────────────────────────
class MDHighlighter(QSyntaxHighlighter):
    def __init__(self, doc):
        super().__init__(doc)
        def f(color, bold=False, italic=False):
            fmt = QTextCharFormat(); fmt.setForeground(QColor(color))
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
        super().__init__(editor); self.editor = editor
    def sizeHint(self): return QSize(self.editor._lnw(), 0)
    def paintEvent(self, e): self.editor._paint_ln(e)

# ── README Score ───────────────────────────────────────────────────────────
def readme_score(text):
    s = 0; tips = []
    if re.search(r"^# ", text, re.M): s += 20
    else: tips.append(" Missing H1 title")
    if len(text) > 150: s += 15
    else: tips.append(" Add more content")
    if re.search(r"##.*install", text, re.I): s += 15
    else: tips.append(" Missing installation section")
    if re.search(r"##.*(usage|example|quick)", text, re.I): s += 15
    else: tips.append(" Add usage examples")
    if re.search(r"shields\.io", text): s += 10
    else: tips.append(" Add badges")
    if "```" in text: s += 10
    else: tips.append(" Add code blocks")
    if re.search(r"##.*license", text, re.I): s += 10
    else: tips.append(" Missing license section")
    if re.search(r"##.*contribut", text, re.I): s += 5
    return s, tips


def get_skeleton_html():
    return """
<div id="skeleton-app" style="margin: 15px 10px;">
<table width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr><td style="background-color:#2A2A2A; border-radius:5px;" width="60%"><div style="font-size:24px;">&nbsp;</div></td><td width="40%"></td></tr>
    <tr><td colspan="2"><div style="font-size:12px;">&nbsp;</div></td></tr>
    <tr><td style="background-color:#2A2A2A; border-radius:5px;" colspan="2"><div style="font-size:16px;">&nbsp;</div></td></tr>
    <tr><td colspan="2"><div style="font-size:8px;">&nbsp;</div></td></tr>
    <tr><td style="background-color:#2A2A2A; border-radius:5px;" colspan="2"><div style="font-size:16px;">&nbsp;</div></td></tr>
    <tr><td colspan="2"><div style="font-size:8px;">&nbsp;</div></td></tr>
    <tr><td style="background-color:#2A2A2A; border-radius:5px;" width="85%"><div style="font-size:16px;">&nbsp;</div></td><td width="15%"></td></tr>
    <tr><td colspan="2"><div style="font-size:24px;">&nbsp;</div></td></tr>
    <tr><td style="background-color:#2A2A2A; border-radius:5px;" colspan="2"><div style="font-size:16px;">&nbsp;</div></td></tr>
    <tr><td colspan="2"><div style="font-size:8px;">&nbsp;</div></td></tr>
    <tr><td style="background-color:#2A2A2A; border-radius:5px;" colspan="2"><div style="font-size:16px;">&nbsp;</div></td></tr>
    <tr><td colspan="2"><div style="font-size:8px;">&nbsp;</div></td></tr>
    <tr><td style="background-color:#2A2A2A; border-radius:5px;" width="45%"><div style="font-size:16px;">&nbsp;</div></td><td width="55%"></td></tr>
</table>
</div>
"""

# ── Render Worker ──────────────────────────────────────────────────────────
class Worker(QObject):
    done = Signal(str)
    def __init__(self): super().__init__(); self._md = ""; self._dirty = False; self.last_html = ""
    def request(self, md): self._md = md; self._dirty = True
    def process(self):
        if not self._dirty: return
        self._dirty = False
        if not self._md.strip():
            html = get_skeleton_html()
        else:
            html = markdown2.markdown(self._md,
                extras=["fenced-code-blocks","tables","task_list","strike","code-friendly"])
            for k, v in [
                ("> [!NOTE]",      '<div class="markdown-alert markdown-alert-note"><b> Note</b><br>'),
                ("> [!WARNING]",   '<div class="markdown-alert markdown-alert-warning"><b> Warning</b><br>'),
                ("> [!TIP]",       '<div class="markdown-alert markdown-alert-tip"><b> Tip</b><br>'),
                ("> [!IMPORTANT]", '<div class="markdown-alert markdown-alert-important"><b> Important</b><br>'),
                ("> [!CAUTION]",   '<div class="markdown-alert markdown-alert-caution"><b> Caution</b><br>'),
            ]: html = html.replace(k, v)
        self.last_html = html; self.done.emit(html)

# ── Smart Editor ───────────────────────────────────────────────────────────
class SnippetAddDialog(QDialog):
    def __init__(self, parent, text):
        super().__init__(parent); self.text = text
        self.setWindowTitle("Save Snippet"); self.setFixedSize(380, 420)
        self.setStyleSheet(f"QDialog{{background:{T['panel']};color:{T['text']};}}")
        lay = QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(15)
        lay.addWidget(QLabel("Snippet Name:"))
        self.name = QLineEdit(); self.name.setPlaceholderText("e.g., table-header")
        self.name.setStyleSheet(f"background:{T['bg']};color:{T['editor']};border:1px solid {T['border']};border-radius:6px;padding:8px;")
        lay.addWidget(self.name)
        lay.addWidget(QLabel("Text Preview:"))
        self.preview = QTextEdit(); self.preview.setReadOnly(True); self.preview.setPlainText(text)
        self.preview.setStyleSheet(f"background:{T['input']};color:{T['dim']};border:none;border-radius:6px;font-family:monospace;font-size:11px;")
        lay.addWidget(self.preview)
        btns = QHBoxLayout(); lay.addLayout(btns); btns.addStretch()
        cancel = QPushButton("Cancel"); cancel.clicked.connect(self.reject)
        cancel.setStyleSheet(f"background:transparent;color:{T['dim']};padding:8px 20px;border:1px solid {T['border']};border-radius:6px;")
        btns.addWidget(cancel)
        save = QPushButton("Save"); save.clicked.connect(self.accept)
        save.setStyleSheet(f"background:{T['accent']};color:#fff;padding:8px 24px;border:none;border-radius:6px;font-weight:600;")
        btns.addWidget(save)

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
        
        self.ai_btn = QToolButton(self)
        self.ai_btn.setText("AI")
        self.ai_btn.setCursor(Qt.PointingHandCursor)
        self.ai_btn.setStyleSheet(f"QToolButton{{background:{T['accent']};color:#fff;border-radius:6px;font-weight:bold;font-size:11px;padding:4px 8px;border:none;}}" "QToolButton::menu-indicator{image:none;}")
        self.ai_btn.setPopupMode(QToolButton.InstantPopup)
        self.ai_btn.hide()
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE())
        for txt in ["Fix Markdown", "Translate to English", "Translate to Arabic", "Improve Structure", "Complete README"]:
            a = menu.addAction(txt)
            a.triggered.connect(lambda _, t=txt: self._trigger_ai(t))
        menu.addSeparator()
        a2 = menu.addAction(" Custom Input...")
        a2.triggered.connect(lambda: self._trigger_ai(""))
        self.ai_btn.setMenu(menu)
        
        QTimer.singleShot(50, self._update_lnw)

    def _trigger_ai(self, prompt):
        if not self.app or not hasattr(self.app, 'ai_panel'): return
        
        sel_text = self.textCursor().selectedText()
        sel_text = sel_text.replace("\u2029", "\n")
        
        if not self.app.ai_panel.isVisible(): self.app._toggle_ai()
        if prompt:
            if sel_text:
                full = f"{prompt}:\n\n```markdown\n{sel_text}\n```"
            else:
                full = prompt
            self.app.ai_panel.inp.setPlainText(full)
            QTimer.singleShot(100, self.app.ai_panel._send)
        else:
            if sel_text:
                self.app.ai_panel.inp.setPlainText(f"Regarding this text:\n```markdown\n{sel_text}\n```\n\n>> ")
                cursor = self.app.ai_panel.inp.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.app.ai_panel.inp.setTextCursor(cursor)
            self.app.ai_panel.inp.setFocus()

    def _lnw(self):
        return 20 + self.fontMetrics().horizontalAdvance("9") * max(len(str(self.document().blockCount())), 3)

    def _update_lnw(self):
        self.setViewportMargins(self._lnw(), 0, 0, 0)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        cr = self.contentsRect()
        self._ln.setGeometry(QRect(cr.left(), cr.top(), self._lnw(), cr.height()))
        self.ai_btn.setGeometry(cr.right() - 55, cr.top() + 15, 45, 24)

    def _highlight_line(self):
        sel = QTextEdit.ExtraSelection()
        sel.format.setBackground(QColor(T["hover"]))
        sel.format.setProperty(QTextCharFormat.FullWidthSelection, True)
        sel.cursor = self.textCursor(); sel.cursor.clearSelection()
        self.setExtraSelections([sel])

    def _paint_ln(self, event):
        p = QPainter(self._ln)
        p.fillRect(event.rect(), QColor(T["input"]))
        block = self.document().begin(); bn = 0
        cur_bn = self.textCursor().blockNumber()
        while block.isValid():
            y = int(self.document().documentLayout().blockBoundingRect(block).top()) \
                - self.verticalScrollBar().value() + self.contentsMargins().top()
            if y > event.rect().bottom(): break
            if y + self.fontMetrics().height() >= event.rect().top():
                p.setPen(QColor(T["accent"] if bn == cur_bn else T["border"]))
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
        cur.movePosition(QTextCursor.End if not cur.hasSelection() else QTextCursor.StartOfLine)
        self.setTextCursor(cur)
        self.insertPlainText(("\n" if self.toPlainText() else "") + text)

    def contextMenuEvent(self, e):
        ms = MENU_STYLE()
        m = QMenu(self); m.setStyleSheet(ms)

        # ── Undo / Redo ──
        for lbl, fn in [(" Undo", self.undo), (" Redo", self.redo)]:
            m.addAction(lbl).triggered.connect(fn)
        m.addSeparator()

        # ── Clipboard ──
        for lbl, fn in [(" Cut", self.cut), (" Copy", self.copy), (" Paste", self.paste), (" Select All", self.selectAll)]:
            m.addAction(lbl).triggered.connect(fn)
        m.addSeparator()

        # ── Headers ──
        hdr = QMenu("# Headers", m); hdr.setStyleSheet(ms)
        for i in range(1, 7):
            hdr.addAction(f"{'#'*i}  H{i}").triggered.connect(lambda _, n=i: self.insert_block(f"{'#'*n} Heading {n}"))
        m.addMenu(hdr)

        # ── Formatting ──
        fmt = QMenu("** Formatting", m); fmt.setStyleSheet(ms)
        for lbl, pre, suf in [
            ("**Bold**",         "**",  "**"),
            ("_Italic_",         "*",   "*"),
            ("~~Strikethrough~~","~~",  "~~"),
            ("`Inline Code`",    "`",   "`"),
            ("==Highlight==",    "<mark>", "</mark>"),
            ("^Superscript^",    "<sup>", "</sup>"),
            ("~Subscript~",      "<sub>", "</sub>"),
        ]:
            fmt.addAction(lbl).triggered.connect(lambda _, p=pre, s=suf: self.insert_md(p, s))
        m.addMenu(fmt)

        # ── Code ──
        code = QMenu("Code Blocks", m); code.setStyleSheet(ms)
        for lbl, txt in [
            ("Code Block",          "```\n\n```"),
            ("Bash Block",          "```bash\n\n```"),
            ("Python Block",        "```python\n\n```"),
            ("JavaScript Block",    "```javascript\n\n```"),
            ("JSON Block",          "```json\n\n```"),
            ("YAML Block",          "```yaml\n\n```"),
            ("Diff Block",          "```diff\n+ added\n- removed\n```"),
        ]:
            code.addAction(lbl).triggered.connect(lambda _, t=txt: self.insert_block(t))
        m.addMenu(code)

        # ── Lists ──
        lst = QMenu("• Lists", m); lst.setStyleSheet(ms)
        for lbl, txt in [
            ("Unordered List",  "- Item 1\n- Item 2\n- Item 3"),
            ("Ordered List",    "1. Item 1\n2. Item 2\n3. Item 3"),
            ("Task List",       "- [x] Done\n- [ ] Todo\n- [ ] Future"),
            ("Nested List",     "- Parent\n  - Child\n  - Child\n- Parent"),
        ]:
            lst.addAction(lbl).triggered.connect(lambda _, t=txt: self.insert_block(t))
        m.addMenu(lst)

        # ── Tables ──
        tbl = QMenu(" Tables", m); tbl.setStyleSheet(ms)
        for lbl, txt in [
            ("2 Columns",
             "| Column 1 | Column 2 |\n|----------|----------|\n| Cell     | Cell     |"),
            ("3 Columns",
             "| Column 1 | Column 2 | Column 3 |\n|----------|----------|----------|\n| Cell     | Cell     | Cell     |"),
            ("4 Columns",
             "| Col 1 | Col 2 | Col 3 | Col 4 |\n|-------|-------|-------|-------|\n| Cell  | Cell  | Cell  | Cell  |"),
            ("Aligned Table",
             "| Left | Center | Right |\n|:-----|:------:|------:|\n| L    |   C    |     R |"),
            ("API Endpoints",
             "| Method | Endpoint | Description |\n|--------|----------|-------------|\n| `GET`  | `/items` | List all    |\n| `POST` | `/items` | Create new  |"),
        ]:
            tbl.addAction(lbl).triggered.connect(lambda _, t=txt: self.insert_block(t))
        m.addMenu(tbl)

        # ── Links & Images ──
        lnk = QMenu(" Links & Images", m); lnk.setStyleSheet(ms)
        for lbl, txt in [
            ("Link",                "[link text](https://example.com)"),
            ("Link with Title",     "[link text](https://example.com \"Title\")"),
            ("Image",               "![alt text](image.png)"),
            ("Image with Link",     "[![alt](image.png)](https://example.com)"),
            ("Reference Link",      "[text][ref]\n\n[ref]: https://example.com"),
            ("Footnote",            "Text[^1]\n\n[^1]: Footnote content."),
        ]:
            lnk.addAction(lbl).triggered.connect(lambda _, t=txt: self.insert_block(t))
        m.addMenu(lnk)

        # ── Badges ──
        bdg = QMenu(" Badges", m); bdg.setStyleSheet(ms)
        for lbl, txt in [
            ("License MIT",     "[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)"),
            ("License Apache",  "[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)"),
            ("Version (PyPI)",  "[![PyPI version](https://badge.fury.io/py/PACKAGE.svg)](https://badge.fury.io/py/PACKAGE)"),
            ("npm version",     "[![npm version](https://badge.fury.io/js/PACKAGE.svg)](https://badge.fury.io/js/PACKAGE)"),
            ("Build Passing",   "[![Build Status](https://img.shields.io/github/actions/workflow/status/USER/REPO/main.yml)](https://github.com/USER/REPO/actions)"),
            ("Coverage",        "[![Coverage](https://img.shields.io/codecov/c/github/USER/REPO)](https://codecov.io/gh/USER/REPO)"),
            ("Stars",           "[![GitHub Stars](https://img.shields.io/github/stars/USER/REPO?style=social)](https://github.com/USER/REPO)"),
            ("Forks",           "[![GitHub Forks](https://img.shields.io/github/forks/USER/REPO?style=social)](https://github.com/USER/REPO)"),
            ("Issues",          "[![GitHub Issues](https://img.shields.io/github/issues/USER/REPO)](https://github.com/USER/REPO/issues)"),
            ("Python 3.x",      "[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)"),
            ("Node.js",         "[![Node.js](https://img.shields.io/badge/node.js-v18+-green.svg)](https://nodejs.org/)"),
            ("Docker Ready",    "[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker)](https://hub.docker.com/)"),
            ("PRs Welcome",     "[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)"),
            ("Maintained",      "[![Maintained](https://img.shields.io/badge/Maintained-yes-green.svg)](https://github.com/USER/REPO)"),
            ("Downloads",       "[![Downloads](https://img.shields.io/pypi/dm/PACKAGE)](https://pypi.org/project/PACKAGE)"),
        ]:
            bdg.addAction(lbl).triggered.connect(lambda _, t=txt: self.insert_block(t))
        m.addMenu(bdg)

        # ── Alerts ──
        alrt = QMenu(" Alerts", m); alrt.setStyleSheet(ms)
        for lbl, txt in [
            (" Note",      "> [!NOTE]\n> Add your note here."),
            (" Warning",   "> [!WARNING]\n> Add your warning here."),
            (" Tip",       "> [!TIP]\n> Add your tip here."),
            (" Important", "> [!IMPORTANT]\n> Add important info here."),
            (" Caution",   "> [!CAUTION]\n> Add caution here."),
            ("Blockquote",   "> Quoted text here."),
        ]:
            alrt.addAction(lbl).triggered.connect(lambda _, t=txt: self.insert_block(t))
        m.addMenu(alrt)

        # ── GitHub Special ──
        gh = QMenu(" GitHub Special", m); gh.setStyleSheet(ms)
        for lbl, txt in [
            ("Collapsible Section",
             "<details>\n<summary>Click to expand</summary>\n\nContent here.\n\n</details>"),
            ("Collapsible Code",
             "<details>\n<summary>Show code</summary>\n\n```python\n# code here\n```\n\n</details>"),
            ("Horizontal Rule",  "\n---\n"),
            ("Math Block",       "$$\nE = mc^2\n$$"),
            ("Inline Math",      "$x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}$"),
            ("Mermaid Diagram",  "```mermaid\ngraph TD\n    A[Start] --> B{Decision}\n    B -->|Yes| C[Result]\n    B -->|No| D[End]\n```"),
            ("Mermaid Sequence", "```mermaid\nsequenceDiagram\n    User->>Server: Request\n    Server-->>User: Response\n```"),
            ("Keyboard Key",     "<kbd>Ctrl</kbd> + <kbd>C</kbd>"),
            ("Center Image",     '<p align="center">\n  <img src="image.png" width="600" alt="alt text">\n</p>'),
            ("Emoji Row",        "         "),
            ("HTML Comment",     "<!-- comment here -->"),
        ]:
            gh.addAction(lbl).triggered.connect(lambda _, t=txt: self.insert_block(t))
        m.addMenu(gh)

        # ── Common Sections ──
        sec = QMenu(" Sections", m); sec.setStyleSheet(ms)
        for lbl, txt in [
            ("Installation",     "##  Installation\n```bash\ngit clone https://github.com/user/repo.git\ncd repo\npip install -r requirements.txt\n```"),
            ("Usage",            "##  Usage\n```python\nimport module\nmodule.run()\n```"),
            ("Features",         "##  Features\n-  Fast and efficient\n-  Easy to use\n-  Highly configurable"),
            ("Requirements",     "##  Requirements\n- Python 3.8+\n- Node.js 18+"),
            ("Configuration",    "##  Configuration\n```yaml\nsetting: value\ndebug: false\n```"),
            ("Contributing",     "##  Contributing\n1. Fork the repo\n2. Create branch `git checkout -b feature/name`\n3. Commit `git commit -m 'Add feature'`\n4. Push `git push origin feature/name`\n5. Open a Pull Request"),
            ("License",          "##  License\nThis project is licensed under the [MIT License](LICENSE)."),
            ("Roadmap",          "##  Roadmap\n- [x] Initial release\n- [x] Core features\n- [ ] Version 2.0\n- [ ] Plugin system"),
            ("Acknowledgements", "##  Acknowledgements\n- [Project Name](https://example.com)\n- [Library](https://example.com)"),
            ("FAQ",              "##  FAQ\n\n**Q: How do I?**\nA: You can...\n\n**Q: Why does?**\nA: Because..."),
            ("Changelog",        "##  Changelog\n\n### [1.0.0] - 2024-01-01\n- Initial release\n\n### [0.9.0] - 2023-12-01\n- Beta version"),
            ("Support",          "##  Support\nFor support, email user@example.com or [open an issue](https://github.com/user/repo/issues)."),
        ]:
            sec.addAction(lbl).triggered.connect(lambda _, t=txt: self.insert_block(t))
        m.addMenu(sec)

        m.addSeparator()

        # ── User Snippets Submenu ──
        if self.app and hasattr(self.app, "user_snippets") and self.app.user_snippets:
            snip_menu = QMenu(" My Snippets", m); snip_menu.setStyleSheet(ms)
            for title, content in self.app.user_snippets.items():
                snip_menu.addAction(title).triggered.connect(lambda _, c=content: self.insertPlainText(c))
            m.addMenu(snip_menu)

        m.exec(e.globalPos())

class FindBar(QFrame):
    def __init__(self, editor, parent=None):
        super().__init__(parent); self.editor = editor; self.setFixedHeight(46)
        self.setStyleSheet(
            f"QFrame{{background:{T['panel']};border-top:1px solid {T['border']};}}"
            f"QLineEdit{{background:{T['input']};color:{T['editor']};border:1px solid {T['border']};"
            f"border-radius:5px;padding:5px 9px;font-size:12px;}}"
            f"QLineEdit:focus{{border-color:{T['accent']};}}"
            f"QPushButton{{background:{T['hover']};color:{T['text']};border:1px solid {T['border']};"
            f"border-radius:5px;padding:5px 10px;font-size:11px;font-weight:600;}}"
            f"QPushButton:hover{{border-color:{T['accent']};}}"
            f"QCheckBox,QLabel{{color:{T['dim']};font-size:11px;background:transparent;}}"
        )
        lay = QHBoxLayout(self); lay.setContentsMargins(10,5,10,5); lay.setSpacing(7)
        lay.addWidget(QLabel(""))
        self.find = QLineEdit(); self.find.setPlaceholderText("Find…"); self.find.setFixedWidth(170)
        self.find.textChanged.connect(self._hl); lay.addWidget(self.find)
        self.repl = QLineEdit(); self.repl.setPlaceholderText("Replace…"); self.repl.setFixedWidth(170)
        lay.addWidget(self.repl)
        self.case = QCheckBox("Aa"); lay.addWidget(self.case)
        self.lbl = QLabel(""); self.lbl.setTextFormat(Qt.RichText); lay.addWidget(self.lbl)
        for lbl, fn in [("▲",self._prev),("▼",self._next),("Replace",self._repl1),("All",self._replAll)]:
            b = QPushButton(lbl); b.clicked.connect(fn); lay.addWidget(b)
        lay.addStretch()
        x = QPushButton(""); x.setFixedWidth(26)
        x.setStyleSheet("background:transparent;color:#555;border:none;font-size:13px;")
        x.clicked.connect(self._close); lay.addWidget(x)
        self.find.returnPressed.connect(self._next)

    def _close(self): self.hide(); self.editor and self.editor.setExtraSelections([]); self.editor and self.editor.setFocus()
    def set_editor(self, editor):
        if self.editor:
            try: self.editor.textChanged.disconnect(self._hl)
            except: pass
        self.editor = editor
        if self.editor:
            self.editor.textChanged.connect(self._hl); self._hl()

    def _flags(self):
        f = QTextDocument.FindFlag(0)
        if self.case.isChecked(): f |= QTextDocument.FindCaseSensitively
        return f

    def _hl(self):
        if not self.editor: return
        t = self.find.text()
        if not t: self.editor.setExtraSelections([]); self.lbl.setText(""); return
        extra = []; fmt = QTextCharFormat()
        fmt.setBackground(QColor("#2A2800")); fmt.setForeground(QColor("#FBBF24"))
        doc = self.editor.document(); ct = 0; fl = self._flags()
        c = doc.find(t, 0, fl)
        while not c.isNull():
            s = QTextEdit.ExtraSelection(); s.cursor = c; s.format = fmt
            extra.append(s); ct += 1; c = doc.find(t, c, fl)
        self.editor.setExtraSelections(extra)
        col = "#4ADE80" if ct else "#F87171"
        self.lbl.setText(f'<span style="color:{col}">{ct}</span>')

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

class StatsBar(QFrame):
    def __init__(self, editor, parent=None):
        super().__init__(parent); self.editor = editor; self.setFixedHeight(24)
        self.setStyleSheet(
            f"QFrame{{background:{T['panel']};border-top:1px solid {T['border']};}}"
            f"QLabel{{font-size:10px;font-family:Consolas,monospace;padding:0 4px;"
            f"background:transparent;color:{T['dim']};}}"
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
        col = c or T["dim"]
        return (f'<span style="color:{T["border"]}">{k}:</span>'
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
            f'<span style="color:{T["border"]}">Ln {cur.blockNumber()+1} Col {cur.columnNumber()+1}</span>')

# ── Templates ──────────────────────────────────────────────────────────────
TEMPLATES = {
    "Python Lib":
        "#  {name}\n\n[![PyPI](https://img.shields.io/pypi/v/{slug}?style=flat-square)](https://pypi.org/project/{slug})\n"
        "[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](#)\n"
        "[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg?style=flat-square)](#)\n\n"
        ">  Short description of what this library does.\n\n"
        "##  Features\n-  Fast and lightweight\n-  Easy to configure\n-  Well documented\n\n"
        "##  Install\n```bash\npip install {slug}\n```\n\n"
        "##  Quick Start\n```python\nimport {slug}\n\n# Example usage\nresult = {slug}.run()\nprint(result)\n```\n\n"
        "##  Documentation\nFull docs at [docs.example.com](#)\n\n"
        "##  Contributing\n1. Fork → Branch → Commit → Push → PR\n\n"
        "##  License\nMIT © [Author](#)\n",

    "Web App":
        "#  {name}\n\n[![Demo](https://img.shields.io/badge/Live-Demo-blue?style=flat-square)](#)\n"
        "[![Build](https://img.shields.io/github/actions/workflow/status/user/{slug}/main.yml?style=flat-square)](#)\n\n"
        "> A modern web application built with [Framework].\n\n"
        "##  Features\n-  Beautiful UI\n-  Fast performance\n-  Fully responsive\n-  Secure\n\n"
        "##  Getting Started\n```bash\ngit clone https://github.com/user/{slug}.git\ncd {slug}\nnpm install\nnpm run dev\n```\n\n"
        "Open [http://localhost:3000](http://localhost:3000) in your browser.\n\n"
        "##  Environment Variables\n```env\nNEXT_PUBLIC_API_URL=https://api.example.com\nDATABASE_URL=postgresql://...\n```\n\n"
        "##  Build\n```bash\nnpm run build\nnpm start\n```\n\n"
        "##  License\nMIT\n",

    "CLI Tool":
        "#  {name}\n\n[![npm](https://img.shields.io/npm/v/{slug}?style=flat-square)](#)\n"
        "[![Downloads](https://img.shields.io/npm/dm/{slug}?style=flat-square)](#)\n\n"
        "> A powerful CLI tool for [purpose].\n\n"
        "##  Install\n```bash\nnpm install -g {slug}\n# or\nbrew install {slug}\n```\n\n"
        "##  Usage\n```bash\n{slug} [command] [options]\n\n# Examples\n{slug} init my-project\n{slug} build --watch\n{slug} deploy --env prod\n```\n\n"
        "##  Commands\n| Command | Description |\n|---------|-------------|\n"
        "| `init` | Initialize project |\n| `build` | Build the project |\n| `deploy` | Deploy to server |\n\n"
        "##  Options\n```\n-v, --version    Show version\n-h, --help       Show help\n--verbose        Verbose output\n```\n\n"
        "##  License\nMIT\n",

    "REST API":
        "#  {name}\n\n[![API](https://img.shields.io/badge/API-REST-green?style=flat-square)](#)\n"
        "[![Swagger](https://img.shields.io/badge/docs-Swagger-85EA2D?style=flat-square&logo=swagger)](#)\n\n"
        "> RESTful API for [purpose].\n\n"
        "##  Base URL\n```\nhttps://api.example.com/v1\n```\n\n"
        "##  Authentication\n```http\nAuthorization: Bearer <token>\n```\n\n"
        "##  Endpoints\n| Method | Endpoint | Description |\n|--------|----------|-------------|\n"
        "| `GET` | `/items` | List all items |\n| `GET` | `/items/:id` | Get by ID |\n"
        "| `POST` | `/items` | Create new |\n| `PUT` | `/items/:id` | Update |\n| `DELETE` | `/items/:id` | Delete |\n\n"
        "##  Response Format\n```json\n{\"status\": \"ok\", \"data\": {}, \"message\": \"\"}\n```\n\n"
        "##  Rate Limits\n- 100 requests/minute per IP\n- 1000 requests/hour per API key\n\n"
        "##  License\nMIT\n",

    "ML Project":
        "#  {name}\n\n[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python)](#)\n"
        "[![PyTorch](https://img.shields.io/badge/PyTorch-2.0-EE4C2C?style=flat-square&logo=pytorch)](#)\n\n"
        "##  Abstract\n> Write your abstract here. Describe the problem, method, and key results.\n\n"
        "##  Results\n| Model | Accuracy | F1 | Params |\n|-------|----------|----|--------|\n"
        "| Ours | **95.2%** | **0.94** | 12M |\n| Baseline | 88.1% | 0.87 | 340M |\n\n"
        "##  Requirements\n```bash\npip install -r requirements.txt\n```\n\n"
        "##  Dataset\n```bash\n# Download dataset\npython scripts/download_data.py\n```\n\n"
        "##  Train\n```bash\npython train.py --config configs/default.yaml --epochs 100\n```\n\n"
        "##  Evaluate\n```bash\npython eval.py --checkpoint checkpoints/best.pt\n```\n\n"
        "##  Citation\n```bibtex\n@article{{name2024,\n  title={{{name}}},\n  year={{2024}}\n}}\n```\n",

    "Docker":
        "#  {name}\n\n[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker)](#)\n"
        "[![Image Size](https://img.shields.io/docker/image-size/user/{slug}?style=flat-square)](#)\n\n"
        "> Containerized [purpose].\n\n"
        "##  Quick Start\n```bash\ndocker pull user/{slug}\ndocker run -d -p 8080:8080 user/{slug}\n```\n\n"
        "##  Docker Compose\n```yaml\nversion: '3.8'\nservices:\n  app:\n    image: user/{slug}\n"
        "    ports:\n      - '8080:8080'\n    environment:\n      - NODE_ENV=production\n    volumes:\n      - ./data:/app/data\n```\n\n"
        "##  Build Locally\n```bash\ndocker build -t {slug} .\ndocker run -p 8080:8080 {slug}\n```\n\n"
        "##  License\nMIT\n",

    "React Component":
        "#  {name}\n\n[![npm](https://img.shields.io/npm/v/{slug}?style=flat-square)](#)\n"
        "[![Bundle Size](https://img.shields.io/bundlephobia/minzip/{slug}?style=flat-square)](#)\n\n"
        "> A reusable React component for [purpose].\n\n"
        "##  Install\n```bash\nnpm install {slug}\n# or\nyarn add {slug}\n```\n\n"
        "##  Usage\n```jsx\nimport {{ {name} }} from '{slug}';\n\nfunction App() {{\n"
        "  return (\n    <{name}\n      prop=\"value\"\n      onClick={{() => console.log('clicked')}}\n    />\n  );\n}}\n```\n\n"
        "##  Props\n| Prop | Type | Default | Description |\n|------|------|---------|-------------|\n"
        "| `prop` | `string` | `''` | Description |\n| `onClick` | `function` | `undefined` | Click handler |\n\n"
        "##  Styling\n```css\n.{slug} {{\n  /* custom styles */\n}}\n```\n\n##  License\nMIT\n",

    "GitHub Action":
        "#  {name}\n\n[![Action](https://img.shields.io/badge/GitHub-Action-2088FF?style=flat-square&logo=github-actions)](#)\n"
        "[![Marketplace](https://img.shields.io/badge/Marketplace-{slug}-blue?style=flat-square)](#)\n\n"
        "> A GitHub Action that [does what].\n\n"
        "##  Usage\n```yaml\n- name: {name}\n  uses: user/{slug}@v1\n  with:\n    token: ${{{{ secrets.GITHUB_TOKEN }}}}\n    setting: value\n```\n\n"
        "##  Inputs\n| Input | Required | Default | Description |\n|-------|----------|---------|-------------|\n"
        "| `token` |  | — | GitHub token |\n| `setting` |  | `default` | Description |\n\n"
        "##  Outputs\n| Output | Description |\n|--------|-------------|\n| `result` | Action result |\n\n"
        "##  License\nMIT\n",

    "Mobile App":
        "#  {name}\n\n[![iOS](https://img.shields.io/badge/iOS-14+-black?style=flat-square&logo=apple)](#)\n"
        "[![Android](https://img.shields.io/badge/Android-8+-green?style=flat-square&logo=android)](#)\n\n"
        "> A cross-platform mobile app for [purpose].\n\n"
        "##  Screenshots\n<p align=\"center\">\n  <img src=\"screenshots/home.png\" width=\"250\">\n"
        "  <img src=\"screenshots/detail.png\" width=\"250\">\n</p>\n\n"
        "##  Features\n-  Works on iOS & Android\n-  Push notifications\n-  Dark mode\n-  Localization\n\n"
        "##  Getting Started\n```bash\nnpm install\nnpx expo start\n```\n\n"
        "##  Download\n[![App Store](https://img.shields.io/badge/App_Store-Download-black?style=for-the-badge&logo=apple)](#)\n"
        "[![Google Play](https://img.shields.io/badge/Google_Play-Download-green?style=for-the-badge&logo=google-play)](#)\n\n"
        "##  License\nMIT\n",

    "Open Source":
        "#  {name}\n\n[![Stars](https://img.shields.io/github/stars/user/{slug}?style=social)](#)\n"
        "[![Forks](https://img.shields.io/github/forks/user/{slug}?style=social)](#)\n"
        "[![Contributors](https://img.shields.io/github/contributors/user/{slug}?style=flat-square)](#)\n"
        "[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](#)\n\n"
        "> {name} is an open-source [type] that [purpose].\n\n"
        "##  Demo\n![Demo](demo.gif)\n\n"
        "##  Features\n-  Feature one\n-  Feature two\n-  Feature three\n\n"
        "##  Installation\n```bash\ngit clone https://github.com/user/{slug}.git\ncd {slug}\npip install -e .\n```\n\n"
        "##  Documentation\n- [Quick Start](#)\n- [API Reference](#)\n- [Examples](#)\n\n"
        "##  Contributing\nWe welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md).\n\n"
        "##  Contributors\n[![Contributors](https://contrib.rocks/image?repo=user/{slug})](#)\n\n"
        "##  License\nMIT © [Author](#) — see [LICENSE](LICENSE)\n",

    "VS Code Extension":
        "#  {name}\n\n[![VS Marketplace](https://img.shields.io/visual-studio-marketplace/v/{slug}?style=flat-square&logo=visual-studio-code)](#)\n"
        "[![Installs](https://img.shields.io/visual-studio-marketplace/i/{slug}?style=flat-square)](#)\n\n"
        "> A VS Code extension that [purpose].\n\n"
        "##  Features\n-  Syntax highlighting\n-  Code snippets\n-  IntelliSense support\n\n"
        "##  Install\n```\next install {slug}\n```\n\n"
        "##  Settings\n| Setting | Default | Description |\n|---------|---------|-------------|\n"
        "| `{slug}.enable` | `true` | Enable the extension |\n\n"
        "##  License\nMIT\n",

    "Flutter App":
        "#  {name}\n\n[![Flutter](https://img.shields.io/badge/Flutter-3.x-02569B?style=flat-square&logo=flutter)](#)\n"
        "[![Dart](https://img.shields.io/badge/Dart-3.x-0175C2?style=flat-square&logo=dart)](#)\n\n"
        "> A beautiful Flutter application for [purpose].\n\n"
        "##  Screenshots\n<p align=\"center\">\n  <img src=\"screenshots/1.png\" width=\"250\">\n  <img src=\"screenshots/2.png\" width=\"250\">\n</p>\n\n"
        "##  Getting Started\n```bash\nflutter pub get\nflutter run\n```\n\n"
        "##  Architecture\n- `lib/models/` — Data models\n- `lib/screens/` — UI screens\n- `lib/widgets/` — Reusable widgets\n- `lib/services/` — API & business logic\n\n"
        "##  License\nMIT\n",

    "Monorepo":
        "#  {name}\n\n[![Turborepo](https://img.shields.io/badge/Turborepo-Monorepo-EF4444?style=flat-square)](#)\n"
        "[![pnpm](https://img.shields.io/badge/pnpm-workspace-F69220?style=flat-square&logo=pnpm)](#)\n\n"
        "> Monorepo for [project].\n\n"
        "##  Packages\n| Package | Description |\n|---------|-------------|\n"
        "| `packages/core` | Shared logic |\n| `packages/ui` | Component library |\n| `apps/web` | Web application |\n| `apps/api` | Backend API |\n\n"
        "##  Setup\n```bash\npnpm install\npnpm dev\n```\n\n"
        "##  Scripts\n| Command | Description |\n|---------|-------------|\n"
        "| `pnpm dev` | Start all apps |\n| `pnpm build` | Build all packages |\n| `pnpm test` | Run tests |\n| `pnpm lint` | Lint all |\n\n"
        "##  License\nMIT\n",

    "Chrome Extension":
        "#  {name}\n\n[![Chrome](https://img.shields.io/badge/Chrome-Extension-4285F4?style=flat-square&logo=googlechrome)](#)\n"
        "[![Version](https://img.shields.io/badge/version-1.0.0-blue?style=flat-square)](#)\n\n"
        "> A Chrome extension that [purpose].\n\n"
        "##  Features\n-  Lightweight & fast\n-  Privacy-first\n-  Customizable settings\n\n"
        "##  Install\n1. Clone this repo\n2. Open `chrome://extensions`\n3. Enable **Developer mode**\n4. Click **Load unpacked** → select the `dist/` folder\n\n"
        "##  Permissions\n| Permission | Reason |\n|------------|--------|\n"
        "| `activeTab` | Access current tab |\n| `storage` | Save settings |\n\n"
        "##  License\nMIT\n",

    "Game Project":
        "#  {name}\n\n[![Engine](https://img.shields.io/badge/Engine-Unity-000?style=flat-square&logo=unity)](#)\n"
        "[![Platform](https://img.shields.io/badge/Platform-PC%20%7C%20Mobile-green?style=flat-square)](#)\n\n"
        "> {name} is a [genre] game where [brief description].\n\n"
        "##  Screenshots\n<p align=\"center\">\n  <img src=\"screenshots/gameplay.png\" width=\"600\">\n</p>\n\n"
        "##  Features\n-  Immersive gameplay\n-  Original soundtrack\n-  Multiple levels\n-  Leaderboard system\n\n"
        "##  Play\n```bash\n# Download the latest release\nhttps://github.com/user/{slug}/releases\n```\n\n"
        "##  Controls\n| Key | Action |\n|-----|--------|\n"
        "| `WASD` | Move |\n| `Space` | Jump |\n| `E` | Interact |\n\n"
        "##  License\nMIT\n",

    "Minimal":
        "#  {name}\n\n> Short description.\n\n"
        "##  Install\n```bash\npip install {slug}\n```\n\n"
        "##  Usage\n```python\nimport {slug}\n{slug}.run()\n```\n\n"
        "##  License\nMIT\n",
}


SNIPPETS = {
    "Installation": "##  Installation\n```bash\ngit clone https://github.com/user/repo.git\npip install -r requirements.txt\n```\n",
    "Contributing": "##  Contributing\n1. Fork → Branch → Commit → Push → PR\n",
    "License MIT":  "##  License\nMIT © [Author](https://github.com/author)\n",
    "Roadmap":      "##  Roadmap\n- [x] Initial release\n- [ ] Version 2.0\n- [ ] Mobile support\n",
    "Note Alert":   "> [!NOTE]\n> Add your note here.\n",
    "Warning Alert":"> [!WARNING]\n> Add your warning here.\n",
    "Tip Alert":    "> [!TIP]\n> Add your tip here.\n",
    "Screenshots":  "##  Screenshots\n| Preview |\n|---|\n| ![](screenshot.png) |\n",
    "GitHub Stats": "##  Stats\n![Stats](https://github-readme-stats.vercel.app/api?username=USER&show_icons=true&theme=dark)\n",
    "Badges Row":   "[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#) [![Stars](https://img.shields.io/github/stars/USER/REPO?style=social)](#)\n",
}

# ── Template Picker ────────────────────────────────────────────────────────
class TemplatePicker(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.result_text = ""
        self.setWindowTitle("Templates"); self.setFixedSize(900, 560)
        self.setStyleSheet(
            f"QDialog{{background:{T['panel']};color:{T['text']};}}"
            f"QLineEdit{{background:{T['input']};color:{T['editor']};border:1px solid {T['border']};"
            f"border-radius:6px;padding:8px 12px;font-size:13px;}}"
            f"QLineEdit:focus{{border-color:{T['accent']};}}"
            f"QPushButton{{background:{T['hover']};color:{T['text']};border:1px solid {T['border']};"
            f"border-radius:7px;padding:8px 14px;font-size:12px;font-weight:600;}}"
            f"QPushButton:hover{{border-color:{T['accent']};}}"
            f"QPushButton#apply{{background:{T['accent']};border:none;color:#fff;}}"
            f"QPushButton#apply:hover{{background:{T['accent2']};}}"
            f"QLabel{{color:{T['text']};background:transparent;}}"
        )
        lay = QVBoxLayout(self); lay.setContentsMargins(18,14,18,14); lay.setSpacing(10)
        lay.addWidget(QLabel(" Quick Templates", styleSheet=f"font-size:16px;font-weight:600;"))
        row = QHBoxLayout()
        row.addWidget(QLabel("Project name:", styleSheet=f"color:{T['dim']};font-size:12px;min-width:90px;"))
        self.name = QLineEdit(); self.name.setPlaceholderText("My Awesome Project")
        self.name.textChanged.connect(self._update_preview)
        row.addWidget(self.name); lay.addLayout(row)

        body = QSplitter(Qt.Horizontal)
        # Left: template buttons
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
                f"QPushButton:checked{{background:{T['accent']};color:#fff;border-color:{T['accent']};}}"
            )
            b.clicked.connect(lambda _, k=k, b=b: self._pick(k, b))
            grid.addWidget(b, i//3, i%3); self._btns.append(b)
        sa.setWidget(inner)
        ll = QVBoxLayout(left); ll.setContentsMargins(0,0,0,0); ll.addWidget(sa)
        body.addWidget(left)

        # Right: preview
        self._preview = QTextBrowser()
        self._preview.setOpenExternalLinks(False)
        self._preview.setStyleSheet(f"QTextBrowser{{background:{T['bg']};color:{T['text']};border:1px solid {T['border']};border-radius:8px;padding:10px;}}")
        self._preview.document().setDefaultStyleSheet(preview_css())
        self._preview.setHtml(f"<p style='color:{T['dim']};text-align:center;margin-top:80px;'>Select a template to preview</p>")
        body.addWidget(self._preview)
        body.setSizes([380, 480])
        lay.addWidget(body, 1)

        row2 = QHBoxLayout()
        c = QPushButton("Cancel"); c.clicked.connect(self.reject); row2.addWidget(c)
        a = QPushButton("Apply"); a.setObjectName("apply"); a.clicked.connect(self._apply); row2.addWidget(a)
        lay.addLayout(row2)

    def _pick(self, k, btn):
        self._sel = k
        for b in self._btns: b.setChecked(False)
        btn.setChecked(True)
        self._update_preview()

    def _update_preview(self):
        if not self._sel: return
        name = self.name.text().strip() or "My Project"
        slug = re.sub(r"[^a-z0-9-]", "-", name.lower()).strip("-")
        md = TEMPLATES[self._sel].replace("{name}", name).replace("{slug}", slug)
        html = markdown2.markdown(md, extras=["fenced-code-blocks","tables","task_list","strike"])
        self._preview.setHtml(html)

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
        self.setStyleSheet(f"QDialog{{background:{T['panel']};}}")
        lay = QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(15)
        
        lbl_top = QLabel("Current Score"); lbl_top.setAlignment(Qt.AlignCenter)
        lbl_top.setStyleSheet(f"color:{T['dim']};font-size:14px;")
        lay.addWidget(lbl_top)
        
        lbl_score = QLabel(f"{score}/100"); lbl_score.setAlignment(Qt.AlignCenter)
        lbl_score.setStyleSheet("font-size:48px;color:#dd8448;font-weight:bold;margin:10px 0;")
        lay.addWidget(lbl_score)
        
        stars = max(1, min(5, (score // 20) + (1 if score % 20 else 0) if score > 0 else 1))
        if score > 80: stars = 5
        
        star_lay = QHBoxLayout(); star_lay.setAlignment(Qt.AlignCenter)
        for i in range(5):
            lbl = QLabel("" if i < stars else "")
            lbl.setStyleSheet("font-size:44px;color:#dd8448;" if i < stars else "font-size:44px;color:#333;")
            star_lay.addWidget(lbl)
        lay.addLayout(star_lay)
        
        if tips:
            tips_area = QScrollArea()
            tips_area.setWidgetResizable(True)
            tips_area.setStyleSheet(f"QScrollArea{{border:1px solid {T['border']};border-radius:10px;background:{T['bg']};}}")
            tips_container = QWidget(); tips_container.setStyleSheet("background:transparent;")
            tips_lay = QVBoxLayout(tips_container); tips_lay.setContentsMargins(15,15,15,15); tips_lay.setSpacing(8)
            tips_header = QLabel("Suggestions:"); tips_header.setStyleSheet(f"color:{T['text']};font-weight:bold;font-size:14px;")
            tips_lay.addWidget(tips_header)
            for t in tips:
                lbl = QLabel(f"• {t}"); lbl.setStyleSheet(f"color:{T['dim']};font-size:13px;")
                lbl.setWordWrap(True)
                tips_lay.addWidget(lbl)
            tips_lay.addStretch()
            tips_area.setWidget(tips_container)
            lay.addWidget(tips_area, 1)
        else:
            lay.addStretch()
            
        btn_lay = QHBoxLayout()
        auto_btn = QPushButton(" Auto-Perfect (AI)")
        auto_btn.setStyleSheet(f"background:{T['accent2']};color:#fff;border:none;border-radius:7px;padding:10px 24px;font-weight:600;")
        def do_auto():
            if not parent: return
            if not hasattr(parent, "ai_panel"): return
            if not parent.ai_panel.isVisible(): parent._toggle_ai()
            parent.ai_panel.inp.setPlainText("Update this README to achieve a 100% score based on standard README sections (Title, Description, Install, Usage, License, Badges).")
            self.accept()
            QTimer.singleShot(100, parent.ai_panel._send)
        auto_btn.clicked.connect(do_auto)
        btn_lay.addWidget(auto_btn)
        
        btn_lay.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(f"background:{T['accent']};color:#fff;border:none;border-radius:7px;padding:10px 24px;font-weight:600;")
        close_btn.clicked.connect(self.accept); btn_lay.addWidget(close_btn)
        lay.addLayout(btn_lay)


# ── Clickable Helper ───────────────────────────────────────────────────────
class ClickableFrame(QFrame):
    clicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self._checked = False
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._checked = not self._checked
            self.update_style()
            self.clicked.emit()
        super().mousePressEvent(event)
    def update_style(self):
        if self._checked:
            self.setStyleSheet(f"QFrame{{background:{T['input']};border:2px solid {T['accent']};border-radius:10px;}}")
        else:
            self.setStyleSheet(f"QFrame{{background:{T['hover']};border:1px solid {T['border']};border-radius:10px;}}"
                               f"QFrame:hover{{background:{T['bg']};border-color:{T['accent']};}}")

# ── Image Manager Dialog ───────────────────────────────────────────────────
class ImageDialog(QDialog):
    def __init__(self, editor, workspace, parent=None):
        super().__init__(parent)
        self.editor = editor; self.workspace = workspace
        self.setWindowTitle("Image Manager"); self.setMinimumSize(780, 540)
        self.setStyleSheet(
            f"QDialog{{background:{T['panel']};color:{T['text']};}}"
            f"QPushButton{{background:{T['hover']};color:{T['text']};border:1px solid {T['border']};"
            f"border-radius:7px;padding:7px 14px;font-size:12px;font-weight:600;}}"
            f"QPushButton:hover{{border-color:{T['accent']};}}"
            f"QPushButton#primary{{background:{T['accent']};border:none;color:#fff;}}"
            f"QPushButton#primary:hover{{background:{T['accent2']};}}"
        )
        lay = QVBoxLayout(self); lay.setContentsMargins(16,14,16,14); lay.setSpacing(10)

        # Top bar
        top = QHBoxLayout()
        title = QLabel("  Image Manager"); title.setStyleSheet("font-size:16px;font-weight:600;")
        top.addWidget(title); top.addStretch()

        # View toggle
        self._view_mode = "grid"
        for lbl, mode in [(" Grid","grid"),(" List","list"),("⊟ Table","table")]:
            b = QPushButton(lbl); b.setFixedHeight(30)
            b.clicked.connect(lambda checked=False, m=mode: self._set_view(m))
            top.addWidget(b)

        add_btn = QPushButton("+ Add Images"); add_btn.setObjectName("primary")
        add_btn.clicked.connect(self._add_images); top.addWidget(add_btn)
        lay.addLayout(top)

        # Main area: scroll for images
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"QScrollArea{{border:1px solid {T['border']};border-radius:8px;background:{T['bg']};}}")
        self.container = QWidget(); self.container.setStyleSheet(f"background:{T['bg']};")
        self.scroll.setWidget(self.container)
        lay.addWidget(self.scroll, 1)

        # Bottom
        bot = QHBoxLayout()
        self.info = QLabel("No images loaded"); self.info.setStyleSheet(f"color:{T['dim']};font-size:11px;")
        bot.addWidget(self.info); bot.addStretch()
        close = QPushButton("Cancel"); close.clicked.connect(self.reject); bot.addWidget(close)
        self.insert_btn = QPushButton("Insert Selected"); self.insert_btn.setObjectName("primary")
        self.insert_btn.clicked.connect(self._insert_selected); bot.addWidget(self.insert_btn)
        lay.addLayout(bot)

        self.images = []  # list of (abs_path, rel_path)
        self.selected_images = set() # set of rel_path
        self._scan_workspace()
        self._render()

    def _scan_workspace(self):
        exts = {".png",".jpg",".jpeg",".gif",".webp",".svg",".bmp"}
        ws = Path(self.workspace)
        for p in ws.rglob("*"):
            if p.suffix.lower() in exts:
                try:
                    rel = p.relative_to(ws)
                    rel_str = "/".join(rel.parts)  # Always use forward slashes
                    self.images.append((str(p), rel_str))
                except: pass

    def _add_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", self.workspace,
            "Images (*.png *.jpg *.jpeg *.gif *.webp *.svg *.bmp)"
        )
        for f in files:
            p = Path(f)
            try:
                rel = p.relative_to(Path(self.workspace))
                rel_str = "/".join(rel.parts)
            except:
                rel_str = p.name
            if (f, rel_str) not in self.images:
                self.images.append((f, rel_str))
        self._render()

    def _set_view(self, mode):
        self._view_mode = mode; self._render()

    def _toggle_select(self, rel_path):
        if rel_path in self.selected_images:
            self.selected_images.remove(rel_path)
        else:
            self.selected_images.add(rel_path)
        self.insert_btn.setText(f"Insert Selected ({len(self.selected_images)})")

    def _insert_selected(self):
        if not self.selected_images:
            QMessageBox.information(self, "No images selected", "Please select at least one image to insert.")
            return
        blocks = []
        for rel_path in self.selected_images:
            alt = Path(rel_path).stem
            blocks.append(f"![{alt}]({rel_path})")
        self.editor.insert_block("\n".join(blocks))
        self.accept()

    def _render(self):
        # Clear
        old = self.container.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                if item.widget(): item.widget().deleteLater()
            old.deleteLater()

        mode = self._view_mode

        if mode == "grid":
            grid = QGridLayout(self.container)
            grid.setContentsMargins(12,12,12,12); grid.setSpacing(10)
            cols = 4
            for i, (abs_p, rel_p) in enumerate(self.images):
                cell = ClickableFrame()
                cell.setFixedSize(160, 160)
                cell._checked = rel_p in self.selected_images
                cell.update_style()
                cell.clicked.connect(lambda r=rel_p: self._toggle_select(r))
                cl = QVBoxLayout(cell); cl.setContentsMargins(8,8,8,8); cl.setSpacing(6)
                img_lbl = QLabel(); img_lbl.setAlignment(Qt.AlignCenter); img_lbl.setFixedHeight(100)
                img_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
                pm = QPixmap(abs_p)
                if not pm.isNull():
                    img_lbl.setPixmap(pm.scaled(140, 95, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                else:
                    img_lbl.setText(""); img_lbl.setStyleSheet(f"font-size:36px;color:{T['dim']};")
                cl.addWidget(img_lbl)
                name = QLabel(Path(rel_p).name); name.setAlignment(Qt.AlignCenter)
                name.setStyleSheet(f"font-size:10px;font-weight:600;color:{T['text']};"); name.setWordWrap(True)
                name.setAttribute(Qt.WA_TransparentForMouseEvents)
                cl.addWidget(name)
                
                chk_lbl = QLabel(" Selected" if rel_p in self.selected_images else "Select")
                chk_lbl.setAlignment(Qt.AlignCenter)
                chk_lbl.setStyleSheet(f"color:{T['accent'] if rel_p in self.selected_images else T['dim']};font-size:10px;font-weight:700;")
                chk_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
                cl.addWidget(chk_lbl)
                
                # To update the label text when clicked:
                cell.clicked.connect(lambda c=chk_lbl, cell=cell: c.setText(" Selected" if cell._checked else "Select"))
                cell.clicked.connect(lambda c=chk_lbl, cell=cell: c.setStyleSheet(f"color:{T['accent'] if cell._checked else T['dim']};font-size:10px;font-weight:700;"))
                
                grid.addWidget(cell, i//cols, i%cols)
            if not self.images:
                lbl = QLabel("No images found.\nClick '+ Add Images' to load images."); lbl.setAlignment(Qt.AlignCenter)
                lbl.setStyleSheet(f"color:{T['dim']};font-size:13px;")
                grid.addWidget(lbl, 0, 0, 1, cols)

        elif mode == "list":
            vlay = QVBoxLayout(self.container); vlay.setContentsMargins(12,12,12,12); vlay.setSpacing(8)
            for abs_p, rel_p in self.images:
                row = ClickableFrame()
                row._checked = rel_p in self.selected_images
                row.update_style()
                row.clicked.connect(lambda r=rel_p: self._toggle_select(r))
                rl = QHBoxLayout(row); rl.setContentsMargins(12,8,12,8)
                thumb = QLabel(); pm = QPixmap(abs_p)
                thumb.setPixmap(pm.scaled(60,60,Qt.KeepAspectRatio,Qt.SmoothTransformation) if not pm.isNull() else QPixmap())
                thumb.setFixedSize(64,64); thumb.setAttribute(Qt.WA_TransparentForMouseEvents)
                rl.addWidget(thumb)
                info = QVBoxLayout()
                l1 = QLabel(Path(rel_p).name); l1.setStyleSheet(f"font-weight:700;font-size:13px;color:{T['text']};")
                l2 = QLabel(rel_p); l2.setStyleSheet(f"color:{T['dim']};font-size:11px;")
                l1.setAttribute(Qt.WA_TransparentForMouseEvents); l2.setAttribute(Qt.WA_TransparentForMouseEvents)
                info.addWidget(l1); info.addWidget(l2)
                size_str = f"{Path(abs_p).stat().st_size//1024} KB" if Path(abs_p).exists() else ""
                l3 = QLabel(size_str); l3.setStyleSheet(f"color:{T['dim']};font-size:11px;")
                l3.setAttribute(Qt.WA_TransparentForMouseEvents)
                info.addWidget(l3)
                rl.addLayout(info); rl.addStretch()
                
                chk = QCheckBox("Select")
                chk.setChecked(row._checked); chk.setAttribute(Qt.WA_TransparentForMouseEvents)
                row.clicked.connect(lambda c=chk, row=row: c.setChecked(row._checked))
                rl.addWidget(chk); vlay.addWidget(row)
            vlay.addStretch()

        elif mode == "table":
            vlay = QVBoxLayout(self.container); vlay.setContentsMargins(12,12,12,12); vlay.setSpacing(2)
            # Header
            hdr = QFrame(); hdr.setStyleSheet(f"background:{T['input']};border-radius:8px 8px 0 0;border:1px solid {T['border']};")
            hl = QHBoxLayout(hdr); hl.setContentsMargins(15,8,15,8)
            for txt, w in [("Preview",70),("File Path",1),("Size",80),("Action",90)]:
                l = QLabel(txt); l.setStyleSheet(f"font-size:11px;font-weight:700;color:{T['dim']};text-transform:uppercase;letter-spacing:1px;")
                if w != 1: l.setFixedWidth(w)
                hl.addWidget(l, 0 if w != 1 else 1)
            vlay.addWidget(hdr)
            for i, (abs_p, rel_p) in enumerate(self.images):
                row = ClickableFrame()
                row._checked = rel_p in self.selected_images
                row.update_style()
                row.clicked.connect(lambda r=rel_p: self._toggle_select(r))
                rl = QHBoxLayout(row); rl.setContentsMargins(15,6,15,6)
                thumb = QLabel(); pm = QPixmap(abs_p)
                thumb.setPixmap(pm.scaled(56,36,Qt.KeepAspectRatio,Qt.SmoothTransformation) if not pm.isNull() else QPixmap())
                thumb.setFixedWidth(70); thumb.setAttribute(Qt.WA_TransparentForMouseEvents)
                rl.addWidget(thumb)
                path_lbl = QLabel(rel_p); path_lbl.setStyleSheet(f"font-size:12px;color:{T['text']};")
                path_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
                rl.addWidget(path_lbl, 1)
                size_str = f"{Path(abs_p).stat().st_size//1024} KB" if Path(abs_p).exists() else "?"
                l_sz = QLabel(size_str); l_sz.setStyleSheet(f"font-size:12px;color:{T['dim']};")
                l_sz.setFixedWidth(80); l_sz.setAttribute(Qt.WA_TransparentForMouseEvents)
                rl.addWidget(l_sz, 0)
                
                chk = QCheckBox("Select"); chk.setFixedWidth(90)
                chk.setChecked(row._checked); chk.setAttribute(Qt.WA_TransparentForMouseEvents)
                row.clicked.connect(lambda c=chk, row=row: c.setChecked(row._checked))
                rl.addWidget(chk); vlay.addWidget(row)
            vlay.addStretch()

        self.info.setText(f"{len(self.images)} image(s) found")

# ── Translate Dialog ───────────────────────────────────────────────────────
class TranslateDialog(QDialog):
    def __init__(self, text, parent=None):
        super().__init__(parent); self.text = text; self.result = ""
        self.setWindowTitle("Translate README"); self.setMinimumSize(680, 500)
        self.setStyleSheet(
            f"QDialog{{background:{T['panel']};color:{T['text']};}}"
            f"QComboBox{{background:{T['input']};color:{T['editor']};border:1px solid {T['border']};border-radius:6px;padding:6px 10px;}}"
            f"QComboBox::drop-down{{border:none;width:20px;}}"
            f"QTextEdit{{background:{T['input']};color:{T['editor']};border:1px solid {T['border']};border-radius:6px;padding:8px;font-size:13px;}}"
            f"QPushButton{{background:{T['hover']};color:{T['text']};border:1px solid {T['border']};border-radius:7px;padding:8px 16px;font-size:12px;font-weight:600;}}"
            f"QPushButton:hover{{border-color:{T['accent']};}}"
        )
        lay = QVBoxLayout(self); lay.setContentsMargins(18,16,18,16); lay.setSpacing(12)
        lay.addWidget(QLabel(" Translate README", styleSheet="font-size:16px;font-weight:600;"))

        top = QHBoxLayout()
        top.addWidget(QLabel("Source:", styleSheet=f"color:{T['dim']};"))
        self.src_combo = QComboBox()
        for code, name in [("en","English"),("fr","French"),("es","Spanish"),("de","German"),("zh","Chinese"),("ja","Japanese"),("ar","Arabic"),("pt","Portuguese"),("ru","Russian"),("ko","Korean")]:
            self.src_combo.addItem(f"{name} ({code})", code)
        top.addWidget(self.src_combo)
        top.addWidget(QLabel("→  Target:", styleSheet=f"color:{T['dim']};"))
        self.tgt_combo = QComboBox()
        for code, name in [("fr","French"),("es","Spanish"),("de","German"),("zh","Chinese"),("ja","Japanese"),("ar","Arabic"),("pt","Portuguese"),("ru","Russian"),("ko","Korean"),("en","English"),("it","Italian")]:
            self.tgt_combo.addItem(f"{name} ({code})", code)
        top.addWidget(self.tgt_combo)
        translate_btn = QPushButton("Translate")
        translate_btn.setStyleSheet(f"background:{T['accent']};color:#fff;border:none;border-radius:7px;padding:8px 20px;font-weight:600;")
        translate_btn.clicked.connect(self._translate); top.addWidget(translate_btn)
        top.addStretch(); lay.addLayout(top)

        split = QHBoxLayout(); lay.addLayout(split, 1)
        for lbl, attr, txt in [("Source", "src_edit", text), ("Translation", "tgt_edit", "")]:
            col = QVBoxLayout(); col.addWidget(QLabel(lbl, styleSheet=f"font-size:11px;color:{T['dim']};font-weight:600;"))
            edit = QTextEdit(); edit.setPlainText(txt)
            if lbl == "Source": edit.setReadOnly(True)
            setattr(self, attr, edit); col.addWidget(edit); split.addLayout(col)

        self.status = QLabel(""); self.status.setStyleSheet(f"color:{T['dim']};font-size:11px;")
        lay.addWidget(self.status)

        bot = QHBoxLayout()
        bot.addWidget(self.status); bot.addStretch()
        cancel = QPushButton("Cancel"); cancel.clicked.connect(self.reject); bot.addWidget(cancel)
        apply = QPushButton("Apply Translation")
        apply.setStyleSheet(f"background:{T['accent']};color:#fff;border:none;border-radius:7px;padding:8px 16px;font-weight:600;")
        apply.clicked.connect(self._apply); bot.addWidget(apply)
        lay.addLayout(bot)

    def _translate(self):
        src = self.src_combo.currentData()
        tgt = self.tgt_combo.currentData()
        text = self.src_edit.toPlainText().strip()
        if not text: return
        self.status.setText("Translating…")
        QApplication.processEvents()
        # Split into chunks (MyMemory has 500 char limit per request)
        paragraphs = text.split("\n\n")
        translated = []
        for para in paragraphs:
            if not para.strip(): translated.append(""); continue
            # Skip code blocks
            if para.strip().startswith("```"):
                translated.append(para); continue
            try:
                q = urllib.parse.quote(para[:450])
                url = f"https://api.mymemory.translated.net/get?q={q}&langpair={src}|{tgt}"
                resp = urllib.request.urlopen(url, timeout=8)
                data = json.loads(resp.read().decode())
                if data.get("responseStatus") == 200:
                    translated.append(data["responseData"]["translatedText"])
                else:
                    translated.append(para)
            except Exception as ex:
                translated.append(para)
        result = "\n\n".join(translated)
        self.tgt_edit.setPlainText(result)
        self.status.setText(f" Translation complete ({src} → {tgt})")

    def _apply(self):
        self.result = self.tgt_edit.toPlainText()
        if self.result: self.accept()

# ── Repair Dialog ──────────────────────────────────────────────────────────
def repair_markdown(text):
    """Auto-fix common Markdown issues."""
    lines = text.split("\n")
    out = []
    issues = []
    prev_blank = False

    for i, line in enumerate(lines):
        # Fix: heading without space (e.g. #Title → # Title)
        m = re.match(r"^(#{1,6})([^ #\n])", line)
        if m:
            line = m.group(1) + " " + line[len(m.group(1)):]
            issues.append(f"Line {i+1}: Added space after heading marker")

        # Fix: double spaces → single
        if "  " in line and not line.strip().startswith("```") and not line.strip().startswith("|"):
            fixed = re.sub(r" {3,}", "  ", line)
            if fixed != line: line = fixed

        # Fix: Windows-style backslash paths in image/link syntax → forward slash
        if "![" in line or "](" in line:
            def fix_path(m):
                pre, path, post = m.group(1), m.group(2), m.group(3)
                if "\\" in path:
                    issues.append(f"Line {i+1}: Converted backslash to forward slash in path")
                return pre + path.replace("\\", "/") + post
            line = re.sub(r'(\!\[.*?\]\()([^)]+)(\))', fix_path, line)
            line = re.sub(r'(\[.*?\]\()([^)]+)(\))', fix_path, line)

        out.append(line)

    result = "\n".join(out)

    # Fix: missing blank line before/after headings
    result2 = []
    lines2 = result.split("\n")
    for i, line in enumerate(lines2):
        if re.match(r"^#{1,6} ", line):
            if i > 0 and lines2[i-1].strip():
                result2.append("")
                issues.append(f"Added blank line before heading")
            result2.append(line)
            if i < len(lines2)-1 and lines2[i+1].strip() and not re.match(r"^#{1,6} ", lines2[i+1]):
                result2.append("")
        else:
            result2.append(line)
    result = "\n".join(result2)

    # Remove excessive blank lines (3+ → 2)
    result = re.sub(r"\n{4,}", "\n\n\n", result)

    # Fix unclosed code blocks
    code_count = result.count("```")
    if code_count % 2 != 0:
        result += "\n```"
        issues.append("Closed unclosed code block")

    # Fix: ensure file ends with single newline
    result = result.rstrip("\n") + "\n"

    return result, issues

class RepairDialog(QDialog):
    def __init__(self, text, parent=None):
        super().__init__(parent); self.text = text; self.result = ""
        self.setWindowTitle("Repair Markdown"); self.setMinimumSize(680, 500)
        self.setStyleSheet(
            f"QDialog{{background:{T['panel']};color:{T['text']};}}"
            f"QTextEdit{{background:{T['input']};color:{T['editor']};border:1px solid {T['border']};border-radius:6px;padding:8px;font-size:12px;font-family:monospace;}}"
            f"QPushButton{{background:{T['hover']};color:{T['text']};border:1px solid {T['border']};border-radius:7px;padding:8px 16px;font-size:12px;font-weight:600;}}"
            f"QPushButton:hover{{border-color:{T['accent']};}}"
        )
        lay = QVBoxLayout(self); lay.setContentsMargins(18,16,18,16); lay.setSpacing(12)
        lay.addWidget(QLabel(" Repair Markdown", styleSheet="font-size:16px;font-weight:600;"))

        fixed, issues = repair_markdown(text)
        self._fixed = fixed

        if issues:
            issue_frame = QFrame()
            issue_frame.setStyleSheet(f"QFrame{{background:#1a2020;border:1px solid #2A4A2A;border-radius:8px;padding:4px;}}")
            ifl = QVBoxLayout(issue_frame); ifl.setContentsMargins(10,8,10,8); ifl.setSpacing(4)
            ifl.addWidget(QLabel(f" Fixed {len(issues)} issue(s):", styleSheet=f"color:#4ADE80;font-weight:600;font-size:12px;"))
            for iss in issues[:10]:
                ifl.addWidget(QLabel(f"  • {iss}", styleSheet=f"color:{T['dim']};font-size:11px;"))
            lay.addWidget(issue_frame)
        else:
            ok = QLabel(" No issues found — your Markdown looks clean!")
            ok.setStyleSheet(f"color:#4ADE80;font-size:13px;")
            lay.addWidget(ok)

        split = QHBoxLayout(); lay.addLayout(split, 1)
        for lbl, attr, t in [("Original", "orig", text), ("Repaired", "repaired", fixed)]:
            col = QVBoxLayout(); col.addWidget(QLabel(lbl, styleSheet=f"font-size:11px;color:{T['dim']};font-weight:600;"))
            edit = QTextEdit(); edit.setPlainText(t); edit.setReadOnly(True)
            setattr(self, attr, edit); col.addWidget(edit); split.addLayout(col)

        bot = QHBoxLayout(); bot.addStretch()
        cancel = QPushButton("Cancel"); cancel.clicked.connect(self.reject); bot.addWidget(cancel)
        apply = QPushButton("Apply Repairs")
        apply.setStyleSheet(f"background:{T['accent']};color:#fff;border:none;border-radius:7px;padding:8px 16px;font-weight:600;")
        apply.clicked.connect(self._apply); bot.addWidget(apply)
        lay.addLayout(bot)

    def _apply(self):
        self.result = self._fixed; self.accept()

# ── Self Install ───────────────────────────────────────────────────────────
def self_install():
    """If running as EXE from a temporary or unwanted path, copy to LocalAppData and create shortcut."""
    if not getattr(sys, 'frozen', False): return
    current_exe = sys.executable
    local_app = os.getenv('LOCALAPPDATA', '')
    if not local_app: return
    target_dir = os.path.join(local_app, 'Programs', 'READMEBuilder')
    target_exe = os.path.join(target_dir, 'READMEBuilder.exe')
    if os.path.normpath(current_exe) == os.path.normpath(target_exe): return
    try:
        os.makedirs(target_dir, exist_ok=True)
        if os.path.exists(target_exe):
            try: os.remove(target_exe)
            except: pass
        shutil.copy2(current_exe, target_exe)
        desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
        lnk_path = os.path.join(desktop, "README Builder.lnk")
        ps_cmd = (
            f'$s=(New-Object -ComObject WScript.Shell).CreateShortcut("{lnk_path}");'
            f'$s.TargetPath="{target_exe}";'
            f'$s.WorkingDirectory="{target_dir}";'
            f'$s.Description="README Builder Pro";'
            f'$s.Save()'
        )
        subprocess.run(["powershell", "-Command", ps_cmd], check=False, creationflags=0x08000000)
        os.startfile(target_exe); sys.exit()
    except: pass

# ── Context Menu Registration (winreg, no admin) ──────────────────────────
def auto_register_context_menu():
    if sys.platform != "win32": return
    import winreg
    if getattr(sys, 'frozen', False): exe_path = sys.executable
    else: exe_path = os.path.abspath(sys.argv[0])
    exe_str = f'"{exe_path}"'
    try:
        # Open With (any file)
        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\*\shell\Open with README Builder")
        winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, exe_path)
        winreg.SetValueEx(winreg.CreateKey(k, "command"), "", 0, winreg.REG_SZ, f'{exe_str} "%1"')
        winreg.CloseKey(k)
        # Right-click folder
        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\Directory\shell\Create README here")
        winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, exe_path)
        winreg.SetValueEx(winreg.CreateKey(k, "command"), "", 0, winreg.REG_SZ, f'{exe_str} "%1"')
        winreg.CloseKey(k)
        # Right-click folder background
        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\Directory\Background\shell\Create README here")
        winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, exe_path)
        winreg.SetValueEx(winreg.CreateKey(k, "command"), "", 0, winreg.REG_SZ, f'{exe_str} "%V"')
        winreg.CloseKey(k)
        # .md files
        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.md\shell\Open in README Builder")
        winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, exe_path)
        winreg.SetValueEx(winreg.CreateKey(k, "command"), "", 0, winreg.REG_SZ, f'{exe_str} "%1"')
        winreg.CloseKey(k)
    except: pass

# ── Minimap ────────────────────────────────────────────────────────────────
class Minimap(QWidget):
    def __init__(self, target, parent=None):
        super().__init__(parent)
        self.target = target; self.setFixedWidth(60)
        self.peer = None; self._sync_drag = False
        self.target.verticalScrollBar().valueChanged.connect(self.update)
        try: self.target.textChanged.connect(self.update)
        except: pass
        self.setCursor(Qt.PointingHandCursor); self.setMouseTracking(True)

    def paintEvent(self, e):
        p = QPainter(self); p.fillRect(self.rect(), QColor(T["panel"]))
        h = self.height(); eh = self.target.height()
        doc = self.target.document()
        if not doc: return
        th = doc.size().height()
        if th == 0 or eh == 0: return
        scale = h / max(th, eh); p.save(); p.scale(scale, scale)
        p.setPen(QColor("#444")); y = 0
        blk = doc.begin()
        while blk.isValid() and y < h/scale:
            r = doc.documentLayout().blockBoundingRect(blk)
            if r.width() > 1: p.drawLine(4, int(r.top()), int(self.width()/scale)-8, int(r.top()))
            blk = blk.next(); y = r.bottom()
        p.restore()
        
        sb = self.target.verticalScrollBar()
        total = sb.maximum() + eh
        if total > 0:
            vy = (sb.value() / total) * h
            vh = (eh / total) * h
            p.fillRect(0, int(vy), self.width(), int(vh), QColor(255,255,255,15))
            p.setPen(QColor(255,255,255,30)); p.drawRect(0, int(vy), self.width()-1, int(vh)-1)

    def _scroll(self, y, sync):
        sb = self.target.verticalScrollBar(); eh = self.target.viewport().height()
        if sb: sb.setValue(int((y/self.height()) * (sb.maximum() + eh) - eh/2))

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton: self._scroll(int(e.position().y()), False)
    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.LeftButton: self._scroll(int(e.position().y()), False)

# ── Document Tab ────────────────────────────────────────────────────────────
class DocTab(QWidget):
    def __init__(self, parent, content=None, workspace=None, title="README.md"):
        super().__init__(parent)
        self.app = parent; self.workspace = workspace; self.file_name = title
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        self.editor = Editor(self.app); self.editor.textChanged.connect(self._on_change)
        if content: self.editor.setPlainText(content)
        self.preview = QTextBrowser(); self.preview.setContextMenuPolicy(Qt.NoContextMenu)
        self.preview.setOpenExternalLinks(True)
        self.preview.setStyleSheet(f"QTextBrowser{{background:{T['bg']};color:{T['text']};border:none;padding:10px;}}")
        self.preview.document().setDefaultStyleSheet(preview_css())
        
        self.e_map = Minimap(self.editor)
        self.p_map = Minimap(self.preview)
        self.e_map.peer = self.p_map; self.p_map.peer = self.e_map

        self.split = QSplitter(Qt.Horizontal)
        self.split.addWidget(self.editor); self.split.addWidget(self.e_map)
        self.split.addWidget(self.preview); self.split.addWidget(self.p_map)
        self.split.setSizes([430, 50, 430, 50])
        self.split.setHandleWidth(2); self.split.setChildrenCollapsible(False)
        self.split.setStyleSheet(f"QSplitter::handle{{background:{T['border']};}}")
        lay.addWidget(self.split)

        self._worker = Worker()
        self._thread = QThread(); self._worker.moveToThread(self._thread)
        self._worker.done.connect(self._on_html); self._thread.start()
        self._timer = QTimer(); self._timer.setSingleShot(True)
        self._timer.timeout.connect(lambda: (self._worker.request(self.editor.toPlainText()), self._worker.process()))
        self.editor.textChanged.connect(lambda: self._timer.start(350))
        
        self._worker.request(self.editor.toPlainText()); self._worker.process()

    def _on_change(self): self.app.stats.refresh()

    def _on_html(self, html):
        self.preview.setHtml(html)

    def stop(self):
        self._timer.stop()
        self._thread.quit(); self._thread.wait(1000)

# ── LocalAI Panel ────────────────────────────────────────────────────────
class OWorker(QObject):
    done = Signal(str, str)
    def __init__(self, model, sys_prompt, prompt):
        super().__init__()
        self.model = model; self.sys_prompt = sys_prompt; self.prompt = prompt
        self._abort = False
    def abort(self):
        self._abort = True
    def run(self):
        try:
            req = urllib.request.Request("http://localhost:11434/api/generate", method="POST")
            req.add_header("Content-Type", "application/json")
            data = json.dumps({"model": self.model, "system": self.sys_prompt, "prompt": self.prompt, "stream": False}).encode("utf-8")
            with urllib.request.urlopen(req, data=data, timeout=60) as f:
                if self._abort: return
                res = json.loads(f.read().decode("utf-8"))
                if not self._abort:
                    self.done.emit(self.prompt, res.get("response", ""))
        except Exception as e:
            if not getattr(self, '_abort', False):
                self.done.emit(self.prompt, f"[Error: {str(e)}]")


class ChatInput(QTextEdit):
    def __init__(self, panel):
        super().__init__()
        self.panel = panel
    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Return, Qt.Key_Enter) and not (e.modifiers() & Qt.ShiftModifier):
            self.panel._send()
            e.accept()
            return
        super().keyPressEvent(e)

class AIPanel(QFrame):
    def __init__(self, app):
        super().__init__(app)
        self.app = app; self.setFixedWidth(260)
        self.setStyleSheet(f"QFrame{{background:{T['panel']};border-left:1px solid {T['border']};font-family: 'Segoe UI', Tahoma, sans-serif;}}"
                           f"QPushButton{{background:{T['hover']};color:{T['text']};border:1px solid {T['border']};border-radius:6px;padding:6px;font-weight:600;font-family: 'Segoe UI', Tahoma, sans-serif;}}"
                           f"QTextBrowser{{background:{T['bg']};border:none;color:{T['text']};font-family: 'Segoe UI', Tahoma, sans-serif;font-size:13px;}}"
                           f"QTextEdit{{background:transparent;color:{T['text']};border:none;padding:8px;font-family: 'Segoe UI', Tahoma, sans-serif;font-size:13px;}}")
        lay = QVBoxLayout(self); lay.setContentsMargins(12,12,12,12); lay.setSpacing(10)
        
        top = QHBoxLayout()
        title = QLabel("LocalAI"); title.setStyleSheet("font-size:16px;font-weight:700;font-family: 'Segoe UI', Tahoma, sans-serif;")
        
        self.model_cb = QComboBox()
        self.model_cb.setStyleSheet(f"background:{T['input']};color:{T['text']};border:1px solid {T['border']};border-radius:6px;padding:2px 6px;font-size:11px;")
        try:
            req = urllib.request.Request("http://localhost:11434/api/tags")
            with urllib.request.urlopen(req, timeout=1) as f:
                data = json.loads(f.read().decode())
                models = [m["name"] for m in data.get("models", [])]
                if models: self.model_cb.addItems(models)
                else: self.model_cb.addItem("No models")
        except:
            self.model_cb.addItem("Error (Ollama?)"); self.model_cb.setEnabled(False)
            
        self.model = self.model_cb.currentText()
        self.model_cb.currentTextChanged.connect(lambda t: setattr(self, 'model', t))
        
        top.addWidget(title); top.addWidget(self.model_cb); top.addStretch()
        
        new_btn = QPushButton("+"); new_btn.setFixedSize(28,28); new_btn.clicked.connect(self._clear_chat)
        new_btn.setToolTip("New Chat")
        
        close_btn = QPushButton(""); close_btn.setFixedSize(28,28); close_btn.clicked.connect(self.hide)
        top.addWidget(new_btn); top.addWidget(close_btn)
        lay.addLayout(top)
        
        self.chat = QTextBrowser()
        self.chat.setOpenLinks(False)
        self.chat.anchorClicked.connect(self._handle_anchor)
        lay.addWidget(self.chat, 1)
        
        imp = QWidget()
        imp.setStyleSheet(f"QWidget{{background:{T['input']};border:1px solid {T['border']};border-radius:20px;}}")
        il = QHBoxLayout(imp); il.setContentsMargins(12,4,4,4); il.setSpacing(6)
        
        self.inp = ChatInput(self); self.inp.setFixedHeight(40); self.inp.setPlaceholderText("Message AI...")
        self.inp.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.inp.document().contentsChanged.connect(self._adjust_inp_size)
        il.addWidget(self.inp)
        
        self.send_btn = QPushButton("➤"); self.send_btn.setFixedSize(32, 32)
        self.send_btn.setStyleSheet(f"QPushButton{{background:{T['accent']};color:#fff;border:none;border-radius:16px;font-size:14px;padding:0px;}} QPushButton:hover{{background:{T['accent2']};}}")
        self.send_btn.clicked.connect(self._send)
        il.addWidget(self.send_btn)
        
        self.stop_btn = QPushButton("⏹"); self.stop_btn.setFixedSize(32, 32)
        self.stop_btn.setStyleSheet(f"QPushButton{{background:#f87171;color:#fff;border:none;border-radius:16px;font-size:14px;padding:0px;}} QPushButton:hover{{background:#ef4444;}}")
        self.stop_btn.clicked.connect(self._stop_generation)
        self.stop_btn.hide()
        il.addWidget(self.stop_btn)
        
        lay.addWidget(imp)
        
        self.model = ""
        self._sys = "You are a specialized Assistant for README and Markdown creation. Always provide direct answers without any conversational filler. You are strictly forbidden from using emojis."
        self._set_empty_state()

    def _set_empty_state(self):
        self.chat.clear()
        self.chat.append(f"<div style='color:{T['dim']}; font-size:12px; margin-bottom:10px;'>Start typing to chat...</div>{get_skeleton_html()}")

    def _clear_chat(self):
        self._set_empty_state()

    def _adjust_inp_size(self):
        h = int(self.inp.document().size().height())
        self.inp.setFixedHeight(min(max(40, h + 10), 100))

    def _handle_anchor(self, url):
        cmd = url.toString()
        if cmd == "copy" and hasattr(self, "last_code"):
            QApplication.clipboard().setText(self.last_code)
            self.app._flash("Code Copied", color="#22c55e")
        elif cmd == "replace" and hasattr(self, "last_code"):
            tab = self.app.tabs.currentWidget()
            if tab and tab.editor:
                tab.editor.setPlainText(self.last_code)
                self.app._flash("Content Replaced", color="#22c55e")
        elif cmd == "regenerate" and hasattr(self, "last_prompt"):
            self.inp.setPlainText(self.last_prompt)
            self._send()

    def _clear_skeleton(self):
        if hasattr(self, '_skel_pos'):
            c = self.chat.textCursor()
            pos = max(0, min(self._skel_pos, self.chat.document().characterCount() - 1))
            c.setPosition(pos)
            c.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
            c.removeSelectedText()
            del self._skel_pos

    def _stop_generation(self):
        if hasattr(self, 'worker') and self.worker:
            self.worker.abort()
        self.send_btn.show()
        self.stop_btn.hide()
        self._clear_skeleton()

    def _send(self):
        text = self.inp.toPlainText().strip()
        if not text: return
        if not self.model:
            QMessageBox.warning(self, "No Model", "Please select a model in Settings first.")
            return
            
        if "Start typing to chat" in self.chat.toPlainText():
            self.chat.clear()
        
        self.last_prompt = text
        self.send_btn.hide()
        self.stop_btn.show()

        context = ""
        try:
            tab = self.app.tabs.currentWidget()
            if tab and tab.editor:
                context = tab.editor.toPlainText()
        except: pass

        sys_prompt = self._sys
        if context:
            sys_prompt += f"\n\nCURRENT EDITOR CONTENT:\n{context}"
        
        self.inp.clear()
        
        self.chat.append(
            f"<div style='margin-top:10px; text-align:right;'>"
            f"<span style='background:{T['input']}; color:{T['text']}; padding:10px 14px; border-radius:15px; display:inline-block; font-family:\"Segoe UI\",sans-serif; text-align:left;'>"
            f"{text}</span></div>"
        )
        
        self._skel_pos = self.chat.document().characterCount() - 1
        self.chat.append(f"<div style='color:{T['dim']};font-size:11px;'>▚▚ Thinking...</div>{get_skeleton_html()}")
        
        self.worker = OWorker(self.model, sys_prompt, text)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.worker.done.connect(self._on_done)
        self.worker.done.connect(self.thread.quit)
        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def _on_done(self, p, r):
        self.send_btn.show()
        self.stop_btn.hide()
        
        self._clear_skeleton()
        
        self.last_code = r.strip()
        
        import markdown2
        r_fmt = markdown2.markdown(self.last_code, extras=["fenced-code-blocks", "tables", "strike"])
        
        r_fmt = r_fmt.replace("<pre><code>", "<pre style='background:#1e1e1e;padding:10px;border-radius:8px;font-family:monospace;'><code>")
        r_fmt = r_fmt.replace("<table>", "<table style='border-collapse:collapse;width:100%;'>")
        r_fmt = r_fmt.replace("<th>", "<th style='border:1px solid #333;padding:5px;background:#2a2a2a;'>")
        r_fmt = r_fmt.replace("<td>", "<td style='border:1px solid #333;padding:5px;'>")
        
        if self.last_code:
            r_fmt += f"<br><br><a href='copy' style='color:{T['accent']};text-decoration:none;font-weight:700;'>[ Copy]</a>"
            r_fmt += f"&nbsp;&nbsp;<a href='replace' style='color:{T['accent']};text-decoration:none;font-weight:700;'>[ Replace]</a>"
        
        r_fmt += f"&nbsp;&nbsp;<a href='regenerate' style='color:{T['dim']};text-decoration:none;font-weight:700;'>[ Regenerate]</a>"
        
        self.chat.append(
            f"<div style='margin-top:10px;'>"
            f"<div style='background:transparent; color:{T['text']}; display:block; font-family:\"Segoe UI\",sans-serif;'>"
            f"{r_fmt}</div></div><br>"
        )
        self.chat.verticalScrollBar().setValue(self.chat.verticalScrollBar().maximum())



# ── Main Window ────────────────────────────────────────────────────────────
class App(QMainWindow):
    def __init__(self, workspace=None):
        super().__init__()
        self.workspace = os.path.abspath(workspace or os.getcwd())
        self.setWindowTitle("README Builder")
        self.resize(1200, 650)

        # Robust Icon Path Resolution for PyInstaller
        if getattr(sys, 'frozen', False):
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        icon_path = os.path.join(base_dir, "icon.ico")
        if os.path.exists(icon_path): self.setWindowIcon(QIcon(icon_path))

        self._apply_global_style()

        central = QWidget(); self.setCentralWidget(central)
        root = QHBoxLayout(central); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        root.addWidget(self._make_sidebar())

        main = QWidget()
        ml = QVBoxLayout(main); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)
        root.addWidget(main)

        self.ai_panel =AIPanel(self)
        self.ai_panel.hide()
        root.addWidget(self.ai_panel)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True); self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.setStyleSheet(
            f"QTabWidget::pane{{border:none;background:{T['bg']};}}"
            f"QTabBar::tab{{background:transparent;color:#D4D4D4;border:1px solid {T['border']};"
            f"border-bottom:none;border-top-left-radius:8px;border-top-right-radius:8px;"
            f"padding:8px 16px;margin-right:2px;font-size:11px;font-weight:600;min-width:100px;}}"
            f"QTabBar::tab:selected{{background:transparent;color:#D4D4D4;border-color:{T['border']};border-bottom:2px solid #2A2A2A;}}"
            f"QTabBar::tab:hover:!selected{{background:{T['hover']};color:{T['text']};}}"
            f"QTabBar::close-button{{background:transparent;border-radius:2px;margin-left:5px;}}"
            f"QTabBar::close-button:hover{{background:#f87171;}}"
        )
        ml.addWidget(self.tabs)

        self.find_bar = FindBar(None, self); self.find_bar.hide()
        ml.addWidget(self.find_bar)

        self._status = QLabel("", self); self._status.setAlignment(Qt.AlignCenter); self._status.setFixedSize(140, 36)
        self._status.setStyleSheet(f"background:{T['accent']};color:#fff;border-radius:8px;font-weight:600;font-size:12px;")
        self._status.hide()

        self.stats = StatsBar(None, self)
        ml.addWidget(self.stats)

        QShortcut(QKeySequence("Ctrl+N"), self, self._new_tab)
        QShortcut(QKeySequence("Ctrl+X"), self, lambda: self._close_tab(self.tabs.currentIndex()))
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
        tab = self.tabs.widget(idx)
        if tab:
            self.stats.editor = tab.editor; self.stats.refresh()
            self.find_bar.editor = tab.editor; self.find_bar._hl()
            tab.editor.ai_btn.setVisible(self.ai_panel.isVisible())

    def _open_find(self):
        tab = self.tabs.currentWidget()
        if tab: self.find_bar.editor = tab.editor; self.find_bar.show(); self.find_bar.find.setFocus()

    def _open_replace(self):
        tab = self.tabs.currentWidget()
        if tab: self.find_bar.editor = tab.editor; self.find_bar.show(); self.find_bar.repl.setFocus()

    def _apply_global_style(self):
        self.setStyleSheet(
            f"QMainWindow{{background:{T['bg']};}}"
            f"QWidget{{background:{T['bg']};color:{T['text']};}}"
            f"QTextEdit{{background:{T['bg']};color:{T['editor']};border:none;"
            f"font-size:14px;padding:18px;font-family:ui-monospace,'SF Mono',Consolas,monospace;line-height:1.7;}}"
            f"QScrollBar:vertical{{border:none;background:{T['bg']};width:7px;}}"
            f"QScrollBar::handle:vertical{{background:{T['scroll']};border-radius:3px;min-height:24px;}}"
            f"QScrollBar::handle:vertical:hover{{background:{T['border']};}}"
            f"QScrollBar:horizontal{{border:none;background:{T['bg']};height:7px;}}"
            f"QScrollBar::handle:horizontal{{background:{T['scroll']};border-radius:3px;min-width:24px;}}"
            f"QComboBox{{background:{T['input']};color:{T['editor']};border:1px solid {T['border']};border-radius:6px;padding:6px;}}"
        )

    def _make_sidebar(self):
        sb = QFrame(); sb.setFixedWidth(80)
        sb.setStyleSheet(
            f"QFrame{{background:{T['panel']};border-right:1px solid {T['border']};}}"
            f"QToolButton{{background:transparent;color:{T['dim']};border:none;border-radius:8px;"
            f"padding:10px 4px;font-size:11px;font-weight:600;}}"
            f"QToolButton:hover{{background:{T['hover']};color:{T['text']};}}"
        )
        lay = QVBoxLayout(sb); lay.setContentsMargins(6,10,6,10); lay.setSpacing(6)
        buttons = [
            ("Template",  self._open_templates, "Ctrl+T"),
            ("Snippet",   self._open_snippets,  ""),
            ("Import",    self._import_gh,       ""),
            ("TOC",       self._gen_toc,         ""),
            ("Score",     self._show_score,      ""),
            ("Images",    self._open_images,     "Ctrl+I"),
            ("Translate", self._translate,       ""),
            ("Repair",    self._repair,          ""),
            ("Find",      lambda: (self.find_bar.show(), self.find_bar.find.setFocus()), "Ctrl+F"),
            ("Export",    self._export,          ""),
            ("LocalAI",  self._toggle_ai,       ""),
            ("Recent",    self._show_recent,     ""),
        ]
        for lbl, fn, sc in buttons:
            b = QToolButton(); b.setText(lbl); b.clicked.connect(fn)
            if sc: b.setToolTip(f"{lbl} ({sc})")
            lay.addWidget(b)
        lay.addStretch()
        credit = QLabel("Yasser-27\non github")
        credit.setAlignment(Qt.AlignCenter)
        credit.setStyleSheet(f"color:{T['border']};font-size:9px;background:transparent;padding:4px;")
        lay.addWidget(credit)
        return sb

    def _toggle_ai(self):
        v = not self.ai_panel.isVisible()
        self.ai_panel.setVisible(v)
        if v:
            self.ai_panel.inp.setFocus()
        
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab and hasattr(tab, 'editor'):
                tab.editor.ai_btn.setVisible(v)

    def _show_recent(self):
        d = QDialog(self); d.setWindowTitle("Recent Files"); d.setFixedSize(400, 450)
        d.setStyleSheet(
            f"QDialog{{background:{T['panel']};color:{T['text']};}}"
            f"QListWidget{{background:{T['input']};border:1px solid {T['border']};border-radius:6px;padding:6px;outline:none;}}"
            f"QListWidget::item{{padding:10px;border-bottom:1px solid {T['border']};color:{T['text']};border-radius:4px;}}"
            f"QListWidget::item:selected{{background:{T['accent']};color:#fff;border:none;}}"
        )
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
            i = QListWidgetItem(os.path.basename(p))
            i.setData(Qt.UserRole, p); lw.addItem(i)
        
        lay.addWidget(lw)
        b = QPushButton("Open Selected"); b.setStyleSheet(BTN_STYLE())
        def _op():
            it = lw.currentItem()
            if it:
                path = it.data(Qt.UserRole)
                try:
                    with open(path, "r", encoding="utf-8") as f: content = f.read()
                    self._new_tab(content, os.path.basename(path))
                    d.accept()
                except Exception as e: QMessageBox.warning(self, "Error", str(e))
        b.clicked.connect(_op); lw.itemDoubleClicked.connect(_op); lay.addWidget(b)
        d.exec()

    def _flash(self, msg, color=None):
        self._status.setText(msg)
        if color: self._status.setStyleSheet(f"background:{color};color:#fff;border-radius:8px;font-weight:600;font-size:12px;")
        else: self._status.setStyleSheet(f"background:{T['accent']};color:#fff;border-radius:8px;font-weight:600;font-size:12px;")
        self._status.move(self.width()//2-70, self.height()-54)
        self._status.show(); QTimer.singleShot(1800, self._status.hide)

    def _quick_save(self):
        if self._save(): self._flash("Saved ")

    def _open_templates(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        d = TemplatePicker(self)
        if d.exec() == QDialog.Accepted and d.result_text:
            tab.editor.setPlainText(d.result_text)

    def _gen_toc(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        lines = tab.editor.toPlainText().split("\n"); toc = ["##  Table of Contents"]; found = False
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
        dlg.setStyleSheet(
            f"QDialog{{background:{T['panel']};color:{T['text']};}}"
            f"QListWidget{{background:{T['input']};border:1px solid {T['border']};border-radius:7px;color:{T['text']};padding:6px;}}"
            f"QListWidget::item{{padding:9px;border-radius:5px;}}"
            f"QListWidget::item:selected{{background:{T['accent']};color:#fff;}}"
            f"QListWidget::item:hover{{background:{T['hover']};}}"
            f"QPushButton{{background:{T['accent']};color:#fff;border:none;border-radius:7px;padding:9px;font-weight:600;font-size:12px;}}"
            f"QPushButton:hover{{background:{T['accent2']};}}"
        )
        lay = QVBoxLayout(dlg); lay.setContentsMargins(16,14,16,14); lay.setSpacing(10)
        lw = QListWidget()
        for k in SNIPPETS: lw.addItem(k)
        lay.addWidget(lw)
        def insert():
            sel = lw.currentItem()
            if sel: tab.editor.insertPlainText(SNIPPETS[sel.text()]); dlg.accept()
        b = QPushButton("Insert"); b.clicked.connect(insert); lay.addWidget(b)
        dlg.exec()

    def _import_gh(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        d = QDialog(self); d.setWindowTitle("Import from GitHub"); d.setFixedSize(420, 160)
        d.setStyleSheet(
            f"QDialog{{background:{T['panel']};color:{T['text']};}}"
            f"QLabel{{color:{T['dim']};font-size:12px;background:transparent;}}"
            f"QLineEdit{{background:{T['input']};color:{T['editor']};border:1px solid {T['border']};"
            f"border-radius:6px;padding:8px 12px;font-size:13px;}}"
            f"QLineEdit:focus{{border-color:{T['accent']};}}"
            f"QPushButton{{background:{T['accent']};color:#fff;border:none;border-radius:7px;padding:8px 16px;font-weight:600;}}"
            f"QPushButton:hover{{background:{T['accent2']};}}"
        )
        lay = QVBoxLayout(d); lay.setContentsMargins(18,14,18,14); lay.setSpacing(10)
        lay.addWidget(QLabel("GitHub repo URL:"))
        inp = QLineEdit(); inp.setPlaceholderText("https://github.com/user/repo"); lay.addWidget(inp)
        row = QHBoxLayout()
        cancel = QPushButton("Cancel"); cancel.setStyleSheet(f"background:{T['hover']};color:{T['text']};border:1px solid {T['border']};border-radius:7px;padding:8px 16px;font-weight:600;"); cancel.clicked.connect(d.reject); row.addWidget(cancel)
        confirm = QPushButton("Import"); confirm.clicked.connect(d.accept); row.addWidget(confirm)
        lay.addLayout(row)
        if d.exec() != QDialog.Accepted: return
        raw = inp.text().strip()
        if not raw: return
        if "github.com" in raw and "raw.githubusercontent" not in raw:
            raw = raw.replace("github.com","raw.githubusercontent.com").rstrip("/") + "/main/README.md"
        try:
            try: resp = urllib.request.urlopen(urllib.request.Request(raw))
            except urllib.error.HTTPError as e:
                if e.code == 404 and "/main/" in raw:
                    resp = urllib.request.urlopen(urllib.request.Request(raw.replace("/main/","/master/")))
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

    def _translate(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        d = TranslateDialog(tab.editor.toPlainText(), self)
        if d.exec() == QDialog.Accepted and d.result:
            tab.editor.setPlainText(d.result)
            self._flash("Translation applied!")

    def _repair(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        d = RepairDialog(tab.editor.toPlainText(), self)
        if d.exec() == QDialog.Accepted and d.result:
            tab.editor.setPlainText(d.result)
            self._flash("Repairs applied ", "#4ADE80")


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
        return tab

    def _close_tab(self, idx):
        if self.tabs.count() > 1:
            tab = self.tabs.widget(idx)
            if tab: tab.stop(); tab.deleteLater()
            self.tabs.removeTab(idx)

    def _add_snippet(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        text = tab.editor.textCursor().selectedText().replace("\u2029", "\n")
        if not text: self._flash("Select text first!"); return
        dlg = SnippetAddDialog(self, text)
        if dlg.exec() == QDialog.Accepted:
            name = dlg.name.text().strip()
            if name:
                self.user_snippets[name] = text
                self._save_snippets()
                self._flash(f"Saved '{name}'!")

    def _load_snippets(self):
        p = Path(self.workspace) / "snippets.json"
        if p.exists():
            try: return json.loads(p.read_text("utf-8"))
            except: pass
        return {}

    def _save_snippets(self):
        try:
            p = Path(self.workspace) / "snippets.json"
            p.write_text(json.dumps(self.user_snippets, indent=4), "utf-8")
        except: pass

    def _rename_tab(self):
        idx = self.tabs.currentIndex()
        tab = self.tabs.widget(idx)
        if not tab: return
        dlg = QInputDialog(self); dlg.setWindowTitle("Rename Tab"); dlg.setLabelText("New name:")
        dlg.setTextValue(tab.file_name)
        dlg.setStyleSheet(
            f"QInputDialog{{background:{T['panel']};color:{T['text']};}}"
            f"QLabel{{color:{T['text']};font-size:13px;}}"
            f"QLineEdit{{background:{T['bg']};color:{T['editor']};border:1px solid {T['border']};border-radius:4px;padding:4px;}}"
            f"QPushButton{{background:{T['accent']};color:#fff;border-radius:4px;padding:5px 15px;min-width:60px;}}"
        )
        if dlg.exec() == QInputDialog.Accepted:
            new_name = dlg.textValue().strip()
            if new_name:
                if "." not in new_name: new_name += ".md"
                tab.file_name = new_name
                self.tabs.setTabText(idx, new_name)
                self._flash(f"Renamed: {new_name}")

    def _load_initial(self):
        self._new_tab("", "README.md")

    def _export(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        p, _ = QFileDialog.getSaveFileName(self,"Export","README.md","Markdown (*.md);;HTML (*.html)")
        if not p: return
        try:
            if p.endswith(".html"):
                css = preview_css()
                html = markdown2.markdown(tab.editor.toPlainText(), extras=["fenced-code-blocks","tables","task_list"])
                Path(p).write_text(f"<!DOCTYPE html><html><head><meta charset='UTF-8'>{css}</head><body>{html}</body></html>","utf-8")
            else:
                Path(p).write_text(f"<!-- README Builder | {datetime.now():%Y-%m-%d} -->\n\n{tab.editor.toPlainText()}","utf-8")
            QMessageBox.information(self," Exported",f"Saved:\n{p}")
        except Exception as e: QMessageBox.critical(self,"Error",str(e))

    def _save(self):
        tab = self.tabs.currentWidget()
        if not tab: return False
        try:
            (Path(self.workspace) / tab.file_name).write_text(tab.editor.toPlainText(), "utf-8")
            return True
        except Exception as e: QMessageBox.critical(self,"Error",str(e)); return False

    def closeEvent(self, e):
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab: tab.stop()
        e.accept()

# ── Entry Point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(
        f"QWidget{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}"
        f"QToolTip{{background:{T['panel']};color:{T['text']};border:1px solid {T['border']};"
        f"border-radius:5px;padding:4px 8px;font-size:11px;}}"
    )
    ws = os.getcwd()
    target_file = None
    if len(sys.argv) > 1:
        p = os.path.abspath(sys.argv[1])
        ws = p if os.path.isdir(p) else os.path.dirname(p)
        if os.path.isfile(p): target_file = p

    window = App(ws)

    if target_file and os.path.exists(target_file):
        try:
            with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            window._new_tab(content, os.path.basename(target_file))
        except: pass

    window.show()
    # Defer heavy init to after window is visible for instant startup
    QTimer.singleShot(200, self_install)
    QTimer.singleShot(400, auto_register_context_menu)
    sys.exit(app.exec())
