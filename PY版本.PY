import sys
import os
import traceback
import json
import requests
import webbrowser
import hashlib
import re

# === 1. 全局崩溃保护 ===
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    try:
        with open("错误日志.txt", "w", encoding="utf-8") as f:
            f.write(err_msg)
    except:
        pass

sys.excepthook = handle_exception

# === 2. 导入库 ===
try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                 QHBoxLayout, QLabel, QPushButton, QScrollArea, 
                                 QFrame, QMessageBox, QGridLayout, QTextEdit, QDialog)
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
    from PyQt6.QtGui import QPixmap, QIcon, QFont, QCursor
    from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
except ImportError as e:
    print(f"缺少库: {e}")
    sys.exit(1)

# === 3. 核心配置 ===
TARGET_URL = "https://github.com/lystv/fmapp/blob/app/yysd-zl.json"
VERSION_INFO_URL = "https://github.com/lystv/fmapp/blob/app/ok.txt"

HISTORY_FILE = "version_history.json"
LAST_OK_FILE = "last_ok_log.txt"  # 新增：用于存储上一次的ok.txt内容
FONGMI_ICON_URL = "https://raw.githubusercontent.com/lystv/fmapp/img/log/ys.jpg"
CACHE_DIR = "icon_cache"

# === 4. 工具函数 ===
def ensure_cache_dir():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def get_cache_path(url):
    if not url: return None
    hash_name = hashlib.md5(url.encode('utf-8')).hexdigest()
    return os.path.join(CACHE_DIR, hash_name + ".png")

def format_github_raw_url(url):
    if "github.com" in url and "/blob/" in url:
        return url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
    return url

# === 5. 样式表 ===
STYLESHEET = """
QMainWindow { background-color: #f2f3f5; }

QFrame#TopBar {
    background-color: white;
    border-bottom: 1px solid #e5e5e5;
}

QLabel#GroupHeader {
    font-family: "Microsoft YaHei";
    font-size: 16px; 
    font-weight: 900; 
    color: #1f1f1f;
    padding-left: 8px;
    border-left: 5px solid #0078d4;
    margin-top: 20px;
    margin-bottom: 10px;
}

QFrame#GridCard {
    background-color: white; 
    border: 1px solid #e0e0e0;
    border-radius: 6px;
}
QFrame#GridCard:hover {
    border: 1px solid #0078d4;
    background-color: #ffffff;
}

QFrame#GridCard[is_new="true"] {
    border: 2px solid #d93025;
    background-color: #fff8f8;
}

QLabel#GridTitle { font-size: 13px; font-weight: bold; color: #333; }
QLabel#GridVer { font-size: 11px; color: #999; }
QLabel#GridVerNew { font-size: 11px; color: #d93025; font-weight: bold; }

QLabel#TimeLabel {
    font-size: 12px;
    color: #888;
    margin-right: 10px;
    font-family: "Consolas", "Microsoft YaHei";
}
"""

# === 新增：显示更新日志的弹窗 ===
class LogDialog(QDialog):
    def __init__(self, log_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("本次维护更新详情")
        self.resize(500, 400)
        layout = QVBoxLayout(self)
        
        lbl = QLabel("检测到以下变动：")
        lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl)
        
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setText(log_text)
        self.text_area.setStyleSheet("font-family: Consolas, Microsoft YaHei; font-size: 12px; line-height: 1.5;")
        layout.addWidget(self.text_area)
        
        btn = QPushButton("关闭")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

class VersionManager:
    def __init__(self):
        self.history = {}
        self.load()
    
    def load(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except: self.history = {}

    def save(self):
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=4)

    # 仅检查是否是新版本，不更新状态（用于生成报告）
    def is_new_version(self, unique_id, current_version):
        old = self.history.get(unique_id)
        if old is None: return False # 第一次运行不视为更新
        return old != current_version

    # 更新状态
    def update_status(self, unique_id, current_version):
        old = self.history.get(unique_id)
        if old != current_version:
            self.history[unique_id] = current_version
            return True, old
        return False, old

class GridAppCard(QFrame):
    def __init__(self, unique_id, app_data, version_mgr, parent=None):
        super().__init__(parent)
        self.setObjectName("GridCard")
        self.setFixedSize(120, 155)
        
        self.url = app_data.get("url", "")
        self.icon_url = app_data.get("icon", "")
        current_ver = str(app_data.get("version", "v?"))
        
        # 这里直接更新状态，因为在MainWindow渲染前我们已经统计过差异了
        is_new, old_ver = version_mgr.update_status(unique_id, current_ver)
        
        if is_new:
            self.setProperty("is_new", "true")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 10, 6, 6)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 1. 图标
        icon_box = QHBoxLayout()
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(48, 48)
        self.icon_label.setScaledContents(True)
        self.icon_label.setStyleSheet("background-color: transparent;")
        icon_box.addStretch()
        icon_box.addWidget(self.icon_label)
        icon_box.addStretch()
        layout.addLayout(icon_box)

        # 2. 名字
        name_label = QLabel(app_data.get("name", "未命名"))
        name_label.setObjectName("GridTitle")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_metrics = name_label.fontMetrics()
        elided = font_metrics.elidedText(name_label.text(), Qt.TextElideMode.ElideRight, 105)
        name_label.setText(elided)
        layout.addWidget(name_label)

        # 3. 版本号
        ver_label = QLabel(current_ver)
        ver_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if is_new:
            ver_label.setObjectName("GridVerNew")
            ver_label.setText(f"🚀 {current_ver}")
        else:
            ver_label.setObjectName("GridVer")
        layout.addWidget(ver_label)

        layout.addStretch()

        # 4. 按钮
        btn_text = "更新" if is_new else "下载"
        dl_btn = QPushButton(btn_text)
        dl_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        dl_btn.setFixedHeight(28)
        
        if is_new:
            dl_btn.setStyleSheet("""
                QPushButton { background-color: #d93025; color: white; border: none; border-radius: 4px; font-weight: bold; font-size: 12px; }
                QPushButton:hover { background-color: #b31412; }
            """)
        else:
            dl_btn.setStyleSheet("""
                QPushButton { background-color: #0078d4; color: white; border: none; border-radius: 4px; font-weight: bold; font-size: 12px; }
                QPushButton:hover { background-color: #005a9e; }
            """)
            
        dl_btn.clicked.connect(self.download)
        layout.addWidget(dl_btn)

        if self.icon_url: self.load_icon()

    def load_icon(self):
        cache_path = get_cache_path(self.icon_url)
        if os.path.exists(cache_path):
            pixmap = QPixmap(cache_path)
            if not pixmap.isNull():
                self.icon_label.setPixmap(pixmap)
                return
        self.nam = QNetworkAccessManager()
        self.nam.finished.connect(lambda r: self.on_dl(r, cache_path))
        self.nam.get(QNetworkRequest(QUrl(self.icon_url)))

    def on_dl(self, reply, path):
        if reply.error() == 0:
            data = reply.readAll()
            if self.icon_label.setPixmap(QPixmap().loadFromData(data)): pass
            try: 
                with open(path, "wb") as f: f.write(data)
            except: pass
        reply.deleteLater()

    def download(self):
        if self.url: webbrowser.open(self.url)

class DataLoader(QThread):
    # 信号增加：raw_txt_content (ok.txt的原始内容)
    data_loaded = pyqtSignal(list, str, str)
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            # 1. 获取 JSON 列表
            json_url = format_github_raw_url(TARGET_URL)
            resp_json = requests.get(json_url, timeout=30)
            resp_json.raise_for_status()
            data_list = resp_json.json()

            # 2. 获取 ok.txt (不仅获取时间，还获取全文)
            txt_url = format_github_raw_url(VERSION_INFO_URL)
            update_time = "时间获取失败"
            raw_txt_content = ""
            
            try:
                resp_txt = requests.get(txt_url, timeout=15)
                if resp_txt.status_code == 200:
                    resp_txt.encoding = 'utf-8'
                    raw_txt_content = resp_txt.text
                    
                    # 提取时间用于显示
                    match = re.search(r"时间 >>\s*(\d{8}-\d{2}:\d{2}:\d{2})", raw_txt_content)
                    if match:
                        raw_time = match.group(1)
                        date_part = f"{raw_time[0:4]}-{raw_time[4:6]}-{raw_time[6:8]}"
                        time_part = raw_time[9:]
                        update_time = f"{date_part} {time_part}"
                    else:
                        # 如果没有匹配到正则，但有内容，可能格式变了，用前20个字符代替
                        if len(raw_txt_content) > 0:
                            update_time = raw_txt_content.strip()[:20]
            except Exception as e:
                print(f"ok.txt 获取失败: {e}")

            self.data_loaded.emit(data_list, update_time, raw_txt_content)

        except Exception as e:
            self.error_occurred.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fongmi 源聚合 (Lystv源)")
        self.resize(950, 750) 
        self.version_mgr = VersionManager()
        self.current_log_content = "" # 存储当前的更新日志
        ensure_cache_dir()
        self.set_window_icon_with_cache(FONGMI_ICON_URL)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        # === 顶部栏 ===
        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        top_bar.setFixedHeight(50)
        tb_layout = QHBoxLayout(top_bar)
        tb_layout.setContentsMargins(20,0,20,0)
        
        # 标题
        title_lbl = QLabel("应用聚合中心")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        
        # 时间标签
        self.time_lbl = QLabel("")
        self.time_lbl.setObjectName("TimeLabel")
        self.time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # 查看更新按钮 (默认隐藏，有更新时显示)
        self.log_btn = QPushButton("📋 查看本次更新")
        self.log_btn.setVisible(False)
        self.log_btn.setFixedSize(110, 30)
        self.log_btn.setStyleSheet("""
            QPushButton { background-color: #fce8e6; border: 1px solid #d93025; border-radius: 4px; color: #d93025; font-weight: bold;}
            QPushButton:hover { background-color: #fad2cf; }
        """)
        self.log_btn.clicked.connect(self.show_update_log)

        # 刷新按钮
        self.refresh_btn = QPushButton("刷新列表")
        self.refresh_btn.setFixedSize(80, 30)
        self.refresh_btn.setStyleSheet("""
            QPushButton { background-color: #fff; border: 1px solid #ccc; border-radius: 4px; color: #333; }
            QPushButton:hover { border: 1px solid #0078d4; color: #0078d4; }
        """)
        self.refresh_btn.clicked.connect(self.start_loading)
        
        tb_layout.addWidget(title_lbl)
        tb_layout.addStretch()
        tb_layout.addWidget(self.log_btn) # 插入更新按钮
        tb_layout.addWidget(self.time_lbl)
        tb_layout.addWidget(self.refresh_btn)
        layout.addWidget(top_bar)

        # 滚动区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background-color: #f2f3f5;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(25, 10, 25, 40)
        self.content_layout.setSpacing(15)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)

        self.start_loading()

    def set_window_icon_with_cache(self, url):
        path = get_cache_path(url)
        if os.path.exists(path):
            self.setWindowIcon(QIcon(path))
            return
        self.inam = QNetworkAccessManager()
        self.inam.finished.connect(lambda r: self.on_wico(r, path))
        self.inam.get(QNetworkRequest(QUrl(url)))
    def on_wico(self, r, p):
        if r.error() == 0:
            d = r.readAll()
            self.setWindowIcon(QIcon(QPixmap().loadFromData(d)))
            try: open(p,"wb").write(d)
            except: pass
        r.deleteLater()

    def start_loading(self):
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("...")
        self.time_lbl.setText("正在获取...")
        self.log_btn.setVisible(False) # 刷新时隐藏日志按钮
        
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        self.loader = DataLoader()
        self.loader.data_loaded.connect(self.on_loaded)
        self.loader.error_occurred.connect(lambda e: QMessageBox.warning(self,"提示",e))
        self.loader.start()

    def on_loaded(self, data, time_str, raw_ok_content):
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("刷新列表")
        self.time_lbl.setText(f"最新维护: {time_str}")
        
        # === 核心逻辑：生成更新报告 ===
        update_report = []
        
        # 1. 检查 ok.txt 内容变动
        old_ok_content = ""
        if os.path.exists(LAST_OK_FILE):
            try:
                with open(LAST_OK_FILE, "r", encoding="utf-8") as f:
                    old_ok_content = f.read()
            except: pass
        
        if old_ok_content.strip() != raw_ok_content.strip():
            # 内容变了，记录下来
            update_report.append(f"【维护公告变更】\n旧：{old_ok_content.strip()[:50]}...\n新：{raw_ok_content.strip()[:50]}...\n")
        
        # 2. 扫描所有 App 检查版本变动
        updated_apps = []
        # 构建ID生成逻辑，必须与 render_group 中的一致
        temp_id_counter = {}
        for cat in data:
            cat_name = cat.get("name", "")
            for app in cat.get("list", []):
                app_name = app.get("name", "")
                base = f"{cat_name}_{app_name}"
                count = temp_id_counter.get(base, 0) + 1
                temp_id_counter[base] = count
                uid = f"{base}#{count}" if count > 1 else base
                
                # 检查版本是否是新的 (注意：这里只检查不更新状态，状态在渲染Card时更新)
                ver = str(app.get("version", ""))
                if self.version_mgr.is_new_version(uid, ver):
                    updated_apps.append(f"• {app_name} ({ver})")
        
        if updated_apps:
            update_report.append("【检测到应用更新】")
            update_report.extend(updated_apps)
        
        # 3. 处理报告结果
        if update_report:
            full_log = "\n".join(update_report)
            full_log += f"\n\n(完整维护信息)\n{raw_ok_content}"
            self.current_log_content = full_log
            self.log_btn.setVisible(True) # 显示按钮
            
            # 保存新的 ok.txt 到本地
            try:
                with open(LAST_OK_FILE, "w", encoding="utf-8") as f:
                    f.write(raw_ok_content)
            except: pass
        else:
            self.current_log_content = "暂无检测到新旧内容变动。\n\n当前维护信息：\n" + raw_ok_content
        
        # === 渲染界面 ===
        for cat in data:
            self.render_group(cat)
        self.version_mgr.save()

    def show_update_log(self):
        dlg = LogDialog(self.current_log_content, self)
        dlg.exec()

    def render_group(self, cat_data):
        name = cat_data.get("name", "")
        apps = cat_data.get("list", [])
        if not apps: return

        header = QLabel(f"{name}")
        header.setObjectName("GroupHeader")
        self.content_layout.addWidget(header)

        grid_container = QWidget()
        grid = QGridLayout(grid_container)
        grid.setContentsMargins(0,0,0,15)
        grid.setSpacing(12)
        grid.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        cols = 6 
        id_counter = {}

        for i, app in enumerate(apps):
            r, c = i // cols, i % cols
            base = f"{name}_{app.get('name')}"
            count = id_counter.get(base, 0) + 1
            id_counter[base] = count
            uid = f"{base}#{count}" if count > 1 else base
            
            card = GridAppCard(uid, app, self.version_mgr)
            grid.addWidget(card, r, c)
            
        self.content_layout.addWidget(grid_container)

if __name__ == "__main__":
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
