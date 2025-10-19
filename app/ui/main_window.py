# app/ui/main_window.py
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QMessageBox, QLineEdit, QLabel, QComboBox, 
                             QPushButton, QCheckBox, QTableWidget,
                             QTableWidgetItem, QFrame)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QColor
from .components.price_chart import PriceChart
from ..services.crypto_data import CryptoDataService
from ..services.technical_analysis import TechnicalAnalysisService
from ..services.pattern_recognition import PatternRecognition

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crypto Analyzer - TradingView Style")
        self.resize(1600, 1000)
        self.setMinimumSize(1400, 900)
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
        """)
        
        # Services
        self.crypto_service = CryptoDataService()
        self.technical_service = TechnicalAnalysisService()
        self.pattern_recognition = None
        
        if hasattr(self.crypto_service, 'load_available_pairs'):
            self.crypto_service.load_available_pairs()
        
        self.df = None
        self.patterns = None
        self.current_symbol = None
        self.current_interval = None
        
        # Setup UI
        self.setup_ui()
        
        # Auto-update timer untuk price
        self.price_timer = QTimer()
        self.price_timer.timeout.connect(self.quick_update_price)
        self.price_timer.start(1000)  # Update harga setiap 1 detik
        
        # Auto-update timer untuk full data
        self.full_timer = QTimer()
        self.full_timer.timeout.connect(self.auto_update)
        self.full_timer.start(60000)  # Update full data setiap 1 menit
        
        # Initial load
        self.load_initial_data()

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # ===== HEADER / CONTROL PANEL =====
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Search bar dengan Enter key
        header_layout.addWidget(QLabel("🔍"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cari pair... (BTC, ETH, BNB)")
        self.search_input.setMaximumWidth(220)
        self.search_input.returnPressed.connect(self.on_search_pair)
        header_layout.addWidget(self.search_input)
        
        header_layout.addWidget(QLabel("|"))
        
        # Pair selector
        header_layout.addWidget(QLabel("Pair:"))
        self.pair_combo = QComboBox()
        self.all_pairs = sorted(getattr(self.crypto_service, 'available_pairs', 
                                        ["BTC/USDT", "ETH/USDT", "BNB/USDT"]))
        self.pair_combo.addItems(self.all_pairs)
        self.pair_combo.setMinimumWidth(120)
        self.pair_combo.currentTextChanged.connect(self.on_pair_changed)
        header_layout.addWidget(self.pair_combo)
        
        # Timeframe selector
        header_layout.addWidget(QLabel("Timeframe:"))
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"])
        self.timeframe_combo.setMinimumWidth(80)
        self.timeframe_combo.currentTextChanged.connect(self.on_timeframe_changed)
        header_layout.addWidget(self.timeframe_combo)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setMaximumWidth(100)
        refresh_btn.clicked.connect(self.update_data)
        header_layout.addWidget(refresh_btn)
        
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
        # ===== MAIN CONTENT =====
        content_layout = QHBoxLayout()
        content_layout.setSpacing(5)
        
        # Chart area (left - 80%)
        self.price_chart = PriceChart()
        content_layout.addWidget(self.price_chart, stretch=8)
        
        # Right sidebar (20%)
        sidebar = QFrame()
        sidebar.setStyleSheet("background-color: #2d2d2d; border-radius: 5px;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(8)
        
        # Price info card
        self.price_info = QLabel("Price: --\nChange: --\nVolume: --")
        self.price_info.setStyleSheet("""
            color: #0d7377; font-weight: bold; font-size: 11px;
            background-color: #1e1e1e; padding: 8px; border-radius: 3px;
        """)
        sidebar_layout.addWidget(QLabel("📊 Current Price"))
        sidebar_layout.addWidget(self.price_info)
        
        # Indicator toggles
        sidebar_layout.addWidget(QLabel("📈 Indicators"))
        indicators_group = QWidget()
        indicators_layout = QVBoxLayout(indicators_group)
        indicators_layout.setContentsMargins(0, 0, 0, 0)
        indicators_layout.setSpacing(4)
        
        self.cb_ma = QCheckBox("Moving Averages (SMA/EMA)")
        self.cb_bollinger = QCheckBox("Bollinger Bands")
        self.cb_rsi = QCheckBox("RSI (Relative Strength)")
        self.cb_macd = QCheckBox("MACD")
        self.cb_volume = QCheckBox("Volume")
        
        self.cb_ma.setChecked(True)
        
        for cb in [self.cb_ma, self.cb_bollinger, self.cb_rsi, self.cb_macd, self.cb_volume]:
            cb.stateChanged.connect(self.update_chart_display)
            indicators_layout.addWidget(cb)
        
        sidebar_layout.addWidget(indicators_group)
        
        # Pattern detection
        sidebar_layout.addWidget(QLabel("⚡ Detected Patterns"))
        self.pattern_list = QTableWidget()
        self.pattern_list.setColumnCount(2)
        self.pattern_list.setHorizontalHeaderLabels(["Pattern", "Count"])
        self.pattern_list.setColumnWidth(0, 100)
        self.pattern_list.setColumnWidth(1, 50)
        self.pattern_list.setMaximumHeight(140)
        self.pattern_list.setStyleSheet("""
            QTableWidget { gridline-color: #444; }
        """)
        sidebar_layout.addWidget(self.pattern_list)
        
        sidebar_layout.addStretch()
        
        content_layout.addWidget(sidebar, stretch=2)
        main_layout.addLayout(content_layout, stretch=1)
        
        # ===== BOTTOM PANEL - STATISTICS =====
        stats_panel = self.create_stats_panel()
        main_layout.addWidget(stats_panel, stretch=0)

    def create_stats_panel(self):
        panel = QFrame()
        panel.setMaximumHeight(100)
        panel.setStyleSheet("background-color: #2d2d2d; border-top: 1px solid #444; border-radius: 5px;")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 8, 10, 8)
        
        self.stats_table = QTableWidget()
        self.stats_table.setRowCount(1)
        self.stats_table.setColumnCount(8)
        self.stats_table.setHorizontalHeaderLabels([
            "RSI (14)", "MACD", "Signal", "Histogram", 
            "SMA20/50", "Stoch K", "ATR", "VWAP"
        ])
        self.stats_table.setMaximumHeight(90)
        self.stats_table.setStyleSheet("""
            QTableWidget { gridline-color: #444; font-size: 9px; }
        """)
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.stats_table)
        return panel

    def on_search_pair(self):
        """Triggered by Enter key in search box"""
        search_text = self.search_input.text().strip().upper()
        if not search_text:
            self.pair_combo.setCurrentIndex(0)
            return
        
        matching_pairs = [p for p in self.all_pairs if search_text in p.upper()]
        
        if matching_pairs:
            self.pair_combo.blockSignals(True)
            self.pair_combo.setCurrentText(matching_pairs[0])
            self.pair_combo.blockSignals(False)
            self.search_input.clear()
            self.update_data()
        else:
            QMessageBox.warning(self, "Not Found", f"Pair '{search_text}' tidak ditemukan")
            self.search_input.clear()

    def on_pair_changed(self):
        """Triggered when pair dropdown changed"""
        if self.pair_combo.currentText():
            self.update_data()

    def on_timeframe_changed(self):
        """Triggered when timeframe dropdown changed"""
        if self.timeframe_combo.currentText():
            self.update_data()

    def load_initial_data(self):
        self.update_data()

    def auto_update(self):
        """Auto update data setiap 1 menit"""
        if self.current_symbol and self.current_interval:
            self.update_data()

    def quick_update_price(self):
        """Update harga saja setiap 1 detik (lebih ringan)"""
        try:
            if self.df is None or self.df.empty:
                return
            
            symbol = self.pair_combo.currentText()
            interval = self.timeframe_combo.currentText()
            
            if not symbol or not interval:
                return
            
            # Fetch hanya last 2 candles untuk compare
            df_latest = self.crypto_service.get_klines_data(symbol, interval, limit=2)
            
            if df_latest is None or df_latest.empty or len(df_latest) < 1:
                return
            
            # Get latest candle data
            latest_row = df_latest.iloc[-1]
            current_row = self.df.iloc[-1]
            
            # Update last row dengan data terbaru
            self.df.iloc[-1, self.df.columns.get_loc('open')] = latest_row['open']
            self.df.iloc[-1, self.df.columns.get_loc('high')] = latest_row['high']
            self.df.iloc[-1, self.df.columns.get_loc('low')] = latest_row['low']
            self.df.iloc[-1, self.df.columns.get_loc('close')] = latest_row['close']
            self.df.iloc[-1, self.df.columns.get_loc('volume')] = latest_row['volume']
            
            # Recalculate last row indicators
            self.df = self.technical_service.calculate_all_indicators(self.df)
            
            # Update UI
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
            
            # Fetch data
            self.df = self.crypto_service.get_klines_data(symbol, interval)
            
            if self.df is None or self.df.empty:
                raise ValueError(f"Data kosong untuk {symbol} {interval}")
            
            # Calculate indicators
            self.df = self.technical_service.calculate_all_indicators(self.df)
            
            # Pattern recognition
            self.pattern_recognition = PatternRecognition(self.df)
            self.patterns = {
                'Double Tops': self.pattern_recognition.find_double_top(),
                'Double Bottoms': self.pattern_recognition.find_double_bottom(),
                'Head & Shoulders': self.pattern_recognition.find_head_and_shoulders(),
                'Triangles': self.pattern_recognition.find_triangle_patterns(),
                'Hammers': self.pattern_recognition.find_hammer_patterns()
            }
            
            self.update_price_info()
            self.update_pattern_list()
            self.update_stats_table()
            self.update_chart_display()
            
        except Exception as e:
            print(f"Error: {str(e)}")

    def update_price_info(self):
        if self.df is None or self.df.empty:
            return
        
        last_row = self.df.iloc[-1]
        current_price = last_row['close']
        open_price = self.df.iloc[0]['close']
        change = current_price - open_price
        change_pct = (change / open_price * 100) if open_price != 0 else 0
        volume = last_row.get('volume', 0)
        
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
            return
        
        row = 0
        for pattern_name, detections in self.patterns.items():
            if detections:
                count = len(detections) if isinstance(detections, list) else (1 if detections else 0)
                if count > 0:
                    item_name = QTableWidgetItem(pattern_name)
                    item_count = QTableWidgetItem(str(count))
                    item_count.setForeground(QColor("#26a69a"))
                    item_count.setFont(QFont("Arial", 10, QFont.Bold))
                    
                    self.pattern_list.insertRow(row)
                    self.pattern_list.setItem(row, 0, item_name)
                    self.pattern_list.setItem(row, 1, item_count)
                    row += 1

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
        
        self.price_chart.update_chart(
            self.df,
            show_rsi=self.cb_rsi.isChecked(),
            show_macd=self.cb_macd.isChecked(),
            show_bollinger=self.cb_bollinger.isChecked(),
            show_ma=self.cb_ma.isChecked(),
            show_volume=self.cb_volume.isChecked(),
            patterns=self.patterns
        )