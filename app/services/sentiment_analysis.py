# app/services/sentiment_analysis.py
import requests
import json
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional
import time

class SentimentAnalysisService:
    """Service untuk analisa sentimen crypto dari berbagai sumber"""
    
    def __init__(self):
        self.base_urls = {
            'coingecko': 'https://api.coingecko.com/api/v3',
            'alternative': 'https://api.alternative.me',
            'cryptopanic': 'https://cryptopanic.com/api/v1',
        }
        self.cache = {}
        self.cache_duration = 300  # 5 menit
        
    def _get_cache(self, key):
        """Get cached data if still valid"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_duration:
                return data
        return None
    
    def _set_cache(self, key, data):
        """Set cache data"""
        self.cache[key] = (data, time.time())
    
    def get_fear_greed_index(self) -> Dict:
        """
        Get Crypto Fear & Greed Index
        0-24: Extreme Fear (Good buying opportunity)
        25-49: Fear
        50-74: Greed
        75-100: Extreme Greed (Potential correction)
        """
        cache_key = 'fear_greed'
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        try:
            url = f"{self.base_urls['alternative']}/fng/"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    fng_data = data['data'][0]
                    result = {
                        'value': int(fng_data['value']),
                        'classification': fng_data['value_classification'],
                        'timestamp': fng_data['timestamp'],
                        'interpretation': self._interpret_fear_greed(int(fng_data['value']))
                    }
                    self._set_cache(cache_key, result)
                    return result
        except Exception as e:
            print(f"Fear & Greed Index error: {e}")
        
        return {'value': 50, 'classification': 'Neutral', 'interpretation': 'Data not available'}
    
    def _interpret_fear_greed(self, value: int) -> str:
        """Interpret fear & greed index value"""
        if value <= 24:
            return "🟢 EXTREME FEAR - Investor sangat takut. Bisa jadi peluang beli yang bagus."
        elif value <= 49:
            return "🟡 FEAR - Pasar cemas. Hati-hati tapi bisa mulai akumulasi."
        elif value <= 74:
            return "🟠 GREED - Pasar optimis. Waspadai koreksi."
        else:
            return "🔴 EXTREME GREED - Euforia tinggi. Risiko koreksi besar, consider take profit."
    
    def get_coin_sentiment(self, coin_id: str) -> Dict:
        """
        Get sentiment data for specific coin from CoinGecko
        coin_id: bitcoin, ethereum, binancecoin, dll
        """
        cache_key = f'sentiment_{coin_id}'
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        try:
            url = f"{self.base_urls['coingecko']}/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'true',
                'developer_data': 'true'
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract sentiment data
                sentiment = {
                    'name': data.get('name', 'Unknown'),
                    'symbol': data.get('symbol', '').upper(),
                    'sentiment_votes_up_percentage': data.get('sentiment_votes_up_percentage', 0),
                    'sentiment_votes_down_percentage': data.get('sentiment_votes_down_percentage', 0),
                    'market_cap_rank': data.get('market_cap_rank', 'N/A'),
                    'coingecko_score': data.get('coingecko_score', 0),
                    'developer_score': data.get('developer_score', 0),
                    'community_score': data.get('community_score', 0),
                    'liquidity_score': data.get('liquidity_score', 0),
                    'public_interest_score': data.get('public_interest_score', 0)
                }
                
                # Market data
                if 'market_data' in data:
                    md = data['market_data']
                    sentiment['price_change_24h_pct'] = md.get('price_change_percentage_24h', 0)
                    sentiment['price_change_7d_pct'] = md.get('price_change_percentage_7d', 0)
                    sentiment['price_change_30d_pct'] = md.get('price_change_percentage_30d', 0)
                    sentiment['market_cap'] = md.get('market_cap', {}).get('usd', 0)
                    sentiment['total_volume'] = md.get('total_volume', {}).get('usd', 0)
                    sentiment['ath_change_percentage'] = md.get('ath_change_percentage', {}).get('usd', 0)
                
                # Community data
                if 'community_data' in data:
                    cd = data['community_data']
                    sentiment['twitter_followers'] = cd.get('twitter_followers', 0)
                    sentiment['reddit_subscribers'] = cd.get('reddit_subscribers', 0)
                
                # Calculate overall sentiment
                sentiment['overall_sentiment'] = self._calculate_overall_sentiment(sentiment)
                
                self._set_cache(cache_key, sentiment)
                return sentiment
                
        except Exception as e:
            print(f"Coin sentiment error for {coin_id}: {e}")
        
        return {'name': coin_id, 'error': 'Data not available'}
    
    def _calculate_overall_sentiment(self, data: Dict) -> Dict:
        """Calculate overall sentiment score"""
        score = 0
        reasons = []
        
        # Sentiment votes
        up_vote = data.get('sentiment_votes_up_percentage', 0)
        if up_vote > 70:
            score += 2
            reasons.append("Community sentiment positif")
        elif up_vote > 50:
            score += 1
        elif up_vote < 30:
            score -= 2
            reasons.append("Community sentiment negatif")
        
        # Price changes
        price_24h = data.get('price_change_24h_pct', 0)
        if price_24h > 5:
            score += 1
            reasons.append("Momentum 24h kuat")
        elif price_24h < -5:
            score -= 1
            reasons.append("Tekanan jual 24h")
        
        price_7d = data.get('price_change_7d_pct', 0)
        if price_7d > 10:
            score += 1
            reasons.append("Trend 7d bullish")
        elif price_7d < -10:
            score -= 1
            reasons.append("Trend 7d bearish")
        
        # Scores
        avg_score = (
            data.get('developer_score', 0) +
            data.get('community_score', 0) +
            data.get('liquidity_score', 0)
        ) / 3
        
        if avg_score > 70:
            score += 2
            reasons.append("Score fundamental tinggi")
        elif avg_score > 50:
            score += 1
        
        # Final classification
        if score >= 4:
            classification = "🟢 VERY BULLISH"
        elif score >= 2:
            classification = "🟢 BULLISH"
        elif score >= 0:
            classification = "🟡 NEUTRAL"
        elif score >= -2:
            classification = "🔴 BEARISH"
        else:
            classification = "🔴 VERY BEARISH"
        
        return {
            'score': score,
            'classification': classification,
            'reasons': reasons
        }
    
    def get_trending_coins(self) -> List[Dict]:
        """Get trending coins on CoinGecko"""
        cache_key = 'trending'
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        try:
            url = f"{self.base_urls['coingecko']}/search/trending"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                trending = []
                
                if 'coins' in data:
                    for item in data['coins'][:10]:  # Top 10
                        coin = item.get('item', {})
                        trending.append({
                            'rank': coin.get('market_cap_rank', 'N/A'),
                            'name': coin.get('name', 'Unknown'),
                            'symbol': coin.get('symbol', ''),
                            'price_btc': coin.get('price_btc', 0),
                            'score': coin.get('score', 0)
                        })
                
                self._set_cache(cache_key, trending)
                return trending
        except Exception as e:
            print(f"Trending coins error: {e}")
        
        return []
    
    def get_global_crypto_stats(self) -> Dict:
        """Get global cryptocurrency market statistics"""
        cache_key = 'global_stats'
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        try:
            url = f"{self.base_urls['coingecko']}/global"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                
                stats = {
                    'total_market_cap_usd': data.get('total_market_cap', {}).get('usd', 0),
                    'total_volume_24h_usd': data.get('total_volume', {}).get('usd', 0),
                    'bitcoin_dominance': data.get('market_cap_percentage', {}).get('btc', 0),
                    'ethereum_dominance': data.get('market_cap_percentage', {}).get('eth', 0),
                    'active_cryptocurrencies': data.get('active_cryptocurrencies', 0),
                    'markets': data.get('markets', 0),
                    'market_cap_change_24h_pct': data.get('market_cap_change_percentage_24h_usd', 0),
                    'updated_at': datetime.fromtimestamp(data.get('updated_at', 0)).strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Interpretation
                btc_dom = stats['bitcoin_dominance']
                if btc_dom > 50:
                    stats['dominance_interpretation'] = "🟡 BTC dominan - Altcoin season belum dimulai"
                elif btc_dom > 40:
                    stats['dominance_interpretation'] = "🟢 Balanced - Capital mulai flow ke altcoin"
                else:
                    stats['dominance_interpretation'] = "🚀 Altcoin season - Capital banyak di altcoin"
                
                self._set_cache(cache_key, stats)
                return stats
        except Exception as e:
            print(f"Global stats error: {e}")
        
        return {}
    
    def convert_symbol_to_coingecko_id(self, symbol: str) -> str:
        """Convert trading symbol to CoinGecko ID"""
        # Remove /USDT, /BUSD, etc.
        clean_symbol = symbol.split('/')[0].lower()
        
        # Common mappings
        mapping = {
            'btc': 'bitcoin',
            'eth': 'ethereum',
            'bnb': 'binancecoin',
            'xrp': 'ripple',
            'ada': 'cardano',
            'doge': 'dogecoin',
            'sol': 'solana',
            'dot': 'polkadot',
            'matic': 'matic-network',
            'link': 'chainlink',
            'uni': 'uniswap',
            'ltc': 'litecoin',
            'avax': 'avalanche-2',
            'atom': 'cosmos',
            'etc': 'ethereum-classic',
            'xlm': 'stellar',
            'near': 'near',
            'algo': 'algorand',
            'trx': 'tron',
            'ftm': 'fantom',
            'ape': 'apecoin',
            'sand': 'the-sandbox',
            'mana': 'decentraland',
            'grt': 'the-graph',
            'aave': 'aave',
            'snx': 'synthetix-network-token'
        }
        
        return mapping.get(clean_symbol, clean_symbol)
    
    def get_comprehensive_analysis(self, symbol: str) -> Dict:
        """Get comprehensive sentiment analysis for a coin"""
        coin_id = self.convert_symbol_to_coingecko_id(symbol)
        
        analysis = {
            'symbol': symbol,
            'coin_id': coin_id,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fear_greed_index': self.get_fear_greed_index(),
            'coin_sentiment': self.get_coin_sentiment(coin_id),
            'global_stats': self.get_global_crypto_stats(),
            'trending_coins': self.get_trending_coins()
        }
        
        return analysis
    
    def get_market_summary(self) -> str:
        """Get human-readable market summary"""
        try:
            fng = self.get_fear_greed_index()
            stats = self.get_global_crypto_stats()
            
            summary = f"""
📊 MARKET SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*60}

🌡️ FEAR & GREED INDEX: {fng['value']}/100 - {fng['classification']}
{fng.get('interpretation', '')}

💰 GLOBAL MARKET CAP: ${stats.get('total_market_cap_usd', 0)/1e12:.2f}T
📈 24h Change: {stats.get('market_cap_change_24h_pct', 0):+.2f}%
💵 24h Volume: ${stats.get('total_volume_24h_usd', 0)/1e9:.2f}B

🪙 BTC Dominance: {stats.get('bitcoin_dominance', 0):.2f}%
⚡ ETH Dominance: {stats.get('ethereum_dominance', 0):.2f}%
{stats.get('dominance_interpretation', '')}

📌 Active Cryptocurrencies: {stats.get('active_cryptocurrencies', 0):,}
🏪 Markets: {stats.get('markets', 0):,}
"""
            return summary
        except Exception as e:
            return f"Error generating market summary: {e}"