# app/ui/main_window.py
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMessageBox, QLineEdit, QLabel, QComboBox,
    QPushButton, QCheckBox, QTableWidget,
    QTableWidgetItem, QFrame, QScrollArea, QTextEdit,
    QSplitter, QTabWidget
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QColor

from .components.price_chart import PriceChart
from .components.sentiment_panel import SentimentPanel
from ..services.crypto_data import CryptoDataService
from ..services.technical_analysis import TechnicalAnalysisService
from ..services.pattern_recognition import PatternRecognition


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crypto Analyzer - TradingView Style with 29+ Patterns & Sentiment")
        self.resize(2000, 1200)
        self.setMinimumSize(1600, 1000)
        self.setFont(QFont("Segoe UI", 10))

        # Dark theme
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; color: #ffffff; }
            QWidget { background-color: #1e1e1e; color: #ffffff; }
            QComboBox { background-color: #2d2d2d; color: #ffffff; border: 1px solid #444; padding: 5px; border-radius: 3px; }
            QLineEdit { background-color: #2d2d2d; color: #ffffff; border: 1px solid #444; padding: 5px; border-radius: 3px; }
            QPushButton { background-color: #0d7377; color: white; border: none; padding: 8px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #14919b; }
            QCheckBox { color: #ffffff; }
            QTableWidget { background-color: #2d2d2d; gridline-color: #444; }
            QHeaderView::section { background-color: #1e1e1e; color: #ffffff; border: none; padding: 5px; }
            QScrollArea { border: none; background-color: #2d2d2d; }
            QTextEdit { background-color: #1e1e1e; color: #ffffff; border: 1px solid #444; padding: 8px; border-radius: 3px; font-family: 'Courier New'; font-size: 9px; }
            QTabWidget::pane { border: 1px solid #444; }
            QTabBar::tab { background-color: #2d2d2d; color: #ffffff; padding: 8px; }
            QTabBar::tab:selected { background-color: #0d7377; }
        """)

        # Services
        self.crypto_service = CryptoDataService()
        self.technical_service = TechnicalAnalysisService()
        self.pattern_recognition = None

        if hasattr(self.crypto_service, 'load_available_pairs'):
            self.crypto_service.load_available_pairs()

        # State
        self.df = None
        self.patterns = None
        self.recent_patterns = None
        self.current_symbol = None
        self.current_interval = None

        # UI
        self.setup_ui()

        # Timers
        self.price_timer = QTimer()
        self.price_timer.timeout.connect(self.quick_update_price)
        self.price_timer.start(1000)

        self.full_timer = QTimer()
        self.full_timer.timeout.connect(self.auto_update)
        self.full_timer.start(60000)

        # Initial load
        self.load_initial_data()

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # ===== Header =====
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        header_layout.addWidget(QLabel("🔍"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cari pair... (BTC, ETH, BNB)")
        self.search_input.setMaximumWidth(220)
        self.search_input.returnPressed.connect(self.on_search_pair)
        header_layout.addWidget(self.search_input)

        header_layout.addWidget(QLabel("|"))

        header_layout.addWidget(QLabel("Pair:"))
        self.pair_combo = QComboBox()
        self.all_pairs = sorted(getattr(self.crypto_service, 'available_pairs',
                                        ["BTC/USDT", "ETH/USDT", "BNB/USDT"]))
        self.pair_combo.addItems(self.all_pairs)
        self.pair_combo.setMinimumWidth(120)
        self.pair_combo.currentTextChanged.connect(self.on_pair_changed)
        header_layout.addWidget(self.pair_combo)

        header_layout.addWidget(QLabel("Timeframe:"))
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"])
        self.timeframe_combo.setMinimumWidth(80)
        self.timeframe_combo.currentTextChanged.connect(self.on_timeframe_changed)
        header_layout.addWidget(self.timeframe_combo)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setMaximumWidth(100)
        refresh_btn.clicked.connect(self.update_data)
        header_layout.addWidget(refresh_btn)

        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # ===== Main Splitter =====
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setStyleSheet("QSplitter::handle { background: #444; }")

        # Left: Chart + Stats
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        self.price_chart = PriceChart()
        left_layout.addWidget(self.price_chart, stretch=1)

        stats_panel = self.create_stats_panel()
        left_layout.addWidget(stats_panel, stretch=0)

        main_splitter.addWidget(left_widget)

        # Right: Tabs
        right_tabs = QTabWidget()

        self.tech_sidebar = self.create_technical_sidebar()
        right_tabs.addTab(self.tech_sidebar, "📊 Technical")

        try:
            self.sentiment_panel = SentimentPanel()
            right_tabs.addTab(self.sentiment_panel, "📈 Sentiment & News")
        except Exception as e:
            print(f"Warning: Sentiment panel not loaded: {e}")
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel(
                f"Sentiment panel error: {e}\n\n"
                f"Make sure all dependencies are installed:\n"
                f"pip install feedparser requests"
            )
            error_label.setStyleSheet("color: #f23645; padding: 10px;")
            error_layout.addWidget(error_label)
            error_layout.addStretch()
            right_tabs.addTab(error_widget, "📈 Sentiment & News")

        main_splitter.addWidget(right_tabs)
        main_splitter.setSizes([1200, 800])
        main_splitter.setCollapsible(0, False)
        main_splitter.setCollapsible(1, True)

        main_layout.addWidget(main_splitter, stretch=1)

    def create_technical_sidebar(self):
        w = QWidget()
        L = QVBoxLayout(w)
        L.setContentsMargins(10, 10, 10, 10)
        L.setSpacing(8)

        self.price_info = QLabel("Price: --\nChange: --\nVolume: --")
        self.price_info.setStyleSheet("""
            color: #0d7377; font-weight: bold; font-size: 11px;
            background-color: #1e1e1e; padding: 8px; border-radius: 3px;
        """)
        L.addWidget(QLabel("📊 Current Price"))
        L.addWidget(self.price_info)

        L.addWidget(QLabel("📈 Indicators"))
        group = QWidget()
        gL = QVBoxLayout(group)
        gL.setContentsMargins(0, 0, 0, 0)
        gL.setSpacing(4)

        self.cb_ma = QCheckBox("Moving Averages (SMA/EMA)")
        self.cb_bollinger = QCheckBox("Bollinger Bands")
        self.cb_rsi = QCheckBox("RSI (Relative Strength)")
        self.cb_macd = QCheckBox("MACD")
        self.cb_volume = QCheckBox("Volume")
        self.cb_recent = QCheckBox("Highlight Recent Patterns")
        self.cb_recent.setChecked(False)
        self.cb_ma.setChecked(True)

        for cb in [self.cb_ma, self.cb_bollinger, self.cb_rsi, self.cb_macd, self.cb_volume, self.cb_recent]:
            cb.stateChanged.connect(self.update_chart_display)
            gL.addWidget(cb)

        L.addWidget(group)

        # Patterns list
        ph = QHBoxLayout()
        ph.addWidget(QLabel("⚡ Detected Patterns"))
        self.pattern_count_label = QLabel("(0)")
        self.pattern_count_label.setStyleSheet("color: #ffd700; font-weight: bold;")
        ph.addWidget(self.pattern_count_label)
        ph.addStretch()
        L.addLayout(ph)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(200)
        self.pattern_list = QTableWidget()
        self.pattern_list.setColumnCount(2)
        self.pattern_list.setHorizontalHeaderLabels(["Pattern", "Count"])
        self.pattern_list.setColumnWidth(0, 250)
        self.pattern_list.setColumnWidth(1, 60)
        self.pattern_list.setStyleSheet("QTableWidget { gridline-color: #444; border: none; }")
        self.pattern_list.cellClicked.connect(self.show_pattern_details)
        scroll.setWidget(self.pattern_list)
        L.addWidget(scroll)

        L.addWidget(QLabel("📋 Pattern Details (Click pattern above)"))
        self.pattern_details = QTextEdit()
        self.pattern_details.setReadOnly(True)
        self.pattern_details.setMaximumHeight(150)
        self.pattern_details.setText("Click pada pattern di tabel untuk melihat detail...")
        L.addWidget(self.pattern_details)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setStyleSheet("color: #444;")
        L.addWidget(sep)

        header_recent = QHBoxLayout()
        header_recent.addWidget(QLabel("⏱ Recent Patterns (1–2 Hari)"))
        header_recent.addStretch()
        header_recent.addWidget(QLabel("Periode:"))
        self.recent_days_combo = QComboBox()
        self.recent_days_combo.addItems(["1 Hari", "2 Hari"])
        self.recent_days_combo.setMaximumWidth(100)
        self.recent_days_combo.currentIndexChanged.connect(self.on_recent_days_changed)
        header_recent.addWidget(self.recent_days_combo)
        refresh_recent_btn = QPushButton("🔄 Update Recent")
        refresh_recent_btn.setMaximumWidth(130)
        refresh_recent_btn.clicked.connect(self.update_recent_patterns_ui)
        header_recent.addWidget(refresh_recent_btn)
        L.addLayout(header_recent)

        self.recent_summary = QTextEdit()
        self.recent_summary.setReadOnly(True)
        self.recent_summary.setMinimumHeight(140)
        self.recent_summary.setMaximumHeight(200)
        self.recent_summary.setText("Belum ada data recent. Klik Update atau ganti Periode.")
        L.addWidget(self.recent_summary)

        L.addStretch()
        return w

    def create_stats_panel(self):
        panel = QFrame()
        panel.setMaximumHeight(100)
        panel.setStyleSheet("background-color: #2d2d2d; border-top: 1px solid #444; border-radius: 5px;")
        L = QHBoxLayout(panel)
        L.setContentsMargins(10, 8, 10, 8)

        self.stats_table = QTableWidget()
        self.stats_table.setRowCount(1)
        self.stats_table.setColumnCount(8)
        self.stats_table.setHorizontalHeaderLabels([
            "RSI (14)", "MACD", "Signal", "Histogram",
            "SMA20/50", "Stoch K", "ATR", "VWAP"
        ])
        self.stats_table.setMaximumHeight(90)
        self.stats_table.setStyleSheet("QTableWidget { gridline-color: #444; font-size: 9px; }")
        self.stats_table.horizontalHeader().setStretchLastSection(True)

        L.addWidget(self.stats_table)
        return panel

    # ====== Logic (tetap) ======
    def show_pattern_details(self, row, column):
        if not self.patterns or self.df is None:
            return
        pattern_name = self.pattern_list.item(row, 0).text()
        if pattern_name not in self.patterns:
            return
        detections = self.patterns[pattern_name]
        if not detections:
            self.pattern_details.setText("No details available.")
            return

        details = f"═══ {pattern_name} ═══\n\n"
        details += f"Total Detected: {len(detections) if isinstance(detections, list) else 1}\n"
        details += "─" * 40 + "\n\n"
        interpretation = self.get_pattern_interpretation(pattern_name)
        details += f"📊 INTERPRETATION:\n{interpretation}\n\n"
        details += "─" * 40 + "\n\n"

        if isinstance(detections, list) and len(detections) > 0:
            details += "🔍 DETECTED INSTANCES:\n\n"
            for i, detection in enumerate(detections[:5]):
                details += f"Instance #{i+1}:\n"
                if isinstance(detection, dict):
                    for key, value in detection.items():
                        if key == 'index' or 'idx' in str(key).lower():
                            if value < len(self.df):
                                ts = self.df.index[value].strftime('%Y-%m-%d %H:%M')
                                details += f"  • Position: {ts} (index: {value})\n"
                        elif 'price' in str(key).lower():
                            details += f"  • {key}: ${value:,.2f}\n"
                        elif isinstance(value, (int, float)):
                            details += f"  • {key}: {value:.4f}\n" if isinstance(value, float) else f"  • {key}: {value}\n"
                        else:
                            details += f"  • {key}: {value}\n"
                else:
                    details += f"  • Detection: {detection}\n"
                details += "\n"
            if len(detections) > 5:
                details += f"... and {len(detections) - 5} more\n"

        self.pattern_details.setText(details)

    def get_pattern_interpretation(self, pattern_name):
        interpretations = {
            # Bullish
            'Double Bottoms': '🟢 BULLISH - Reversal naik. Dua kali uji support lalu berbalik.',
            'Triple Bottoms': '🟢 BULLISH - Reversal kuat. Tiga kali uji support gagal tembus.',
            'Inverse Head & Shoulders': '🟢 BULLISH - Reversal klasik berbentuk W.',
            'Rounding Bottom': '🟢 BULLISH - Akumulasi U-shape sebelum naik.',
            'Cup & Handle': '🟢 BULLISH - Continuation; handle = pullback kecil.',
            'Bullish Flag': '🟢 BULLISH - Konsolidasi singkat dalam tren naik.',
            'Bullish Engulfing': '🟢 BULLISH - Candle bullish menelan bearish sebelumnya.',
            'Morning Star': '🟢 BULLISH - Pola 3-candle reversal.',
            'Hammer': '🟢 BULLISH - Lower shadow panjang; reject turun.',
            'Piercing Pattern': '🟢 BULLISH - Bullish menembus >50% body bearish.',
            'Three White Soldiers': '🟢 BULLISH - 3 candle bullish berturut.',
            'Bullish Harami': '🟢 BULLISH - Bullish kecil di dalam bearish besar.',
            # Bearish
            'Double Tops': '🔴 BEARISH - Reversal turun; dua kali uji resistance.',
            'Triple Tops': '🔴 BEARISH - Reversal kuat; tiga kali uji resistance.',
            'Head & Shoulders': '🔴 BEARISH - Reversal klasik berbentuk M.',
            'Dead Cat Bounce': '🔴 BEARISH - Relief rally lemah; lanjut turun.',
            'Bearish Flag': '🔴 BEARISH - Konsolidasi singkat dalam tren turun.',
            'Bearish Engulfing': '🔴 BEARISH - Bearish menelan bullish sebelumnya.',
            'Evening Star': '🔴 BEARISH - Pola 3-candle reversal.',
            'Shooting Star': '🔴 BEARISH - Upper shadow panjang; reject naik.',
            'Dark Cloud': '🔴 BEARISH - Bearish turun >50% body bullish.',
            'Three Black Crows': '🔴 BEARISH - 3 candle bearish berturut.',
            # Triangles
            'Ascending Triangle': '🟢 BULLISH - Bias breakout atas (resistance datar, support naik).',
            'Descending Triangle': '🔴 BEARISH - Bias breakdown (support datar, resistance turun).',
            'Symmetric Triangle': '🟡 NEUTRAL - Tunggu arah breakout.',
        }
        for k, v in interpretations.items():
            if k.lower() in pattern_name.lower() or pattern_name.lower() in k.lower():
                return v
        return '🔵 Pattern terdeteksi. Perlu konfirmasi indikator & volume.'

    # ====== Pair/TF/Price lifecycle ======
    def on_search_pair(self):
        search_text = self.search_input.text().strip().upper()
        if not search_text:
            self.pair_combo.setCurrentIndex(0)
            return
        matching = [p for p in self.all_pairs if search_text in p.upper()]
        if matching:
            self.pair_combo.blockSignals(True)
            self.pair_combo.setCurrentText(matching[0])
            self.pair_combo.blockSignals(False)
            self.search_input.clear()
            self.update_data()
        else:
            QMessageBox.warning(self, "Not Found", f"Pair '{search_text}' tidak ditemukan")
            self.search_input.clear()

    def on_pair_changed(self):
        if self.pair_combo.currentText():
            self.update_data()

    def on_timeframe_changed(self):
        if self.timeframe_combo.currentText():
            self.update_data()

    def load_initial_data(self):
        self.update_data()

    def auto_update(self):
        if self.current_symbol and self.current_interval:
            self.update_data()

    def quick_update_price(self):
        try:
            if self.df is None or self.df.empty:
                return
            symbol = self.pair_combo.currentText()
            interval = self.timeframe_combo.currentText()
            if not symbol or not interval:
                return
            df_latest = self.crypto_service.get_klines_data(symbol, interval, limit=2)
            if df_latest is None or df_latest.empty or len(df_latest) < 1:
                return
            latest_row = df_latest.iloc[-1]
            self.df.iloc[-1, self.df.columns.get_loc('open')] = latest_row['open']
            self.df.iloc[-1, self.df.columns.get_loc('high')] = latest_row['high']
            self.df.iloc[-1, self.df.columns.get_loc('low')] = latest_row['low']
            self.df.iloc[-1, self.df.columns.get_loc('close')] = latest_row['close']
            self.df.iloc[-1, self.df.columns.get_loc('volume')] = latest_row['volume']
            self.df = self.technical_service.calculate_all_indicators(self.df)
            self.update_price_info()
            self.update_stats_table()
            self.update_chart_display()
        except Exception as e:
            print(f"Quick update error: {e}")

    def update_data(self):
        try:
            symbol = self.pair_combo.currentText()
            interval = self.timeframe_combo.currentText()
            if not symbol or not interval:
                return

            self.current_symbol = symbol
            self.current_interval = interval

            self.df = self.crypto_service.get_klines_data(symbol, interval)
            if self.df is None or self.df.empty:
                raise ValueError(f"Data kosong untuk {symbol} {interval}")

            self.df = self.technical_service.calculate_all_indicators(self.df)

            self.pattern_recognition = PatternRecognition(self.df)
            self.patterns = self.pattern_recognition.detect_all_patterns()

            # Recent patterns (1–2 hari)
            self.update_recent_patterns_ui()

            self.update_price_info()
            self.update_pattern_list()
            self.update_stats_table()
            self.update_chart_display()

            # Sinkronkan SentimentPanel
            if hasattr(self, 'sentiment_panel'):
                try:
                    self.sentiment_panel.update_coin_sentiment(symbol)
                except Exception:
                    pass

        except Exception as e:
            print(f"Error: {str(e)}")

    def update_price_info(self):
        if self.df is None or self.df.empty:
            return
        last = self.df.iloc[-1]
        current_price = last['close']
        open_price = self.df.iloc[0]['close']
        change = current_price - open_price
        change_pct = (change / open_price * 100) if open_price != 0 else 0
        volume = last.get('volume', 0)
        color = "#26a69a" if change >= 0 else "#f23645"
        info_text = f"Price: ${current_price:,.2f}\nChange: {change:+.2f} ({change_pct:+.2f}%)\nVolume: {volume:,.0f}"
        self.price_info.setText(info_text)
        self.price_info.setStyleSheet(f"""
            color: {color}; font-weight: bold; font-size: 11px;
            background-color: #1e1e1e; padding: 8px; border-radius: 3px;
        """)

    def update_pattern_list(self):
        self.pattern_list.setRowCount(0)
        if not self.patterns:
            self.pattern_count_label.setText("(0)")
            return

        row = 0
        total = 0
        sorted_patterns = sorted(
            self.patterns.items(),
            key=lambda x: len(x[1]) if isinstance(x[1], list) else (1 if x[1] else 0),
            reverse=True
        )
        for pattern_name, detections in sorted_patterns:
            if detections:
                cnt = len(detections) if isinstance(detections, list) else (1 if detections else 0)
                if cnt > 0:
                    total += cnt
                    name_item = QTableWidgetItem(pattern_name)
                    cnt_item = QTableWidgetItem(str(cnt))

                    if any(x in pattern_name.lower() for x in ['bullish', 'bottom', 'morning', 'white', 'hammer', 'piercing', 'inverse', 'ascending']):
                        cnt_item.setForeground(QColor("#26a69a"))
                        name_item.setForeground(QColor("#26a69a"))
                    elif any(x in pattern_name.lower() for x in ['bearish', 'top', 'evening', 'black', 'shooting', 'dark', 'dead', 'descending']):
                        cnt_item.setForeground(QColor("#f23645"))
                        name_item.setForeground(QColor("#f23645"))
                    else:
                        cnt_item.setForeground(QColor("#ffd700"))
                        name_item.setForeground(QColor("#ffd700"))

                    cnt_item.setFont(QFont("Arial", 10, QFont.Bold))
                    self.pattern_list.insertRow(row)
                    self.pattern_list.setItem(row, 0, name_item)
                    self.pattern_list.setItem(row, 1, cnt_item)
                    row += 1

        self.pattern_count_label.setText(f"({total})")
        self.setWindowTitle(f"Crypto Analyzer - {total} Patterns Detected")

    def update_stats_table(self):
        if self.df is None or self.df.empty:
            return
        last = self.df.iloc[-1]
        stats = [
            f"{last.get('rsi', 0):.2f}",
            f"{last.get('macd', 0):.6f}",
            f"{last.get('macd_signal', 0):.6f}",
            f"{last.get('macd_histogram', 0):.6f}",
            f"{last.get('sma_20', 0):.2f}",
            f"{last.get('stoch_k', 0):.2f}",
            f"{last.get('atr', 0):.4f}",
            f"{last.get('vwap', 0):.2f}"
        ]
        for col, stat in enumerate(stats):
            item = QTableWidgetItem(stat)
            item.setFont(QFont("Courier New", 9))
            self.stats_table.setItem(0, col, item)

    def update_chart_display(self):
        if self.df is None or self.df.empty:
            return
        recent_for_chart = self.recent_patterns if getattr(self, 'cb_recent', None) and self.cb_recent.isChecked() else None
        self.price_chart.update_chart(
            self.df,
            show_rsi=self.cb_rsi.isChecked(),
            show_macd=self.cb_macd.isChecked(),
            show_bollinger=self.cb_bollinger.isChecked(),
            show_ma=self.cb_ma.isChecked(),
            show_volume=self.cb_volume.isChecked(),
            patterns=self.patterns,
            recent_patterns=recent_for_chart
        )

    # ===== Recent patterns helpers =====
    def _get_selected_recent_days(self) -> int:
        if not hasattr(self, 'recent_days_combo'):
            return 1
        text = self.recent_days_combo.currentText().strip().lower()
        return 2 if text.startswith("2") else 1

    def on_recent_days_changed(self):
        self.update_recent_patterns_ui()
        self.update_chart_display()

    def update_recent_patterns_ui(self):
        if self.df is None or self.df.empty:
            return
        if self.pattern_recognition is None:
            self.pattern_recognition = PatternRecognition(self.df)
        else:
            self.pattern_recognition.df = self.df

        days = self._get_selected_recent_days()
        try:
            self.recent_patterns = self.pattern_recognition.get_recent_patterns(days=days)
            summary_text = self.pattern_recognition.get_recent_patterns_summary(days=days)
        except Exception as e:
            self.recent_patterns = {}
            summary_text = f"Terjadi error saat menghitung recent patterns: {e}"

        if hasattr(self, 'recent_summary') and self.recent_summary is not None:
            self.recent_summary.setText(summary_text)

    def load_initial_data(self):
        self.update_data()

    def auto_update(self):
        if self.current_symbol and self.current_interval:
            self.update_data()
