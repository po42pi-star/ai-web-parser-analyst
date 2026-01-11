"""
Мониторинг конкурентов - Desktop приложение на PyQt6
"""
import sys
import os
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QLineEdit, QFrame, QScrollArea,
    QFileDialog, QStackedWidget, QSplitter, QMessageBox, QProgressBar,
    QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QFont, QIcon, QDragEnterEvent, QDropEvent
from styles import DARK_THEME
from api_client import api_client

class WorkerThread(QThread):
    """Поток для выполнения API запросов"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class ImageDropZone(QFrame):
    """Зона для drag & drop изображений"""
    fileDropped = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setObjectName("uploadZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(200)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.icon_label = QLabel("📁")
        self.icon_label.setStyleSheet("font-size: 48px;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.text_label = QLabel("Перетащите изображение или нажмите для выбора")
        self.text_label.setStyleSheet("color: #94a3b8; font-size: 14px;")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.hint_label = QLabel("PNG, JPG, GIF, WEBP до 10MB")
        self.hint_label.setStyleSheet("color: #64748b; font-size: 12px;")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.hide()
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        layout.addWidget(self.hint_label)
        layout.addWidget(self.preview_label)
        
        self.selected_file = None
    
    def mousePressEvent(self, event):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение", "", "Изображения (*.png *.jpg *.jpeg *.gif *.webp)"
        )
        if file_path:
            self.set_file(file_path)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("QFrame#uploadZone { border-color: #06b6d4; background-color: rgba(6, 182, 212, 0.1); }")
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet("")
    
    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("")
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                self.set_file(file_path)
    
    def set_file(self, file_path: str):
        self.selected_file = file_path
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(300, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.preview_label.setPixmap(pixmap)
            self.preview_label.show()
            self.icon_label.hide()
            self.text_label.setText(Path(file_path).name)
            self.hint_label.setText("Нажмите для замены")
            self.fileDropped.emit(file_path)
    
    def clear(self):
        self.selected_file = None
        self.preview_label.hide()
        self.icon_label.show()
        self.text_label.setText("Перетащите изображение или нажмите для выбора")
        self.hint_label.setText("PNG, JPG, GIF, WEBP до 10MB")

class PDFDropZone(QFrame):
    """Зона для drag & drop PDF"""
    fileDropped = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setObjectName("uploadZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(150)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.icon_label = QLabel("📄")
        self.icon_label.setStyleSheet("font-size: 48px;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.text_label = QLabel("Перетащите PDF файл или нажмите для выбора")
        self.text_label.setStyleSheet("color: #94a3b8; font-size: 14px;")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.hint_label = QLabel("PDF файлы до 10MB")
        self.hint_label.setStyleSheet("color: #64748b; font-size: 12px;")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.filename_label = QLabel()
        self.filename_label.setStyleSheet("color: #22d3ee; font-size: 14px; font-weight: bold;")
        self.filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.filename_label.hide()
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        layout.addWidget(self.hint_label)
        layout.addWidget(self.filename_label)
        
        self.selected_file = None
    
    def mousePressEvent(self, event):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите PDF файл", "", "PDF (*.pdf)"
        )
        if file_path:
            self.set_file(file_path)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("QFrame#uploadZone { border-color: #06b6d4; background-color: rgba(6, 182, 212, 0.1); }")
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet("")
    
    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("")
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith('.pdf'):
                self.set_file(file_path)
    
    def set_file(self, file_path: str):
        self.selected_file = file_path
        self.filename_label.setText(Path(file_path).name)
        self.filename_label.show()
        self.icon_label.hide()
        self.text_label.hide()
        self.hint_label.hide()
        self.fileDropped.emit(file_path)
    
    def clear(self):
        self.selected_file = None
        self.filename_label.hide()
        self.icon_label.show()
        self.text_label.show()
        self.hint_label.show()

class ResultBlock(QFrame):
    """Блок результата анализа"""
    def __init__(self, title: str, items: list, icon: str = "→"):
        super().__init__()
        self.setObjectName("resultBlock")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        
        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        layout.addWidget(title_label)
        
        for item in items:
            item_label = QLabel(f"{icon} {item}")
            item_label.setWordWrap(True)
            item_label.setStyleSheet("color: #94a3b8; margin-left: 8px; line-height: 1.5;")
            layout.addWidget(item_label)

class ScoreBlock(QFrame):
    """Блок оценки"""
    def __init__(self, title: str, score: int, max_score: int = 10):
        super().__init__()
        self.setObjectName("resultBlock")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        
        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        layout.addWidget(title_label)
        
        # Оценка
        score_layout = QHBoxLayout()
        score_value = QLabel(f"{score}/{max_score}")
        percent = (score / max_score) * 100
        color = "#10b981" if percent >= 70 else "#f59e0b" if percent >= 40 else "#ef4444"
        score_value.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color};")
        score_layout.addWidget(score_value)
        score_layout.addStretch()
        
        # Progress bar
        progress = QProgressBar()
        progress.setRange(0, max_score)
        progress.setValue(score)
        progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: #1e293b;
                border-radius: 4px;
                height: 8px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(progress)
        layout.addLayout(score_layout)

class MainWindow(QMainWindow):
    """Главное окно приложения"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Мониторинг конкурентов | AI Ассистент")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        self.setStyleSheet(DARK_THEME)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.setup_sidebar(main_layout)
        self.setup_content(main_layout)
        
        self.current_worker = None
        self.current_analysis = None  # Для генерации отчётов
        self.check_server_connection()
    
    def setup_sidebar(self, parent_layout):
        """Создание боковой панели"""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(280)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        logo = QLabel("⚡ CompetitorAI")
        logo.setObjectName("logo")
        layout.addWidget(logo)
        
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(12, 16, 12, 16)
        nav_layout.setSpacing(4)
        
        self.nav_buttons = []
        # Порядок: Текст, PDF, Изображения, Парсинг, История
        nav_items = [
            ("📝 Анализ текста", 0),
            ("📄 Анализ PDF", 1),
            ("🖼️ Анализ изображений", 2),
            ("🌐 Парсинг сайта", 3),
            ("📋 История", 4)
        ]
        
        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, idx=index: self.switch_tab(idx))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)
        
        self.nav_buttons[0].setChecked(True)
        nav_layout.addStretch()
        
        self.status_label = QLabel("● Проверка подключения...")
        self.status_label.setStyleSheet("color: #f59e0b; padding: 16px;")
        nav_layout.addWidget(self.status_label)
        layout.addWidget(nav_widget)
        parent_layout.addWidget(sidebar)
    
    def setup_content(self, parent_layout):
        """Создание области контента"""
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 32, 40, 32)
        
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 24)
        
        title = QLabel("Мониторинг конкурентов")
        title.setObjectName("title")
        subtitle = QLabel("AI-ассистент для анализа конкурентной среды")
        subtitle.setObjectName("subtitle")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        content_layout.addWidget(header)
        
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.create_text_tab())      # 0
        self.stacked_widget.addWidget(self.create_pdf_tab())       # 1 - НОВАЯ
        self.stacked_widget.addWidget(self.create_image_tab())     # 2
        self.stacked_widget.addWidget(self.create_parse_tab())     # 3
        self.stacked_widget.addWidget(self.create_history_tab())   # 4
        content_layout.addWidget(self.stacked_widget)
        
        # Results area
        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.hide()
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_scroll.setWidget(self.results_widget)
        content_layout.addWidget(self.results_scroll)
        
        # Loading
        self.loading_widget = QWidget()
        loading_layout = QVBoxLayout(self.loading_widget)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedWidth(300)
        
        self.loading_label = QLabel("Анализирую данные...")
        self.loading_label.setStyleSheet("color: #94a3b8; font-size: 16px;")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        loading_layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)
        loading_layout.addWidget(self.loading_label)
        self.loading_widget.hide()
        content_layout.addWidget(self.loading_widget)
        
        parent_layout.addWidget(content_widget)
    
    def create_text_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel("Анализ текста конкурента")
        title.setObjectName("cardTitle")
        desc = QLabel("Вставьте текст с сайта конкурента, из рекламы или описания продукта")
        desc.setObjectName("cardDescription")
        
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Вставьте текст конкурента для анализа...")
        self.text_input.setMinimumHeight(200)
        
        self.analyze_text_btn = QPushButton("⚡ Проанализировать")
        self.analyze_text_btn.setObjectName("primaryButton")
        self.analyze_text_btn.clicked.connect(self.analyze_text)
        
        card_layout.addWidget(title)
        card_layout.addWidget(desc)
        card_layout.addSpacing(16)
        card_layout.addWidget(self.text_input)
        card_layout.addSpacing(16)
        card_layout.addWidget(self.analyze_text_btn)
        layout.addWidget(card)
        layout.addStretch()
        return widget
    
    def create_pdf_tab(self) -> QWidget:
        """Вкладка анализа PDF"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel("Анализ PDF документов")
        title.setObjectName("cardTitle")
        desc = QLabel("Загрузите PDF файл для извлечения и анализа текста")
        desc.setObjectName("cardDescription")
        
        self.pdf_drop_zone = PDFDropZone()
        self.pdf_drop_zone.fileDropped.connect(self.on_pdf_selected)
        
        self.analyze_pdf_btn = QPushButton("⚡ Проанализировать PDF")
        self.analyze_pdf_btn.setObjectName("primaryButton")
        self.analyze_pdf_btn.clicked.connect(self.analyze_pdf)
        self.analyze_pdf_btn.setEnabled(False)
        
        card_layout.addWidget(title)
        card_layout.addWidget(desc)
        card_layout.addSpacing(16)
        card_layout.addWidget(self.pdf_drop_zone)
        card_layout.addSpacing(16)
        card_layout.addWidget(self.analyze_pdf_btn)
        layout.addWidget(card)
        layout.addStretch()
        return widget
    
    def create_image_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel("Анализ изображений")
        title.setObjectName("cardTitle")
        desc = QLabel("Загрузите скриншот сайта, баннер или фото упаковки конкурента")
        desc.setObjectName("cardDescription")
        
        self.image_drop_zone = ImageDropZone()
        self.analyze_image_btn = QPushButton("⚡ Проанализировать")
        self.analyze_image_btn.setObjectName("primaryButton")
        self.analyze_image_btn.clicked.connect(self.analyze_image)
        
        card_layout.addWidget(title)
        card_layout.addWidget(desc)
        card_layout.addSpacing(16)
        card_layout.addWidget(self.image_drop_zone)
        card_layout.addSpacing(16)
        card_layout.addWidget(self.analyze_image_btn)
        layout.addWidget(card)
        layout.addStretch()
        return widget
    
    def create_parse_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel("Парсинг сайта конкурента")
        title.setObjectName("cardTitle")
        desc = QLabel("Введите URL сайта для автоматического извлечения и анализа контента")
        desc.setObjectName("cardDescription")
        
        url_layout = QHBoxLayout()
        prefix = QLabel("https://")
        prefix.setStyleSheet("background-color: #243049; padding: 12px 16px; border-radius: 8px 0 0 8px; color: #64748b;")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("example.com")
        self.url_input.setStyleSheet("border-radius: 0 8px 8px 0;")
        url_layout.addWidget(prefix)
        url_layout.addWidget(self.url_input)
        
        self.parse_btn = QPushButton("⚡ Парсить и анализировать")
        self.parse_btn.setObjectName("primaryButton")
        self.parse_btn.clicked.connect(self.parse_site)
        
        card_layout.addWidget(title)
        card_layout.addWidget(desc)
        card_layout.addSpacing(16)
        card_layout.addLayout(url_layout)
        card_layout.addSpacing(16)
        card_layout.addWidget(self.parse_btn)
        layout.addWidget(card)
        layout.addStretch()
        return widget
    
    def create_history_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        header = QHBoxLayout()
        title = QLabel("История запросов")
        title.setObjectName("cardTitle")
        self.clear_history_btn = QPushButton("🗑️ Очистить")
        self.clear_history_btn.setObjectName("secondaryButton")
        self.clear_history_btn.clicked.connect(self.clear_history)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.clear_history_btn)
        layout.addLayout(header)
        
        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_widget = QWidget()
        self.history_layout = QVBoxLayout(self.history_widget)
        self.history_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.history_scroll.setWidget(self.history_widget)
        layout.addWidget(self.history_scroll)
        return widget
    
    def switch_tab(self, index: int):
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        self.stacked_widget.setCurrentIndex(index)
        self.results_scroll.hide()
        if index == 4:
            self.load_history()
    
    def check_server_connection(self):
        if api_client.check_health():
            self.status_label.setText("● Система активна")
            self.status_label.setStyleSheet("color: #10b981; padding: 16px;")
        else:
            self.status_label.setText("● Сервер недоступен")
            self.status_label.setStyleSheet("color: #ef4444; padding: 16px;")
    
    def show_loading(self, message: str = "Анализирую данные..."):
        self.loading_label.setText(message)
        self.loading_widget.show()
        self.results_scroll.hide()
        self.analyze_text_btn.setEnabled(False)
        self.analyze_image_btn.setEnabled(False)
        self.analyze_pdf_btn.setEnabled(False)
        self.parse_btn.setEnabled(False)
    
    def hide_loading(self):
        self.loading_widget.hide()
        self.analyze_text_btn.setEnabled(True)
        self.analyze_image_btn.setEnabled(True)
        self.analyze_pdf_btn.setEnabled(True)
        self.parse_btn.setEnabled(True)
    
    def show_results(self, analysis: dict, result_type: str = "text"):
        while self.results_layout.count():
            child = self.results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Заголовок с кнопкой скачивания отчёта
        header_layout = QHBoxLayout()
        title = QLabel("📊 Результаты анализа")
        title.setObjectName("cardTitle")
        title.setStyleSheet("font-size: 18px;")
        header_layout.addWidget(title)
        
        # Выбор формата отчёта
        self.report_format = QComboBox()
        self.report_format.addItems(["HTML", "Markdown", "PDF"])
        self.report_format.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                color: #f1f5f9;
                padding: 8px 12px;
                border: 1px solid #334155;
                border-radius: 6px;
            }
        """)
        
        self.download_report_btn = QPushButton("📥 Скачать отчёт")
        self.download_report_btn.setObjectName("secondaryButton")
        self.download_report_btn.clicked.connect(self.download_report)
        
        header_layout.addStretch()
        header_layout.addWidget(self.report_format)
        header_layout.addWidget(self.download_report_btn)
        
        title_container = QWidget()
        title_container.setLayout(header_layout)
        self.results_layout.addWidget(title_container)
        
        # Сильные стороны
        if analysis.get("strengths"):
            block = ResultBlock("✅ Сильные стороны", analysis["strengths"])
            self.results_layout.addWidget(block)
        
        # Слабые стороны
        if analysis.get("weaknesses"):
            block = ResultBlock("⚠️ Слабые стороны", analysis["weaknesses"])
            self.results_layout.addWidget(block)
        
        # Уникальные предложения
        if analysis.get("unique_offers"):
            block = ResultBlock("⭐ Уникальные предложения", analysis["unique_offers"])
            self.results_layout.addWidget(block)
        
        # Рекомендации
        if analysis.get("recommendations"):
            block = ResultBlock("💡 Рекомендации", analysis["recommendations"])
            self.results_layout.addWidget(block)
        
        # Оценки
        if analysis.get("design_score") is not None:
            block = ScoreBlock("🎨 Оценка дизайна", analysis["design_score"])
            self.results_layout.addWidget(block)
        
        if analysis.get("technology_potential") is not None:
            block = ScoreBlock("⚡ Технологический потенциал", analysis["technology_potential"])
            self.results_layout.addWidget(block)
        
        # Резюме
        if analysis.get("summary"):
            summary_frame = QFrame()
            summary_frame.setObjectName("resultBlock")
            summary_frame.setStyleSheet("QFrame#resultBlock { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(6, 182, 212, 0.1), stop:1 rgba(139, 92, 246, 0.1)); }")
            summary_layout = QVBoxLayout(summary_frame)
            summary_title = QLabel("📝 Резюме")
            summary_title.setObjectName("sectionTitle")
            summary_text = QLabel(analysis["summary"])
            summary_text.setWordWrap(True)
            summary_text.setStyleSheet("color: #f1f5f9; font-size: 15px; line-height: 1.6;")
            summary_layout.addWidget(summary_title)
            summary_layout.addWidget(summary_text)
            self.results_layout.addWidget(summary_frame)
        
        self.results_layout.addStretch()
        self.results_scroll.show()
        self.current_analysis = analysis
    
    def show_error(self, message: str):
        QMessageBox.critical(self, "Ошибка", message)
    
    # === API методы ===
    def analyze_text(self):
        text = self.text_input.toPlainText().strip()
        if len(text) < 10:
            self.show_error("Введите текст минимум 10 символов")
            return
        self.show_loading("Анализирую текст...")
        self.current_worker = WorkerThread(api_client.analyze_text, text)
        self.current_worker.finished.connect(self.on_text_analysis_complete)
        self.current_worker.error.connect(lambda e: self.on_error(e))
        self.current_worker.start()
    
    def on_text_analysis_complete(self, result: dict):
        self.hide_loading()
        if result.get("success") and result.get("analysis"):
            self.show_results(result["analysis"], "text")
        else:
            self.show_error(result.get("error", "Неизвестная ошибка"))
    
    def on_pdf_selected(self, file_path: str):
        self.analyze_pdf_btn.setEnabled(True)
    
    def analyze_pdf(self):
        if not self.pdf_drop_zone.selected_file:
            self.show_error("Выберите PDF файл")
            return
        self.show_loading("Анализирую PDF...")
        self.current_worker = WorkerThread(api_client.analyze_pdf, self.pdf_drop_zone.selected_file)
        self.current_worker.finished.connect(self.on_pdf_analysis_complete)
        self.current_worker.error.connect(lambda e: self.on_error(e))
        self.current_worker.start()
    
    def on_pdf_analysis_complete(self, result: dict):
        self.hide_loading()
        if result.get("success") and result.get("analysis"):
            self.show_results(result["analysis"], "text")
        else:
            self.show_error(result.get("error", "Неизвестная ошибка"))
    
    def analyze_image(self):
        if not self.image_drop_zone.selected_file:
            self.show_error("Выберите изображение")
            return
        self.show_loading("Анализирую изображение...")
        self.current_worker = WorkerThread(api_client.analyze_image, self.image_drop_zone.selected_file)
        self.current_worker.finished.connect(self.on_image_analysis_complete)
        self.current_worker.error.connect(lambda e: self.on_error(e))
        self.current_worker.start()
    
    def on_image_analysis_complete(self, result: dict):
        self.hide_loading()
        if result.get("success") and result.get("analysis"):
            self.show_results(result["analysis"], "image")
        else:
            self.show_error(result.get("error", "Неизвестная ошибка"))
    
    def parse_site(self):
        url = self.url_input.text().strip()
        if not url:
            self.show_error("Введите URL сайта")
            return
        self.show_loading("Загружаю и анализирую сайт...")
        self.current_worker = WorkerThread(api_client.parse_demo, url)
        self.current_worker.finished.connect(self.on_parse_complete)
        self.current_worker.error.connect(lambda e: self.on_error(e))
        self.current_worker.start()
    
    def on_parse_complete(self, result: dict):
        self.hide_loading()
        if result.get("success") and result.get("data"):
            data = result["data"]
            if data.get("analysis"):
                self.show_results(data["analysis"], "parse")
            else:
                self.show_error("Не удалось проанализировать сайт")
        else:
            self.show_error(result.get("error", "Неизвестная ошибка"))
    
    def load_history(self):
        result = api_client.get_history()
        while self.history_layout.count():
            child = self.history_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if result.get("items"):
            for item in result["items"]:
                frame = QFrame()
                frame.setObjectName("historyItem")
                layout = QHBoxLayout(frame)
                
                icons = {"text": "📝", "image": "🖼️", "parse": "🌐", "pdf": "📄"}
                icon = QLabel(icons.get(item.get("request_type", ""), "📄"))
                icon.setStyleSheet("font-size: 24px;")
                
                content = QWidget()
                content_layout = QVBoxLayout(content)
                content_layout.setContentsMargins(0, 0, 0, 0)
                
                type_labels = {"text": "Анализ текста", "image": "Анализ изображения", 
                              "parse": "Парсинг сайта", "pdf": "Анализ PDF"}
                type_label = QLabel(type_labels.get(item.get("request_type", ""), item.get("request_type", "")))
                type_label.setStyleSheet("color: #22d3ee; font-size: 12px; font-weight: bold;")
                summary = QLabel(item.get("request_summary", "")[:60] + "...")
                summary.setStyleSheet("color: #94a3b8;")
                content_layout.addWidget(type_label)
                content_layout.addWidget(summary)
                
                timestamp = item.get("timestamp", "")
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        time_str = dt.strftime("%d.%m %H:%M")
                    except:
                        time_str = timestamp[:16]
                else:
                    time_str = ""
                
                time_label = QLabel(time_str)
                time_label.setStyleSheet("color: #64748b; font-size: 12px;")
                
                layout.addWidget(icon)
                layout.addWidget(content, stretch=1)
                layout.addWidget(time_label)
                self.history_layout.addWidget(frame)
        else:
            empty_label = QLabel("📋 История пуста")
            empty_label.setStyleSheet("color: #64748b; font-size: 16px; padding: 40px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_layout.addWidget(empty_label)
        
        self.history_layout.addStretch()
    
    def clear_history(self):
        reply = QMessageBox.question(
            self, "Подтверждение", "Вы уверены, что хотите очистить историю?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            api_client.clear_history()
            self.load_history()
    
    def download_report(self):
        """Скачать отчёт"""
        if not self.current_analysis:
            self.show_error("Нет данных для отчёта")
            return
        
        format_map = {"HTML": "html", "Markdown": "markdown", "PDF": "pdf"}
        fmt = format_map.get(self.report_format.currentText(), "html")
        
        self.show_loading("Генерирую отчёт...")
        self.current_worker = WorkerThread(api_client.generate_report, self.current_analysis, fmt)
        self.current_worker.finished.connect(self.on_report_generated)
        self.current_worker.error.connect(lambda e: self.on_error(e))
        self.current_worker.start()
    
    def on_report_generated(self, result: dict):
        self.hide_loading()
        if result.get("success"):
            filename = result.get("filename", f"report.{result.get('format', 'html')}")
            
            if result.get("format") == "pdf":
                # PDF - base64
                import base64
                content = base64.b64decode(result["content"])
                mime = "application/pdf"
            else:
                # HTML/Markdown - text
                content = result["content"].encode('utf-8')
                mime = "text/html" if result.get("format") == "html" else "text/markdown"
            
            # Сохраняем файл
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить отчёт", filename,
                f"{result.get('format', 'html').upper()} (*.{result.get('format', 'html')})"
            )
            if file_path:
                with open(file_path, 'wb') as f:
                    f.write(content)
                QMessageBox.information(self, "Успех", f"Отчёт сохранён: {file_path}")
        else:
            self.show_error(result.get("error", "Ошибка генерации отчёта"))
    
    def on_error(self, error: str):
        self.hide_loading()
        self.show_error(error)

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()