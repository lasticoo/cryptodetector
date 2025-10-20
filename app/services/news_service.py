# app/services/news_service.py
import os
import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict
import time

class NewsService:
    """Service untuk mendapatkan berita crypto real-time + radar 'awal' berbasis sumber publik"""

    def __init__(self):
        self.sources = {
            'cointelegraph_rss': 'https://cointelegraph.com/rss',
            'coindesk_rss': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
            'cryptonews_rss': 'https://cryptonews.com/news/feed/',
            # Reddit RSS (publik)
            'reddit_cc': 'https://www.reddit.com/r/CryptoCurrency/new/.rss',
            'reddit_markets': 'https://www.reddit.com/r/CryptoMarkets/new/.rss',
            'reddit_altcoin': 'https://www.reddit.com/r/Altcoin/new/.rss',
            # Optional event calendar (butuh API key, aman jika kosong)
            'coinmarketcal_api': 'https://developers.coinmarketcal.com/v1/events'
        }
        self.cache = {}
        self.cache_duration = 180  # 3 menit untuk news
        self.long_cache_duration = 900  # 15 menit untuk feed yang lebih berat

        # Opsional API keys (biarkan kosong jika tidak ada)
        self.cmc_api_key = os.environ.get("COINMARKETCAL_API_KEY", "").strip()

    # -------------- cache helpers --------------
    def _get_cache(self, key):
        if key in self.cache:
            data, timestamp, ttl = self.cache[key]
            if time.time() - timestamp < ttl:
                return data
        return None

    def _set_cache(self, key, data, ttl=None):
        if ttl is None:
            ttl = self.cache_duration
        self.cache[key] = (data, time.time(), ttl)

    # -------------- core news --------------
    def get_latest_news(self, limit: int = 10) -> List[Dict]:
        """Get latest crypto news dari beberapa sumber RSS (publik)"""
        cache_key = f'news_latest_{limit}'
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        all_news = []
        # Major sites
        all_news.extend(self._safe_fetch_rss(self.sources['cointelegraph_rss'], 'CoinTelegraph', take=10))
        all_news.extend(self._safe_fetch_rss(self.sources['coindesk_rss'], 'CoinDesk', take=10))
        all_news.extend(self._safe_fetch_rss(self.sources['cryptonews_rss'], 'CryptoNews', take=10))

        # Sort by date desc
        all_news.sort(key=lambda x: x['published_timestamp'], reverse=True)
        result = all_news[:limit]
        self._set_cache(cache_key, result)
        return result

    def _safe_fetch_rss(self, url: str, source: str, take: int = 15) -> List[Dict]:
        try:
            feed = feedparser.parse(url)
            news_list = []
            for entry in feed.entries[:take]:
                # published
                try:
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6])
                    else:
                        pub_date = datetime.utcnow()
                except:
                    pub_date = datetime.utcnow()

                summary = entry.get('summary', '') or entry.get('description', '') or ''
                summary = summary.replace('\n', ' ').strip()
                if len(summary) > 220:
                    summary = summary[:220] + '...'

                news_item = {
                    'title': entry.get('title', 'No Title'),
                    'link': entry.get('link', ''),
                    'summary': summary,
                    'source': source,
                    'published': pub_date.strftime('%Y-%m-%d %H:%M'),
                    'published_timestamp': pub_date.timestamp(),
                    'time_ago': self._time_ago(pub_date)
                }
                news_list.append(news_item)
            return news_list
        except Exception as e:
            print(f"RSS error ({source}): {e}")
            return []

    def _time_ago(self, dt: datetime) -> str:
        now = datetime.now()
        diff = now - dt
        if diff.days > 0:
            return f"{diff.days} hari lalu"
        elif diff.seconds >= 3600:
            return f"{diff.seconds // 3600} jam lalu"
        elif diff.seconds >= 60:
            return f"{diff.seconds // 60} menit lalu"
        return "Baru saja"

    # -------------- per coin --------------
    def get_coin_specific_news(self, coin_name: str, limit: int = 8) -> List[Dict]:
        """Filter headline publik yang mengandung nama koin (title/summary)"""
        all_news = self.get_latest_news(limit=50)
        keywords = [w for w in coin_name.lower().split() if w]
        filtered = []
        for n in all_news:
            text = (n['title'] + ' ' + n['summary']).lower()
            if any(k in text for k in keywords):
                filtered.append(n)
        return filtered[:limit]

    # -------------- trending topics --------------
    def get_trending_topics(self) -> List[str]:
        """Ekstrak topik tren dari headline publik"""
        news = self.get_latest_news(limit=25)
        topics = {}
        keywords = [
            'bitcoin','btc','ethereum','eth','etf','defi','staking','airdrop',
            'listing','binance','coinbase','regulation','sec','halving','layer 2',
            'scaling','nft','metaverse','restaking','l2','zk','rollup','ai'
        ]
        for n in news:
            text = (n['title'] + ' ' + n['summary']).lower()
            for k in keywords:
                if k in text:
                    topics[k] = topics.get(k, 0) + 1
        return [k for k, _ in sorted(topics.items(), key=lambda x: x[1], reverse=True)[:10]]

    # -------------- sentiment dari news (sederhana) --------------
    def analyze_news_sentiment(self, news_list: List[Dict]) -> Dict:
        if not news_list:
            return {'sentiment': 'neutral', 'score': 0, 'analysis': 'No news available',
                    'bullish_signals': 0, 'bearish_signals': 0, 'total_news': 0}

        bullish_kw = [
            'surge','soar','rally','gain','rise','pump','breakout','bullish','growth',
            'adoption','partnership','upgrade','launch','record','high','approval','etf',
            'integrat','invest','fund','listing','whale buy','burn','mint successful'
        ]
        bearish_kw = [
            'crash','plunge','fall','drop','dump','decline','bearish','hack','scam',
            'regulation','ban','lawsuit','warning','risk','concern','investigate','fraud',
            'delist','exploit','outage','halt'
        ]

        bpos, bneg = 0, 0
        for n in news_list:
            text = (n['title'] + ' ' + n['summary']).lower()
            bpos += sum(1 for k in bullish_kw if k in text)
            bneg += sum(1 for k in bearish_kw if k in text)

        total = max(1, bpos + bneg)
        ratio = (bpos - bneg) / total
        score = int((ratio + 1) * 50)  # 0..100

        if score >= 70:
            label = "very_bullish"; analysis = "🟢 Sangat positif (headline dominan bullish)"
        elif score >= 55:
            label = "bullish"; analysis = "🟢 Positif (bullish > bearish)"
        elif score > 45:
            label = "neutral"; analysis = "🟡 Netral"
        elif score > 30:
            label = "bearish"; analysis = "🔴 Negatif (bearish > bullish)"
        else:
            label = "very_bearish"; analysis = "🔴 Sangat negatif (headline dominan bearish)"

        return {
            'sentiment': label, 'score': score, 'analysis': analysis,
            'bullish_signals': bpos, 'bearish_signals': bneg, 'total_news': len(news_list)
        }

    # -------------- Reddit radar (publik) --------------
    def get_reddit_stream(self, limit: int = 20) -> List[Dict]:
        """Ambil judul post terbaru dari subreddit crypto (RSS publik)"""
        cache_key = f"reddit_stream_{limit}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        items = []
        for url, src in [
            (self.sources['reddit_cc'], 'r/CryptoCurrency'),
            (self.sources['reddit_markets'], 'r/CryptoMarkets'),
            (self.sources['reddit_altcoin'], 'r/Altcoin')
        ]:
            items.extend(self._safe_fetch_rss(url, src, take=limit))

        items.sort(key=lambda x: x['published_timestamp'], reverse=True)
        items = items[:limit]
        self._set_cache(cache_key, items, ttl=self.long_cache_duration)
        return items

    def get_coin_rumor_feed(self, coin: str, limit: int = 15) -> List[Dict]:
        """Saring post Reddit/berita publik yang mengandung kata kunci 'rumor/leak/listing' terkait coin."""
        stream = self.get_reddit_stream(limit=60) + self.get_latest_news(limit=40)
        kws = [coin.lower(), coin.lower().split('/')[0]]
        rumor_kw = ['rumor','leak','insider','listing','airdrop','snapshot','testnet','mainnet','upgrade','partnership']
        out = []
        for it in stream:
            text = (it['title'] + ' ' + it.get('summary', '')).lower()
            if any(k in text for k in kws) and any(r in text for r in rumor_kw):
                out.append(it)
        out.sort(key=lambda x: x['published_timestamp'], reverse=True)
        return out[:limit]

    # -------------- Calendar events (opsional – publik via API key) --------------
    def get_coin_events(self, symbol_or_name: str, limit: int = 5) -> List[Dict]:
        """
        Ambil event dari CoinMarketCal jika API key tersedia.
        Aman: bila key kosong/invalid -> return [] tanpa error fatal.
        """
        cache_key = f"cmc_events_{symbol_or_name}_{limit}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        if not self.cmc_api_key:
            self._set_cache(cache_key, [], ttl=self.long_cache_duration)
            return []

        try:
            headers = {'x-api-key': self.cmc_api_key, 'Accept': 'application/json'}
            params = {
                'max': limit,
                'coins': symbol_or_name,
                'page': 1,
                'showOnly': 'true'  # hanya upcoming/verified jika tersedia
            }
            r = requests.get(self.sources['coinmarketcal_api'], headers=headers, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json().get('body', []) if isinstance(r.json(), dict) else []
                events = []
                for e in data[:limit]:
                    events.append({
                        'title': e.get('title', 'Event'),
                        'date_event': e.get('date_event', ''),
                        'coin': e.get('coins', [{}])[0].get('name', ''),
                        'source': 'CoinMarketCal',
                        'link': e.get('source', ''),
                        'is_conference': e.get('is_conference', False)
                    })
                self._set_cache(cache_key, events, ttl=self.long_cache_duration)
                return events
        except Exception as e:
            print(f"CoinMarketCal error: {e}")

        self._set_cache(cache_key, [], ttl=self.long_cache_duration)
        return []

    # -------------- Summary helpers --------------
    def get_news_summary_text(self, limit: int = 5) -> str:
        news_list = self.get_latest_news(limit=limit)
        sentiment = self.analyze_news_sentiment(news_list)
        summary = f"""
📰 LATEST CRYPTO NEWS
{'='*60}

{sentiment['analysis']} (Score: {sentiment['score']}/100)
Bullish: {sentiment['bullish_signals']} | Bearish: {sentiment['bearish_signals']} | Total: {sentiment['total_news']}
"""
        for i, n in enumerate(news_list, 1):
            summary += f"""
[{i}] {n['title']}
    📌 {n['source']} | ⏰ {n['time_ago']}
    🔗 {n['link']}
"""
        trending = self.get_trending_topics()
        if trending:
            summary += f"\n🔥 Trending Topics: {', '.join(trending[:5])}\n"
        return summary
