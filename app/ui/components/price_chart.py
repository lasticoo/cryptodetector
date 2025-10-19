# app/ui/components/price_chart.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import mplfinance as mpf
from matplotlib.patches import Rectangle
import numpy as np

class PriceChart(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Dark theme
        plt.style.use('dark_background')
        
        self.figure = Figure(figsize=(14, 8), dpi=100)
        self.figure.patch.set_facecolor('#1e1e1e')
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # Grid dari axes
        self.ax_price = self.figure.add_subplot(4, 1, (1, 2))  # Candlestick (40%)
        self.ax_rsi = self.figure.add_subplot(4, 1, 3)         # RSI (20%)
        self.ax_macd = self.figure.add_subplot(4, 1, 4)        # MACD (20%)
        
        self.figure.subplots_adjust(hspace=0.3, left=0.07, right=0.95, top=0.95, bottom=0.08)
        
        # Style
        for ax in [self.ax_price, self.ax_rsi, self.ax_macd]:
            ax.set_facecolor('#2d2d2d')
            ax.grid(True, alpha=0.2, color='gray')

    def update_chart(self, df, show_rsi=False, show_macd=False, show_bollinger=False, 
                     show_ma=False, show_volume=False, patterns=None):
        if df.empty:
            return
        
        # Clear
        self.ax_price.clear()
        self.ax_rsi.clear()
        self.ax_macd.clear()
        
        x_idx = np.arange(len(df))
        
        # ===== CANDLESTICK =====
        width = 0.6
        for i in range(len(df)):
            open_p = df['open'].iloc[i]
            close_p = df['close'].iloc[i]
            high_p = df['high'].iloc[i]
            low_p = df['low'].iloc[i]
            
            color = '#26a69a' if close_p >= open_p else '#f23645'
            
            # High-Low line
            self.ax_price.plot([i, i], [low_p, high_p], color=color, linewidth=1)
            
            # Open-Close rectangle
            height = abs(close_p - open_p)
            bottom = min(open_p, close_p)
            rect = Rectangle((i - width/2, bottom), width, height, 
                           facecolor=color, edgecolor=color, linewidth=0.5)
            self.ax_price.add_patch(rect)
        
        # Moving Averages
        if show_ma:
            for col, color in [('sma_20', '#00d9ff'), ('sma_50', '#ffd700'), 
                               ('ema_20', '#00ff00'), ('ema_50', '#ff00ff')]:
                if col in df.columns:
                    self.ax_price.plot(x_idx, df[col], color=color, linewidth=1.5, 
                                      label=col.upper(), alpha=0.8)
        
        # Bollinger Bands
        if show_bollinger and all(x in df.columns for x in ['bb_high', 'bb_mid', 'bb_low']):
            self.ax_price.fill_between(x_idx, df['bb_high'], df['bb_low'], 
                                       alpha=0.1, color='cyan')
            self.ax_price.plot(x_idx, df['bb_high'], 'c--', linewidth=1, alpha=0.5)
            self.ax_price.plot(x_idx, df['bb_mid'], 'b-', linewidth=1, alpha=0.7)
            self.ax_price.plot(x_idx, df['bb_low'], 'c--', linewidth=1, alpha=0.5)
        
        # Volume
        if show_volume and 'volume' in df.columns:
            ax_vol = self.ax_price.twinx()
            ax_vol.bar(x_idx, df['volume'], alpha=0.2, color='gray', width=0.8)
            ax_vol.set_ylabel('Volume', color='gray', fontsize=9)
            ax_vol.tick_params(axis='y', labelcolor='gray')
        
        # ===== RSI =====
        if show_rsi and 'rsi' in df.columns:
            self.ax_rsi.plot(x_idx, df['rsi'], color='#9c27b0', linewidth=1.5)
            self.ax_rsi.axhline(70, color='red', linestyle='--', linewidth=0.7, alpha=0.7)
            self.ax_rsi.axhline(30, color='green', linestyle='--', linewidth=0.7, alpha=0.7)
            self.ax_rsi.fill_between(x_idx, 30, 70, alpha=0.1, color='gray')
            self.ax_rsi.set_ylabel('RSI', fontsize=9)
            self.ax_rsi.set_ylim(0, 100)
            self.ax_rsi.grid(True, alpha=0.2)
        
        # ===== MACD =====
        if show_macd and all(x in df.columns for x in ['macd', 'macd_signal', 'macd_histogram']):
            colors = ['#26a69a' if x >= 0 else '#f23645' for x in df['macd_histogram']]
            self.ax_macd.bar(x_idx, df['macd_histogram'], color=colors, alpha=0.3, width=0.8)
            self.ax_macd.plot(x_idx, df['macd'], color='#2196f3', linewidth=1.5, label='MACD')
            self.ax_macd.plot(x_idx, df['macd_signal'], color='#ff9800', linewidth=1.5, label='Signal')
            self.ax_macd.axhline(0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
            self.ax_macd.set_ylabel('MACD', fontsize=9)
            self.ax_macd.grid(True, alpha=0.2)
            self.ax_macd.legend(loc='upper left', fontsize=8)
        
        # ===== PATTERN ANNOTATIONS =====
        if patterns:
            text_y = 0.98
            for pattern_type, detections in patterns.items():
                if detections:
                    count = len(detections) if isinstance(detections, list) else 1
                    self.ax_price.text(0.02, text_y, f"⚡ {pattern_type.replace('_', ' ').upper()}", 
                                      transform=self.ax_price.transAxes, fontsize=10, 
                                      color='#ff6b6b', weight='bold', verticalalignment='top')
                    text_y -= 0.05
        
        # Formatting
        self.ax_price.set_ylabel('Price', fontsize=10, fontweight='bold')
        self.ax_price.tick_params(axis='x', labelsize=8)
        self.ax_price.tick_params(axis='y', labelsize=8)
        
        if show_rsi:
            self.ax_rsi.tick_params(axis='x', labelsize=8)
            self.ax_rsi.tick_params(axis='y', labelsize=8)
        
        if show_macd:
            self.ax_macd.set_xlabel('Time', fontsize=9)
            self.ax_macd.tick_params(axis='x', labelsize=8)
            self.ax_macd.tick_params(axis='y', labelsize=8)
        
        self.canvas.draw()