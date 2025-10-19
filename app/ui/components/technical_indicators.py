# app/ui/components/technical_indicators.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel
from PyQt5.QtGui import QFont

class TechnicalIndicatorsPanel(QWidget):
    """Panel untuk toggle technical indicators"""
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("📈 Technical Indicators")
        title.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addWidget(title)
        
        # Checkboxes
        self.cb_ma = QCheckBox("Moving Averages (SMA/EMA)")
        self.cb_bollinger = QCheckBox("Bollinger Bands")
        self.cb_rsi = QCheckBox("RSI (14)")
        self.cb_macd = QCheckBox("MACD")
        self.cb_volume = QCheckBox("Volume")
        
        self.cb_ma.setChecked(True)
        
        layout.addWidget(self.cb_ma)
        layout.addWidget(self.cb_bollinger)
        layout.addWidget(self.cb_rsi)
        layout.addWidget(self.cb_macd)
        layout.addWidget(self.cb_volume)
        
        layout.addStretch()