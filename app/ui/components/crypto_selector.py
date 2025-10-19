from PyQt5.QtWidgets import QWidget, QHBoxLayout, QComboBox, QPushButton, QLabel, QLineEdit

class CryptoSelector(QWidget):
    def __init__(self, available_pairs=None):
        super().__init__()
        layout = QHBoxLayout(self)

        # Search pair
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search pair...")
        self.search_input.textChanged.connect(self.filter_pairs)

        # Dropdown pair
        self.pair_combo = QComboBox()
        self.all_pairs = available_pairs or ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
        self.pair_combo.addItems(sorted(self.all_pairs))

        # Timeframe selector
        self.timeframe_label = QLabel("Timeframe:")
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["1m", "5m", "15m", "1h", "4h", "1d"])

        # Refresh button
        self.refresh_btn = QPushButton("Refresh")

        # Layout
        layout.addWidget(QLabel("Search Pair:"))
        layout.addWidget(self.search_input)
        layout.addWidget(QLabel("Pair:"))
        layout.addWidget(self.pair_combo)
        layout.addWidget(self.timeframe_label)
        layout.addWidget(self.timeframe_combo)
        layout.addWidget(self.refresh_btn)
        layout.addStretch()

    def filter_pairs(self, text):
        filtered = [p for p in self.all_pairs if text.upper() in p.upper()]
        self.pair_combo.clear()
        self.pair_combo.addItems(filtered)
