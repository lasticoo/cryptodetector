import numpy as np
import pandas as pd
from scipy.signal import argrelextrema

class PatternRecognition:
    def __init__(self, df):
        self.df = df
        
    def _find_peaks(self, data, order=5):
        """Find local peaks using scipy"""
        try:
            peaks = argrelextrema(data.values, np.greater, order=order)[0]
            return peaks.tolist() if len(peaks) > 0 else []
        except:
            return []
    
    def _find_troughs(self, data, order=5):
        """Find local troughs using scipy"""
        try:
            troughs = argrelextrema(data.values, np.less, order=order)[0]
            return troughs.tolist() if len(troughs) > 0 else []
        except:
            return []
        
    def find_double_top(self, threshold=0.02):
        """Detect Double Top pattern"""
        if len(self.df) < 10:
            return []
        
        peaks = self._find_peaks(self.df['high'], order=5)
        
        if len(peaks) < 2:
            return []
        
        double_tops = []
        for i in range(len(peaks)-1):
            try:
                p1_price = self.df['high'].iloc[peaks[i]]
                p2_price = self.df['high'].iloc[peaks[i+1]]
                
                price_diff = abs(p1_price - p2_price) / p1_price
                
                if price_diff < threshold and peaks[i+1] - peaks[i] >= 5:
                    double_tops.append({
                        'first_top': peaks[i],
                        'second_top': peaks[i+1],
                        'price': p1_price,
                        'difference': price_diff
                    })
            except:
                pass
        
        return double_tops
    
    def find_double_bottom(self, threshold=0.02):
        """Detect Double Bottom pattern"""
        if len(self.df) < 10:
            return []
        
        troughs = self._find_troughs(self.df['low'], order=5)
        
        if len(troughs) < 2:
            return []
        
        double_bottoms = []
        for i in range(len(troughs)-1):
            try:
                t1_price = self.df['low'].iloc[troughs[i]]
                t2_price = self.df['low'].iloc[troughs[i+1]]
                
                price_diff = abs(t1_price - t2_price) / t1_price
                
                if price_diff < threshold and troughs[i+1] - troughs[i] >= 5:
                    double_bottoms.append({
                        'first_bottom': troughs[i],
                        'second_bottom': troughs[i+1],
                        'price': t1_price,
                        'difference': price_diff
                    })
            except:
                pass
        
        return double_bottoms
    
    def find_head_and_shoulders(self, threshold=0.02):
        """Detect Head and Shoulders pattern"""
        if len(self.df) < 15:
            return []
        
        peaks = self._find_peaks(self.df['high'], order=5)
        
        if len(peaks) < 3:
            return []
        
        head_shoulders = []
        for i in range(len(peaks)-2):
            try:
                left_shoulder = self.df['high'].iloc[peaks[i]]
                head = self.df['high'].iloc[peaks[i+1]]
                right_shoulder = self.df['high'].iloc[peaks[i+2]]
                
                # Head should be higher
                if head > left_shoulder and head > right_shoulder:
                    shoulder_diff = abs(left_shoulder - right_shoulder) / left_shoulder
                    
                    if shoulder_diff < threshold and peaks[i+1] - peaks[i] >= 5:
                        head_shoulders.append({
                            'left_shoulder': peaks[i],
                            'head': peaks[i+1],
                            'right_shoulder': peaks[i+2],
                            'shoulder_price': (left_shoulder + right_shoulder) / 2
                        })
            except:
                pass
        
        return head_shoulders
    
    def find_triangle_patterns(self, window=20):
        """Detect Triangle patterns (Ascending, Descending, Symmetric)"""
        if len(self.df) < window:
            return []
        
        triangles = []
        
        for i in range(window, len(self.df)):
            try:
                segment = self.df.iloc[i-window:i]
                
                highs = segment['high'].values
                lows = segment['low'].values
                
                # Linear regression
                x = np.arange(window)
                
                high_coeffs = np.polyfit(x, highs, 1)
                low_coeffs = np.polyfit(x, lows, 1)
                
                high_slope = high_coeffs[0]
                low_slope = low_coeffs[0]
                
                # Identify triangle patterns
                if abs(high_slope) < 0.001 and low_slope > 0.001:
                    triangles.append({
                        'index': i,
                        'type': 'ascending_triangle',
                        'high_slope': high_slope,
                        'low_slope': low_slope
                    })
                elif high_slope < -0.001 and abs(low_slope) < 0.001:
                    triangles.append({
                        'index': i,
                        'type': 'descending_triangle',
                        'high_slope': high_slope,
                        'low_slope': low_slope
                    })
                elif high_slope < -0.001 and low_slope > 0.001:
                    triangles.append({
                        'index': i,
                        'type': 'symmetric_triangle',
                        'high_slope': high_slope,
                        'low_slope': low_slope
                    })
            except:
                pass
        
        return triangles
    
    def find_hammer_patterns(self):
        """Detect Hammer and Inverted Hammer patterns"""
        if len(self.df) < 2:
            return []
        
        hammers = []
        
        for i in range(len(self.df)):
            try:
                candle = self.df.iloc[i]
                body = abs(candle['open'] - candle['close'])
                upper_shadow = candle['high'] - max(candle['open'], candle['close'])
                lower_shadow = min(candle['open'], candle['close']) - candle['low']
                
                total_height = candle['high'] - candle['low']
                
                if total_height == 0:
                    continue
                
                # Hammer: long lower shadow, small body, small upper shadow
                if lower_shadow > (2 * body) and upper_shadow < (0.5 * body):
                    hammers.append({
                        'index': i,
                        'type': 'hammer',
                        'strength': lower_shadow / body if body > 0 else 0
                    })
                
                # Inverted Hammer: long upper shadow, small body, small lower shadow
                elif upper_shadow > (2 * body) and lower_shadow < (0.5 * body):
                    hammers.append({
                        'index': i,
                        'type': 'inverted_hammer',
                        'strength': upper_shadow / body if body > 0 else 0
                    })
            except:
                pass
        
        return hammers
