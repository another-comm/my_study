import sys
import os
import subprocess
import json
import datetime
import socket
import re
import shutil
from PIL import Image
import google.generativeai as genai

# 引入 PySide6 界面库
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QTextEdit, QLabel, 
                               QFileDialog, QMessageBox, QProgressBar, QTabWidget,
                               QListWidget, QListWidgetItem, QSplitter, QMenu, QScrollArea,
                               QSizePolicy, QComboBox, QDialog, QFormLayout, QLineEdit, QGroupBox, QCheckBox,
                               QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QDialogButtonBox)
from PySide6.QtCore import QThread, Signal, Qt, QSize, QMimeData
from PySide6.QtGui import QImage, QPixmap, QRegion, QCursor, QIcon, QColor, QTextCursor, QDragEnterEvent, QDropEvent

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
# ⚙️ 配置管理
# ==========================================
CONFIG_FILE = "config.json"
HISTORY_FILE = "history_data.json"

INTERNAL_API_KEY = "AIzaSyBjsq1zAg7O2xunwiPJaLIf5HiJ1h9-DnI"

# ✅ 重点修改：细化 tabularx 语法，并禁止特殊字符
DEFAULT_PROMPTS = {
    "标准试卷/文档": """
你是一个顶级的 LaTeX 排版专家。请将提供的图片内容识别并合并转换为一个排版精美、专业的 LaTeX 文档。

**排版核心要求**：
1. **文档类与版面**：
   - 使用 `\\documentclass[12pt, a4paper]{article}`。
   - 使用 `\\usepackage[margin=2cm]{geometry}`。
2. **必备宏包**：
   - 数学：`amsmath, amssymb`
   - 图片：`graphicx, float`
   - 表格：`booktabs, array, tabularx, longtable, multirow, adjustbox` (⚠️必须包含 tabularx)。
   - 中文支持：**必须仅使用 `\\usepackage{ctex}`**。
3. **防止溢出与报错规则(⚠️严格执行)**：
   - **图片**：所有 `\\includegraphics` **必须**带上参数 `[width=\\linewidth]`。
   - **表格（重点优化）**：
     - **优先使用 `tabularx` 环境**。
     - **语法警告**：必须指定宽度参数！
       - ✅ 正确：`\\begin{tabularx}{\\linewidth}{|c|X|c|}` (注意 `{\\linewidth}` 不能少)
       - ❌ 错误：`\\begin{tabularx}{|c|X|c|}` (会导致 Missing number 报错)
     - 列格式中使用 `X` 来自动换行。
   - **特殊符号处理**：
     - **禁止使用** ⭕ 数字符号（如 ①, ②...），因为这极易导致编译失败。
     - 请替换为普通文本格式：(1), (2) 或 1., 2.。
4. **输出格式**：只返回纯 LaTeX 代码，不要 Markdown 标记。
""",

    "读书笔记/摘要": """
你是一个高效的笔记整理助手。请识别图片内容，并整理成一份结构清晰的 LaTeX 读书笔记。
**核心要求**：
1. **文档类**：`article`。
2. **中文支持**：使用 `\\usepackage{ctex}`。
3. **防止溢出**：
   - 图片：一律使用 `[width=\\linewidth]`。
   - 表格：使用 `tabularx` 环境，且必须指定 `{\\linewidth}` 宽度。
4. **符号清洗**：将 ①, ② 等特殊符号替换为 (1), (2)。
5. **输出**：只返回纯代码。
""",

    "纯公式提取": """
请只提取图片中的所有数学公式。
**核心要求**：
1. **文档类**：`article`。
2. **中文支持**：使用 `\\usepackage{ctex}`。
3. **内容**：只保留公式，使用 `align*` 环境。
4. **输出**：只返回纯代码。
"""
}

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
                    if "custom_prompts" not in self.data: 
                        self.data["custom_prompts"] = DEFAULT_PROMPTS
                    else:
                         # 确保 Prompt 更新生效，同时保留用户自定义
                        for k, v in DEFAULT_PROMPTS.items():
                            if k not in self.data["custom_prompts"]:
                                self.data["custom_prompts"][k] = v
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
QFrame#chatSeparator { border: 1px solid #3E3E42; border-radius: 0px; background-color: #3E3E42; }
QLabel#attachmentLabel { background-color: #333; border: 1px solid #444; border-radius: 4px; padding: 2px 6px; color: #81ecec; font-size: 12px; margin-bottom: 4px; }
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

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: return []
    return []

def save_history(record):
    history = load_history()
    existing_index = -1
    for i, h in enumerate(history):
        if h.get('pdf') == record.get('pdf'):
            existing_index = i
            break
    if existing_index != -1:
        history[existing_index] = record 
        item = history.pop(existing_index)
        history.insert(0, item)
    else:
        history.insert(0, record)
    if len(history) > 50: history = history[:50]
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except: pass

def delete_history_records(pdf_paths_to_remove):
    history = load_history()
    new_history = []
    for h in history:
        path = h.get('pdf') or h.get('pdf_path')
        if path in pdf_paths_to_remove:
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

def sanitize_latex_code(code):
    code = re.sub(r'\\includegraphics\{([^}]+)\}', r'\\includegraphics[width=\\linewidth]{\1}', code)
    code = code.replace(r'\usepackage[fontset=windows]{ctex}', r'\usepackage{ctex}')
    code = code.replace(r'\usepackage[fontset=ubuntu]{ctex}', r'\usepackage{ctex}')
    code = code.replace("```latex", "").replace("```", "").strip()
    replacements = {
        '①': '(1)', '②': '(2)', '③': '(3)', '④': '(4)', '⑤': '(5)',
        '⑥': '(6)', '⑦': '(7)', '⑧': '(8)', '⑨': '(9)', '⑩': '(10)',
        '⑪': '(11)', '⑫': '(12)', '⑬': '(13)', '⑭': '(14)', '⑮': '(15)',
        '⑯': '(16)', '⑰': '(17)', '⑱': '(18)', '⑲': '(19)', '⑳': '(20)',
        '●': '$\\bullet$', '○': '$\\circ$', '■': '$\\blacksquare$'
    }
    for k, v in replacements.items():
        code = code.replace(k, v)
    return code

# ==========================================
# 📝 提示词编辑器
# ==========================================
class PromptEditorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📝 对话指令编辑器")
        self.resize(700, 500)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("选择指令模式:"))
        self.combo_prompts = QComboBox()
        self.combo_prompts.addItems(list(DEFAULT_PROMPTS.keys()))
        self.combo_prompts.currentTextChanged.connect(self.load_prompt_text)
        top_layout.addWidget(self.combo_prompts)
        top_layout.addStretch()
        
        self.btn_reset = QPushButton("🔄 初始化/重置")
        self.btn_reset.setToolTip("将当前模式的指令恢复为代码默认值")
        self.btn_reset.clicked.connect(self.reset_current_prompt)
        top_layout.addWidget(self.btn_reset)
        
        layout.addLayout(top_layout)
        
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("在此编辑提示词...")
        layout.addWidget(self.editor)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.save_and_close)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        
        # 初始加载
        self.load_prompt_text(self.combo_prompts.currentText())

    def load_prompt_text(self, key):
        current_prompts = config.get("custom_prompts")
        if key in current_prompts:
            self.editor.setPlainText(current_prompts[key])
        else:
            self.editor.setPlainText(DEFAULT_PROMPTS.get(key, ""))

    def reset_current_prompt(self):
        key = self.combo_prompts.currentText()
        if key in DEFAULT_PROMPTS:
            self.editor.setPlainText(DEFAULT_PROMPTS[key])
            QMessageBox.information(self, "提示", "已恢复为默认指令（需点击 Save 保存生效）。")

    def save_and_close(self):
        key = self.combo_prompts.currentText()
        text = self.editor.toPlainText()
        current_prompts = config.get("custom_prompts")
        current_prompts[key] = text
        config.set("custom_prompts", current_prompts)
        self.accept()

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
# 设置与预览组件 (修改版)
# ==========================================
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ 设置")
        self.resize(600, 450) # 稍微宽一点
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # --- AI 服务设置组 ---
        group_api = QGroupBox("🤖 AI 服务设置")
        form_api = QFormLayout()
        
        self.combo_provider = QComboBox()
        self.combo_provider.addItems(["Google Gemini", "Alibaba Qwen (通义千问)"])
        self.combo_provider.setCurrentText(config.get("provider", "Google Gemini"))
        
        self.input_key = QLineEdit(config.get("api_key"))
        self.input_key.setEchoMode(QLineEdit.Password)
        
        # --- 模型选择区域 (修改部分) ---
        model_layout = QHBoxLayout()
        self.combo_model = QComboBox()
        self.combo_model.setEditable(True)
        self.combo_model.setMinimumWidth(300)
        
        # 增加一个刷新按钮
        self.btn_refresh_models = QPushButton("🔄 获取云端列表")
        self.btn_refresh_models.setToolTip("使用当前 API Key 获取 Google 实际可用的模型列表")
        self.btn_refresh_models.clicked.connect(self.fetch_google_models)
        
        model_layout.addWidget(self.combo_model)
        model_layout.addWidget(self.btn_refresh_models)
        
        # 初始化现有值
        current_model = config.get("model_name", "gemini-2.0-flash")
        self.combo_model.addItem(current_model)
        self.combo_model.setCurrentText(current_model)

        form_api.addRow("服务商:", self.combo_provider)
        form_api.addRow("API Key:", self.input_key)
        form_api.addRow("模型:", model_layout) # 使用 Layout 替代单一控件
        
        group_api.setLayout(form_api)
        layout.addWidget(group_api)
        
        # ... (后续网络设置和保存按钮代码保持不变) ...
        # --- 网络连接设置组 ---
        group_net = QGroupBox("🌐 网络连接")
        form_net = QFormLayout()
        self.chk_auto_proxy = QCheckBox("自动检测代理")
        self.chk_auto_proxy.setChecked(config.get("auto_proxy"))
        self.input_proxy = QLineEdit(config.get("proxy_url"))
        self.chk_auto_proxy.toggled.connect(lambda: self.input_proxy.setEnabled(not self.chk_auto_proxy.isChecked()))
        form_net.addRow(self.chk_auto_proxy)
        form_net.addRow("代理地址:", self.input_proxy)
        group_net.setLayout(form_net)
        layout.addWidget(group_net)
        self.input_proxy.setEnabled(not self.chk_auto_proxy.isChecked())

        btn_box = QHBoxLayout()
        btn_save = QPushButton("保存"); btn_save.setObjectName("primaryBtn")
        btn_save.clicked.connect(self.save_settings)
        btn_cancel = QPushButton("取消"); btn_cancel.clicked.connect(self.reject)
        btn_box.addStretch(); btn_box.addWidget(btn_cancel); btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def fetch_google_models(self):
        """主动从 Google API 获取模型列表"""
        api_key = self.input_key.text().strip()
        if not api_key:
            QMessageBox.warning(self, "错误", "请先填写 API Key")
            return

        if self.combo_provider.currentText() != "Google Gemini":
            QMessageBox.information(self, "提示", "目前仅支持获取 Google Gemini 模型列表")
            return

        self.btn_refresh_models.setText("正在获取...")
        self.btn_refresh_models.setEnabled(False)
        QApplication.processEvents() # 强制刷新界面

        try:
            # 临时配置代理 (如果界面上填了)
            proxy_url = self.input_proxy.text().strip()
            if not self.chk_auto_proxy.isChecked() and proxy_url:
                os.environ["HTTP_PROXY"] = proxy_url
                os.environ["HTTPS_PROXY"] = proxy_url
            
            genai.configure(api_key=api_key)
            
            # 获取列表
            found_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    # 去掉 'models/' 前缀，界面显示更清爽
                    name = m.name.replace("models/", "")
                    found_models.append(name)
            
            if found_models:
                self.combo_model.clear()
                self.combo_model.addItems(found_models)
                QMessageBox.information(self, "成功", f"成功获取 {len(found_models)} 个可用模型！\n请在下拉框中选择。")
            else:
                QMessageBox.warning(self, "提示", "未找到支持文本生成的模型。")
                
        except Exception as e:
            QMessageBox.critical(self, "获取失败", f"连接 API 失败：\n{str(e)}")
        finally:
            self.btn_refresh_models.setText("🔄 获取云端列表")
            self.btn_refresh_models.setEnabled(True)

    def save_settings(self):
        # ... (保存逻辑保持不变) ...
        config.set("provider", self.combo_provider.currentText())
        config.set("api_key", self.input_key.text().strip())
        config.set("model_name", self.combo_model.currentText().strip()) # 直接取当前文本
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
# 💬 支持拖拽的聊天窗口组件
# ==========================================
class ChatWidget(QWidget):
    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 10, 0, 0)
        
        # 分割线
        sep = QFrame(); sep.setObjectName("chatSeparator"); sep.setFrameShape(QFrame.HLine); sep.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(sep)
        
        chat_header = QLabel("💬 AI 对话修改 (可拖入文件)")
        chat_header.setStyleSheet("color: #6C5CE7; font-weight: bold; margin-top: 5px;")
        self.layout.addWidget(chat_header)
        
        self.chat_history = QTextEdit(); self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("background-color: #252526; border: 1px solid #3E3E42; border-radius: 4px; padding: 5px;")
        
        # 📎 附件预览区
        self.attachment_widget = QWidget()
        self.attachment_layout = QHBoxLayout(self.attachment_widget)
        self.attachment_layout.setContentsMargins(0,0,0,0)
        self.attachment_label = QLabel("")
        self.attachment_label.setObjectName("attachmentLabel")
        self.attachment_label.setVisible(False)
        self.attachment_layout.addWidget(self.attachment_label)
        self.attachment_layout.addStretch()
        self.layout.addWidget(self.attachment_widget)

        chat_input_box = QHBoxLayout()
        self.btn_attach = QPushButton("📎")
        self.btn_attach.setFixedSize(30, 30)
        self.btn_attach.setToolTip("上传图片或文档")
        
        self.chat_input = QLineEdit(); self.chat_input.setPlaceholderText("例如：把标题字体改大一点，或者把这张图放在下面...")
        self.btn_send = QPushButton("发送 / 修改"); self.btn_send.setObjectName("actionBtn")
        
        chat_input_box.addWidget(self.btn_attach)
        chat_input_box.addWidget(self.chat_input)
        chat_input_box.addWidget(self.btn_send)
        
        self.layout.addWidget(self.chat_history)
        self.layout.addLayout(chat_input_box)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.files_dropped.emit(files)
            event.accept()

# ==========================================
# 🔨 编译逻辑
# ==========================================
def run_tectonic(tex_code, output_name, log_callback=None, status_callback=None):
    tectonic_path = get_resource_path("tectonic.exe")
    if not os.path.exists(tectonic_path): return False, "❌ 找不到 tectonic.exe", None
    
    tex_file = f"{output_name}.tex"
    pdf_file = f"{output_name}.pdf"
    
    try:
        with open(tex_file, "w", encoding="utf-8") as f: f.write(tex_code)
    except Exception as e: return False, str(e), None

    cmd = [tectonic_path, tex_file]
    env = os.environ.copy()
    if 'FANDOL_PATH' in env: del env['FANDOL_PATH']
    
    try:
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            encoding='utf-8', 
            errors='replace', 
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
                if "Fontconfig error" in text:
                    full_log.append(f"⚠️ [忽略] {text}")
                    continue
                if "Overfull" in text:
                    full_log.append(f"⚠️ [排版溢出] {text[:50]}...")
                else:
                    full_log.append(text)
                
                if log_callback: 
                    if "Overfull" in text: log_callback(f"⚠️ 警告: 内容溢出")
                    else: log_callback(text)
                
                if status_callback:
                    if "downloading" in text.lower(): status_callback("downloading", text)
                    elif "error" in text.lower() and "fontconfig" not in text.lower() and "overfull" not in text.lower(): 
                        status_callback("error", text)
                    else: status_callback("compiling", text)
        
        return_code = process.poll()
        
        if os.path.exists(pdf_file): 
            return True, "\n".join(full_log), os.path.abspath(pdf_file)
        else: 
            return False, "\n".join(full_log), None
            
    except Exception as e: return False, str(e), None

# ==========================================
# 🧵 工作线程
# ==========================================
class CodeGenerationWorker(QThread):
    log_signal = Signal(str)
    status_signal = Signal(str)
    code_ready_signal = Signal(str, list) 
    finished_signal = Signal(bool, str)
    progress_signal = Signal(int)
    
    def __init__(self, image_paths, prompt_key, is_refine=False, base_code="", user_instruction="", additional_files=None):
        super().__init__()
        self.image_paths = image_paths
        self.prompt_key = prompt_key
        self.is_refine = is_refine
        self.base_code = base_code
        self.user_instruction = user_instruction
        self.additional_files = additional_files or []
        self._is_interrupted = False

    def stop(self):
        self._is_interrupted = True
        self.requestInterruption()

    def extract_text_content(self, path):
        """从文档中提取文本内容"""
        ext = os.path.splitext(path)[1].lower()
        content = ""
        try:
            if ext == '.pdf':
                if fitz:
                    with fitz.open(path) as doc:
                        for page in doc: content += page.get_text() + "\n"
                else:
                    return "[PDF读取失败: 缺少 PyMuPDF]"
            elif ext in ['.txt', '.md', '.tex', '.json', '.log']:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            else:
                return f"[未知的文本格式: {ext}]"
        except Exception as e:
            return f"[读取错误: {str(e)}]"
        return content[:10000]  # 限制长度防止 token 溢出

    def run(self):
        try:
            self.progress_signal.emit(10)
            
            api_key = config.get("api_key").strip()
            if not api_key:
                self.finished_signal.emit(False, "API Key 未配置")
                return

            img_objects = []
            text_context = ""
            provider = config.get("provider")
            
            # 1. 处理主文件列表（区分图片和文档）
            for p in self.image_paths:
                if self.isInterruptionRequested(): return
                ext = os.path.splitext(p)[1].lower()
                if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.webp']:
                    if provider == "Google Gemini": img_objects.append(Image.open(p))
                    else: img_objects.append(f"file://{p}")
                else:
                    # 非图片文件，尝试提取文本
                    self.log_signal.emit(f"📖 读取文档内容: {os.path.basename(p)}...")
                    text_context += f"\n\n--- 文档附件: {os.path.basename(p)} ---\n{self.extract_text_content(p)}\n----------------\n"

            # 2. 处理对话附件（与主列表逻辑类似）
            new_image_names = []
            for p in self.additional_files:
                ext = os.path.splitext(p)[1].lower()
                if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.webp']:
                    if provider == "Google Gemini": img_objects.append(Image.open(p))
                    else: img_objects.append(f"file://{p}")
                    new_image_names.append(os.path.basename(p))
                else:
                    text_context += f"\n\n--- 对话附件: {os.path.basename(p)} ---\n{self.extract_text_content(p)}\n----------------\n"
            
            self.log_signal.emit(f"📡 连接 {provider}...")
            genai.configure(api_key=api_key)
            model_name = config.get("model_name")
            
            # ✅ 构建 Prompt
            if self.is_refine:
                self.log_signal.emit("🧠 [阶段1] 正在根据您的要求修改代码...")
                
                extra_instruction = ""
                if new_image_names:
                    extra_instruction = f"\n\n**图片附件提示**: 用户本次对话上传了新图片: {', '.join(new_image_names)}。如果用户要求插入这些图片，请使用这些文件名作为 \\includegraphics 的参数。"
                
                final_prompt = f"""
你是一个 LaTeX 专家。用户希望修改以下现有的 LaTeX 代码。
请根据用户的要求，**只修改必要的部分**，保持文档整体结构完整。

**现有代码**:
```latex
{self.base_code}
```

**用户修改要求**:
{self.user_instruction}
{extra_instruction}

**参考文档内容**:
{text_context}

**指令**:
1. 输出完整的、可编译的 LaTeX 代码。
2. 不要省略未修改的部分。
3. 保持 `ctex` 和 `adjustbox` 等关键包的引用。
4. **表格处理（防止溢出）**：
   - 如果用户修改涉及表格，**优先使用 `tabularx`**，并设置宽度为 `\\linewidth`，将长文本列设为 `X`。
5. **特殊字符**：
   - 检查并替换 ①, ② 为 (1), (2)，防止编译错误。
6. **只输出纯代码**。
"""
            else:
                self.log_signal.emit("🚀 [阶段1] 开始生成代码...")
                # 从配置中读取（此时可能已被 PromptEditor 修改）
                base_prompt = config.get("custom_prompts").get(self.prompt_key, DEFAULT_PROMPTS["标准试卷/文档"])
                final_prompt = f"这里有 {len(img_objects)} 张图片资源。\n"
                if text_context:
                    final_prompt += f"以下是参考文档内容：\n{text_context}\n"
                final_prompt += base_prompt
            
            current_code = ""
            
            if provider == "Google Gemini":
                try: model = genai.GenerativeModel(model_name)
                except: model = genai.GenerativeModel('gemini-2.5-flash')
                self.log_signal.emit("⏳ AI 思考中...")
                response = model.generate_content([final_prompt] + img_objects)
                current_code = response.text
            elif provider == "Alibaba Qwen (通义千问)":
                if not dashscope: self.finished_signal.emit(False, "缺少 dashscope 库"); return
                dashscope.api_key = api_key
                # Qwen 接受 content list，包含 text 和 image url
                content_list = [{'text': final_prompt}] + [{'image': img} for img in img_objects if isinstance(img, str)] 
                # 注意：如果是 Gemini PIL Image 对象，Qwen API 处理方式不同，这里简化处理只支持 url 路径
                
                self.log_signal.emit("⏳ AI 思考中...")
                response = dashscope.MultiModalConversation.call(model=model_name, messages=[{'role': 'user', 'content': content_list}])
                if response.status_code == HTTPStatus.OK: current_code = response.output.choices[0].message.content[0]['text']
                else: self.finished_signal.emit(False, f"Qwen Error: {response.message}"); return

            current_code = sanitize_latex_code(current_code)
            
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
        self.setWindowTitle("AI LaTeX 助手 Ultimate (Chat + Docs)")
        self.resize(1400, 900)
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
        lbl_tasks = QLabel("文件队列"); lbl_tasks.setObjectName("headerLabel"); lbl_tasks.setStyleSheet("margin-left: 10px;")
        top_bar.addWidget(self.btn_settings); top_bar.addWidget(lbl_tasks); top_bar.addStretch()
        left_layout.addLayout(top_bar)

        self.btn_add_files = QPushButton("➕ 添加文件 (图片/文档)"); self.btn_add_files.setObjectName("actionBtn")
        self.btn_add_files.clicked.connect(self.add_files_dialog)
        
        mode_layout = QHBoxLayout(); 
        mode_layout.addWidget(QLabel("模式:"))
        self.combo_mode = QComboBox(); self.combo_mode.addItems(list(DEFAULT_PROMPTS.keys()))
        # 增加编辑指令按钮
        self.btn_edit_prompt = QPushButton("✏️")
        self.btn_edit_prompt.setFixedSize(30, 30)
        self.btn_edit_prompt.setToolTip("编辑当前对话指令")
        self.btn_edit_prompt.clicked.connect(lambda: PromptEditorDialog(self).exec())
        
        mode_layout.addWidget(self.combo_mode)
        mode_layout.addWidget(self.btn_edit_prompt)
        left_layout.addLayout(mode_layout)

        self.btn_run_stop = QPushButton("⚡ 开始转换"); self.btn_run_stop.setObjectName("primaryBtn")
        self.btn_run_stop.clicked.connect(self.start_initial_generation)
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

        # === 中间 (编辑器 + 聊天) ===
        mid_splitter = QSplitter(Qt.Vertical)
        mid_splitter.setHandleWidth(1)
        
        # 上半部分：编辑器
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget); editor_layout.setContentsMargins(0,0,0,0)
        
        editor_tools = QHBoxLayout()
        editor_tools.addWidget(QLabel("EDITOR / 编辑器"))
        editor_tools.addStretch()
        self.btn_manual_compile = QPushButton("🛠️ 手动编译")
        self.btn_manual_compile.setToolTip("修改代码后点击此按钮重新生成 PDF")
        self.btn_manual_compile.clicked.connect(self.manual_compile)
        editor_tools.addWidget(self.btn_manual_compile)
        editor_layout.addLayout(editor_tools)

        self.tabs = QTabWidget()
        self.code_area = QTextEdit()
        self.log_area = QTextEdit(); self.log_area.setReadOnly(True)
        self.tabs.addTab(self.code_area, "代码"); self.tabs.addTab(self.log_area, "日志")
        editor_layout.addWidget(self.tabs)
        mid_splitter.addWidget(editor_widget)

        # 下半部分：聊天框 (改为自定义 ChatWidget 以支持独立拖拽)
        self.chat_widget = ChatWidget()
        self.chat_widget.files_dropped.connect(self.handle_chat_drop)
        self.chat_widget.btn_attach.clicked.connect(self.select_chat_attachment)
        self.chat_widget.btn_send.clicked.connect(self.send_chat_message)
        self.chat_widget.chat_input.returnPressed.connect(self.send_chat_message)
        
        # 禁用初始状态
        self.chat_widget.chat_input.setEnabled(False)
        self.chat_widget.btn_send.setEnabled(False)
        self.chat_widget.btn_attach.setEnabled(False)
        
        mid_splitter.addWidget(self.chat_widget)
        mid_splitter.setStretchFactor(0, 7) 
        mid_splitter.setStretchFactor(1, 3) 

        # === 右侧 (预览) ===
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

        main_splitter.addWidget(left_widget); main_splitter.addWidget(mid_splitter); main_splitter.addWidget(prev_widget)
        main_splitter.setStretchFactor(0, 200); main_splitter.setStretchFactor(1, 400); main_splitter.setStretchFactor(2, 500)

        self.current_paths = []
        self.selected_chat_files = [] 
        self.last_uploaded_files = [] 
        self.current_pdf_path = None
        self.temp_code = ""  
        self.temp_job_name = "" 
        self.load_history_to_ui()

    # 主窗口的拖拽（如果不小心拖到聊天框外，默认为添加到主列表）
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls(): e.accept()
        else: e.ignore()
        
    def dropEvent(self, e):
        files = [u.toLocalFile() for u in e.mimeData().urls()]
        if files: self.add_files(files)

    def add_files_dialog(self):
        # 扩展支持的文件类型
        files, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", 
            "Files (*.png *.jpg *.jpeg *.bmp *.pdf *.txt *.md *.tex)")
        if files: self.add_files(files)

    def add_files(self, files):
        for f in files:
            if f not in self.current_paths:
                self.current_paths.append(f)
                # 根据文件类型显示不同图标
                ext = os.path.splitext(f)[1].lower()
                icon = "🖼️" if ext in ['.png','.jpg','.jpeg','.bmp'] else "📄"
                
                item = QListWidgetItem(f"{icon} {os.path.basename(f)}")
                item.setData(Qt.UserRole, {"type":"file", "path":f})
                self.file_list.addItem(item)
        self.btn_run_stop.setEnabled(bool(self.current_paths))

    # 聊天附件逻辑
    def handle_chat_drop(self, files):
        self.selected_chat_files.extend(files)
        self.update_chat_attachment_label()

    def select_chat_attachment(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择附件", "", "Files (*.png *.jpg *.jpeg *.txt *.md *.tex *.pdf)")
        if files:
            self.selected_chat_files.extend(files)
            self.update_chat_attachment_label()

    def update_chat_attachment_label(self):
        if self.selected_chat_files:
            names = [os.path.basename(f) for f in self.selected_chat_files]
            self.chat_widget.attachment_label.setText(f"📎 已选: {', '.join(names)}")
            self.chat_widget.attachment_label.setVisible(True)
        else:
            self.chat_widget.attachment_label.setVisible(False)

    def send_chat_message(self):
        text = self.chat_widget.chat_input.text().strip()
        if not text and not self.selected_chat_files: return
        
        display_text = text
        if self.selected_chat_files:
            names = [os.path.basename(f) for f in self.selected_chat_files]
            display_text += f" <br><span style='font-size:10px; color:#888;'>[附件: {', '.join(names)}]</span>"
        
        self.append_chat_message("User", display_text)
        self.chat_widget.chat_input.clear()
        self.last_uploaded_files = self.selected_chat_files[:]
        
        self.start_generation_process(is_refine=True, instruction=text, additional_files=self.selected_chat_files)
        
        self.selected_chat_files = []
        self.update_chat_attachment_label()

    def append_chat_message(self, role, text):
        color = "#6C5CE7" if role == "System" else ("#2ecc71" if role == "User" else "#e74c3c")
        self.chat_widget.chat_history.append(f"<span style='color:{color}; font-weight:bold;'>[{role}]</span>: {text}")
        self.chat_widget.chat_history.moveCursor(QTextCursor.End)

    # ... (其余编译、生成、历史记录等逻辑保持不变，仅引用名可能需微调) ...
    
    def manual_compile(self):
        code = self.code_area.toPlainText()
        if not code.strip(): 
            QMessageBox.warning(self, "提示", "编辑器为空")
            return

        self.temp_code = code
        self.toggle_inputs(False)
        self.log_area.clear()
        self.tabs.setCurrentIndex(1)
        
        if not self.temp_job_name:
             self.temp_job_name = f"Manual_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        missing_images = []
        matches = re.findall(r'\\includegraphics(?:\[.*?\])?\{([^}]+)\}', code)
        for m in matches:
            if not os.path.exists(m) and not os.path.isabs(m):
                missing_images.append(m)
        missing_images = list(set(missing_images))

        if missing_images:
            self.log_area.append(f"⚠️ 手动编译检测到缺图: {len(missing_images)} 张")
            dlg = ImageMappingDialog(missing_images, self)
            if dlg.exec() == QDialog.Accepted:
                for filename, local_path in dlg.file_map.items():
                    if local_path and os.path.exists(local_path):
                        try:
                            shutil.copy(local_path, filename) 
                            self.log_area.append(f"✅ 已准备图片: {filename}")
                        except Exception as e:
                            self.log_area.append(f"❌ 复制图片失败: {e}")
            else:
                 self.lbl_status.setText("手动编译已取消")
                 self.toggle_inputs(True)
                 return

        self.start_compilation()

    def start_initial_generation(self):
        if not self.current_paths: return
        self.start_generation_process(is_refine=False)

    def start_generation_process(self, is_refine=False, instruction="", additional_files=None):
        self.toggle_inputs(False)
        self.log_area.clear(); self.tabs.setCurrentIndex(1)
        
        if not is_refine:
            self.chat_widget.chat_history.clear()
            self.temp_job_name = f"Merged_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.btn_run_stop.setText("⏳ 生成中...")
        else:
            self.btn_run_stop.setText("🔄 修改中...")
            
        self.gen_worker = CodeGenerationWorker(
            self.current_paths, 
            self.combo_mode.currentText(),
            is_refine=is_refine,
            base_code=self.temp_code,
            user_instruction=instruction,
            additional_files=additional_files
        )
        self.gen_worker.log_signal.connect(self.log_area.append)
        self.gen_worker.status_signal.connect(self.lbl_status.setText)
        self.gen_worker.progress_signal.connect(self.update_progress)
        self.gen_worker.code_ready_signal.connect(self.on_code_generated)
        self.gen_worker.finished_signal.connect(self.on_gen_failed)
        self.gen_worker.start()

    def toggle_inputs(self, enabled):
        self.btn_run_stop.setEnabled(enabled)
        self.chat_widget.chat_input.setEnabled(enabled)
        self.chat_widget.btn_send.setEnabled(enabled)
        self.chat_widget.btn_attach.setEnabled(enabled)
        self.btn_manual_compile.setEnabled(enabled)
        if enabled: self.btn_run_stop.setText("⚡ 开始转换")

    def on_code_generated(self, code, missing_images):
        self.temp_code = code
        self.code_area.setPlainText(code)
        self.tabs.setCurrentIndex(0)

        if missing_images and self.last_uploaded_files:
            still_missing = []
            for missing in missing_images:
                found = False
                for uploaded in self.last_uploaded_files:
                    if os.path.basename(uploaded) == missing:
                        try:
                            shutil.copy(uploaded, missing)
                            self.log_area.append(f"🤖 [智能搬运] 自动复制附件图片: {missing}")
                            found = True
                        except Exception as e:
                            self.log_area.append(f"❌ 自动复制失败: {e}")
                        break
                if not found:
                    still_missing.append(missing)
            missing_images = still_missing

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
                self.toggle_inputs(True)
        else:
            self.start_compilation()

    def on_gen_failed(self, success, msg):
        if not success:
            QMessageBox.warning(self, "错误", msg)
            self.toggle_inputs(True)

    def start_compilation(self):
        self.btn_run_stop.setText("⚙️ 编译中...")
        self.compile_worker = CompileWorker(self.temp_code, self.temp_job_name)
        self.compile_worker.log_signal.connect(self.log_area.append)
        self.compile_worker.status_signal.connect(self.lbl_status.setText)
        self.compile_worker.progress_signal.connect(self.update_progress)
        self.compile_worker.finished_signal.connect(self.on_compile_finished)
        self.compile_worker.start()

    def on_compile_finished(self, success, pdf_path, msg):
        self.toggle_inputs(True)
        self.progress_bar.setValue(100 if success else 0)
        
        if success:
            self.current_pdf_path = pdf_path
            self.pdf_preview.load_pdf(pdf_path)
            self.btn_open_pdf.setEnabled(True)
            self.append_chat_message("System", "PDF 已更新！请输入新的要求继续修改。")
            self.chat_widget.chat_input.setFocus()
            
            hist = {
                "date": datetime.datetime.now().strftime("%m-%d %H:%M"),
                "name": f"批量({len(self.current_paths)})",
                "pdf": pdf_path, "code": self.temp_code
            }
            save_history(hist)
            self.load_history_to_ui()
        else:
            QMessageBox.warning(self, "失败", f"编译失败，请查看日志。\n{msg}")
            self.append_chat_message("System", "编译失败，请检查代码或重试。")

    def update_progress(self, val):
        if val == -1: self.progress_bar.setRange(0,0)
        else: self.progress_bar.setRange(0,100); self.progress_bar.setValue(val)
    
    def on_item_clicked(self, item):
        d = item.data(Qt.UserRole)
        if d and d['type']=='history':
            self.code_area.setPlainText(d['code'])
            self.temp_code = d['code']
            if os.path.exists(d['pdf']): 
                self.pdf_preview.load_pdf(d['pdf'])
                self.current_pdf_path = d['pdf']
                self.btn_open_pdf.setEnabled(True)
                self.toggle_inputs(True)
                base = os.path.basename(d['pdf'])
                self.temp_job_name = os.path.splitext(base)[0]

    def open_current_pdf(self):
        if self.current_pdf_path: os.startfile(self.current_pdf_path)

    def load_history_to_ui(self):
        self.file_list.clear()
        for f in self.current_paths:
            ext = os.path.splitext(f)[1].lower()
            icon = "🖼️" if ext in ['.png','.jpg','.jpeg','.bmp'] else "📄"
            item = QListWidgetItem(f"{icon} {os.path.basename(f)}")
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