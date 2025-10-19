# app/services/economic_indicators.py
import requests
from datetime import datetime, timedelta
from typing import Dict, List
import time

class EconomicIndicatorsService:
    """Service untuk data ekonomi makro yang mempengaruhi crypto"""
    
    def __init__(self):
        # Free APIs
        self.apis = {
            'exchangerate': 'https://api.exchangerate-api.com/v4/latest/USD',
            'blockchain': 'https://blockchain.info',
            'mempool': 'https://mempool.space/api'
        }
        self.cache = {}
        self.cache_duration = 600  # 10 menit
    
    def _get_cache(self, key):
        """Get cached data"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_duration:
                return data
        return None
    
    def _set_cache(self, key, data):
        """Set cache"""
        self.cache[key] = (data, time.time())
    
    def get_usd_strength(self) -> Dict:
        """Get USD strength against major currencies"""
        cache_key = 'usd_strength'
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        try:
            response = requests.get(self.apis['exchangerate'], timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                rates = data.get('rates', {})
                
                # Calculate USD index (simplified)
                # Normally uses EUR, JPY, GBP, CAD, SEK, CHF
                major_currencies = {
                    'EUR': rates.get('EUR', 1),
                    'JPY': rates.get('JPY', 1),
                    'GBP': rates.get('GBP', 1),
                    'CAD': rates.get('CAD', 1),
                    'CHF': rates.get('CHF', 1)
                }
                
                result = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'rates': major_currencies,
                    'interpretation': self._interpret_usd_strength(major_currencies)
                }
                
                self._set_cache(cache_key, result)
                return result
        except Exception as e:
            print(f"USD strength error: {e}")
        
        return {'error': 'Data not available'}
    
    def _interpret_usd_strength(self, rates: Dict) -> str:
        """Interpret USD strength"""
        # When USD strengthens against EUR, EUR rate decreases
        eur_rate = rates.get('EUR', 0.85)
        
        if eur_rate < 0.80:
            return "💪 USD sangat kuat - Biasanya bearish untuk crypto (capital flight to USD)"
        elif eur_rate < 0.85:
            return "💪 USD menguat - Tekanan pada crypto"
        elif eur_rate > 0.95:
            return "💸 USD lemah - Bullish untuk crypto (capital seek alternatives)"
        else:
            return "🟡 USD stabil - Dampak netral pada crypto"
    
    def get_bitcoin_network_stats(self) -> Dict:
        """Get Bitcoin network statistics"""
        cache_key = 'btc_network'
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        try:
            # Get mempool stats
            response = requests.get(f"{self.apis['mempool']}/v1/fees/recommended", timeout=10)
            
            if response.status_code == 200:
                fees_data = response.json()
                
                # Get blocks info
                blocks_response = requests.get(f"{self.apis['mempool']}/api/blocks", timeout=10)
                blocks_data = blocks_response.json() if blocks_response.status_code == 200 else []
                
                # Get mempool info
                mempool_response = requests.get(f"{self.apis['mempool']}/api/mempool", timeout=10)
                mempool_data = mempool_response.json() if mempool_response.status_code == 200 else {}
                
                stats = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'recommended_fees': {
                        'fastest': fees_data.get('fastestFee', 0),
                        'half_hour': fees_data.get('halfHourFee', 0),
                        'hour': fees_data.get('hourFee', 0),
                        'minimum': fees_data.get('minimumFee', 0)
                    },
                    'mempool_size': mempool_data.get('count', 0),
                    'mempool_bytes': mempool_data.get('vsize', 0),
                    'recent_blocks': len(blocks_data),
                    'network_congestion': self._interpret_network_congestion(
                        fees_data.get('fastestFee', 0),
                        mempool_data.get('count', 0)
                    )
                }
                
                self._set_cache(cache_key, stats)
                return stats
        except Exception as e:
            print(f"Bitcoin network stats error: {e}")
        
        return {'error': 'Data not available'}
    
    def _interpret_network_congestion(self, fee: int, mempool_count: int) -> str:
        """Interpret network congestion level"""
        if fee > 100:
            return "🔴 SANGAT TINGGI - Network congested, hindari transaksi kecil"
        elif fee > 50:
            return "🟠 TINGGI - Network busy, fees mahal"
        elif fee > 20:
            return "🟡 SEDANG - Network normal"
        else:
            return "🟢 RENDAH - Network lancar, waktu yang baik untuk transaksi"
    
    def get_crypto_market_indicators(self) -> Dict:
        """Get various crypto market indicators"""
        cache_key = 'market_indicators'
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        try:
            # Bitcoin halving countdown
            # Next halving approximately April 2024
            next_halving = datetime(2028, 4, 20)  # Estimated
            days_to_halving = (next_halving - datetime.now()).days
            
            indicators = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'halving_countdown': {
                    'days_remaining': days_to_halving,
                    'next_date': next_halving.strftime('%Y-%m-%d'),
                    'interpretation': self._interpret_halving(days_to_halving)
                },
                'market_cycle': self._estimate_market_cycle(),
                'risk_factors': self._assess_risk_factors()
            }
            
            self._set_cache(cache_key, indicators)
            return indicators
        except Exception as e:
            print(f"Market indicators error: {e}")
        
        return {}
    
    def _interpret_halving(self, days: int) -> str:
        """Interpret halving countdown"""
        if days < 0:
            return "✅ Halving sudah terjadi"
        elif days < 180:
            return "🚀 Mendekati halving - Historically bullish period"
        elif days < 365:
            return "📈 Pre-halving year - Akumulasi phase"
        else:
            return f"⏳ Masih {days} hari lagi"
    
    def _estimate_market_cycle(self) -> Dict:
        """Estimate current market cycle phase"""
        # This is simplified - in reality you'd use multiple indicators
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Simplified cycle estimation
        phase = "Accumulation"
        description = "Market sideways, akumulasi oleh smart money"
        
        # You would normally check actual price data, volume, etc.
        return {
            'phase': phase,
            'description': description,
            'recommendation': "Good time to DCA and accumulate quality projects"
        }
    
    def _assess_risk_factors(self) -> List[Dict]:
        """Assess current market risk factors"""
        risks = []
        
        # Macro risks
        risks.append({
            'category': 'Regulatory',
            'level': 'Medium',
            'description': 'Ongoing regulatory discussions globally',
            'impact': 'Dapat menyebabkan volatilitas jangka pendek'
        })
        
        risks.append({
            'category': 'Macro Economy',
            'level': 'Medium',
            'description': 'Interest rates dan inflasi masih menjadi perhatian',
            'impact': 'Mempengaruhi risk appetite investor'
        })
        
        risks.append({
            'category': 'Technical',
            'level': 'Low',
            'description': 'Network fundamentals kuat',
            'impact': 'Minimal impact'
        })
        
        return risks
    
    def get_comprehensive_economic_analysis(self) -> str:
        """Get comprehensive economic analysis text"""
        usd = self.get_usd_strength()
        btc_network = self.get_bitcoin_network_stats()
        indicators = self.get_crypto_market_indicators()
        
        analysis = f"""
🌍 ECONOMIC & MACRO ANALYSIS
{'='*60}

💵 USD STRENGTH
{usd.get('interpretation', 'Data unavailable')}

⛓️ BITCOIN NETWORK STATUS
{btc_network.get('network_congestion', 'Data unavailable')}
• Mempool: {btc_network.get('mempool_size', 0):,} transactions
• Recommended Fee: {btc_network.get('recommended_fees', {}).get('fastest', 0)} sat/vB

📊 MARKET CYCLE
Phase: {indicators.get('market_cycle', {}).get('phase', 'Unknown')}
{indicators.get('market_cycle', {}).get('description', '')}

⏰ BITCOIN HALVING
{indicators.get('halving_countdown', {}).get('interpretation', 'N/A')}
Next: {indicators.get('halving_countdown', {}).get('next_date', 'N/A')}
Days: {indicators.get('halving_countdown', {}).get('days_remaining', 'N/A')}

⚠️ RISK FACTORS
"""
        
        for risk in indicators.get('risk_factors', []):
            analysis += f"""
• {risk['category']} - Level: {risk['level']}
  {risk['description']}
  Impact: {risk['impact']}
"""
        
        return analysis