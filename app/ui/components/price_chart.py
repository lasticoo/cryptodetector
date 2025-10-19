# app/ui/components/price_chart.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from matplotlib.dates import DateFormatter
import numpy as np

class PriceChart(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Dark theme
        plt.style.use('dark_background')
        
        self.figure = Figure(figsize=(14, 8), dpi=100)
        self.figure.patch.set_facecolor('#1e1e1e')
        self.canvas = FigureCanvas(self.figure)
        
        # Grid dari axes
        self.ax_price = self.figure.add_subplot(4, 1, (1, 2))
        self.ax_rsi = self.figure.add_subplot(4, 1, 3)
        self.ax_macd = self.figure.add_subplot(4, 1, 4)
        
        self.figure.subplots_adjust(hspace=0.35, left=0.08, right=0.95, top=0.96, bottom=0.12)
        
        # Style
        for ax in [self.ax_price, self.ax_rsi, self.ax_macd]:
            ax.set_facecolor('#2d2d2d')
            ax.grid(True, alpha=0.15, color='gray', linestyle='--')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
        
        layout.addWidget(self.canvas)
        
        # Zoom buttons layout
        zoom_layout = QHBoxLayout()
        zoom_layout.setSpacing(5)
        zoom_layout.setContentsMargins(10, 5, 10, 5)
        
        self.btn_zoom_in = QPushButton("🔍+ Zoom In")
        self.btn_zoom_out = QPushButton("🔍- Zoom Out")
        self.btn_reset = QPushButton("↺ Reset View")
        
        self.btn_zoom_in.setMaximumWidth(120)
        self.btn_zoom_out.setMaximumWidth(120)
        self.btn_reset.setMaximumWidth(120)
        
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        self.btn_reset.clicked.connect(self.reset_view)
        
        zoom_layout.addWidget(self.btn_zoom_in)
        zoom_layout.addWidget(self.btn_zoom_out)
        zoom_layout.addWidget(self.btn_reset)
        zoom_layout.addStretch()
        
        layout.addLayout(zoom_layout)
        
        # Zoom state
        self.x_min = 0
        self.x_max = None
        self.df_backup = None
        self.current_params = {}

    def zoom_in(self):
        """Zoom in ke tengah chart"""
        if self.x_max is None:
            return
        
        center = (self.x_min + self.x_max) / 2
        range_val = (self.x_max - self.x_min) / 4
        
        self.x_min = max(0, center - range_val)
        self.x_max = min(len(self.df_backup), center + range_val)
        
        self.redraw_chart()

    def zoom_out(self):
        """Zoom out untuk melihat lebih lebar"""
        if self.x_max is None:
            return
        
        center = (self.x_min + self.x_max) / 2
        range_val = (self.x_max - self.x_min)
        
        self.x_min = max(0, center - range_val)
        self.x_max = min(len(self.df_backup), center + range_val)
        
        self.redraw_chart()

    def reset_view(self):
        """Reset ke view awal (semua data)"""
        self.x_min = 0
        self.x_max = None
        self.redraw_chart()

    def redraw_chart(self):
        """Redraw chart dengan current zoom level"""
        if self.df_backup is None:
            return
        
        self.update_chart(
            self.df_backup,
            show_rsi=self.current_params.get('show_rsi', False),
            show_macd=self.current_params.get('show_macd', False),
            show_bollinger=self.current_params.get('show_bollinger', False),
            show_ma=self.current_params.get('show_ma', False),
            show_volume=self.current_params.get('show_volume', False),
            patterns=self.current_params.get('patterns', None)
        )

    def update_chart(self, df, show_rsi=False, show_macd=False, show_bollinger=False, 
                     show_ma=False, show_volume=False, patterns=None):
        if df.empty:
            return
        
        # Backup data dan params
        self.df_backup = df.copy()
        self.current_params = {
            'show_rsi': show_rsi,
            'show_macd': show_macd,
            'show_bollinger': show_bollinger,
            'show_ma': show_ma,
            'show_volume': show_volume,
            'patterns': patterns
        }
        
        # Set x_max jika belum
        if self.x_max is None:
            self.x_max = len(df)
        
        # Slice data sesuai zoom level
        x_idx = np.arange(len(df))
        df_display = df.iloc[int(self.x_min):int(self.x_max)]
        x_display = x_idx[int(self.x_min):int(self.x_max)]
        
        # Clear
        self.ax_price.clear()
        self.ax_rsi.clear()
        self.ax_macd.clear()
        
        # Re-style after clear
        for ax in [self.ax_price, self.ax_rsi, self.ax_macd]:
            ax.set_facecolor('#2d2d2d')
            ax.grid(True, alpha=0.15, color='gray', linestyle='--')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
        
        # ===== CANDLESTICK =====
        width = 0.6
        for i, (idx, row) in enumerate(df_display.iterrows()):
            open_p = row['open']
            close_p = row['close']
            high_p = row['high']
            low_p = row['low']
            
            color = '#26a69a' if close_p >= open_p else '#f23645'
            x_pos = x_display[i]
            
            # High-Low line (wick)
            self.ax_price.plot([x_pos, x_pos], [low_p, high_p], color=color, linewidth=1.2)
            
            # Open-Close rectangle (body)
            height = abs(close_p - open_p)
            if height == 0:
                height = 0.0001
            bottom = min(open_p, close_p)
            rect = Rectangle((x_pos - width/2, bottom), width, height, 
                           facecolor=color, edgecolor=color, linewidth=0.5, alpha=0.9)
            self.ax_price.add_patch(rect)
        
        # Moving Averages
        if show_ma:
            colors_ma = {'sma_20': '#00d9ff', 'sma_50': '#ffd700', 
                         'ema_20': '#00ff00', 'ema_50': '#ff00ff'}
            for col, color in colors_ma.items():
                if col in df_display.columns:
                    valid = df_display[col].dropna()
                    if len(valid) > 0:
                        self.ax_price.plot(x_display, df_display[col], color=color, linewidth=2, 
                                          label=col.upper(), alpha=0.8)
        
        # Bollinger Bands
        if show_bollinger and all(x in df_display.columns for x in ['bb_high', 'bb_mid', 'bb_low']):
            self.ax_price.fill_between(x_display, df_display['bb_high'], df_display['bb_low'], 
                                       alpha=0.08, color='cyan')
            self.ax_price.plot(x_display, df_display['bb_high'], 'c--', linewidth=1, alpha=0.5, label='BB High')
            self.ax_price.plot(x_display, df_display['bb_mid'], 'b-', linewidth=1.5, alpha=0.7, label='BB Mid')
            self.ax_price.plot(x_display, df_display['bb_low'], 'c--', linewidth=1, alpha=0.5, label='BB Low')
        
        # Volume bars
        if show_volume and 'volume' in df_display.columns:
            ax_vol = self.ax_price.twinx()
            vol_colors = ['#26a69a' if df_display['close'].iloc[i] >= df_display['open'].iloc[i] else '#f23645' 
                         for i in range(len(df_display))]
            ax_vol.bar(x_display, df_display['volume'], alpha=0.15, color=vol_colors, width=0.8)
            ax_vol.set_ylabel('Volume', color='gray', fontsize=9)
            ax_vol.tick_params(axis='y', labelcolor='gray', labelsize=8)
            ax_vol.spines['right'].set_color('gray')
        
        # ===== RSI =====
        if show_rsi and 'rsi' in df_display.columns:
            self.ax_rsi.plot(x_display, df_display['rsi'], color='#9c27b0', linewidth=2)
            self.ax_rsi.axhline(70, color='#f23645', linestyle='--', linewidth=1, alpha=0.7, label='Overbought')
            self.ax_rsi.axhline(30, color='#26a69a', linestyle='--', linewidth=1, alpha=0.7, label='Oversold')
            self.ax_rsi.fill_between(x_display, 30, 70, alpha=0.05, color='gray')
            self.ax_rsi.set_ylabel('RSI', fontsize=10, fontweight='bold')
            self.ax_rsi.set_ylim(0, 100)
            self.ax_rsi.grid(True, alpha=0.15)
            self.ax_rsi.legend(loc='upper right', fontsize=8)
            self.ax_rsi.tick_params(axis='y', labelsize=8)
        
        # ===== MACD =====
        if show_macd and all(x in df_display.columns for x in ['macd', 'macd_signal', 'macd_histogram']):
            colors = ['#26a69a' if x >= 0 else '#f23645' for x in df_display['macd_histogram']]
            self.ax_macd.bar(x_display, df_display['macd_histogram'], color=colors, alpha=0.3, width=0.8, label='Histogram')
            self.ax_macd.plot(x_display, df_display['macd'], color='#2196f3', linewidth=2, label='MACD')
            self.ax_macd.plot(x_display, df_display['macd_signal'], color='#ff9800', linewidth=2, label='Signal')
            self.ax_macd.axhline(0, color='gray', linestyle='-', linewidth=0.8, alpha=0.5)
            self.ax_macd.set_ylabel('MACD', fontsize=10, fontweight='bold')
            self.ax_macd.set_xlabel('Time', fontsize=10, fontweight='bold')
            self.ax_macd.grid(True, alpha=0.15)
            self.ax_macd.legend(loc='upper left', fontsize=8)
            self.ax_macd.tick_params(axis='both', labelsize=8)
        
        # ===== DATE LABELS =====
        # Format x-axis dengan tanggal
        date_labels = [df.index[int(self.x_min + i)].strftime('%m-%d %H:%M') 
                      for i in range(min(10, len(x_display)))]
        
        if len(x_display) > 10:
            step = len(x_display) // 10
            tick_positions = x_display[::step]
            tick_labels = [df.index[int(self.x_min + i*step)].strftime('%m-%d %H:%M') 
                          for i in range(len(tick_positions))]
            self.ax_price.set_xticks(tick_positions)
            self.ax_price.set_xticklabels(tick_labels, rotation=45, ha='right', fontsize=9)
        else:
            self.ax_price.set_xticklabels(date_labels, rotation=45, ha='right', fontsize=9)
        
        # ===== PATTERN ANNOTATIONS =====
        if patterns:
            text_y = 0.97
            for pattern_name, detections in patterns.items():
                if detections:
                    count = len(detections) if isinstance(detections, list) else 1
                    self.ax_price.text(0.01, text_y, f"⚡ {pattern_name} ({count})", 
                                      transform=self.ax_price.transAxes, fontsize=11, 
                                      color='#ff6b6b', weight='bold', verticalalignment='top',
                                      bbox=dict(boxstyle='round,pad=0.5', facecolor='#1e1e1e', alpha=0.7))
                    text_y -= 0.06
        
        # Formatting
        self.ax_price.set_ylabel('Price (USD)', fontsize=11, fontweight='bold')
        self.ax_price.tick_params(axis='y', labelsize=9)
        self.ax_price.grid(True, alpha=0.15)
        
        if show_ma:
            self.ax_price.legend(loc='upper left', fontsize=8, framealpha=0.9)
        
        self.canvas.draw()