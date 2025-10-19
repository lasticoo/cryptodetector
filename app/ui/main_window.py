# app/ui/main_window.py
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QMessageBox, QLineEdit, QLabel, QComboBox, 
                             QPushButton, QCheckBox, QTableWidget,
                             QTableWidgetItem, QFrame, QScrollArea, QTextEdit,
                             QSplitter, QTabWidget)
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
        
        # ===== MAIN CONTENT dengan Splitter =====
        # Splitter untuk resize area chart vs sidebar
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setStyleSheet("QSplitter::handle { background: #444; }")
        
        # LEFT SIDE: Chart + Stats (60%)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)
        
        # Chart area
        self.price_chart = PriceChart()
        left_layout.addWidget(self.price_chart, stretch=1)
        
        # Bottom panel - Statistics
        stats_panel = self.create_stats_panel()
        left_layout.addWidget(stats_panel, stretch=0)
        
        main_splitter.addWidget(left_widget)
        
        # RIGHT SIDE: Tab Widget dengan Sidebar + Sentiment (40%)
        right_tabs = QTabWidget()
        
        # Tab 1: Technical Analysis Sidebar
        self.tech_sidebar = self.create_technical_sidebar()
        right_tabs.addTab(self.tech_sidebar, "📊 Technical")
        
        # Tab 2: Sentiment & News Panel
        try:
            self.sentiment_panel = SentimentPanel()
            right_tabs.addTab(self.sentiment_panel, "📈 Sentiment & News")
        except Exception as e:
            print(f"Warning: Sentiment panel not loaded: {e}")
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel(f"Sentiment panel error: {str(e)}\n\nMake sure all dependencies are installed:\npip install feedparser requests")
            error_label.setStyleSheet("color: #f23645; padding: 10px;")
            error_layout.addWidget(error_label)
            error_layout.addStretch()
            right_tabs.addTab(error_widget, "📈 Sentiment & News")
        
        main_splitter.addWidget(right_tabs)
        
        # Set splitter proportions (60% left, 40% right)
        main_splitter.setSizes([1200, 800])
        main_splitter.setCollapsible(0, False)
        main_splitter.setCollapsible(1, True)
        
        main_layout.addWidget(main_splitter, stretch=1)

    def create_technical_sidebar(self):
        """Create technical analysis sidebar"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Price info card
        self.price_info = QLabel("Price: --\nChange: --\nVolume: --")
        self.price_info.setStyleSheet("""
            color: #0d7377; font-weight: bold; font-size: 11px;
            background-color: #1e1e1e; padding: 8px; border-radius: 3px;
        """)
        layout.addWidget(QLabel("📊 Current Price"))
        layout.addWidget(self.price_info)
        
        # Indicator toggles
        layout.addWidget(QLabel("📈 Indicators"))
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
        
        layout.addWidget(indicators_group)
        
        # Pattern detection - dengan scroll area
        pattern_header = QHBoxLayout()
        pattern_header.addWidget(QLabel("⚡ Detected Patterns"))
        self.pattern_count_label = QLabel("(0)")
        self.pattern_count_label.setStyleSheet("color: #ffd700; font-weight: bold;")
        pattern_header.addWidget(self.pattern_count_label)
        pattern_header.addStretch()
        layout.addLayout(pattern_header)
        
        # Scroll area untuk pattern list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(200)
        
        self.pattern_list = QTableWidget()
        self.pattern_list.setColumnCount(2)
        self.pattern_list.setHorizontalHeaderLabels(["Pattern", "Count"])
        self.pattern_list.setColumnWidth(0, 250)
        self.pattern_list.setColumnWidth(1, 60)
        self.pattern_list.setStyleSheet("""
            QTableWidget { gridline-color: #444; border: none; }
        """)
        self.pattern_list.cellClicked.connect(self.show_pattern_details)
        
        scroll_area.setWidget(self.pattern_list)
        layout.addWidget(scroll_area)
        
        # Pattern Details Area
        layout.addWidget(QLabel("📋 Pattern Details (Click pattern above)"))
        self.pattern_details = QTextEdit()
        self.pattern_details.setReadOnly(True)
        self.pattern_details.setMaximumHeight(150)
        self.pattern_details.setText("Click pada pattern di tabel untuk melihat detail...")
        layout.addWidget(self.pattern_details)
        
        layout.addStretch()
        
        return widget

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

    def show_pattern_details(self, row, column):
        """Show detailed information about selected pattern"""
        if not self.patterns or self.df is None:
            return
        
        pattern_name = self.pattern_list.item(row, 0).text()
        
        if pattern_name not in self.patterns:
            return
        
        detections = self.patterns[pattern_name]
        
        if not detections:
            self.pattern_details.setText("No details available.")
            return
        
        # Build detailed info
        details = f"═══ {pattern_name} ═══\n\n"
        details += f"Total Detected: {len(detections) if isinstance(detections, list) else 1}\n"
        details += "─" * 40 + "\n\n"
        
        # Get pattern interpretation
        interpretation = self.get_pattern_interpretation(pattern_name)
        details += f"📊 INTERPRETATION:\n{interpretation}\n\n"
        details += "─" * 40 + "\n\n"
        
        # Show individual detections
        if isinstance(detections, list) and len(detections) > 0:
            details += "🔍 DETECTED INSTANCES:\n\n"
            
            for i, detection in enumerate(detections[:5]):  # Show max 5
                details += f"Instance #{i+1}:\n"
                
                if isinstance(detection, dict):
                    for key, value in detection.items():
                        if key == 'index' or 'idx' in str(key).lower():
                            if value < len(self.df):
                                timestamp = self.df.index[value].strftime('%Y-%m-%d %H:%M')
                                details += f"  • Position: {timestamp} (index: {value})\n"
                        elif 'price' in str(key).lower():
                            details += f"  • {key}: ${value:,.2f}\n"
                        elif isinstance(value, (int, float)):
                            if isinstance(value, float):
                                details += f"  • {key}: {value:.4f}\n"
                            else:
                                details += f"  • {key}: {value}\n"
                        else:
                            details += f"  • {key}: {value}\n"
                else:
                    details += f"  • Detection: {detection}\n"
                
                details += "\n"
            
            if len(detections) > 5:
                details += f"... and {len(detections) - 5} more\n"
        
        self.pattern_details.setText(details)

    def get_pattern_interpretation(self, pattern_name):
        """Get interpretation/meaning of each pattern"""
        interpretations = {
            # Bullish Patterns
            'Double Bottoms': '🟢 BULLISH - Sinyal reversal naik. Harga mencoba turun 2x di level yang sama lalu berbalik naik.',
            'Triple Bottoms': '🟢 BULLISH - Reversal kuat. 3 kali harga test support dan gagal tembus.',
            'Inverse Head & Shoulders': '🟢 BULLISH - Pattern reversal klasik. Left shoulder - head - right shoulder membentuk W.',
            'Rounding Bottom': '🟢 BULLISH - Akumulasi bertahap. Harga membentuk U shape sebelum naik.',
            'Cup & Handle': '🟢 BULLISH - Continuation pattern. Setelah cup, handle adalah pullback kecil sebelum breakout.',
            'Bullish Flag': '🟢 BULLISH - Short-term continuation. Setelah rally kuat, konsolidasi kecil lalu lanjut naik.',
            'Bullish Engulfing': '🟢 BULLISH - Candle bullish "menelan" candle bearish sebelumnya. Sinyal pembalikan.',
            'Morning Star': '🟢 BULLISH - 3-candle reversal. Bearish → Small body → Bullish besar.',
            'Hammer': '🟢 BULLISH - Long lower shadow. Pembeli reject penurunan harga.',
            'Piercing Pattern': '🟢 BULLISH - Candle bullish menembus 50% body candle bearish sebelumnya.',
            'Three White Soldiers': '🟢 BULLISH - 3 candle bullish berturut-turut. Momentum kuat.',
            'Bullish Harami': '🟢 BULLISH - Small bullish inside large bearish. Sinyal pembalikan.',
            
            # Bearish Patterns
            'Double Tops': '🔴 BEARISH - Sinyal reversal turun. Harga mencoba naik 2x di level yang sama lalu berbalik turun.',
            'Triple Tops': '🔴 BEARISH - Reversal kuat. 3 kali harga test resistance dan gagal tembus.',
            'Head & Shoulders': '🔴 BEARISH - Pattern reversal klasik. Left shoulder - head - right shoulder membentuk M.',
            'Dead Cat Bounce': '🔴 BEARISH - Rally lemah setelah penurunan tajam. Harga lanjut turun.',
            'Bearish Flag': '🔴 BEARISH - Continuation pattern. Setelah drop tajam, konsolidasi kecil lalu lanjut turun.',
            'Bearish Engulfing': '🔴 BEARISH - Candle bearish "menelan" candle bullish sebelumnya.',
            'Evening Star': '🔴 BEARISH - 3-candle reversal. Bullish → Small body → Bearish besar.',
            'Shooting Star': '🔴 BEARISH - Long upper shadow. Penjual reject kenaikan harga.',
            'Dark Cloud': '🔴 BEARISH - Candle bearish menembus 50% body candle bullish sebelumnya.',
            'Three Black Crows': '🔴 BEARISH - 3 candle bearish berturut-turut. Momentum turun kuat.',
            
            # Triangles
            'Ascending Triangle': '🟢 BULLISH - Resistance datar, support naik. Biasanya breakout keatas.',
            'Descending Triangle': '🔴 BEARISH - Support datar, resistance turun. Biasanya breakdown.',
            'Symmetric Triangle': '🟡 NEUTRAL - Converging pattern. Breakout menentukan arah.',
            
            # Default
        }
        
        for key in interpretations:
            if key.lower() in pattern_name.lower() or pattern_name.lower() in key.lower():
                return interpretations[key]
        
        return '🔵 Pattern terdeteksi. Analisa lebih lanjut diperlukan untuk interpretasi.'

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
            
            self.update_price_info()
            self.update_pattern_list()
            self.update_stats_table()
            self.update_chart_display()
            
            # Update sentiment panel jika ada
            if hasattr(self, 'sentiment_panel'):
                try:
                    self.sentiment_panel.update_coin_sentiment(symbol)
                except:
                    pass
            
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
            self.pattern_count_label.setText("(0)")
            return
        
        row = 0
        total_count = 0
        
        sorted_patterns = sorted(self.patterns.items(), 
                                key=lambda x: len(x[1]) if isinstance(x[1], list) else (1 if x[1] else 0), 
                                reverse=True)
        
        for pattern_name, detections in sorted_patterns:
            if detections:
                count = len(detections) if isinstance(detections, list) else (1 if detections else 0)
                if count > 0:
                    total_count += count
                    
                    item_name = QTableWidgetItem(pattern_name)
                    item_count = QTableWidgetItem(str(count))
                    
                    if any(x in pattern_name.lower() for x in ['bullish', 'bottom', 'morning', 'white', 'hammer', 'piercing', 'inverse', 'ascending']):
                        item_count.setForeground(QColor("#26a69a"))
                        item_name.setForeground(QColor("#26a69a"))
                    elif any(x in pattern_name.lower() for x in ['bearish', 'top', 'evening', 'black', 'shooting', 'dark', 'dead', 'descending']):
                        item_count.setForeground(QColor("#f23645"))
                        item_name.setForeground(QColor("#f23645"))
                    else:
                        item_count.setForeground(QColor("#ffd700"))
                        item_name.setForeground(QColor("#ffd700"))
                    
                    item_count.setFont(QFont("Arial", 10, QFont.Bold))
                    
                    self.pattern_list.insertRow(row)
                    self.pattern_list.setItem(row, 0, item_name)
                    self.pattern_list.setItem(row, 1, item_count)
                    row += 1
        
        self.pattern_count_label.setText(f"({total_count})")
        self.setWindowTitle(f"Crypto Analyzer - {total_count} Patterns Detected")

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