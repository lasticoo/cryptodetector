# app/services/technical_analysis.py
import numpy as np
import pandas as pd
from ta.trend import SMAIndicator, EMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator, StochasticOscillator, ROCIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import VolumeWeightedAveragePrice, OnBalanceVolumeIndicator

class TechnicalAnalysisService:
    def __init__(self):
        self.df = pd.DataFrame()

    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate semua indikator teknikal"""
        self.df = df.copy()
        
        try:
            self.calculate_moving_averages()
            self.calculate_rsi()
            self.calculate_macd()
            self.calculate_bollinger_bands()
            self.calculate_stochastic()
            self.calculate_vwap()
            self.calculate_atr()
            self.calculate_adx()
            self.calculate_obv()
            self.calculate_roc()
        except Exception as e:
            print(f"Error calculating indicators: {e}")
        
        return self.df

    def calculate_rsi(self, period=14):
        try:
            self.df["rsi"] = RSIIndicator(self.df["close"], window=period).rsi()
        except:
            self.df["rsi"] = 50

    def calculate_macd(self, fast=12, slow=26, signal=9):
        try:
            macd = MACD(self.df["close"], window_slow=slow, window_fast=fast, window_sign=signal)
            self.df["macd"] = macd.macd()
            self.df["macd_signal"] = macd.macd_signal()
            self.df["macd_histogram"] = macd.macd_diff()
        except:
            self.df["macd"] = 0
            self.df["macd_signal"] = 0
            self.df["macd_histogram"] = 0

    def calculate_bollinger_bands(self, window=20, window_dev=2):
        try:
            bb = BollingerBands(self.df["close"], window=window, window_dev=window_dev)
            self.df["bb_high"] = bb.bollinger_hband()
            self.df["bb_mid"] = bb.bollinger_mavg()
            self.df["bb_low"] = bb.bollinger_lband()
        except:
            self.df["bb_high"] = self.df["close"]
            self.df["bb_mid"] = self.df["close"]
            self.df["bb_low"] = self.df["close"]

    def calculate_moving_averages(self):
        try:
            self.df["sma_20"] = SMAIndicator(self.df["close"], window=20).sma_indicator()
            self.df["sma_50"] = SMAIndicator(self.df["close"], window=50).sma_indicator()
            self.df["sma_200"] = SMAIndicator(self.df["close"], window=200).sma_indicator()
            self.df["ema_20"] = EMAIndicator(self.df["close"], window=20).ema_indicator()
            self.df["ema_50"] = EMAIndicator(self.df["close"], window=50).ema_indicator()
        except:
            pass

    def calculate_stochastic(self, window=14, smooth_window=3):
        try:
            stoch = StochasticOscillator(
                self.df["high"], self.df["low"], self.df["close"], 
                window=window, smooth_window=smooth_window
            )
            self.df["stoch_k"] = stoch.stoch()
            self.df["stoch_d"] = stoch.stoch_signal()
        except:
            self.df["stoch_k"] = 50
            self.df["stoch_d"] = 50

    def calculate_vwap(self, window=14):
        try:
            vwap = VolumeWeightedAveragePrice(
                self.df["high"], self.df["low"], self.df["close"], 
                self.df["volume"], window=window
            )
            self.df["vwap"] = vwap.volume_weighted_average_price()
        except:
            self.df["vwap"] = self.df["close"]

    def calculate_atr(self, window=14):
        try:
            atr = AverageTrueRange(
                self.df["high"], self.df["low"], self.df["close"], window=window
            )
            self.df["atr"] = atr.average_true_range()
        except:
            self.df["atr"] = 0

    def calculate_adx(self, window=14):
        try:
            adx = ADXIndicator(
                self.df["high"], self.df["low"], self.df["close"], window=window
            )
            self.df["adx"] = adx.adx()
        except:
            self.df["adx"] = 20

    def calculate_obv(self):
        try:
            obv = OnBalanceVolumeIndicator(self.df["close"], self.df["volume"])
            self.df["obv"] = obv.on_balance_volume()
        except:
            self.df["obv"] = 0

    def calculate_roc(self, window=12):
        try:
            roc = ROCIndicator(self.df["close"], window=window)
            self.df["roc"] = roc.roc()
        except:
            self.df["roc"] = 0
