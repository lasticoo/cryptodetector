# app/services/news_service.py
import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict
import time

class NewsService:
    """Service untuk mendapatkan berita crypto real-time"""
    
    def __init__(self):
        self.sources = {
            'cointelegraph_rss': 'https://cointelegraph.com/rss',
            'coindesk_rss': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
            'coingecko': 'https://api.coingecko.com/api/v3',
            'cryptonews': 'https://cryptonews.com/news/feed/'
        }
        self.cache = {}
        self.cache_duration = 180  # 3 menit untuk news
        
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
    
    def get_latest_news(self, limit: int = 10) -> List[Dict]:
        """Get latest crypto news from multiple sources"""
        cache_key = f'news_latest_{limit}'
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        all_news = []
        
        # Get from CoinTelegraph RSS
        try:
            ct_news = self._fetch_rss_feed(self.sources['cointelegraph_rss'], 'CoinTelegraph')
            all_news.extend(ct_news[:5])
        except Exception as e:
            print(f"CoinTelegraph RSS error: {e}")
        
        # Get from CoinDesk RSS
        try:
            cd_news = self._fetch_rss_feed(self.sources['coindesk_rss'], 'CoinDesk')
            all_news.extend(cd_news[:5])
        except Exception as e:
            print(f"CoinDesk RSS error: {e}")
        
        # Get from CryptoNews RSS
        try:
            cn_news = self._fetch_rss_feed(self.sources['cryptonews'], 'CryptoNews')
            all_news.extend(cn_news[:5])
        except Exception as e:
            print(f"CryptoNews RSS error: {e}")
        
        # Sort by date
        all_news.sort(key=lambda x: x['published_timestamp'], reverse=True)
        
        result = all_news[:limit]
        self._set_cache(cache_key, result)
        return result
    
    def _fetch_rss_feed(self, url: str, source: str) -> List[Dict]:
        """Fetch and parse RSS feed"""
        try:
            feed = feedparser.parse(url)
            news_list = []
            
            for entry in feed.entries[:10]:
                # Parse date
                published = entry.get('published', '')
                try:
                    if hasattr(entry, 'published_parsed'):
                        pub_date = datetime(*entry.published_parsed[:6])
                    else:
                        pub_date = datetime.now()
                except:
                    pub_date = datetime.now()
                
                news_item = {
                    'title': entry.get('title', 'No Title'),
                    'link': entry.get('link', ''),
                    'summary': entry.get('summary', '')[:200] + '...' if len(entry.get('summary', '')) > 200 else entry.get('summary', ''),
                    'source': source,
                    'published': pub_date.strftime('%Y-%m-%d %H:%M'),
                    'published_timestamp': pub_date.timestamp(),
                    'time_ago': self._time_ago(pub_date)
                }
                
                news_list.append(news_item)
            
            return news_list
        except Exception as e:
            print(f"RSS Feed error for {source}: {e}")
            return []
    
    def _time_ago(self, dt: datetime) -> str:
        """Calculate time ago string"""
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days} hari lalu"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} jam lalu"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} menit lalu"
        else:
            return "Baru saja"
    
    def get_coin_specific_news(self, coin_name: str, limit: int = 5) -> List[Dict]:
        """Get news specific to a coin"""
        all_news = self.get_latest_news(limit=30)
        
        # Filter by coin name
        coin_keywords = coin_name.lower().split()
        filtered = []
        
        for news in all_news:
            title_lower = news['title'].lower()
            summary_lower = news['summary'].lower()
            
            # Check if any keyword matches
            if any(keyword in title_lower or keyword in summary_lower for keyword in coin_keywords):
                filtered.append(news)
        
        return filtered[:limit]
    
    def analyze_news_sentiment(self, news_list: List[Dict]) -> Dict:
        """Analyze sentiment from news headlines"""
        if not news_list:
            return {'sentiment': 'neutral', 'score': 0, 'analysis': 'No news available'}
        
        # Simple keyword-based sentiment
        bullish_keywords = [
            'surge', 'soar', 'rally', 'bull', 'gain', 'rise', 'pump', 'breakout',
            'bullish', 'growth', 'adoption', 'partnership', 'upgrade', 'launch',
            'positive', 'record', 'high', 'milestone', 'integration', 'approval'
        ]
        
        bearish_keywords = [
            'crash', 'plunge', 'bear', 'fall', 'drop', 'dump', 'decline',
            'bearish', 'hack', 'scam', 'regulation', 'ban', 'lawsuit',
            'negative', 'warning', 'risk', 'concern', 'investigate', 'fraud'
        ]
        
        bullish_count = 0
        bearish_count = 0
        
        for news in news_list:
            text = (news['title'] + ' ' + news['summary']).lower()
            
            for keyword in bullish_keywords:
                if keyword in text:
                    bullish_count += 1
            
            for keyword in bearish_keywords:
                if keyword in text:
                    bearish_count += 1
        
        # Calculate score
        total = bullish_count + bearish_count
        if total == 0:
            sentiment = 'neutral'
            score = 0
            analysis = "🟡 Sentimen berita netral"
        else:
            ratio = (bullish_count - bearish_count) / total
            score = ratio * 100
            
            if score > 20:
                sentiment = 'very_bullish'
                analysis = "🟢 Sentimen berita sangat positif - Banyak berita bullish"
            elif score > 0:
                sentiment = 'bullish'
                analysis = "🟢 Sentimen berita positif - Lebih banyak berita bullish"
            elif score > -20:
                sentiment = 'bearish'
                analysis = "🔴 Sentimen berita negatif - Lebih banyak berita bearish"
            else:
                sentiment = 'very_bearish'
                analysis = "🔴 Sentimen berita sangat negatif - Banyak berita bearish"
        
        return {
            'sentiment': sentiment,
            'score': score,
            'bullish_signals': bullish_count,
            'bearish_signals': bearish_count,
            'total_news': len(news_list),
            'analysis': analysis
        }
    
    def get_trending_topics(self) -> List[str]:
        """Extract trending topics from news"""
        news = self.get_latest_news(limit=20)
        
        # Common crypto topics
        topics = {}
        keywords = [
            'bitcoin', 'ethereum', 'btc', 'eth', 'defi', 'nft', 'metaverse',
            'regulation', 'sec', 'etf', 'halving', 'mining', 'staking',
            'layer 2', 'scaling', 'adoption', 'institutional'
        ]
        
        for news_item in news:
            text = (news_item['title'] + ' ' + news_item['summary']).lower()
            
            for keyword in keywords:
                if keyword in text:
                    topics[keyword] = topics.get(keyword, 0) + 1
        
        # Sort by frequency
        sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
        
        return [topic[0] for topic in sorted_topics[:10]]
    
    def get_news_summary_text(self, limit: int = 5) -> str:
        """Get formatted news summary text"""
        news_list = self.get_latest_news(limit=limit)
        sentiment = self.analyze_news_sentiment(news_list)
        
        summary = f"""
📰 LATEST CRYPTO NEWS
{'='*60}

{sentiment['analysis']}
Bullish Signals: {sentiment['bullish_signals']} | Bearish Signals: {sentiment['bearish_signals']}

"""
        
        for i, news in enumerate(news_list, 1):
            summary += f"""
[{i}] {news['title']}
    📌 Source: {news['source']} | ⏰ {news['time_ago']}
    🔗 {news['link']}
    
"""
        
        trending = self.get_trending_topics()
        if trending:
            summary += f"\n🔥 Trending Topics: {', '.join(trending[:5])}\n"
        
        return summary