# app/ui/components/crypto_selector.py
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QComboBox, QPushButton, QLabel, QLineEdit
from PyQt5.QtGui import QFont

class CryptoSelector(QWidget):
    """Component untuk memilih crypto pair dan timeframe"""
    def __init__(self, available_pairs=None):
        super().__init__()
        self.all_pairs = available_pairs or ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(10)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search pair...")
        self.search_input.setMaximumWidth(200)
        layout.addWidget(QLabel("Search:"))
        layout.addWidget(self.search_input)

        # Pair combo
        layout.addWidget(QLabel("Pair:"))
        self.pair_combo = QComboBox()
        self.pair_combo.addItems(sorted(self.all_pairs))
        self.pair_combo.setMinimumWidth(120)
        layout.addWidget(self.pair_combo)

        # Timeframe combo
        layout.addWidget(QLabel("Timeframe:"))
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"])
        self.timeframe_combo.setMinimumWidth(80)
        layout.addWidget(self.timeframe_combo)

        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setMaximumWidth(100)
        layout.addWidget(self.refresh_btn)

        layout.addStretch()

    def filter_pairs(self, text):
        """Filter pairs berdasarkan text"""
        filtered = [p for p in self.all_pairs if text.upper() in p.upper()]
        self.pair_combo.clear()
        self.pair_combo.addItems(filtered if filtered else self.all_pairs)