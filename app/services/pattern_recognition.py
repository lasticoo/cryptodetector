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
    
    def _calculate_slope(self, points):
        """Calculate slope from list of (index, value) tuples"""
        if len(points) < 2:
            return 0
        x = np.array([p[0] for p in points])
        y = np.array([p[1] for p in points])
        return np.polyfit(x, y, 1)[0]
        
    # ========== EXISTING PATTERNS ==========
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

    # ========== NEW PATTERNS FROM IMAGE ==========
    
    def find_triple_top(self, threshold=0.02):
        """Detect Triple Top pattern"""
        if len(self.df) < 15:
            return []
        
        peaks = self._find_peaks(self.df['high'], order=5)
        if len(peaks) < 3:
            return []
        
        triple_tops = []
        for i in range(len(peaks)-2):
            try:
                p1 = self.df['high'].iloc[peaks[i]]
                p2 = self.df['high'].iloc[peaks[i+1]]
                p3 = self.df['high'].iloc[peaks[i+2]]
                
                diff1 = abs(p1 - p2) / p1
                diff2 = abs(p2 - p3) / p2
                
                if diff1 < threshold and diff2 < threshold:
                    triple_tops.append({
                        'peaks': [peaks[i], peaks[i+1], peaks[i+2]],
                        'price': (p1 + p2 + p3) / 3
                    })
            except:
                pass
        
        return triple_tops
    
    def find_triple_bottom(self, threshold=0.02):
        """Detect Triple Bottom pattern"""
        if len(self.df) < 15:
            return []
        
        troughs = self._find_troughs(self.df['low'], order=5)
        if len(troughs) < 3:
            return []
        
        triple_bottoms = []
        for i in range(len(troughs)-2):
            try:
                t1 = self.df['low'].iloc[troughs[i]]
                t2 = self.df['low'].iloc[troughs[i+1]]
                t3 = self.df['low'].iloc[troughs[i+2]]
                
                diff1 = abs(t1 - t2) / t1
                diff2 = abs(t2 - t3) / t2
                
                if diff1 < threshold and diff2 < threshold:
                    triple_bottoms.append({
                        'troughs': [troughs[i], troughs[i+1], troughs[i+2]],
                        'price': (t1 + t2 + t3) / 3
                    })
            except:
                pass
        
        return triple_bottoms
    
    def find_rounding_bottom(self, window=20):
        """Detect Rounding Bottom (Cup) pattern"""
        if len(self.df) < window:
            return []
        
        patterns = []
        for i in range(window, len(self.df)):
            try:
                segment = self.df.iloc[i-window:i]
                lows = segment['low'].values
                
                # Fit parabola
                x = np.arange(len(lows))
                coeffs = np.polyfit(x, lows, 2)
                
                # Check if U-shaped (positive curvature)
                if coeffs[0] > 0.00001:
                    patterns.append({
                        'index': i,
                        'start': i-window,
                        'curvature': coeffs[0]
                    })
            except:
                pass
        
        return patterns
    
    def find_cup_and_handle(self, window=30):
        """Detect Cup and Handle pattern"""
        if len(self.df) < window + 10:
            return []
        
        patterns = []
        rounding = self.find_rounding_bottom(window)
        
        for cup in rounding:
            try:
                # Check for handle after cup
                handle_start = cup['index']
                handle_segment = self.df.iloc[handle_start:handle_start+10]
                
                if len(handle_segment) >= 5:
                    # Handle should show slight pullback
                    handle_high = handle_segment['high'].max()
                    handle_low = handle_segment['low'].min()
                    
                    if (handle_high - handle_low) / handle_high < 0.15:
                        patterns.append({
                            'cup_start': cup['start'],
                            'cup_end': cup['index'],
                            'handle_end': handle_start + 10
                        })
            except:
                pass
        
        return patterns
    
    def find_ascending_wedge(self, window=15):
        """Detect Ascending Wedge (Broadening pattern)"""
        if len(self.df) < window:
            return []
        
        patterns = []
        for i in range(window, len(self.df)):
            try:
                segment = self.df.iloc[i-window:i]
                highs = segment['high'].values
                lows = segment['low'].values
                
                x = np.arange(len(highs))
                high_slope = np.polyfit(x, highs, 1)[0]
                low_slope = np.polyfit(x, lows, 1)[0]
                
                # Both slopes positive, converging upward
                if high_slope > 0 and low_slope > 0 and high_slope < low_slope * 2:
                    patterns.append({
                        'index': i,
                        'start': i-window,
                        'high_slope': high_slope,
                        'low_slope': low_slope
                    })
            except:
                pass
        
        return patterns
    
    def find_descending_wedge(self, window=15):
        """Detect Descending Wedge (Broadening pattern)"""
        if len(self.df) < window:
            return []
        
        patterns = []
        for i in range(window, len(self.df)):
            try:
                segment = self.df.iloc[i-window:i]
                highs = segment['high'].values
                lows = segment['low'].values
                
                x = np.arange(len(highs))
                high_slope = np.polyfit(x, highs, 1)[0]
                low_slope = np.polyfit(x, lows, 1)[0]
                
                # Both slopes negative, converging downward
                if high_slope < 0 and low_slope < 0 and low_slope < high_slope * 2:
                    patterns.append({
                        'index': i,
                        'start': i-window,
                        'high_slope': high_slope,
                        'low_slope': low_slope
                    })
            except:
                pass
        
        return patterns
    
    def find_rising_wedge(self, window=15):
        """Detect Rising Wedge (narrowing upward)"""
        if len(self.df) < window:
            return []
        
        patterns = []
        for i in range(window, len(self.df)):
            try:
                segment = self.df.iloc[i-window:i]
                
                peaks = self._find_peaks(segment['high'], order=3)
                troughs = self._find_troughs(segment['low'], order=3)
                
                if len(peaks) >= 2 and len(troughs) >= 2:
                    peak_prices = [segment['high'].iloc[p] for p in peaks]
                    trough_prices = [segment['low'].iloc[t] for t in troughs]
                    
                    peak_slope = self._calculate_slope(list(zip(peaks, peak_prices)))
                    trough_slope = self._calculate_slope(list(zip(troughs, trough_prices)))
                    
                    # Both rising, but converging
                    if peak_slope > 0 and trough_slope > 0 and trough_slope > peak_slope:
                        patterns.append({
                            'index': i,
                            'start': i-window,
                            'type': 'rising_wedge'
                        })
            except:
                pass
        
        return patterns
    
    def find_falling_wedge(self, window=15):
        """Detect Falling Wedge (narrowing downward)"""
        if len(self.df) < window:
            return []
        
        patterns = []
        for i in range(window, len(self.df)):
            try:
                segment = self.df.iloc[i-window:i]
                
                peaks = self._find_peaks(segment['high'], order=3)
                troughs = self._find_troughs(segment['low'], order=3)
                
                if len(peaks) >= 2 and len(troughs) >= 2:
                    peak_prices = [segment['high'].iloc[p] for p in peaks]
                    trough_prices = [segment['low'].iloc[t] for t in troughs]
                    
                    peak_slope = self._calculate_slope(list(zip(peaks, peak_prices)))
                    trough_slope = self._calculate_slope(list(zip(troughs, trough_prices)))
                    
                    # Both falling, but converging
                    if peak_slope < 0 and trough_slope < 0 and peak_slope < trough_slope:
                        patterns.append({
                            'index': i,
                            'start': i-window,
                            'type': 'falling_wedge'
                        })
            except:
                pass
        
        return patterns
    
    def find_flag_pattern(self, window=10):
        """Detect Flag patterns (Bullish and Bearish)"""
        if len(self.df) < window + 5:
            return []
        
        patterns = []
        for i in range(window + 5, len(self.df)):
            try:
                # Look for strong move (pole)
                pole = self.df.iloc[i-window-5:i-window]
                flag = self.df.iloc[i-window:i]
                
                pole_change = (pole['close'].iloc[-1] - pole['close'].iloc[0]) / pole['close'].iloc[0]
                
                # Strong bullish pole
                if pole_change > 0.05:
                    flag_slope = np.polyfit(range(len(flag)), flag['close'].values, 1)[0]
                    # Slight downward consolidation
                    if -0.002 < flag_slope < 0:
                        patterns.append({
                            'index': i,
                            'type': 'bullish_flag',
                            'pole_start': i-window-5
                        })
                
                # Strong bearish pole
                elif pole_change < -0.05:
                    flag_slope = np.polyfit(range(len(flag)), flag['close'].values, 1)[0]
                    # Slight upward consolidation
                    if 0 < flag_slope < 0.002:
                        patterns.append({
                            'index': i,
                            'type': 'bearish_flag',
                            'pole_start': i-window-5
                        })
            except:
                pass
        
        return patterns
    
    def find_pennant_pattern(self, window=10):
        """Detect Pennant patterns (similar to flags but triangular)"""
        if len(self.df) < window + 5:
            return []
        
        patterns = []
        for i in range(window + 5, len(self.df)):
            try:
                pole = self.df.iloc[i-window-5:i-window]
                pennant = self.df.iloc[i-window:i]
                
                pole_change = (pole['close'].iloc[-1] - pole['close'].iloc[0]) / pole['close'].iloc[0]
                
                if abs(pole_change) > 0.05:
                    # Check if pennant is converging
                    highs = pennant['high'].values
                    lows = pennant['low'].values
                    
                    range_start = highs[0] - lows[0]
                    range_end = highs[-1] - lows[-1]
                    
                    if range_end < range_start * 0.5:
                        pattern_type = 'bullish_pennant' if pole_change > 0 else 'bearish_pennant'
                        patterns.append({
                            'index': i,
                            'type': pattern_type,
                            'pole_start': i-window-5
                        })
            except:
                pass
        
        return patterns
    
    def find_channel_patterns(self, window=20):
        """Detect Ascending and Descending Channels"""
        if len(self.df) < window:
            return []
        
        patterns = []
        for i in range(window, len(self.df)):
            try:
                segment = self.df.iloc[i-window:i]
                highs = segment['high'].values
                lows = segment['low'].values
                
                x = np.arange(len(highs))
                high_slope = np.polyfit(x, highs, 1)[0]
                low_slope = np.polyfit(x, lows, 1)[0]
                
                # Check if slopes are parallel
                slope_diff = abs(high_slope - low_slope) / abs(high_slope) if high_slope != 0 else 1
                
                if slope_diff < 0.3:  # Relatively parallel
                    if high_slope > 0.001 and low_slope > 0.001:
                        patterns.append({
                            'index': i,
                            'type': 'ascending_channel',
                            'start': i-window
                        })
                    elif high_slope < -0.001 and low_slope < -0.001:
                        patterns.append({
                            'index': i,
                            'type': 'descending_channel',
                            'start': i-window
                        })
            except:
                pass
        
        return patterns
    
    def find_bump_and_run(self, window=30):
        """Detect Bump and Run Reversal pattern"""
        if len(self.df) < window:
            return []
        
        patterns = []
        for i in range(window, len(self.df)):
            try:
                segment = self.df.iloc[i-window:i]
                
                # Divide into three phases
                lead_in = segment.iloc[:window//3]
                bump = segment.iloc[window//3:2*window//3]
                run = segment.iloc[2*window//3:]
                
                # Lead-in: moderate slope
                lead_slope = np.polyfit(range(len(lead_in)), lead_in['close'].values, 1)[0]
                
                # Bump: steeper slope
                bump_slope = np.polyfit(range(len(bump)), bump['close'].values, 1)[0]
                
                # Run: reversal
                run_slope = np.polyfit(range(len(run)), run['close'].values, 1)[0]
                
                if lead_slope > 0 and bump_slope > lead_slope * 2 and run_slope < 0:
                    patterns.append({
                        'index': i,
                        'start': i-window,
                        'type': 'bump_and_run_reversal'
                    })
            except:
                pass
        
        return patterns
    
    def find_dragon_pattern(self):
        """Detect Dragon pattern (multiple retracements forming dragon shape)"""
        if len(self.df) < 20:
            return []
        
        patterns = []
        troughs = self._find_troughs(self.df['low'], order=4)
        
        if len(troughs) >= 3:
            for i in range(len(troughs)-2):
                try:
                    t1 = self.df['low'].iloc[troughs[i]]
                    t2 = self.df['low'].iloc[troughs[i+1]]
                    t3 = self.df['low'].iloc[troughs[i+2]]
                    
                    # Progressive higher lows
                    if t2 > t1 * 0.98 and t3 > t2 * 0.98:
                        patterns.append({
                            'troughs': [troughs[i], troughs[i+1], troughs[i+2]],
                            'type': 'dragon'
                        })
                except:
                    pass
        
        return patterns
    
    def find_inverse_head_shoulders(self, threshold=0.02):
        """Detect Inverse Head and Shoulders pattern"""
        if len(self.df) < 15:
            return []
        
        troughs = self._find_troughs(self.df['low'], order=5)
        
        if len(troughs) < 3:
            return []
        
        inv_hs = []
        for i in range(len(troughs)-2):
            try:
                left_shoulder = self.df['low'].iloc[troughs[i]]
                head = self.df['low'].iloc[troughs[i+1]]
                right_shoulder = self.df['low'].iloc[troughs[i+2]]
                
                # Head should be lower
                if head < left_shoulder and head < right_shoulder:
                    shoulder_diff = abs(left_shoulder - right_shoulder) / left_shoulder
                    
                    if shoulder_diff < threshold:
                        inv_hs.append({
                            'left_shoulder': troughs[i],
                            'head': troughs[i+1],
                            'right_shoulder': troughs[i+2],
                            'type': 'inverse_head_shoulders'
                        })
            except:
                pass
        
        return inv_hs
    
    def find_adam_eve_pattern(self, threshold=0.03):
        """Detect Adam and Eve double bottom pattern (sharp + rounded)"""
        if len(self.df) < 20:
            return []
        
        troughs = self._find_troughs(self.df['low'], order=5)
        
        if len(troughs) < 2:
            return []
        
        patterns = []
        for i in range(len(troughs)-1):
            try:
                idx1 = troughs[i]
                idx2 = troughs[i+1]
                
                # Check if first bottom is sharp (V-shaped)
                window1 = 3
                before1 = self.df['low'].iloc[max(0, idx1-window1):idx1]
                after1 = self.df['low'].iloc[idx1+1:idx1+window1+1]
                
                sharp1 = len(before1) > 0 and len(after1) > 0
                
                # Check if second bottom is rounded (U-shaped)
                window2 = 5
                bottom2_segment = self.df['low'].iloc[max(0, idx2-window2):idx2+window2+1]
                
                if len(bottom2_segment) >= 5:
                    x = np.arange(len(bottom2_segment))
                    coeffs = np.polyfit(x, bottom2_segment.values, 2)
                    rounded2 = coeffs[0] > 0
                    
                    price_diff = abs(self.df['low'].iloc[idx1] - self.df['low'].iloc[idx2]) / self.df['low'].iloc[idx1]
                    
                    if sharp1 and rounded2 and price_diff < threshold:
                        patterns.append({
                            'adam': idx1,
                            'eve': idx2,
                            'type': 'adam_eve_double_bottom'
                        })
            except:
                pass
        
        return patterns
    
    def find_megaphone_pattern(self, window=15):
        """Detect Megaphone/Broadening pattern"""
        if len(self.df) < window:
            return []
        
        patterns = []
        for i in range(window, len(self.df)):
            try:
                segment = self.df.iloc[i-window:i]
                
                # Calculate expanding range
                ranges = []
                for j in range(5, len(segment)):
                    recent = segment.iloc[j-5:j]
                    ranges.append(recent['high'].max() - recent['low'].min())
                
                if len(ranges) >= 3:
                    # Check if range is expanding
                    range_slope = np.polyfit(range(len(ranges)), ranges, 1)[0]
                    
                    if range_slope > 0:
                        patterns.append({
                            'index': i,
                            'start': i-window,
                            'type': 'megaphone'
                        })
            except:
                pass
        
        return patterns
    
    def find_dead_cat_bounce(self, window=10):
        """Detect Dead Cat Bounce pattern"""
        if len(self.df) < window + 5:
            return []
        
        patterns = []
        for i in range(window + 5, len(self.df)):
            try:
                # Large drop
                drop_segment = self.df.iloc[i-window-5:i-window]
                drop_pct = (drop_segment['close'].iloc[-1] - drop_segment['close'].iloc[0]) / drop_segment['close'].iloc[0]
                
                # Small bounce
                bounce_segment = self.df.iloc[i-window:i]
                bounce_pct = (bounce_segment['close'].max() - bounce_segment['close'].iloc[0]) / bounce_segment['close'].iloc[0]
                
                # Continue down
                after_bounce = self.df.iloc[i-3:i]
                continued_drop = after_bounce['close'].iloc[-1] < after_bounce['close'].iloc[0]
                
                if drop_pct < -0.10 and 0 < bounce_pct < 0.05 and continued_drop:
                    patterns.append({
                        'index': i,
                        'drop_start': i-window-5,
                        'bounce_start': i-window,
                        'type': 'dead_cat_bounce'
                    })
            except:
                pass
        
        return patterns
    
    def find_abcd_pattern(self, threshold=0.02):
        """Detect AB=CD harmonic pattern"""
        if len(self.df) < 20:
            return []
        
        patterns = []
        peaks = self._find_peaks(self.df['high'], order=4)
        troughs = self._find_troughs(self.df['low'], order=4)
        
        # Combine and sort all turning points
        all_points = [(p, 'peak', self.df['high'].iloc[p]) for p in peaks]
        all_points += [(t, 'trough', self.df['low'].iloc[t]) for t in troughs]
        all_points.sort(key=lambda x: x[0])
        
        for i in range(len(all_points) - 3):
            try:
                A, B, C, D = all_points[i:i+4]
                
                # Check alternating pattern
                if A[1] != B[1] and B[1] != C[1] and C[1] != D[1]:
                    AB = abs(B[2] - A[2])
                    CD = abs(D[2] - C[2])
                    
                    # AB should equal CD (within threshold)
                    if abs(AB - CD) / AB < threshold:
                        patterns.append({
                            'A': A[0], 'B': B[0], 'C': C[0], 'D': D[0],
                            'type': 'abcd_pattern'
                        })
            except:
                pass
        
        return patterns
    
    def find_rectangle_pattern(self, window=20, threshold=0.02):
        """Detect Rectangle/Trading Range pattern"""
        if len(self.df) < window:
            return []
        
        patterns = []
        for i in range(window, len(self.df)):
            try:
                segment = self.df.iloc[i-window:i]
                
                resistance = segment['high'].max()
                support = segment['low'].min()
                
                # Count touches
                resistance_touches = sum(abs(segment['high'] - resistance) / resistance < threshold)
                support_touches = sum(abs(segment['low'] - support) / support < threshold)
                
                # Check horizontal movement
                price_range = (resistance - support) / support
                
                if resistance_touches >= 2 and support_touches >= 2 and 0.03 < price_range < 0.15:
                    patterns.append({
                        'index': i,
                        'start': i-window,
                        'resistance': resistance,
                        'support': support,
                        'type': 'rectangle'
                    })
            except:
                pass
        
        return patterns
    
    def find_bullish_engulfing(self):
        """Detect Bullish Engulfing candlestick pattern"""
        if len(self.df) < 2:
            return []
        
        patterns = []
        for i in range(1, len(self.df)):
            try:
                prev = self.df.iloc[i-1]
                curr = self.df.iloc[i]
                
                # Previous bearish
                prev_bearish = prev['close'] < prev['open']
                # Current bullish
                curr_bullish = curr['close'] > curr['open']
                
                # Current engulfs previous
                engulfs = (curr['open'] <= prev['close'] and 
                          curr['close'] >= prev['open'])
                
                if prev_bearish and curr_bullish and engulfs:
                    patterns.append({
                        'index': i,
                        'type': 'bullish_engulfing'
                    })
            except:
                pass
        
        return patterns
    
    def find_bearish_engulfing(self):
        """Detect Bearish Engulfing candlestick pattern"""
        if len(self.df) < 2:
            return []
        
        patterns = []
        for i in range(1, len(self.df)):
            try:
                prev = self.df.iloc[i-1]
                curr = self.df.iloc[i]
                
                # Previous bullish
                prev_bullish = prev['close'] > prev['open']
                # Current bearish
                curr_bearish = curr['close'] < curr['open']
                
                # Current engulfs previous
                engulfs = (curr['open'] >= prev['close'] and 
                          curr['close'] <= prev['open'])
                
                if prev_bullish and curr_bearish and engulfs:
                    patterns.append({
                        'index': i,
                        'type': 'bearish_engulfing'
                    })
            except:
                pass
        
        return patterns
    
    def find_morning_star(self):
        """Detect Morning Star pattern (bullish reversal)"""
        if len(self.df) < 3:
            return []
        
        patterns = []
        for i in range(2, len(self.df)):
            try:
                first = self.df.iloc[i-2]
                second = self.df.iloc[i-1]
                third = self.df.iloc[i]
                
                # First: large bearish
                first_bearish = first['close'] < first['open']
                first_body = abs(first['close'] - first['open'])
                
                # Second: small body (star)
                second_body = abs(second['close'] - second['open'])
                second_small = second_body < first_body * 0.3
                
                # Third: large bullish
                third_bullish = third['close'] > third['open']
                third_body = abs(third['close'] - third['open'])
                third_large = third_body > first_body * 0.6
                
                # Third closes well into first
                recovery = third['close'] > (first['open'] + first['close']) / 2
                
                if first_bearish and second_small and third_bullish and third_large and recovery:
                    patterns.append({
                        'index': i,
                        'type': 'morning_star'
                    })
            except:
                pass
        
        return patterns
    
    def find_evening_star(self):
        """Detect Evening Star pattern (bearish reversal)"""
        if len(self.df) < 3:
            return []
        
        patterns = []
        for i in range(2, len(self.df)):
            try:
                first = self.df.iloc[i-2]
                second = self.df.iloc[i-1]
                third = self.df.iloc[i]
                
                # First: large bullish
                first_bullish = first['close'] > first['open']
                first_body = abs(first['close'] - first['open'])
                
                # Second: small body (star)
                second_body = abs(second['close'] - second['open'])
                second_small = second_body < first_body * 0.3
                
                # Third: large bearish
                third_bearish = third['close'] < third['open']
                third_body = abs(third['close'] - third['open'])
                third_large = third_body > first_body * 0.6
                
                # Third closes well into first
                decline = third['close'] < (first['open'] + first['close']) / 2
                
                if first_bullish and second_small and third_bearish and third_large and decline:
                    patterns.append({
                        'index': i,
                        'type': 'evening_star'
                    })
            except:
                pass
        
        return patterns
    
    def find_doji_patterns(self):
        """Detect Doji candlestick patterns"""
        if len(self.df) < 1:
            return []
        
        patterns = []
        for i in range(len(self.df)):
            try:
                candle = self.df.iloc[i]
                body = abs(candle['close'] - candle['open'])
                total_range = candle['high'] - candle['low']
                
                if total_range == 0:
                    continue
                
                # Doji: very small body relative to range
                if body / total_range < 0.1:
                    upper_shadow = candle['high'] - max(candle['open'], candle['close'])
                    lower_shadow = min(candle['open'], candle['close']) - candle['low']
                    
                    # Classify doji type
                    if upper_shadow > 2 * lower_shadow:
                        doji_type = 'dragonfly_doji'
                    elif lower_shadow > 2 * upper_shadow:
                        doji_type = 'gravestone_doji'
                    else:
                        doji_type = 'standard_doji'
                    
                    patterns.append({
                        'index': i,
                        'type': doji_type
                    })
            except:
                pass
        
        return patterns
    
    def find_shooting_star(self):
        """Detect Shooting Star pattern (bearish reversal)"""
        if len(self.df) < 2:
            return []
        
        patterns = []
        for i in range(1, len(self.df)):
            try:
                prev = self.df.iloc[i-1]
                curr = self.df.iloc[i]
                
                body = abs(curr['close'] - curr['open'])
                upper_shadow = curr['high'] - max(curr['open'], curr['close'])
                lower_shadow = min(curr['open'], curr['close']) - curr['low']
                
                # Long upper shadow, small body, small lower shadow
                # After uptrend
                if (upper_shadow > 2 * body and 
                    lower_shadow < 0.5 * body and
                    curr['close'] < curr['open'] and
                    prev['close'] > prev['open']):
                    
                    patterns.append({
                        'index': i,
                        'type': 'shooting_star'
                    })
            except:
                pass
        
        return patterns
    
    def find_piercing_pattern(self):
        """Detect Piercing Line pattern (bullish reversal)"""
        if len(self.df) < 2:
            return []
        
        patterns = []
        for i in range(1, len(self.df)):
            try:
                prev = self.df.iloc[i-1]
                curr = self.df.iloc[i]
                
                # Previous bearish
                prev_bearish = prev['close'] < prev['open']
                # Current bullish
                curr_bullish = curr['close'] > curr['open']
                
                # Opens below previous close
                gaps_down = curr['open'] < prev['close']
                
                # Closes above midpoint of previous
                prev_mid = (prev['open'] + prev['close']) / 2
                closes_above_mid = curr['close'] > prev_mid and curr['close'] < prev['open']
                
                if prev_bearish and curr_bullish and gaps_down and closes_above_mid:
                    patterns.append({
                        'index': i,
                        'type': 'piercing_pattern'
                    })
            except:
                pass
        
        return patterns
    
    def find_dark_cloud_cover(self):
        """Detect Dark Cloud Cover pattern (bearish reversal)"""
        if len(self.df) < 2:
            return []
        
        patterns = []
        for i in range(1, len(self.df)):
            try:
                prev = self.df.iloc[i-1]
                curr = self.df.iloc[i]
                
                # Previous bullish
                prev_bullish = prev['close'] > prev['open']
                # Current bearish
                curr_bearish = curr['close'] < curr['open']
                
                # Opens above previous close
                gaps_up = curr['open'] > prev['close']
                
                # Closes below midpoint of previous
                prev_mid = (prev['open'] + prev['close']) / 2
                closes_below_mid = curr['close'] < prev_mid and curr['close'] > prev['open']
                
                if prev_bullish and curr_bearish and gaps_up and closes_below_mid:
                    patterns.append({
                        'index': i,
                        'type': 'dark_cloud_cover'
                    })
            except:
                pass
        
        return patterns
    
    def find_three_white_soldiers(self):
        """Detect Three White Soldiers pattern (strong bullish)"""
        if len(self.df) < 3:
            return []
        
        patterns = []
        for i in range(2, len(self.df)):
            try:
                first = self.df.iloc[i-2]
                second = self.df.iloc[i-1]
                third = self.df.iloc[i]
                
                # All three bullish
                all_bullish = (first['close'] > first['open'] and
                              second['close'] > second['open'] and
                              third['close'] > third['open'])
                
                # Progressive higher closes
                higher_closes = (second['close'] > first['close'] and
                               third['close'] > second['close'])
                
                # Each opens within previous body
                opens_within = (first['open'] < second['open'] < first['close'] and
                              second['open'] < third['open'] < second['close'])
                
                if all_bullish and higher_closes and opens_within:
                    patterns.append({
                        'index': i,
                        'type': 'three_white_soldiers'
                    })
            except:
                pass
        
        return patterns
    
    def find_three_black_crows(self):
        """Detect Three Black Crows pattern (strong bearish)"""
        if len(self.df) < 3:
            return []
        
        patterns = []
        for i in range(2, len(self.df)):
            try:
                first = self.df.iloc[i-2]
                second = self.df.iloc[i-1]
                third = self.df.iloc[i]
                
                # All three bearish
                all_bearish = (first['close'] < first['open'] and
                             second['close'] < second['open'] and
                             third['close'] < third['open'])
                
                # Progressive lower closes
                lower_closes = (second['close'] < first['close'] and
                              third['close'] < second['close'])
                
                # Each opens within previous body
                opens_within = (first['close'] < second['open'] < first['open'] and
                              second['close'] < third['open'] < second['open'])
                
                if all_bearish and lower_closes and opens_within:
                    patterns.append({
                        'index': i,
                        'type': 'three_black_crows'
                    })
            except:
                pass
        
        return patterns
    
    def find_tweezer_patterns(self):
        """Detect Tweezer Top and Bottom patterns"""
        if len(self.df) < 2:
            return []
        
        patterns = []
        for i in range(1, len(self.df)):
            try:
                prev = self.df.iloc[i-1]
                curr = self.df.iloc[i]
                
                # Tweezer Top: same highs
                if abs(prev['high'] - curr['high']) / prev['high'] < 0.002:
                    if prev['close'] > prev['open'] and curr['close'] < curr['open']:
                        patterns.append({
                            'index': i,
                            'type': 'tweezer_top'
                        })
                
                # Tweezer Bottom: same lows
                if abs(prev['low'] - curr['low']) / prev['low'] < 0.002:
                    if prev['close'] < prev['open'] and curr['close'] > curr['open']:
                        patterns.append({
                            'index': i,
                            'type': 'tweezer_bottom'
                        })
            except:
                pass
        
        return patterns
    
    def find_harami_patterns(self):
        """Detect Harami patterns (bullish and bearish)"""
        if len(self.df) < 2:
            return []
        
        patterns = []
        for i in range(1, len(self.df)):
            try:
                prev = self.df.iloc[i-1]
                curr = self.df.iloc[i]
                
                prev_body = abs(prev['close'] - prev['open'])
                curr_body = abs(curr['close'] - curr['open'])
                
                # Current inside previous
                inside = (min(curr['open'], curr['close']) > min(prev['open'], prev['close']) and
                         max(curr['open'], curr['close']) < max(prev['open'], prev['close']))
                
                # Smaller body
                smaller = curr_body < prev_body * 0.5
                
                if inside and smaller:
                    # Bullish Harami
                    if prev['close'] < prev['open'] and curr['close'] > curr['open']:
                        patterns.append({
                            'index': i,
                            'type': 'bullish_harami'
                        })
                    # Bearish Harami
                    elif prev['close'] > prev['open'] and curr['close'] < curr['open']:
                        patterns.append({
                            'index': i,
                            'type': 'bearish_harami'
                        })
            except:
                pass
        
        return patterns
    
    def detect_all_patterns(self):
        """
        Detect all available patterns and return comprehensive results
        """
        results = {}
        
        # Original patterns
        results['Double Tops'] = self.find_double_top()
        results['Double Bottoms'] = self.find_double_bottom()
        results['Head & Shoulders'] = self.find_head_and_shoulders()
        results['Triangles'] = self.find_triangle_patterns()
        results['Hammers'] = self.find_hammer_patterns()
        
        # New patterns from image
        results['Triple Tops'] = self.find_triple_top()
        results['Triple Bottoms'] = self.find_triple_bottom()
        results['Rounding Bottom'] = self.find_rounding_bottom()
        results['Cup & Handle'] = self.find_cup_and_handle()
        results['Ascending Wedge'] = self.find_ascending_wedge()
        results['Descending Wedge'] = self.find_descending_wedge()
        results['Rising Wedge'] = self.find_rising_wedge()
        results['Falling Wedge'] = self.find_falling_wedge()
        results['Flag Patterns'] = self.find_flag_pattern()
        results['Pennants'] = self.find_pennant_pattern()
        results['Channels'] = self.find_channel_patterns()
        results['Bump & Run'] = self.find_bump_and_run()
        results['Dragon'] = self.find_dragon_pattern()
        results['Inv H&S'] = self.find_inverse_head_shoulders()
        results['Adam & Eve'] = self.find_adam_eve_pattern()
        results['Megaphone'] = self.find_megaphone_pattern()
        results['Dead Cat Bounce'] = self.find_dead_cat_bounce()
        results['ABCD Pattern'] = self.find_abcd_pattern()
        results['Rectangle'] = self.find_rectangle_pattern()
        
        # Candlestick patterns
        results['Bullish Engulfing'] = self.find_bullish_engulfing()
        results['Bearish Engulfing'] = self.find_bearish_engulfing()
        results['Morning Star'] = self.find_morning_star()
        results['Evening Star'] = self.find_evening_star()
        results['Doji'] = self.find_doji_patterns()
        results['Shooting Star'] = self.find_shooting_star()
        results['Piercing Pattern'] = self.find_piercing_pattern()
        results['Dark Cloud'] = self.find_dark_cloud_cover()
        results['3 White Soldiers'] = self.find_three_white_soldiers()
        results['3 Black Crows'] = self.find_three_black_crows()
        results['Tweezers'] = self.find_tweezer_patterns()
        results['Harami'] = self.find_harami_patterns()
        
        return results