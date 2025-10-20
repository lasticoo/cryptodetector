# app/ui/components/sentiment_panel.py - FONT DIPERBESAR
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QTabWidget, QScrollArea,
                             QFrame, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from ...services.sentiment_analysis import SentimentAnalysisService
from ...services.news_service import NewsService
from ...services.economic_indicators import EconomicIndicatorsService

class SentimentPanel(QWidget):
    """Panel untuk menampilkan sentiment, news, dan economic analysis"""
    
    refresh_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.sentiment_service = SentimentAnalysisService()
        self.news_service = NewsService()
        self.economic_service = EconomicIndicatorsService()
        
        self.current_symbol = None
        self.init_ui()
        
        # Auto refresh timer (setiap 3 menit)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(180000)  # 3 menit
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("📊 SENTIMENT & NEWS ANALYSIS")
        title_font = QFont("Arial", 13, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #0d7377;")
        header.addWidget(title)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setMaximumWidth(100)
        self.refresh_btn.clicked.connect(self.manual_refresh)
        header.addWidget(self.refresh_btn)
        
        # Last update label
        self.last_update_label = QLabel("Last update: Never")
        self.last_update_label.setStyleSheet("color: #888; font-size: 10px;")
        header.addWidget(self.last_update_label)
        
        header.addStretch()
        layout.addLayout(header)
        
        # Tab widget for different analyses
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #444; background: #2d2d2d; }
            QTabBar::tab { background: #1e1e1e; color: #fff; padding: 8px 15px; margin: 2px; border: 1px solid #444; font-size: 11px; font-weight: bold; }
            QTabBar::tab:selected { background: #0d7377; }
            QTabBar::tab:hover { background: #14919b; }
        """)
        
        # Tab 1: Market Overview
        self.market_tab = self.create_market_overview_tab()
        self.tabs.addTab(self.market_tab, "🌍 Market")
        
        # Tab 2: Coin Sentiment
        self.coin_tab = self.create_coin_sentiment_tab()
        self.tabs.addTab(self.coin_tab, "💰 Coin")
        
        # Tab 3: News
        self.news_tab = self.create_news_tab()
        self.tabs.addTab(self.news_tab, "📰 News")
        
        # Tab 4: Economic Indicators
        self.economic_tab = self.create_economic_tab()
        self.tabs.addTab(self.economic_tab, "📊 Economic")
        
        layout.addWidget(self.tabs)
        
        # Initial load
        self.load_all_data()
    
    def create_market_overview_tab(self) -> QWidget:
        """Create market overview tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Fear & Greed Index
        fng_frame = QFrame()
        fng_frame.setStyleSheet("background: #1e1e1e; border: 1px solid #444; border-radius: 5px; padding: 10px;")
        fng_layout = QVBoxLayout(fng_frame)
        
        fng_title = QLabel("🌡️ FEAR & GREED INDEX")
        fng_title_font = QFont("Arial", 12, QFont.Bold)
        fng_title.setFont(fng_title_font)
        fng_layout.addWidget(fng_title)
        
        self.fng_value_label = QLabel("Loading...")
        fng_value_font = QFont("Arial", 28, QFont.Bold)
        self.fng_value_label.setFont(fng_value_font)
        self.fng_value_label.setAlignment(Qt.AlignCenter)
        fng_layout.addWidget(self.fng_value_label)
        
        self.fng_progress = QProgressBar()
        self.fng_progress.setMaximum(100)
        self.fng_progress.setStyleSheet("""
            QProgressBar { border: 2px solid #444; border-radius: 5px; text-align: center; background: #2d2d2d; height: 25px; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f23645, stop:0.5 #ffd700, stop:1 #26a69a); }
        """)
        fng_layout.addWidget(self.fng_progress)
        
        self.fng_interpretation = QLabel("")
        interp_font = QFont("Arial", 11)
        self.fng_interpretation.setFont(interp_font)
        self.fng_interpretation.setWordWrap(True)
        self.fng_interpretation.setStyleSheet("color: #ccc; padding: 5px;")
        fng_layout.addWidget(self.fng_interpretation)
        
        layout.addWidget(fng_frame)
        
        # Global Stats
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background: #1e1e1e; border: 1px solid #444; border-radius: 5px; padding: 10px;")
        stats_layout = QVBoxLayout(stats_frame)
        
        stats_title = QLabel("💰 GLOBAL CRYPTO MARKET")
        stats_title_font = QFont("Arial", 12, QFont.Bold)
        stats_title.setFont(stats_title_font)
        stats_layout.addWidget(stats_title)
        
        self.global_stats_text = QTextEdit()
        self.global_stats_text.setReadOnly(True)
        self.global_stats_text.setMaximumHeight(150)
        self.global_stats_text.setStyleSheet("""
            QTextEdit { background: #2d2d2d; color: #fff; border: none; font-family: 'Courier New'; font-size: 11px; padding: 5px; }
        """)
        stats_layout.addWidget(self.global_stats_text)
        
        layout.addWidget(stats_frame)
        
        # Trending Coins
        trending_frame = QFrame()
        trending_frame.setStyleSheet("background: #1e1e1e; border: 1px solid #444; border-radius: 5px; padding: 10px;")
        trending_layout = QVBoxLayout(trending_frame)
        
        trending_title = QLabel("🔥 TRENDING COINS")
        trending_title_font = QFont("Arial", 12, QFont.Bold)
        trending_title.setFont(trending_title_font)
        trending_layout.addWidget(trending_title)
        
        self.trending_text = QTextEdit()
        self.trending_text.setReadOnly(True)
        self.trending_text.setMaximumHeight(120)
        self.trending_text.setStyleSheet("""
            QTextEdit { background: #2d2d2d; color: #fff; border: none; font-family: 'Courier New'; font-size: 11px; padding: 5px; }
        """)
        trending_layout.addWidget(self.trending_text)
        
        layout.addWidget(trending_frame)
        layout.addStretch()
        
        return widget
    
    def create_coin_sentiment_tab(self) -> QWidget:
        """Create coin-specific sentiment tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Coin selector info
        info_label = QLabel("Select a coin from the main chart to see its sentiment analysis")
        info_font = QFont("Arial", 11)
        info_label.setFont(info_font)
        info_label.setStyleSheet("color: #888; font-style: italic; padding: 10px;")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        # Sentiment scores
        scores_frame = QFrame()
        scores_frame.setStyleSheet("background: #1e1e1e; border: 1px solid #444; border-radius: 5px; padding: 10px;")
        scores_layout = QVBoxLayout(scores_frame)
        
        self.coin_name_label = QLabel("Select a coin...")
        coin_name_font = QFont("Arial", 16, QFont.Bold)
        self.coin_name_label.setFont(coin_name_font)
        self.coin_name_label.setAlignment(Qt.AlignCenter)
        scores_layout.addWidget(self.coin_name_label)
        
        self.sentiment_score_label = QLabel("")
        score_font = QFont("Arial", 20, QFont.Bold)
        self.sentiment_score_label.setFont(score_font)
        self.sentiment_score_label.setAlignment(Qt.AlignCenter)
        scores_layout.addWidget(self.sentiment_score_label)
        
        layout.addWidget(scores_frame)
        
        # Detailed metrics
        self.coin_details_text = QTextEdit()
        self.coin_details_text.setReadOnly(True)
        self.coin_details_text.setStyleSheet("""
            QTextEdit { background: #2d2d2d; color: #fff; border: 1px solid #444; border-radius: 5px; font-family: 'Courier New'; font-size: 10px; padding: 8px; }
        """)
        layout.addWidget(self.coin_details_text)
        
        return widget
    
    def create_news_tab(self) -> QWidget:
        """Create news tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # News sentiment summary
        sentiment_frame = QFrame()
        sentiment_frame.setStyleSheet("background: #1e1e1e; border: 1px solid #444; border-radius: 5px; padding: 10px;")
        sentiment_layout = QVBoxLayout(sentiment_frame)
        
        self.news_sentiment_label = QLabel("📊 News Sentiment: Loading...")
        news_sentiment_font = QFont("Arial", 12, QFont.Bold)
        self.news_sentiment_label.setFont(news_sentiment_font)
        sentiment_layout.addWidget(self.news_sentiment_label)
        
        layout.addWidget(sentiment_frame)
        
        # News list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        self.news_content = QTextEdit()
        self.news_content.setReadOnly(True)
        self.news_content.setStyleSheet("""
            QTextEdit { background: #2d2d2d; color: #fff; border: none; font-family: 'Segoe UI'; font-size: 11px; padding: 10px; }
        """)
        
        scroll.setWidget(self.news_content)
        layout.addWidget(scroll)
        
        return widget
    
    def create_economic_tab(self) -> QWidget:
        """Create economic indicators tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        self.economic_content = QTextEdit()
        self.economic_content.setReadOnly(True)
        self.economic_content.setStyleSheet("""
            QTextEdit { background: #2d2d2d; color: #fff; border: none; font-family: 'Courier New'; font-size: 11px; padding: 10px; }
        """)
        
        scroll.setWidget(self.economic_content)
        layout.addWidget(scroll)
        
        return widget
    
    def load_all_data(self):
        """Load all sentiment, news, and economic data"""
        try:
            self.load_market_overview()
            self.load_news()
            self.load_economic_data()
            
            from datetime import datetime
            self.last_update_label.setText(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"Error loading sentiment data: {e}")
    
    def load_market_overview(self):
        """Load market overview data"""
        try:
            fng = self.sentiment_service.get_fear_greed_index()
            value = fng.get('value', 50)
            classification = fng.get('classification', 'Neutral')
            interpretation = fng.get('interpretation', '')
            
            self.fng_value_label.setText(f"{value}/100")
            self.fng_progress.setValue(value)
            self.fng_interpretation.setText(f"{classification}\n\n{interpretation}")
            
            if value <= 24:
                color = "#26a69a"
            elif value <= 49:
                color = "#ffd700"
            elif value <= 74:
                color = "#ff9800"
            else:
                color = "#f23645"
            
            self.fng_value_label.setStyleSheet(f"color: {color};")
            
            stats = self.sentiment_service.get_global_crypto_stats()
            stats_text = f"""
Total Market Cap: ${stats.get('total_market_cap_usd', 0)/1e12:.2f}T
24h Volume: ${stats.get('total_volume_24h_usd', 0)/1e9:.2f}B
24h Change: {stats.get('market_cap_change_24h_pct', 0):+.2f}%

BTC Dominance: {stats.get('bitcoin_dominance', 0):.2f}%
ETH Dominance: {stats.get('ethereum_dominance', 0):.2f}%

{stats.get('dominance_interpretation', '')}

Active Cryptos: {stats.get('active_cryptocurrencies', 0):,}
Markets: {stats.get('markets', 0):,}
"""
            self.global_stats_text.setText(stats_text)
            
            trending = self.sentiment_service.get_trending_coins()
            trending_text = ""
            for i, coin in enumerate(trending[:10], 1):
                trending_text += f"{i}. {coin['name']} ({coin['symbol'].upper()}) - Rank #{coin['rank']}\n"
            
            self.trending_text.setText(trending_text if trending_text else "No trending data available")
            
        except Exception as e:
            print(f"Error loading market overview: {e}")
    
    def load_news(self):
        """Load latest news"""
        try:
            news_list = self.news_service.get_latest_news(limit=10)
            sentiment = self.news_service.analyze_news_sentiment(news_list)
            
            self.news_sentiment_label.setText(f"📊 News Sentiment: {sentiment['analysis']}")
            
            news_text = f"""
Bullish Signals: {sentiment['bullish_signals']} | Bearish Signals: {sentiment['bearish_signals']}
Total News: {sentiment['total_news']}

{'='*60}

"""
            
            for i, news in enumerate(news_list, 1):
                news_text += f"""
[{i}] {news['title']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 {news['source']} | ⏰ {news['time_ago']}
{news['summary']}
🔗 {news['link']}

"""
            
            self.news_content.setText(news_text)
            
        except Exception as e:
            print(f"Error loading news: {e}")
            self.news_content.setText("Error loading news. Please try again.")
    
    def load_economic_data(self):
        """Load economic indicators"""
        try:
            analysis = self.economic_service.get_comprehensive_economic_analysis()
            self.economic_content.setText(analysis)
        except Exception as e:
            print(f"Error loading economic data: {e}")
            self.economic_content.setText("Error loading economic data. Please try again.")
    
    def update_coin_sentiment(self, symbol: str):
        """Update coin-specific sentiment"""
        self.current_symbol = symbol
        
        try:
            coin_id = self.sentiment_service.convert_symbol_to_coingecko_id(symbol)
            sentiment = self.sentiment_service.get_coin_sentiment(coin_id)
            
            if 'error' not in sentiment:
                self.coin_name_label.setText(f"{sentiment['name']} ({sentiment['symbol']})")
                
                overall = sentiment.get('overall_sentiment', {})
                classification = overall.get('classification', 'Unknown')
                score = overall.get('score', 0)
                
                self.sentiment_score_label.setText(f"{classification}")
                
                if 'BULLISH' in classification:
                    color = "#26a69a"
                elif 'BEARISH' in classification:
                    color = "#f23645"
                else:
                    color = "#ffd700"
                
                self.sentiment_score_label.setStyleSheet(f"color: {color};")
                
                details = f"""
═══════════════════════════════════════════
SENTIMENT ANALYSIS FOR {sentiment['name']}
═══════════════════════════════════════════

Overall Score: {score}/10
Classification: {classification}

Reasons:
"""
                for reason in overall.get('reasons', []):
                    details += f"  • {reason}\n"
                
                details += f"""

MARKET DATA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Market Cap Rank: #{sentiment.get('market_cap_rank', 'N/A')}
Market Cap: ${sentiment.get('market_cap', 0)/1e9:.2f}B
24h Volume: ${sentiment.get('total_volume', 0)/1e9:.2f}B

PRICE CHANGES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
24h: {sentiment.get('price_change_24h_pct', 0):+.2f}%
7d: {sentiment.get('price_change_7d_pct', 0):+.2f}%
30d: {sentiment.get('price_change_30d_pct', 0):+.2f}%
From ATH: {sentiment.get('ath_change_percentage', 0):+.2f}%

SCORES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CoinGecko Score: {sentiment.get('coingecko_score', 0):.1f}/100
Developer Score: {sentiment.get('developer_score', 0):.1f}/100
Community Score: {sentiment.get('community_score', 0):.1f}/100
Liquidity Score: {sentiment.get('liquidity_score', 0):.1f}/100

COMMUNITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Twitter Followers: {sentiment.get('twitter_followers', 0):,}
Reddit Subscribers: {sentiment.get('reddit_subscribers', 0):,}

SENTIMENT VOTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👍 Bullish: {sentiment.get('sentiment_votes_up_percentage', 0):.1f}%
👎 Bearish: {sentiment.get('sentiment_votes_down_percentage', 0):.1f}%
"""
                
                self.coin_details_text.setText(details)
            else:
                self.coin_name_label.setText(f"{symbol} - Data Not Available")
                self.sentiment_score_label.setText("")
                self.coin_details_text.setText("Unable to fetch sentiment data for this coin.")
                
        except Exception as e:
            print(f"Error updating coin sentiment: {e}")
            self.coin_details_text.setText(f"Error: {str(e)}")
    
    def manual_refresh(self):
        """Manual refresh button clicked"""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("⏳ Refreshing...")
        self.load_all_data()
        
        QTimer.singleShot(2000, lambda: self.refresh_btn.setEnabled(True))
        QTimer.singleShot(2000, lambda: self.refresh_btn.setText("🔄 Refresh"))
    
    def auto_refresh(self):
        """Auto refresh (called by timer)"""
        self.load_all_data()