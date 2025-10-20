# app/ui/components/sentiment_panel.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QTabWidget, QScrollArea,
                             QFrame, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from ...services.sentiment_analysis import SentimentAnalysisService
from ...services.news_service import NewsService
from ...services.economic_indicators import EconomicIndicatorsService

class SentimentPanel(QWidget):
    """Panel sentiment, news, economic + Alpha Candidates (public predictive signals, non-insider)."""
    
    refresh_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.sentiment_service = SentimentAnalysisService()
        self.news_service = NewsService()
        self.economic_service = EconomicIndicatorsService()

        # Optional service khusus alpha signals (buat sendiri; lihat metode yg dipakai di bawah)
        self.alpha_service = None
        try:
            from ...services.alpha_signals import AlphaSignalsService  # optional
            self.alpha_service = AlphaSignalsService()
        except Exception:
            self.alpha_service = None
        
        self.current_symbol = None
        self._last_coin_news_sentiment = None  # cache ringan
        
        self.init_ui()
        
        # Auto refresh timer (3 menit)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(180000)
    
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

        # Tab 5: Alpha Candidates (publik predictive signals)
        self.alpha_tab = self.create_alpha_radar_tab()
        self.tabs.addTab(self.alpha_tab, "🧭 Alpha Radar")
        
        layout.addWidget(self.tabs)
        
        # Initial load
        self.load_all_data()
        # Isi alpha candidates global biar tidak kosong
        self.populate_alpha_candidates_global()
    
    # ---------- Tabs ----------
    def create_market_overview_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Fear & Greed Index
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
        
        stats_title = QLabel("💰 GLOBAL CRYPTO MARKET")
        stats_title.setFont(QFont("Arial", 12, QFont.Bold))
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
        trending_title.setFont(QFont("Arial", 12, QFont.Bold))
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
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info_label = QLabel("Select a coin from the main chart to see its sentiment analysis")
        info_label.setFont(QFont("Arial", 11))
        info_label.setStyleSheet("color: #888; font-style: italic; padding: 10px;")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        scores_frame = QFrame()
        scores_frame.setStyleSheet("background: #1e1e1e; border: 1px solid #444; border-radius: 5px; padding: 10px;")
        scores_layout = QVBoxLayout(scores_frame)
        
        self.coin_name_label = QLabel("Select a coin...")
        self.coin_name_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.coin_name_label.setAlignment(Qt.AlignCenter)
        scores_layout.addWidget(self.coin_name_label)
        
        self.sentiment_score_label = QLabel("")
        self.sentiment_score_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.sentiment_score_label.setAlignment(Qt.AlignCenter)
        scores_layout.addWidget(self.sentiment_score_label)
        
        layout.addWidget(scores_frame)
        
        self.coin_details_text = QTextEdit()
        self.coin_details_text.setReadOnly(True)
        self.coin_details_text.setStyleSheet("""
            QTextEdit { background: #2d2d2d; color: #fff; border: 1px solid #444; border-radius: 5px; font-family: 'Courier New'; font-size: 10px; padding: 8px; }
        """)
        layout.addWidget(self.coin_details_text)
        
        return widget
    
    def create_news_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        sentiment_frame = QFrame()
        sentiment_frame.setStyleSheet("background: #1e1e1e; border: 1px solid #444; border-radius: 5px; padding: 10px;")
        sentiment_layout = QVBoxLayout(sentiment_frame)
        
        self.news_sentiment_label = QLabel("📊 News Sentiment: Loading...")
        self.news_sentiment_label.setFont(QFont("Arial", 12, QFont.Bold))
        sentiment_layout.addWidget(self.news_sentiment_label)
        
        layout.addWidget(sentiment_frame)
        
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

    def create_alpha_radar_tab(self) -> QWidget:
        """Alpha Radar: menilai kandidat koin via public predictive signals (non-insider)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Composite score (global/per-coin akan di-set oleh populate_*)
        score_box = QFrame()
        score_box.setStyleSheet("background:#1e1e1e;border:1px solid #444;border-radius:5px;padding:10px;")
        sL = QVBoxLayout(score_box)
        title = QLabel("🧭 Composite Sentiment (0–100) — public predictive signals")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        sL.addWidget(title)

        self.comp_score_bar = QProgressBar()
        self.comp_score_bar.setMaximum(100)
        self.comp_score_bar.setStyleSheet("""
            QProgressBar{border:2px solid #444;border-radius:5px;text-align:center;background:#2d2d2d;height:25px;}
            QProgressBar::chunk{background:#00b894;}
        """)
        sL.addWidget(self.comp_score_bar)

        self.comp_score_label = QLabel("—")
        self.comp_score_label.setAlignment(Qt.AlignCenter)
        self.comp_score_label.setStyleSheet("color:#ccc;padding:4px;")
        sL.addWidget(self.comp_score_label)
        layout.addWidget(score_box)

        # Alpha Candidates (Ranked)
        cand_box = QFrame()
        cand_box.setStyleSheet("background:#1e1e1e;border:1px solid #444;border-radius:5px;padding:10px;")
        cL = QVBoxLayout(cand_box)
        t2 = QLabel("🏁 Top Alpha Candidates — Ranked (non-insider)")
        t2.setFont(QFont("Arial", 12, QFont.Bold))
        cL.addWidget(t2)
        self.alpha_candidates_text = QTextEdit()
        self.alpha_candidates_text.setReadOnly(True)
        self.alpha_candidates_text.setStyleSheet("QTextEdit{background:#2d2d2d;color:#fff;border:none;font-family:'Courier New';font-size:11px;padding:8px;}")
        cL.addWidget(self.alpha_candidates_text)
        layout.addWidget(cand_box)

        # Signals Breakdown
        brk_box = QFrame()
        brk_box.setStyleSheet("background:#1e1e1e;border:1px solid #444;border-radius:5px;padding:10px;")
        bL = QVBoxLayout(brk_box)
        t3 = QLabel("🔎 Signals Breakdown (SmartMoney, Listings, On-chain, Derivatives, Social/Dev)")
        t3.setFont(QFont("Arial", 12, QFont.Bold))
        bL.addWidget(t3)
        self.alpha_breakdown_text = QTextEdit()
        self.alpha_breakdown_text.setReadOnly(True)
        self.alpha_breakdown_text.setStyleSheet("QTextEdit{background:#2d2d2d;color:#fff;border:none;font-family:'Courier New';font-size:11px;padding:8px;}")
        bL.addWidget(self.alpha_breakdown_text)
        layout.addWidget(brk_box)

        # Disclaimer
        disclaimer = QLabel("Catatan: Radar ini memakai sumber publik tepercaya (non-insider). BUKAN ajakan membeli / bukan jaminan keuntungan.")
        disclaimer.setStyleSheet("color:#888;font-size:10px;")
        layout.addWidget(disclaimer)

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
""".strip()
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
            
            news_text = f"""Bullish Signals: {sentiment['bullish_signals']} | Bearish Signals: {sentiment['bearish_signals']}
Total News: {sentiment['total_news']}
{'='*60}"""
            for i, news in enumerate(news_list, 1):
                news_text += f"""

[{i}] {news['title']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 {news['source']} | ⏰ {news['time_ago']}
{news['summary']}
🔗 {news['link']}"""
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

    # ---------- Alpha Radar: helpers ----------
    def _safe(self, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            print(f"Alpha helper error: {e}")
            return None

    def _score_components(self, comp):
        """Clamp & sum komponen menjadi total 0–100."""
        def c(x, lo=0, hi=100): 
            try: return max(lo, min(hi, float(x)))
            except: return 0.0
        weights = {'smart': 40, 'listings': 25, 'onchain': 20, 'derivs': 10, 'socialdev': 5}
        total = (
            c(comp.get('smart', 0))/100*weights['smart'] +
            c(comp.get('listings', 0))/100*weights['listings'] +
            c(comp.get('onchain', 0))/100*weights['onchain'] +
            c(comp.get('derivs', 0))/100*weights['derivs'] +
            c(comp.get('socialdev', 0))/100*weights['socialdev']
        )
        return round(total, 1)

    def _rank_candidates(self, raw_candidates):
        """raw_candidates: list of dict {'symbol','name','components':{...},'notes':[],'sources':[]}"""
        ranked = []
        for r in raw_candidates:
            comps = r.get('components', {})
            score = self._score_components(comps)
            r['score'] = score
            ranked.append(r)
        ranked.sort(key=lambda x: x.get('score', 0), reverse=True)
        return ranked

    # ---------- Alpha Radar: Global (default) ----------
    def populate_alpha_candidates_global(self):
        """
        Buat shortlist kandidat GLOBAL dari public predictive signals.
        Menggunakan AlphaSignalsService jika ada; jika tidak, fallback sederhana.
        """
        try:
            candidates = []

            if self.alpha_service:
                # ====== Sinyal utama dari service khusus (disarankan dibuat) ======
                # Harap sediakan metode-metode berikut di AlphaSignalsService (semua optional):
                # - get_upcoming_listings(limit=50) -> [{'symbol','name','exchange','date','confidence(0-100)'}]
                # - get_smart_money_flows(limit=200) -> [{'symbol','side','size_usd','score(0-100)','source'}]
                # - get_onchain_strength(symbols:list) -> {symbol:{'netflows','active_addrs','dev','score(0-100)'}}
                # - get_derivatives_positioning(symbols:list) -> {symbol:{'funding','oi_change','long_short','score(0-100)'}}
                # - get_social_dev_momentum(symbols:list) -> {symbol:{'social','dev','score(0-100)'}}
                listings = self._safe(self.alpha_service.get_upcoming_listings, 50) or []
                smartflows = self._safe(self.alpha_service.get_smart_money_flows, 200) or []
                # Ambil kandidat awal dari listings & smartmoney
                base_syms = set([x.get('symbol','').upper() for x in listings if x.get('symbol')] +
                                [x.get('symbol','').upper() for x in smartflows if x.get('symbol')])

                # Ambil metrik tambahan untuk scoring
                onchain = self._safe(self.alpha_service.get_onchain_strength, list(base_syms)) or {}
                derivs  = self._safe(self.alpha_service.get_derivatives_positioning, list(base_syms)) or {}
                socdev  = self._safe(self.alpha_service.get_social_dev_momentum, list(base_syms)) or {}

                for sym in base_syms:
                    comps = {
                        'smart': max([f.get('score', 0) for f in smartflows if f.get('symbol','').upper()==sym] or [0]),
                        'listings': max([l.get('confidence', 0) for l in listings if l.get('symbol','').upper()==sym] or [0]),
                        'onchain': (onchain.get(sym, {}) or {}).get('score', 0),
                        'derivs':  (derivs.get(sym,  {}) or {}).get('score', 0),
                        'socialdev': (socdev.get(sym, {}) or {}).get('score', 0),
                    }
                    notes = []
                    if comps['listings']>0:
                        exs = [l.get('exchange') for l in listings if l.get('symbol','').upper()==sym and l.get('exchange')]
                        if exs: notes.append(f"Upcoming listing: {', '.join(sorted(set(exs)))}")
                    if comps['smart']>0:
                        notes.append("Smart-money inflow detected")
                    if (onchain.get(sym) or {}).get('netflows') is not None:
                        nf = onchain[sym]['netflows']
                        notes.append(f"Netflows: {nf:+.2f}")
                    name = (onchain.get(sym) or {}).get('name') or sym
                    sources = []
                    for l in listings:
                        if l.get('symbol','').upper()==sym and l.get('exchange'):
                            sources.append(f"Listing:{l.get('exchange')}")
                    for f in smartflows:
                        if f.get('symbol','').upper()==sym and f.get('source'):
                            sources.append(f"Smart:{f.get('source')}")
                    candidates.append({
                        'symbol': sym, 'name': name,
                        'components': comps, 'notes': notes, 'sources': sorted(set(sources))
                    })
            else:
                # ====== Fallback publik sederhana (tetap non-insider) ======
                # Pakai trending + likuiditas + FNG agar tidak kosong
                trending = self._safe(self.sentiment_service.get_trending_coins) or []
                fng = self._safe(self.sentiment_service.get_fear_greed_index) or {'value':50}
                base = trending[:8]
                for c in base:
                    sym = (c.get('symbol') or '').upper()
                    name = c.get('name') or sym
                    rank = float(c.get('rank') or 9999)
                    # proxy scoring kasar
                    comps = {
                        'smart': max(0, 100 - min(rank, 100)),    # rank kecil → proxy institutional interest
                        'listings': 0,
                        'onchain': 50,
                        'derivs': 50,
                        'socialdev': 50,
                    }
                    notes = [f"Trending proxy; rank #{int(rank) if rank!=9999 else '?'}",
                             f"Macro FNG={fng.get('value',50)}"]
                    candidates.append({'symbol': sym, 'name': name, 'components': comps, 'notes': notes, 'sources': ['Public:Trending']})

            ranked = self._rank_candidates(candidates)[:10]

            # Composite global (pakai rata-rata top 5)
            if ranked:
                avg = sum([x['score'] for x in ranked[:5]])/min(5, len(ranked))
                self.comp_score_bar.setValue(int(round(avg)))
                self.comp_score_label.setText(f"Global Composite (Top-5 Avg) — {avg:.1f}/100")
            else:
                self.comp_score_bar.setValue(50)
                self.comp_score_label.setText("Global Composite — 50/100")

            # Render Top Candidates
            txt = "TOP ALPHA CANDIDATES (GLOBAL)\n" + "─"*60 + "\n"
            if ranked:
                for i, r in enumerate(ranked, 1):
                    notes = "; ".join(r.get('notes', [])[:3])
                    srcs  = ", ".join(r.get('sources', [])[:4])
                    txt += f"{i:>2}. {r['symbol']:<8}  {r['score']:>5.1f}  — {r.get('name','')}\n"
                    if notes: txt += f"    • {notes}\n"
                    if srcs:  txt += f"    • Sources: {srcs}\n"
            else:
                txt += "—\n"
            self.alpha_candidates_text.setText(txt)

            # Render Breakdown
            br = "SIGNALS BREAKDOWN\n" + "─"*60 + "\n"
            if ranked:
                for r in ranked[:8]:
                    c = r['components']
                    br += (f"{r['symbol']}:  smart={c.get('smart',0):.0f}  listings={c.get('listings',0):.0f}  "
                           f"onchain={c.get('onchain',0):.0f}  derivs={c.get('derivs',0):.0f}  social/dev={c.get('socialdev',0):.0f}  "
                           f"→ score {r['score']:.1f}\n")
            else:
                br += "—\n"
            self.alpha_breakdown_text.setText(br)

        except Exception as e:
            print(f"populate_alpha_candidates_global error: {e}")
            self.alpha_candidates_text.setText("Alpha Candidates global tidak tersedia saat ini.")
            self.alpha_breakdown_text.setText("—")

    # ---------- Per-coin update + Alpha (still available) ----------
    def update_coin_sentiment(self, symbol: str):
        """Update coin-specific sentiment + refresh Alpha (per-coin composite + global list tetap ada)."""
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
                if 'BULLISH' in classification: color = "#26a69a"
                elif 'BEARISH' in classification: color = "#f23645"
                else: color = "#ffd700"
                self.sentiment_score_label.setStyleSheet(f"color: {color};")
                
                details = f"""
═══════════════════════════════════════════
SENTIMENT ANALYSIS FOR {sentiment['name']}
═══════════════════════════════════════════

Overall Score: {score}/10
Classification: {classification}

Reasons:
""".strip()
                for reason in overall.get('reasons', []):
                    details += f"\n  • {reason}"
                
                details += f"""

\nMARKET DATA
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

                # Per-coin composite (pakai berita spesifik hanya sebagai pelengkap, bukan penentu)
                try:
                    coin_news = self.news_service.get_coin_specific_news(sentiment['name'], limit=6)
                    coin_news_sent = self.news_service.analyze_news_sentiment(coin_news) if coin_news is not None else None
                    self._last_coin_news_sentiment = coin_news_sent
                except Exception:
                    coin_news_sent = None

                # Hitung composite ringkas untuk bar atas (opsional)
                fng = self.sentiment_service.get_fear_greed_index()
                pseudo = {'overall_sentiment': {'score': (score or 0)*10}}  # skala 0-100
                if hasattr(self.sentiment_service, 'compute_composite_score'):
                    comp = self.sentiment_service.compute_composite_score(pseudo, fng, coin_news_sent or {'score':50})
                    self.comp_score_bar.setValue(comp['score'])
                    self.comp_score_label.setText(
                        f"{comp['label']} — {comp['score']}/100  "
                        f"(coin:{comp['components']['coin']:.0f}, news:{comp['components']['news']:.0f}, invFNG:{comp['components']['fear_greed_inverted']:.0f})"
                    )
                else:
                    self.comp_score_bar.setValue(int((score or 5) * 10))
                    self.comp_score_label.setText(f"Composite ~ {(score or 5)*10:.0f}/100")

                # Tetap update global alpha candidates (list ranking)
                self.populate_alpha_candidates_global()

            else:
                self.coin_name_label.setText(f"{symbol} - Data Not Available")
                self.sentiment_score_label.setText("")
                self.coin_details_text.setText("Unable to fetch sentiment data for this coin.")
                self.populate_alpha_candidates_global()
                
        except Exception as e:
            print(f"Error updating coin sentiment: {e}")
            self.coin_details_text.setText(f"Error: {str(e)}")
            self.populate_alpha_candidates_global()
    
    # ---------- Refresh ----------
    def manual_refresh(self):
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("⏳ Refreshing...")
        self.load_all_data()
        if self.current_symbol:
            self.update_coin_sentiment(self.current_symbol)
        else:
            self.populate_alpha_candidates_global()
        QTimer.singleShot(2000, lambda: self.refresh_btn.setEnabled(True))
        QTimer.singleShot(2000, lambda: self.refresh_btn.setText("🔄 Refresh"))
    
    def auto_refresh(self):
        self.load_all_data()
        if self.current_symbol:
            self.update_coin_sentiment(self.current_symbol)
        else:
            self.populate_alpha_candidates_global()
