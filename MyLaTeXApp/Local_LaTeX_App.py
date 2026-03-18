import sys
import os
import subprocess
import json
import datetime
import socket
import re
import shutil
from PIL import Image

# 引入 PySide6 界面库
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QTextEdit, QLabel, 
                               QFileDialog, QMessageBox, QProgressBar, QTabWidget,
                               QListWidget, QListWidgetItem, QSplitter, QMenu, QScrollArea,
                               QSizePolicy, QComboBox, QDialog, QFormLayout, QLineEdit, QGroupBox, QCheckBox,
                               QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import QThread, Signal, Qt, QMimeData
from PySide6.QtGui import QImage, QPixmap, QRegion, QCursor, QIcon, QDragEnterEvent, QDropEvent

# 引入 PyMuPDF
try:
    import fitz
except ImportError:
    print("❌ 缺少 pymupdf 库。请运行: pip install pymupdf")
    fitz = None

# 引入 AI 库
import google.generativeai as genai
try:
    import dashscope
    from http import HTTPStatus
except ImportError:
    dashscope = None

# ==========================================
# ⚙️ 配置管理 (顺序至关重要！)
# ==========================================
CONFIG_FILE = "config.json"
HISTORY_FILE = "history_data.json"

# ✅ 1. 先定义 Key (解决 NameError)
INTERNAL_API_KEY = "AIzaSyBjsq1zAg7O2xunwiPJaLIf5HiJ1h9-DnI"

# ✅ 2. 再定义 Prompt
# 修改后的 DEFAULT_PROMPTS
DEFAULT_PROMPTS = {
    "标准试卷/文档": """
你是一个顶级的 LaTeX 排版专家。请将提供的图片内容识别并合并转换为一个排版精美、专业的 LaTeX 文档。

**排版核心要求**：
1. **文档类与版面**：
   - 使用 `\\documentclass[12pt, a4paper]{article}`。
   - 使用 `\\usepackage[margin=2cm]{geometry}` (⚠️重要：增加版面宽度以防止溢出)。
2. **必备宏包**：
   - 数学：`amsmath, amssymb`
   - 图片：`graphicx, float`
   - 表格：`booktabs, array, tabularx, longtable, multirow`
   - 中文支持：**必须仅使用 `\\usepackage{ctex}`** (⚠️不要加 fontset 参数，防止编译崩溃)。
3. **防止溢出规则(⚠️严格执行)**：
   - 图片：必须设置宽度，例如 `\\includegraphics[width=\\linewidth]{filename}`。
   - 表格：**必须**使用 `tabularx` 环境，总宽度设为 `\\textwidth`。
     例如：`\\begin{tabularx}{\\textwidth}{X|c|X}` (使用 X 列自动换行)。
4. **输出格式**：只返回纯 LaTeX 代码，不要 Markdown 标记。
""",

    "读书笔记/摘要": """
你是一个高效的笔记整理助手。请识别图片内容，并整理成一份结构清晰的 LaTeX 读书笔记。
**核心要求**：
1. **文档类**：`article`。
2. **中文支持**：使用 `\\usepackage{ctex}` (不要加 fontset)。
3. **内容**：提取核心观点，使用 `tcolorbox` 包裹重点。
4. **输出**：只返回纯代码。
""",

    "纯公式提取": """
请只提取图片中的所有数学公式。
**核心要求**：
1. **文档类**：`article`。
2. **中文支持**：使用 `\\usepackage{ctex}` (不要加 fontset)。
3. **内容**：只保留公式，使用 `align*` 环境。
4. **输出**：只返回纯代码。
"""
}

# ✅ 3. 最后定义 Config (现在可以引用 INTERNAL_API_KEY 了)
DEFAULT_CONFIG = {
    "provider": "Google Gemini", 
    "api_key": INTERNAL_API_KEY, 
    "proxy_url": "http://127.0.0.1:7897",
    "auto_proxy": True,
    "model_name": "gemini-2.5-flash",
    "custom_prompts": DEFAULT_PROMPTS
}

class ConfigManager:
    def __init__(self):
        self.data = DEFAULT_CONFIG.copy()
        self.load()
    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    self.data.update(saved)
                    if "custom_prompts" not in self.data: self.data["custom_prompts"] = DEFAULT_PROMPTS
            except: pass
    def save(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
        except: pass
    def get(self, key, default=None):
        return self.data.get(key, default if default is not None else DEFAULT_CONFIG.get(key))
    def set(self, key, value):
        self.data[key] = value
        self.save()

config = ConfigManager()

# ==========================================
# 🎨 全局样式表
# ==========================================
DARK_THEME_STYLESHEET = """
QWidget { background-color: #1E1E1E; color: #D4D4D4; font-family: "Segoe UI", sans-serif; font-size: 14px; }
QScrollBar:vertical { border: none; background: #1E1E1E; width: 10px; margin: 0px; }
QScrollBar::handle:vertical { background: #424242; min-height: 20px; border-radius: 5px; }
QScrollBar::handle:vertical:hover { background: #686868; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QListWidget, QTableWidget { background-color: #252526; border: 1px solid #333337; border-radius: 8px; outline: none; }
QListWidget::item { padding: 8px; margin: 2px 5px; border-radius: 4px; border-bottom: 1px solid #2D2D30; }
QListWidget::item:selected { background-color: #37373D; color: #FFFFFF; border-left: 3px solid #6C5CE7; }
QPushButton { background-color: #333337; border: 1px solid #3E3E42; border-radius: 6px; padding: 6px 12px; color: #E0E0E0; }
QPushButton:hover { background-color: #3E3E42; border-color: #666; }
QPushButton:pressed { background-color: #1E1E1E; padding-top: 7px; }
QPushButton:disabled { background-color: #252526; color: #555; border-color: #2D2D30; }
QPushButton#primaryBtn { background-color: #6C5CE7; color: white; border: none; font-weight: bold; }
QPushButton#primaryBtn:hover { background-color: #5A4BCB; }
QPushButton#stopBtn { background-color: #D32F2F; color: white; border: none; font-weight: bold; }
QPushButton#stopBtn:hover { background-color: #B71C1C; }
QPushButton#actionBtn { background-color: #0984e3; color: white; border: none; }
QPushButton#actionBtn:hover { background-color: #007acc; }
QPushButton#dangerBtn { color: #FF6B6B; border: 1px solid #FF6B6B; background-color: transparent; }
QPushButton#dangerBtn:hover { background-color: rgba(255, 107, 107, 0.1); }
QPushButton#zoomBtn { background-color: #3C3C3C; border: 1px solid #555; color: #FFF; padding: 2px; border-radius: 4px; font-weight: bold; font-size: 16px; }
QTextEdit { background-color: #1E1E1E; border: 1px solid #333; font-family: "Consolas", monospace; color: #DCDCDC; }
QComboBox { background-color: #333337; border: 1px solid #3E3E42; border-radius: 4px; padding: 5px; color: #E0E0E0; }
QComboBox::drop-down { border: none; }
QLabel#headerLabel { color: #888; font-weight: bold; font-size: 12px; text-transform: uppercase; margin-bottom: 5px; }
QProgressBar { border: 1px solid #3E3E42; border-radius: 5px; text-align: center; color: #FFF; background-color: #252526; height: 15px; }
QProgressBar::chunk { background-color: #6C5CE7; border-radius: 4px; }
QDialog { background-color: #1E1E1E; }
QGroupBox { border: 1px solid #3E3E42; border-radius: 6px; margin-top: 12px; font-weight: bold; color: #ccc; }
QLineEdit { background-color: #252526; border: 1px solid #3E3E42; border-radius: 4px; padding: 6px; color: #EEE; }
QHeaderView::section { background-color: #333337; color: #DDD; padding: 4px; border: none; }
QTableWidget { gridline-color: #333; }
"""

# ==========================================
# 🛠️ 工具函数
# ==========================================
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'): return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def check_port(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except: return False

def apply_proxy_settings():
    os.environ.pop("HTTP_PROXY", None)
    os.environ.pop("HTTPS_PROXY", None)
    use_auto = config.get("auto_proxy")
    manual_url = config.get("proxy_url", "").strip()
    final_proxy = None
    if not use_auto:
        if manual_url: final_proxy = manual_url
    else:
        manual_port = None
        if manual_url and ":" in manual_url:
            try: manual_port = int(manual_url.split(":")[-1])
            except: pass
        ports_to_check = []
        if manual_port: ports_to_check.append(manual_port)
        ports_to_check.extend([7897, 7890, 10809, 4780, 1080])
        seen = set()
        unique_ports = [x for x in ports_to_check if not (x in seen or seen.add(x))]
        for port in unique_ports:
            if check_port(port):
                final_proxy = f"http://127.0.0.1:{port}"
                break
    if final_proxy:
        os.environ["HTTP_PROXY"] = final_proxy
        os.environ["HTTPS_PROXY"] = final_proxy
    return final_proxy

apply_proxy_settings()

# 历史记录相关
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: return []
    return []

def save_history(record):
    history = load_history()
    history.insert(0, record)
    if len(history) > 50: history = history[:50]
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except: pass

# ✅ 修复：确保这个函数存在，并且包含物理文件删除逻辑
def delete_history_records(pdf_paths_to_remove):
    history = load_history()
    new_history = []
    for h in history:
        path = h.get('pdf') or h.get('pdf_path')
        if path in pdf_paths_to_remove:
            # 物理删除文件
            if os.path.exists(path):
                try: os.remove(path)
                except: pass
            tex_path = os.path.splitext(path)[0] + ".tex"
            if os.path.exists(tex_path):
                try: os.remove(tex_path)
                except: pass
        else:
            new_history.append(h)
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_history, f, ensure_ascii=False, indent=2)
    except: pass

# ==========================================
# 🖼️ 图片填空对话框
# ==========================================
class ImageMappingDialog(QDialog):
    def __init__(self, missing_files, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📷 补充图片资源")
        self.resize(600, 400)
        self.missing_files = missing_files 
        self.file_map = {} 
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        info = QLabel(f"⚠️ AI 生成的代码中引用了 {len(self.missing_files)} 张图片。\n请为这些图片指定本地文件，以便正确编译 PDF。")
        info.setStyleSheet("color: #ff9f43; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["代码中的文件名", "拖入或选择本地图片"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setRowCount(len(self.missing_files))
        self.table.setAcceptDrops(True) 
        for i, filename in enumerate(self.missing_files):
            item_name = QTableWidgetItem(filename)
            item_name.setFlags(Qt.ItemIsEnabled) 
            self.table.setItem(i, 0, item_name)
            widget = QWidget()
            h_layout = QHBoxLayout(widget)
            h_layout.setContentsMargins(2, 2, 2, 2)
            lbl_path = QLabel("等待上传...")
            lbl_path.setStyleSheet("color: #666; font-style: italic;")
            btn_select = QPushButton("📂 选择")
            btn_select.setFixedSize(60, 25)
            btn_select.clicked.connect(lambda checked, r=i: self.select_image(r))
            h_layout.addWidget(lbl_path)
            h_layout.addWidget(btn_select)
            self.table.setCellWidget(i, 1, widget)
        layout.addWidget(self.table)
        btn_box = QHBoxLayout()
        btn_ok = QPushButton("✅ 确认并继续编译")
        btn_ok.setObjectName("primaryBtn")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("取消任务")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_ok)
        layout.addLayout(btn_box)
        self.table.dragEnterEvent = self.table_dragEnterEvent
        self.table.dragMoveEvent = self.table_dragMoveEvent
        self.table.dropEvent = self.table_dropEvent
    def select_image(self, row):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Images (*.png *.jpg *.jpeg *.bmp *.pdf)")
        if file_path: self.set_row_file(row, file_path)
    def set_row_file(self, row, path):
        filename = self.table.item(row, 0).text()
        self.file_map[filename] = path
        widget = self.table.cellWidget(row, 1)
        if widget:
            lbl = widget.findChild(QLabel)
            if lbl:
                lbl.setText(os.path.basename(path))
                lbl.setStyleSheet("color: #2ecc71; font-weight: bold;")
    def table_dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()
    def table_dragMoveEvent(self, event): event.accept()
    def table_dropEvent(self, event):
        pos = event.position().toPoint()
        item = self.table.itemAt(pos)
        if not item: return
        row = item.row()
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files: self.set_row_file(row, files[0])

# ==========================================
# 设置与预览组件
# ==========================================
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ 设置")
        self.resize(500, 450)
        self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self); layout.setSpacing(15)
        group_api = QGroupBox("🤖 AI 服务设置")
        form_api = QFormLayout()
        self.combo_provider = QComboBox()
        self.combo_provider.addItems(["Google Gemini", "Alibaba Qwen (通义千问)"])
        self.combo_provider.setCurrentText(config.get("provider", "Google Gemini"))
        self.combo_provider.currentTextChanged.connect(self.update_model_list)
        self.input_key = QLineEdit(config.get("api_key")); self.input_key.setEchoMode(QLineEdit.Password)
        self.combo_model = QComboBox(); self.combo_model.setEditable(True)
        self.update_model_list(self.combo_provider.currentText())
        self.combo_model.setCurrentText(config.get("model_name"))
        form_api.addRow("服务商:", self.combo_provider)
        form_api.addRow("API Key:", self.input_key)
        form_api.addRow("模型:", self.combo_model)
        group_api.setLayout(form_api)
        layout.addWidget(group_api)
        
        group_net = QGroupBox("🌐 网络连接")
        form_net = QFormLayout()
        self.chk_auto_proxy = QCheckBox("自动检测代理")
        self.chk_auto_proxy.setChecked(config.get("auto_proxy"))
        self.chk_auto_proxy.toggled.connect(lambda: self.input_proxy.setEnabled(not self.chk_auto_proxy.isChecked()))
        self.input_proxy = QLineEdit(config.get("proxy_url"))
        form_net.addRow(self.chk_auto_proxy); form_net.addRow("代理地址:", self.input_proxy)
        group_net.setLayout(form_net); layout.addWidget(group_net)
        self.input_proxy.setEnabled(not self.chk_auto_proxy.isChecked())
        
        btn_box = QHBoxLayout()
        btn_save = QPushButton("保存"); btn_save.setObjectName("primaryBtn")
        btn_save.clicked.connect(self.save_settings)
        btn_cancel = QPushButton("取消"); btn_cancel.clicked.connect(self.reject)
        btn_box.addStretch(); btn_box.addWidget(btn_cancel); btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)
    def update_model_list(self, provider):
        self.combo_model.clear()
        if provider == "Google Gemini": self.combo_model.addItems(["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"])
        else: self.combo_model.addItems(["qwen-vl-max", "qwen-vl-plus"])
    def save_settings(self):
        config.set("provider", self.combo_provider.currentText())
        config.set("api_key", self.input_key.text().strip())
        config.set("model_name", self.combo_model.currentText())
        config.set("auto_proxy", self.chk_auto_proxy.isChecked())
        config.set("proxy_url", self.input_proxy.text().strip())
        apply_proxy_settings()
        self.accept()

class MagnifierLabel(QLabel):
    def __init__(self, parent=None, size=200, scale=2.0):
        super().__init__(parent)
        self.setFixedSize(size, size); self.scale_factor = scale
        self.setMask(QRegion(0, 0, size, size, QRegion.Ellipse))
        self.setStyleSheet("background-color: white; border: 3px solid white; border-radius: 100px;")
        self.setVisible(False); self.setAttribute(Qt.WA_TransparentForMouseEvents)
    def update_view(self, original_pixmap, mouse_pos):
        if not original_pixmap: return
        ew, eh = self.width()/self.scale_factor, self.height()/self.scale_factor
        x, y = mouse_pos.x()-ew/2, mouse_pos.y()-eh/2
        extracted = original_pixmap.copy(int(x), int(y), int(ew), int(eh))
        if not extracted.isNull(): self.setPixmap(extracted.scaled(self.width(), self.height(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        self.move(int(mouse_pos.x()-self.width()/2), int(mouse_pos.y()-self.height()/2))

class PDFPageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent); self.setMouseTracking(True)
        self.magnifier = MagnifierLabel(self); self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed); self.setCursor(Qt.CrossCursor)
    def mouseMoveEvent(self, e):
        if self.pixmap() and not self.pixmap().isNull():
            pos = e.position().toPoint() if hasattr(e, 'position') else e.pos()
            self.magnifier.update_view(self.pixmap(), pos)
            if not self.magnifier.isVisible(): self.magnifier.show(); self.setCursor(Qt.BlankCursor)
        super().mouseMoveEvent(e)
    def leaveEvent(self, e): self.magnifier.hide(); self.setCursor(Qt.ArrowCursor); super().leaveEvent(e)

class PDFPreviewWidget(QScrollArea):
    def __init__(self):
        super().__init__(); self.setWidgetResizable(True)
        self.content_widget = QWidget(); self.layout = QVBoxLayout(self.content_widget)
        self.layout.setContentsMargins(30, 30, 30, 30); self.layout.setSpacing(20); self.layout.setAlignment(Qt.AlignHCenter)
        self.setWidget(self.content_widget); self.setStyleSheet("background-color: #252526; border: none;")
        self.current_zoom = 1.5; self.current_pdf_path = None
        self.placeholder = QLabel("PDF 预览区域 (Ctrl+滚轮缩放)"); self.placeholder.setStyleSheet("font-size: 18px; color: #666; font-weight: bold;")
        self.layout.addWidget(self.placeholder)
    def load_pdf(self, pdf_path=None):
        if not fitz: return
        target_path = pdf_path if pdf_path else self.current_pdf_path
        if not target_path: return
        self.current_pdf_path = target_path
        while self.layout.count(): item = self.layout.takeAt(0); 
        if item.widget(): item.widget().deleteLater()
        if not os.path.exists(target_path): return
        try:
            v_val = self.verticalScrollBar().value()
            with open(target_path, "rb") as f: doc = fitz.open("pdf", f.read())
            for i in range(len(doc)):
                pix = doc.load_page(i).get_pixmap(matrix=fitz.Matrix(self.current_zoom, self.current_zoom))
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                lbl = PDFPageLabel(); lbl.setPixmap(QPixmap.fromImage(img)); lbl.setStyleSheet("border: 1px solid #000; background: white;")
                self.layout.addWidget(lbl)
            doc.close(); self.verticalScrollBar().setValue(v_val)
        except: pass
    def wheelEvent(self, e):
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            if e.angleDelta().y() > 0: self.zoom_in()
            else: self.zoom_out()
            e.accept()
        else: super().wheelEvent(e)
    def zoom_in(self): 
        if self.current_pdf_path and self.current_zoom < 4.0: self.current_zoom += 0.25; self.load_pdf()
    def zoom_out(self):
        if self.current_pdf_path and self.current_zoom > 0.5: self.current_zoom -= 0.25; self.load_pdf()
    def zoom_reset(self): 
        if self.current_pdf_path: self.current_zoom = 1.5; self.load_pdf()

# ==========================================
# 🔨 编译逻辑 (支持外部图片)
# ==========================================
# 找到 run_tectonic 函数，替换为以下版本
def run_tectonic(tex_code, output_name, log_callback=None, status_callback=None):
    tectonic_path = get_resource_path("tectonic.exe")
    if not os.path.exists(tectonic_path): return False, "❌ 找不到 tectonic.exe", None
    
    tex_file = f"{output_name}.tex"
    pdf_file = f"{output_name}.pdf"
    
    # 1. 写入文件 (确保 UTF-8)
    try:
        with open(tex_file, "w", encoding="utf-8") as f: f.write(tex_code)
    except Exception as e: return False, str(e), None

    # 2. 构建命令 (显式清理可能导致冲突的环境变量)
    cmd = [tectonic_path, tex_file]
    
    # 复制当前环境变量，但移除可能导致干扰的项
    env = os.environ.copy()
    if 'FANDOL_PATH' in env: del env['FANDOL_PATH'] # 有时会导致路径冲突
    
    try:
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        # 3. 执行编译
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            encoding='utf-8', 
            errors='replace', # ⚠️ 防止读取日志时因为特殊字符报错
            startupinfo=startupinfo, 
            env=env, 
            bufsize=1
        )
        
        full_log = []
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None: break
            if line:
                text = line.strip()
                # 过滤掉一些吓人的非致命警告
                if "Fontconfig error" in text:
                    full_log.append(f"⚠️ [忽略系统配置警告] {text}")
                    continue 
                    
                full_log.append(text)
                if log_callback: log_callback(text)
                
                # 状态回调优化
                if status_callback:
                    if "downloading" in text.lower(): status_callback("downloading", text)
                    elif "error" in text.lower() and "fontconfig" not in text.lower(): 
                        status_callback("error", text)
                    else: status_callback("compiling", text)
        
        return_code = process.poll()
        
        # 4. 检查结果
        if os.path.exists(pdf_file): 
            return True, "\n".join(full_log), os.path.abspath(pdf_file)
        else: 
            return False, "\n".join(full_log), None
            
    except Exception as e: return False, str(e), None
# ==========================================
# 🧵 工作线程: 第一阶段 - 生成代码
# ==========================================
class CodeGenerationWorker(QThread):
    log_signal = Signal(str)
    status_signal = Signal(str)
    code_ready_signal = Signal(str, list) # code, missing_images
    finished_signal = Signal(bool, str)
    progress_signal = Signal(int)
    
    def __init__(self, image_paths, prompt_key):
        super().__init__()
        self.image_paths = image_paths
        self.prompt_key = prompt_template_key = prompt_key
        self._is_interrupted = False

    def stop(self):
        self._is_interrupted = True
        self.requestInterruption()

    def run(self):
        try:
            self.progress_signal.emit(10)
            self.log_signal.emit("🚀 [阶段1] 开始处理图片...")
            
            api_key = config.get("api_key").strip()
            if not api_key:
                self.finished_signal.emit(False, "API Key 未配置")
                return

            img_objects = []
            provider = config.get("provider")
            for p in self.image_paths:
                if self.isInterruptionRequested(): return
                if provider == "Google Gemini": img_objects.append(Image.open(p))
                else: img_objects.append(f"file://{p}")
            
            self.log_signal.emit(f"📡 连接 {provider}...")
            genai.configure(api_key=api_key)
            model_name = config.get("model_name")
            
            base_prompt = config.get("custom_prompts").get(self.prompt_key, DEFAULT_PROMPTS["标准试卷/文档"])
            final_prompt = f"这里有 {len(self.image_paths)} 张图片。\n" + base_prompt
            
            current_code = ""
            
            if provider == "Google Gemini":
                try: model = genai.GenerativeModel(model_name)
                except: model = genai.GenerativeModel('gemini-2.5-flash')
                self.log_signal.emit("⏳ 正在生成代码...")
                response = model.generate_content([final_prompt] + img_objects)
                current_code = response.text
            elif provider == "Alibaba Qwen (通义千问)":
                if not dashscope: self.finished_signal.emit(False, "缺少 dashscope 库"); return
                dashscope.api_key = api_key
                content = [{'text': final_prompt}] + [{'image': img} for img in img_objects]
                self.log_signal.emit("⏳ 正在生成代码...")
                response = dashscope.MultiModalConversation.call(model=model_name, messages=[{'role': 'user', 'content': content}])
                if response.status_code == HTTPStatus.OK: current_code = response.output.choices[0].message.content[0]['text']
                else: self.finished_signal.emit(False, f"Qwen Error: {response.message}"); return

            current_code = current_code.replace("```latex", "").replace("```", "").strip()
            
            # 🔍 正则检查缺少的图片
            missing_images = []
            matches = re.findall(r'\\includegraphics(?:\[.*?\])?\{([^}]+)\}', current_code)
            for m in matches:
                if not os.path.exists(m) and not os.path.isabs(m):
                    missing_images.append(m)
            missing_images = list(set(missing_images))
            
            self.progress_signal.emit(50)
            self.log_signal.emit("✅ 代码生成完毕")
            self.code_ready_signal.emit(current_code, missing_images)

        except Exception as e:
            self.finished_signal.emit(False, str(e))

# ==========================================
# 🧵 工作线程: 第二阶段 - 编译
# ==========================================
class CompileWorker(QThread):
    log_signal = Signal(str)
    status_signal = Signal(str)
    finished_signal = Signal(bool, str, str) # success, path, msg
    progress_signal = Signal(int)

    def __init__(self, code, output_name):
        super().__init__()
        self.code = code
        self.output_name = output_name

    def run(self):
        self.log_signal.emit("⚙️ [阶段2] 开始编译 PDF...")
        self.progress_signal.emit(60)
        
        def status_cb(t, text):
            if t == "downloading": 
                self.status_signal.emit(f"📦 下载环境: {text[:20]}...")
                self.progress_signal.emit(-1)
            else: self.progress_signal.emit(80)

        success, log, pdf_path = run_tectonic(self.code, self.output_name, 
                                              log_callback=lambda x: self.log_signal.emit(x),
                                              status_callback=status_cb)
        
        if success:
            self.progress_signal.emit(100)
            self.finished_signal.emit(True, pdf_path, "编译成功")
        else:
            self.finished_signal.emit(False, "", log)

# ==========================================
# 主界面
# ==========================================
class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI LaTeX 助手 Ultimate (图片填空版)")
        self.resize(1280, 850)
        self.setAcceptDrops(True)
        QApplication.instance().setStyleSheet(DARK_THEME_STYLESHEET)

        if not config.get("api_key"):
            QThread.msleep(100)
            QMessageBox.information(self, "欢迎", "请点击【⚙️ 设置】配置 API Key。")

        main_splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(main_splitter)

        # === 左侧 ===
        left_widget = QWidget(); left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(15,15,15,15); left_layout.setSpacing(10)
        
        top_bar = QHBoxLayout()
        self.btn_settings = QPushButton("⚙️ 设置"); self.btn_settings.setObjectName("actionBtn"); self.btn_settings.setFixedSize(80, 30)
        self.btn_settings.clicked.connect(lambda: SettingsDialog(self).exec())
        lbl_tasks = QLabel("任务队列"); lbl_tasks.setObjectName("headerLabel"); lbl_tasks.setStyleSheet("margin-left: 10px;")
        top_bar.addWidget(self.btn_settings); top_bar.addWidget(lbl_tasks); top_bar.addStretch()
        left_layout.addLayout(top_bar)

        self.btn_add_files = QPushButton("➕ 添加图片"); self.btn_add_files.setObjectName("actionBtn")
        self.btn_add_files.clicked.connect(self.add_files_dialog)
        
        mode_layout = QHBoxLayout(); mode_layout.addWidget(QLabel("模式:"))
        self.combo_mode = QComboBox(); self.combo_mode.addItems(list(DEFAULT_PROMPTS.keys()))
        mode_layout.addWidget(self.combo_mode); left_layout.addLayout(mode_layout)

        self.btn_run_stop = QPushButton("⚡ 开始转换"); self.btn_run_stop.setObjectName("primaryBtn")
        self.btn_run_stop.clicked.connect(self.start_generation)
        self.btn_run_stop.setEnabled(False)

        self.file_list = QListWidget(); self.file_list.setDragDropMode(QListWidget.InternalMove); self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.file_list.itemClicked.connect(self.on_item_clicked)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu); self.file_list.customContextMenuRequested.connect(self.show_context_menu)

        self.progress_bar = QProgressBar(); self.progress_bar.setRange(0, 100); self.progress_bar.setValue(0)
        self.lbl_status = QLabel("就绪")
        
        bottom_tools = QHBoxLayout()
        self.btn_del = QPushButton("❌ 删除"); self.btn_del.setObjectName("dangerBtn"); self.btn_del.clicked.connect(self.delete_selected_items)
        self.btn_clr = QPushButton("🗑️ 清空"); self.btn_clr.clicked.connect(self.clear_list)
        bottom_tools.addWidget(self.btn_del); bottom_tools.addWidget(self.btn_clr)

        left_layout.addWidget(self.btn_add_files); left_layout.addWidget(self.file_list)
        left_layout.addWidget(self.lbl_status); left_layout.addWidget(self.progress_bar)
        left_layout.addWidget(self.btn_run_stop); left_layout.addLayout(bottom_tools)

        # === 右侧 ===
        right_splitter = QSplitter(Qt.Horizontal); right_splitter.setHandleWidth(1)
        
        mid_widget = QWidget(); mid_layout = QVBoxLayout(mid_widget); mid_layout.setContentsMargins(10,15,10,15)
        mid_layout.addWidget(QLabel("EDITOR / 编辑器"))
        self.tabs = QTabWidget()
        self.code_area = QTextEdit()
        self.log_area = QTextEdit(); self.log_area.setReadOnly(True)
        self.tabs.addTab(self.code_area, "代码"); self.tabs.addTab(self.log_area, "日志")
        mid_layout.addWidget(self.tabs)
        
        prev_widget = QWidget(); prev_layout = QVBoxLayout(prev_widget); prev_layout.setContentsMargins(10,15,15,15)
        prev_bar = QHBoxLayout()
        prev_bar.addWidget(QLabel("PREVIEW"))
        prev_bar.addStretch()
        b_out = QPushButton("-"); b_out.setFixedSize(30,25); b_in = QPushButton("+"); b_in.setFixedSize(30,25)
        
        self.pdf_preview = PDFPreviewWidget()
        b_out.clicked.connect(self.pdf_preview.zoom_out); b_in.clicked.connect(self.pdf_preview.zoom_in)
        
        self.btn_open_pdf = QPushButton("📂 系统打开"); self.btn_open_pdf.setObjectName("actionBtn")
        self.btn_open_pdf.clicked.connect(self.open_current_pdf); self.btn_open_pdf.setEnabled(False)

        prev_bar.addWidget(b_out); prev_bar.addWidget(b_in)
        prev_layout.addLayout(prev_bar); prev_layout.addWidget(self.pdf_preview); prev_layout.addWidget(self.btn_open_pdf)

        right_splitter.addWidget(mid_widget); right_splitter.addWidget(prev_widget)
        main_splitter.addWidget(left_widget); main_splitter.addWidget(right_splitter)
        main_splitter.setStretchFactor(0, 250); main_splitter.setStretchFactor(1, 1000)

        self.current_paths = []
        self.current_pdf_path = None
        self.temp_code = ""      # 暂存生成的代码
        self.temp_job_name = ""  # 暂存任务名
        self.load_history_to_ui()

    # --- 第一阶段：生成代码 ---
    def start_generation(self):
        if not self.current_paths: return
        self.btn_run_stop.setEnabled(False)
        self.btn_run_stop.setText("⏳ 生成中...")
        self.log_area.clear(); self.tabs.setCurrentIndex(1)
        
        self.gen_worker = CodeGenerationWorker(self.current_paths, self.combo_mode.currentText())
        self.gen_worker.log_signal.connect(self.log_area.append)
        self.gen_worker.status_signal.connect(self.lbl_status.setText)
        self.gen_worker.progress_signal.connect(self.update_progress)
        self.gen_worker.code_ready_signal.connect(self.on_code_generated)
        self.gen_worker.finished_signal.connect(self.on_gen_failed)
        self.gen_worker.start()

    def on_code_generated(self, code, missing_images):
        self.temp_code = code
        self.code_area.setPlainText(code)
        self.tabs.setCurrentIndex(0)
        self.temp_job_name = f"Merged_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if missing_images:
            self.log_area.append(f"⚠️ 检测到需要 {len(missing_images)} 张外部图片...")
            dlg = ImageMappingDialog(missing_images, self)
            if dlg.exec() == QDialog.Accepted:
                for filename, local_path in dlg.file_map.items():
                    if local_path and os.path.exists(local_path):
                        try:
                            shutil.copy(local_path, filename) 
                            self.log_area.append(f"✅ 已准备图片: {filename}")
                        except Exception as e:
                            self.log_area.append(f"❌ 复制图片失败: {e}")
                self.start_compilation()
            else:
                self.lbl_status.setText("已取消编译")
                self.btn_run_stop.setText("⚡ 开始转换"); self.btn_run_stop.setEnabled(True)
        else:
            self.start_compilation()

    def on_gen_failed(self, success, msg):
        if not success:
            QMessageBox.warning(self, "错误", msg)
            self.btn_run_stop.setText("⚡ 开始转换"); self.btn_run_stop.setEnabled(True)

    # --- 第二阶段：编译 PDF ---
    def start_compilation(self):
        self.btn_run_stop.setText("⚙️ 编译中...")
        self.compile_worker = CompileWorker(self.temp_code, self.temp_job_name)
        self.compile_worker.log_signal.connect(self.log_area.append)
        self.compile_worker.status_signal.connect(self.lbl_status.setText)
        self.compile_worker.progress_signal.connect(self.update_progress)
        self.compile_worker.finished_signal.connect(self.on_compile_finished)
        self.compile_worker.start()

    def on_compile_finished(self, success, pdf_path, msg):
        self.btn_run_stop.setText("⚡ 开始转换"); self.btn_run_stop.setEnabled(True)
        self.progress_bar.setValue(100 if success else 0)
        
        if success:
            self.current_pdf_path = pdf_path
            self.pdf_preview.load_pdf(pdf_path)
            self.btn_open_pdf.setEnabled(True)
            
            hist = {
                "date": datetime.datetime.now().strftime("%m-%d %H:%M"),
                "name": f"批量({len(self.current_paths)})",
                "pdf": pdf_path, "code": self.temp_code
            }
            save_history(hist)
            self.load_history_to_ui()
            self.current_paths = []
            self.file_list.clear()
            
            QMessageBox.information(self, "成功", "PDF 生成成功！")
        else:
            QMessageBox.warning(self, "失败", f"编译失败，请查看日志。\n{msg}")

    # --- 通用 UI 逻辑 ---
    def update_progress(self, val):
        if val == -1: self.progress_bar.setRange(0,0)
        else: self.progress_bar.setRange(0,100); self.progress_bar.setValue(val)

    def add_files_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选图", "", "Images (*.png *.jpg *.jpeg)")
        if files: self.add_files(files)
    def add_files(self, files):
        for f in files:
            if f not in self.current_paths:
                self.current_paths.append(f)
                item = QListWidgetItem(f"🖼️ {os.path.basename(f)}")
                item.setData(Qt.UserRole, {"type":"file", "path":f})
                self.file_list.addItem(item)
        self.btn_run_stop.setEnabled(bool(self.current_paths))
    
    def on_item_clicked(self, item):
        d = item.data(Qt.UserRole)
        if d and d['type']=='history':
            self.code_area.setPlainText(d['code'])
            if os.path.exists(d['pdf']): 
                self.pdf_preview.load_pdf(d['pdf'])
                self.current_pdf_path = d['pdf']
                self.btn_open_pdf.setEnabled(True)

    def open_current_pdf(self):
        if self.current_pdf_path: os.startfile(self.current_pdf_path)

    def dragEnterEvent(self, e): e.accept() if e.mimeData().hasUrls() else e.ignore()
    def dropEvent(self, e):
        files = [u.toLocalFile() for u in e.mimeData().urls()]
        imgs = [f for f in files if f.lower().endswith(('.png','.jpg','.jpeg'))]
        if imgs: self.add_files(imgs)

    def load_history_to_ui(self):
        self.file_list.clear()
        for f in self.current_paths:
            item = QListWidgetItem(f"🖼️ {os.path.basename(f)}")
            item.setData(Qt.UserRole, {"type":"file", "path":f})
            self.file_list.addItem(item)
            
        history = load_history()
        if history:
            sep = QListWidgetItem("--- 历史 ---"); sep.setFlags(Qt.NoItemFlags); sep.setTextAlignment(Qt.AlignCenter)
            self.file_list.addItem(sep)
            for h in history:
                item = QListWidgetItem(f"📜 {h.get('name','Doc')} - {h['date']}")
                h['type'] = 'history'
                item.setData(Qt.UserRole, h)
                self.file_list.addItem(item)

    # 删除逻辑
    def show_context_menu(self, pos):
        menu = QMenu(self); act = menu.addAction("删除"); act.triggered.connect(self.delete_selected_items)
        menu.exec(self.file_list.mapToGlobal(pos))
    def delete_selected_items(self):
        items = self.file_list.selectedItems()
        if not items: return
        if QMessageBox.question(self, "确认", "确定删除吗？历史记录文件也将被物理删除。") == QMessageBox.No: return
        
        to_remove_pdf = []
        for item in items:
            d = item.data(Qt.UserRole)
            if not d: continue
            if d['type'] == 'history':
                if d.get('pdf'): to_remove_pdf.append(d['pdf'])
            elif d['type'] == 'file':
                if d['path'] in self.current_paths: self.current_paths.remove(d['path'])
            self.file_list.takeItem(self.file_list.row(item))
        
        if to_remove_pdf: delete_history_records(to_remove_pdf)
        self.btn_run_stop.setEnabled(bool(self.current_paths))
    def clear_list(self):
        self.current_paths = []
        self.load_history_to_ui()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec())