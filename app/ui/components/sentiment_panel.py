# app/ui/components/sentiment_panel.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QTabWidget, QScrollArea,
                             QFrame, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from ...services.sentiment_analysis import SentimentAnalysisService
from ...services.news_service import NewsService
from ...services.economic_indicators import EconomicIndicatorsService
from ...services.alpha_signals import AlphaSignalsService   # 🔥 NEW
from ...services.alpha_signals import AlphaSignalsService
 
class SentimentPanel(QWidget):
    """Panel untuk menampilkan sentiment, news, economic analysis + Alpha/Rumor Radar (publik & derivatif)"""
    
    refresh_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.alpha_service = AlphaSignalsService()  # sudah default baca COINGLASS_API_KEY atau key bawaan
        self.sentiment_service = SentimentAnalysisService()
        self.news_service = NewsService()
        self.economic_service = EconomicIndicatorsService()
        self.alpha_service = AlphaSignalsService()          # 🔥 NEW
        
        self.current_symbol = None
        self._last_coin_news_sentiment = None  # cache ringan
        
        self.init_ui()
        
        # Auto refresh timer (setiap 3 menit)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(180000)  # 3 menit
    
    # ---------- UI ----------
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("📊 SENTIMENT, NEWS & ALPHA RADAR")
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
        
        # Tab widget
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

        # Tab 5: Alpha/Radar
        self.alpha_tab = self.create_alpha_radar_tab()
        self.tabs.addTab(self.alpha_tab, "🧭 Alpha Radar")
        
        layout.addWidget(self.tabs)
        
        # Initial load
        self.load_all_data()
    
    # ---------- Tabs ----------
    def create_market_overview_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Fear & Greed
        fng_frame = QFrame()
        fng_frame.setStyleSheet("background: #1e1e1e; border: 1px solid #444; border-radius: 5px; padding: 10px;")
        fng_layout = QVBoxLayout(fng_frame)
        
        fng_title = QLabel("🌡️ FEAR & GREED INDEX")
        fng_title.setFont(QFont("Arial", 12, QFont.Bold))
        fng_layout.addWidget(fng_title)
        
        self.fng_value_label = QLabel("Loading...")
        self.fng_value_label.setFont(QFont("Arial", 28, QFont.Bold))
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
        self.fng_interpretation.setFont(QFont("Arial", 11))
        self.fng_interpretation.setWordWrap(True)
        self.fng_interpretation.setStyleSheet("color: #ccc; padding: 5px;")
        fng_layout.addWidget(self.fng_interpretation)
        
        layout.addWidget(fng_frame)
        
        # Global Stats
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background: #1e1e1e; border: 1px solid #444; border-radius: 5px; padding: 10px;")
        stats_layout = QVBoxLayout(stats_frame)
        
        st = QLabel("💰 GLOBAL CRYPTO MARKET")
        st.setFont(QFont("Arial", 12, QFont.Bold))
        stats_layout.addWidget(st)
        
        self.global_stats_text = QTextEdit()
        self.global_stats_text.setReadOnly(True)
        self.global_stats_text.setMaximumHeight(150)
        self.global_stats_text.setStyleSheet("""
            QTextEdit { background: #2d2d2d; color: #fff; border: none; font-family: 'Courier New'; font-size: 11px; padding: 5px; }
        """)
        stats_layout.addWidget(self.global_stats_text)
        
        layout.addWidget(stats_frame)
        
        # Trending
        trending_frame = QFrame()
        trending_frame.setStyleSheet("background: #1e1e1e; border: 1px solid #444; border-radius: 5px; padding: 10px;")
        tL = QVBoxLayout(trending_frame)
        
        lt = QLabel("🔥 TRENDING COINS")
        lt.setFont(QFont("Arial", 12, QFont.Bold))
        tL.addWidget(lt)
        
        self.trending_text = QTextEdit()
        self.trending_text.setReadOnly(True)
        self.trending_text.setMaximumHeight(120)
        self.trending_text.setStyleSheet("""
            QTextEdit { background: #2d2d2d; color: #fff; border: none; font-family: 'Courier New'; font-size: 11px; padding: 5px; }
        """)
        tL.addWidget(self.trending_text)
        
        layout.addWidget(trending_frame)
        layout.addStretch()
        return widget
    
    def create_coin_sentiment_tab(self) -> QWidget:
        widget = QWidget(); layout = QVBoxLayout(widget)
        info = QLabel("Select a coin from the main chart to see its sentiment analysis")
        info.setFont(QFont("Arial", 11)); info.setStyleSheet("color: #888; font-style: italic; padding: 10px;")
        info.setAlignment(Qt.AlignCenter); layout.addWidget(info)
        
        scores_frame = QFrame(); scores_frame.setStyleSheet("background: #1e1e1e; border: 1px solid #444; border-radius: 5px; padding: 10px;")
        sL = QVBoxLayout(scores_frame)
        self.coin_name_label = QLabel("Select a coin..."); self.coin_name_label.setFont(QFont("Arial", 16, QFont.Bold)); self.coin_name_label.setAlignment(Qt.AlignCenter); sL.addWidget(self.coin_name_label)
        self.sentiment_score_label = QLabel(""); self.sentiment_score_label.setFont(QFont("Arial", 20, QFont.Bold)); self.sentiment_score_label.setAlignment(Qt.AlignCenter); sL.addWidget(self.sentiment_score_label)
        layout.addWidget(scores_frame)
        
        self.coin_details_text = QTextEdit(); self.coin_details_text.setReadOnly(True)
        self.coin_details_text.setStyleSheet("QTextEdit { background: #2d2d2d; color: #fff; border: 1px solid #444; border-radius: 5px; font-family: 'Courier New'; font-size: 10px; padding: 8px; }")
        layout.addWidget(self.coin_details_text)
        return widget
    
    def create_news_tab(self) -> QWidget:
        widget = QWidget(); layout = QVBoxLayout(widget)
        sentiment_frame = QFrame(); sentiment_frame.setStyleSheet("background: #1e1e1e; border: 1px solid #444; border-radius: 5px; padding: 10px;")
        sL = QVBoxLayout(sentiment_frame)
        self.news_sentiment_label = QLabel("📊 News Sentiment: Loading..."); self.news_sentiment_label.setFont(QFont("Arial", 12, QFont.Bold)); sL.addWidget(self.news_sentiment_label)
        layout.addWidget(sentiment_frame)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setStyleSheet("border: none;")
        self.news_content = QTextEdit(); self.news_content.setReadOnly(True)
        self.news_content.setStyleSheet("QTextEdit { background: #2d2d2d; color: #fff; border: none; font-family: 'Segoe UI'; font-size: 11px; padding: 10px; }")
        scroll.setWidget(self.news_content); layout.addWidget(scroll)
        return widget
    
    def create_economic_tab(self) -> QWidget:
        widget = QWidget(); layout = QVBoxLayout(widget)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setStyleSheet("border: none;")
        self.economic_content = QTextEdit(); self.economic_content.setReadOnly(True)
        self.economic_content.setStyleSheet("QTextEdit { background: #2d2d2d; color: #fff; border: none; font-family: 'Courier New'; font-size: 11px; padding: 10px; }")
        scroll.setWidget(self.economic_content); layout.addWidget(scroll)
        return widget

    def create_alpha_radar_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

    # Composite score bar
        score_box = QFrame()
        score_box.setStyleSheet("background:#1e1e1e;border:1px solid #444;border-radius:5px;padding:10px;")
        sL = QVBoxLayout(score_box)
        title = QLabel("🧭 Alpha Signals (Derivatives & Smart-Money) — CoinGlass/Binance")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        sL.addWidget(title)

        self.comp_score_bar = QProgressBar()
        self.comp_score_bar.setMaximum(100)
        self.comp_score_bar.setStyleSheet("""
        QProgressBar{border:2px solid #444;border-radius:5px;text-align:center;background:#2d2d2d;height:24px;}
        QProgressBar::chunk{background:#00b894;}
        """)
        sL.addWidget(self.comp_score_bar)

        self.comp_score_label = QLabel("NEUTRAL — 50/100")
        self.comp_score_label.setAlignment(Qt.AlignCenter)
        self.comp_score_label.setStyleSheet("color:#ccc;padding:4px;")
        sL.addWidget(self.comp_score_label)
        layout.addWidget(score_box)

    # Smart-Money box
        sm_box = QFrame()
        sm_box.setStyleSheet("background:#1e1e1e;border:1px solid #444;border-radius:5px;padding:10px;")
        smL = QVBoxLayout(sm_box)
        t2 = QLabel("⚡ Smart-Money Flow (24h)")
        t2.setFont(QFont("Arial", 12, QFont.Bold))
        smL.addWidget(t2)
        self.smart_money_label = QLabel("—")
        self.smart_money_label.setStyleSheet("color:#ffd700;padding:4px;")
        smL.addWidget(self.smart_money_label)
        layout.addWidget(sm_box)

    # Detail area (insight + headlines publik)
        feed_box = QFrame()
        feed_box.setStyleSheet("background:#1e1e1e;border:1px solid #444;border-radius:5px;padding:10px;")
        fL = QVBoxLayout(feed_box)
        t3 = QLabel("📝 Smart-Money & Derivatives Detail")
        t3.setFont(QFont("Arial", 12, QFont.Bold))
        fL.addWidget(t3)
        self.alpha_text = QTextEdit()
        self.alpha_text.setReadOnly(True)
        self.alpha_text.setStyleSheet("QTextEdit{background:#2d2d2d;color:#fff;border:none;font-family:'Courier New';font-size:11px;padding:8px;}")
        fL.addWidget(self.alpha_text)
        layout.addWidget(feed_box)

        layout.addStretch()
        return widget

    
    # ---------- Loaders ----------
    def load_all_data(self):
        try:
            self.load_market_overview()
            self.load_news()
            self.load_economic_data()
            from datetime import datetime as dt
            self.last_update_label.setText(f"Last update: {dt.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"Error loading sentiment data: {e}")
    
    def load_market_overview(self):
        try:
            fng = self.sentiment_service.get_fear_greed_index()
            value = fng.get('value', 50)
            classification = fng.get('classification', 'Neutral')
            interpretation = fng.get('interpretation', '')
            
            self.fng_value_label.setText(f"{value}/100")
            self.fng_progress.setValue(value)
            self.fng_interpretation.setText(f"{classification}\n\n{interpretation}")
            
            if value <= 24: color = "#26a69a"
            elif value <= 49: color = "#ffd700"
            elif value <= 74: color = "#ff9800"
            else: color = "#f23645"
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
                sym = (coin.get('symbol') or '').upper()
                trending_text += f"{i}. {coin.get('name','?')} ({sym}) - Rank #{coin.get('rank','?')}\n"
            self.trending_text.setText(trending_text if trending_text else "No trending data available")
        except Exception as e:
            print(f"Error loading market overview: {e}")
    
    def load_news(self):
        try:
            news_list = self.news_service.get_latest_news(limit=12)
            sentiment = self.news_service.analyze_news_sentiment(news_list)
            self.news_sentiment_label.setText(f"📊 News Sentiment: {sentiment['analysis']} (Score {sentiment['score']}/100)")
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
            self.news_content.setText(news_text.strip())
        except Exception as e:
            print(f"Error loading news: {e}")
            self.news_content.setText("Error loading news. Please try again.")
    
    def load_economic_data(self):
        try:
            analysis = self.economic_service.get_comprehensive_economic_analysis()
            self.economic_content.setText(analysis)
        except Exception as e:
            print(f"Error loading economic data: {e}")
            self.economic_content.setText("Error loading economic data. Please try again.")
    
    # ---------- Per-coin update + Alpha Radar ----------
    def update_coin_sentiment(self, symbol: str):
        """Update coin-specific sentiment & isi Alpha Radar (derivatives)"""
        self.current_symbol = symbol
        try:
            # ----- Sentiment (CoinGecko) -----
            coin_id = self.sentiment_service.convert_symbol_to_coingecko_id(symbol)
            sentiment = self.sentiment_service.get_coin_sentiment(coin_id)
            if 'error' in sentiment:
                self.coin_name_label.setText(f"{symbol} - Data Not Available")
                self.sentiment_score_label.setText("")
                self.coin_details_text.setText("Unable to fetch sentiment data for this coin.")
            else:
                self.coin_name_label.setText(f"{sentiment['name']} ({sentiment['symbol']})")
                overall = sentiment.get('overall_sentiment', {})
                cls = overall.get('classification', 'Unknown')
                score = overall.get('score', 0)
                self.sentiment_score_label.setText(f"{cls}")
                if 'BULLISH' in cls: color = "#26a69a"
                elif 'BEARISH' in cls: color = "#f23645"
                else: color = "#ffd700"
                self.sentiment_score_label.setStyleSheet(f"color: {color};")
                details = f"""
═══════════════════════════════════════════
SENTIMENT ANALYSIS FOR {sentiment['name']}
═══════════════════════════════════════════

Overall Score: {score}/10
Classification: {cls}

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
""".strip()
                self.coin_details_text.setText(details)

            # ----- Alpha Signals (CoinGlass) -----
            base_symbol = symbol.split("/")[0] if "/" in symbol else symbol
            alpha = self.alpha_service.get_alpha_for_symbol(base_symbol)
            self.comp_score_bar.setValue(alpha["score"])
            self.comp_score_label.setText(f"{alpha['label']} — {alpha['score']}/100")

            # Build readable details
            m = alpha["metrics"]
            fr = m.get("funding_rate_8h")
            fr_txt = f"{fr*100:.3f}%" if isinstance(fr, (int,float)) else "—"
            oi_txt = f"{(m.get('oi_change_24h_pct') or 0):+.2f}%"
            oi_lvl = m.get("oi_level")
            oi_lvl_txt = f"${oi_lvl/1e9:.2f}B" if (isinstance(oi_lvl,(int,float)) and oi_lvl>0) else "—"
            ls_acc = m.get("ls_accounts")
            ls_pos = m.get("ls_positions")
            liq_l = m.get("liq_24h_long_usd") or 0
            liq_s = m.get("liq_24h_short_usd") or 0

            txt = "DERIVATIVES SNAPSHOT\n" + "─"*60 + "\n"
            txt += f"Funding (8h): {fr_txt}  [{alpha['metrics'].get('funding_bias','neutral')}]\n"
            txt += f"Open Interest: {oi_lvl_txt}  (Δ24h {oi_txt})\n"
            txt += f"Long/Short Ratio — Accounts: {ls_acc:.2f} | Positions: {ls_pos:.2f}\n" if (ls_acc or ls_pos) else "Long/Short Ratio: —\n"
            txt += f"Liquidations 24h — Long: ${liq_l:,.0f} | Short: ${liq_s:,.0f}\n"
            txt += "\nINSIGHTS\n" + "─"*60 + "\n"
            for r in alpha["insights"]:
                txt += f"• {r}\n"
            self.alpha_text.setText(txt.strip())

        except Exception as e:
            print(f"Error updating coin sentiment: {e}")
            self.coin_details_text.setText(f"Error: {str(e)}")
            self.alpha_text.setText("—")
            # === ALPHA SIGNALS (CoinGlass/Binance) + SMART-MONEY ===
        try:
            alpha = self.alpha_service.get_alpha_for_symbol(symbol)
    # bar & label
            self.comp_score_bar.setValue(alpha['score'])
            self.comp_score_label.setText(f"{alpha['label']} — {alpha['score']}/100")

            sm = alpha.get('smart_money', {})
            sm_label = sm.get('label', 'NEUTRAL')
            sm_score = sm.get('score', 50)
            dls = sm.get('delta_long_share_pp')
            sm_desc = f"Smart-Money Flow: {sm_label} ({sm_score}/100)"
            if dls is not None:
                arrow = '↑' if dls>=0 else '↓'
                sm_desc += f" — Top Trader Long Share {arrow}{abs(dls):.1f} pp/24h"
            self.smart_money_label.setText(sm_desc)

    # detail text
            m = alpha['metrics']
            details_alpha = []
            details_alpha.append("DERIVATIVES SNAPSHOT")
            details_alpha.append("—"*60)
            fr = m.get('funding_rate_8h')
            fr_txt = f"{fr:+.4%}" if (fr is not None) else "—"
            details_alpha.append(f"Funding (8h): {fr_txt}")
            oi_chg = m.get('oi_change_24h_pct')
            oi_txt = f"{oi_chg:+.2f}%" if oi_chg is not None else "—"
            details_alpha.append(f"Open Interest 24h: {oi_txt}")
            ls_acc = m.get('ls_accounts'); ls_pos = m.get('ls_positions')
            details_alpha.append(f"Long/Short Ratio (acc/pos): {ls_acc or '—'} / {ls_pos or '—'}")
            L = m.get('liq_24h_long_usd') or 0; S = m.get('liq_24h_short_usd') or 0
            details_alpha.append(f"Liquidations 24h — Long: ${L:,.0f} | Short: ${S:,.0f}")
            details_alpha.append("")
            details_alpha.append("INSIGHTS")
            details_alpha.append("—"*60)
            for r in alpha.get('insights', []):
                details_alpha.append(f"* {r}")
            details_alpha.append("")
            details_alpha.append("SMART-MONEY NOTES")
            for r in sm.get('reasons', []):
                details_alpha.append(f"* {r}")

            self.alpha_text.setText("\n".join(details_alpha))
        except Exception as _e:
    # jangan blok UI jika gagal
            pass

    # ---------- Refresh ----------
    def manual_refresh(self):
        self.refresh_btn.setEnabled(False); self.refresh_btn.setText("⏳ Refreshing...")
        self.load_all_data()
        QTimer.singleShot(1200, lambda: self.refresh_btn.setEnabled(True))
        QTimer.singleShot(1200, lambda: self.refresh_btn.setText("🔄 Refresh"))
    
    def auto_refresh(self):
        self.load_all_data()
