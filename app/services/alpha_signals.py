# app/services/alpha_signals.py
import os, time, requests
from typing import Dict, Any, Optional, List, Tuple

def _safe_float(x, default=None):
    try:
        if x is None: return default
        return float(x)
    except Exception:
        return default

# ---------------- Binance Fallback (public, no key) ----------------
class _BinanceFallback:
    BASE = "https://fapi.binance.com"
    DATA = "https://fapi.binance.com/futures/data"

    @staticmethod
    def _sym(symbol: str) -> str:
        s = symbol.upper().replace("/", "")
        if not s.endswith("USDT"):
            s = s + "USDT"
        return s

    def get_funding_rate(self, symbol: str) -> Optional[float]:
        sym = self._sym(symbol)
        url = f"{self.BASE}/fapi/v1/fundingRate"
        try:
            r = requests.get(url, params={"symbol": sym, "limit": 1}, timeout=12)
            if r.status_code == 200:
                arr = r.json()
                if isinstance(arr, list) and arr:
                    return _safe_float(arr[-1].get("fundingRate"))
        except Exception:
            pass
        return None

    def get_open_interest_change(self, symbol: str) -> Dict[str, Optional[float]]:
        sym = self._sym(symbol)
        url = f"{self.DATA}/openInterestHist"
        params = {"symbol": sym, "period": "4h", "limit": 7}
        oi_level = None; oi_chg = None
        try:
            r = requests.get(url, params=params, timeout=12)
            if r.status_code == 200:
                arr = r.json()
                vals = [_safe_float(x.get("sumOpenInterestValue")) for x in arr if _safe_float(x.get("sumOpenInterestValue")) is not None]
                if len(vals) >= 2:
                    oi_level = vals[-1]
                    prev = vals[0]
                    if prev and prev != 0:
                        oi_chg = (oi_level - prev) / prev * 100.0
        except Exception:
            pass
        return {"oi_level": oi_level, "oi_change_24h_pct": oi_chg}

    def get_long_short_ratio(self, symbol: str) -> Dict[str, Optional[float]]:
        sym = self._sym(symbol)
        def fetch(endpoint):
            url = f"{self.DATA}/{endpoint}"
            try:
                r = requests.get(url, params={"symbol": sym, "period": "4h", "limit": 1}, timeout=12)
                if r.status_code == 200:
                    arr = r.json()
                    if isinstance(arr, list) and arr:
                        long_account = _safe_float(arr[-1].get("longAccount"))
                        short_account = _safe_float(arr[-1].get("shortAccount"))
                        long_pos = _safe_float(arr[-1].get("longPosition"))
                        short_pos = _safe_float(arr[-1].get("shortPosition"))
                        ratio = _safe_float(arr[-1].get("longShortRatio"))
                        if ratio is not None:
                            return ratio
                        if long_account and short_account:
                            return long_account / short_account
                        if long_pos and short_pos:
                            return long_pos / short_pos
            except Exception:
                pass
            return None

        return {
            "ls_accounts": fetch("topLongShortAccountRatio"),
            "ls_positions": fetch("topLongShortPositionRatio")
        }

    def get_liquidations_24h(self, symbol: str) -> Dict[str, Optional[float]]:
        sym = self._sym(symbol)
        url = f"{self.DATA}/liquidationOrders"
        params = {"symbol": sym, "limit": 1000}
        long_usd = short_usd = None
        try:
            r = requests.get(url, params=params, timeout=12)
            if r.status_code == 200:
                arr = r.json()
                if isinstance(arr, list):
                    L = S = 0.0
                    from time import time as _now
                    cutoff = _now() * 1000 - 24*60*60*1000
                    for x in arr:
                        t = _safe_float(x.get("time"))
                        if t is not None and t < cutoff:
                            continue
                        side = (x.get("side") or "").upper()  # BUY = long liq, SELL = short liq
                        quote = _safe_float(x.get("quoteQty"))
                        if quote is None:
                            price = _safe_float(x.get("price"), 0.0)
                            qty = _safe_float(x.get("origQty"), 0.0)
                            quote = price * qty
                        if side == "BUY":
                            L += quote or 0.0
                        elif side == "SELL":
                            S += quote or 0.0
                    long_usd = L if L > 0 else None
                    short_usd = S if S > 0 else None
        except Exception:
            pass
        return {"liq_24h_long_usd": long_usd, "liq_24h_short_usd": short_usd}

    # --- SERIES untuk Smart-Money Flow ---
    def get_top_trader_pos_series(self, symbol: str, period: str = "1h", limit: int = 24) -> List[float]:
        sym = self._sym(symbol)
        url = f"{self.DATA}/topLongShortPositionRatio"
        try:
            r = requests.get(url, params={"symbol": sym, "period": period, "limit": limit}, timeout=12)
            if r.status_code == 200:
                arr = r.json()
                out = []
                for x in arr:
                    v = _safe_float(x.get("longShortRatio"))
                    if v is not None:
                        out.append(v)
                return out
        except Exception:
            pass
        return []

# ---------------- CoinGlass Primary (best-effort) ----------------
class _CoinGlassPrimary:
    BASES = [
        "https://open-api-v4.coinglass.com/api",
        "https://open-api.coinglass.com/api/pro/v1"
    ]
    def __init__(self, api_key: str, timeout: int = 15):
        self.api_key = api_key
        self.timeout = timeout

    def _header_candidates(self):
        return [{"CG-API-KEY": self.api_key}, {"coinglassSecret": self.api_key}]

    def _try(self, paths: List[str], params: Dict[str, Any]):
        for base in self.BASES:
            for hdr in self._header_candidates():
                for p in paths:
                    url = f"{base}{p}"
                    try:
                        r = requests.get(url, headers=hdr, params=params, timeout=self.timeout)
                        if r.status_code != 200:
                            continue
                        j = r.json()
                        if isinstance(j, dict) and str(j.get("code", "0")) == "0":
                            return j.get("data")
                        if "data" in j:
                            return j["data"]
                        return j
                    except Exception:
                        continue
        return None

    @staticmethod
    def _base(symbol: str) -> str:
        s = symbol.upper()
        if "/" in s: s = s.split("/")[0]
        for suf in ("USDT","USDC","USD","PERP"):
            if s.endswith(suf) and len(s) > len(suf):
                s = s[:-len(suf)]
        return s

    def get_funding_rate(self, symbol: str) -> Optional[float]:
        base = self._base(symbol)
        paths = ["/futures/funding-rates", "/futures/funding_rates"]
        for params in [{"symbol": base}, {"currency": base}, {"symbol": base, "period":"8h","limit":1}]:
            d = self._try(paths, params)
            if not d: continue
            if isinstance(d, list) and d:
                vals = [_safe_float(x.get("fundingRate", x.get("funding_rate"))) for x in d if _safe_float(x.get("fundingRate", x.get("funding_rate"))) is not None]
                if vals: return sum(vals)/len(vals)
            if isinstance(d, dict):
                return _safe_float(d.get("fundingRate", d.get("funding_rate")))
        return None

    def get_open_interest_change(self, symbol: str) -> Dict[str, Optional[float]]:
        base = self._base(symbol)
        paths = ["/futures/open-interest/aggregated-history", "/futures/open_interest/history"]
        d = self._try(paths, {"symbol": base, "period":"4h", "limit":7}) or self._try(paths, {"currency": base, "period":"4h", "limit":7})
        level = change = None
        if isinstance(d, list) and len(d)>=2:
            vals = [_safe_float(x.get("valueUsd", x.get("openInterestUsd", x.get("sumOpenInterestUsd")))) for x in d]
            vals = [v for v in vals if v is not None]
            if len(vals)>=2:
                level = vals[-1]; prev = vals[0]
                if prev: change = (level - prev)/prev*100.0
        return {"oi_level": level, "oi_change_24h_pct": change}

    def get_long_short_ratio(self, symbol: str) -> Dict[str, Optional[float]]:
        base = self._base(symbol)
        def last_ratio(paths):
            d = self._try(paths, {"symbol": base, "period":"4h","limit":1}) or self._try(paths, {"currency": base, "period":"4h","limit":1})
            if isinstance(d, list) and d:
                x = d[-1]
                r = _safe_float(x.get("ratio"))
                if r is not None: return r
                lo = _safe_float(x.get("long")); sh = _safe_float(x.get("short"))
                if lo and sh: return lo/sh
            return None
        return {
            "ls_accounts": last_ratio(["/futures/long-short-account-ratio","/futures/long_short_account_ratio"]),
            "ls_positions": last_ratio(["/futures/long-short-position-ratio","/futures/long_short_position_ratio"])
        }

    def get_liquidations_24h(self, symbol: str) -> Dict[str, Optional[float]]:
        base = self._base(symbol)
        d = self._try(
            ["/futures/liquidation/history","/futures/liquidations/history"],
            {"symbol": base, "period":"1h", "limit":30}
        ) or self._try(
            ["/futures/liquidation/history","/futures/liquidations/history"],
            {"currency": base, "period":"1h", "limit":30}
        )
        L=S=None
        if isinstance(d, list) and d:
            l=s=0.0
            for x in d[-24:]:
                l+= _safe_float(x.get("longUsd", x.get("long", x.get("longVolUsd"))),0)
                s+= _safe_float(x.get("shortUsd", x.get("short", x.get("shortVolUsd"))),0)
            L = l if l>0 else None; S = s if s>0 else None
        return {"liq_24h_long_usd": L, "liq_24h_short_usd": S}

# ---------------- Aggregator & Scoring ----------------
class AlphaSignalsService:
    """
    CoinGlass (pakai API key) -> fallback Binance Futures (public).
    Termasuk Smart-Money Flow (inflow/outflow).
    """
    def __init__(self, api_key: Optional[str] = None, timeout: int = 15, cache_ttl: int = 60):
        self.api_key = api_key or os.getenv("COINGLASS_API_KEY") or "c6a9dfe74c8b4764969945d4de5e73e4"
        self.cg = _CoinGlassPrimary(self.api_key, timeout=timeout)
        self.bn = _BinanceFallback()
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._ttl = cache_ttl

    def _get(self, k): 
        v = self._cache.get(k)
        return v[0] if v and (time.time()-v[1])<self._ttl else None
    def _set(self,k,d): self._cache[k]=(d,time.time())

    @staticmethod
    def _normalize_pct(x: Optional[float], clamp=30.0) -> float:
        if x is None: return 50.0
        x = max(-clamp, min(clamp, x))
        return 50.0 + (x / clamp) * 50.0

    @staticmethod
    def _ratio_to_score(r: Optional[float]) -> float:
        if r is None or r <= 0: return 50.0
        r = max(0.2, min(5.0, r))
        if r >= 1.0:
            return 50.0 + min(50.0, (r - 1.0) / 4.0 * 50.0)
        return 50.0 - min(50.0, (1.0 - r) / 0.8 * 50.0)

    @staticmethod
    def _bias_from_funding(rate: Optional[float]) -> str:
        if rate is None: return "neutral"
        if rate > 0.01:   return "bullish_crowded"
        if rate > 0.0:    return "slightly_bullish"
        if rate < -0.005: return "bearish_crowded"
        if rate < 0.0:    return "slightly_bearish"
        return "neutral"

    # -------- smart money flow (in/out) ----------
    def _smart_money_flow(self, oi_change_pct: Optional[float], ls_pos_series: List[float], funding_rate: Optional[float], liq_long: Optional[float], liq_short: Optional[float]) -> Dict[str, Any]:
        # long share dari ratio => share = r/(1+r)
        long_share_now = None
        long_share_prev = None
        if ls_pos_series:
            r_now = ls_pos_series[-1]
            long_share_now = r_now/(1.0+r_now) if r_now is not None and r_now>0 else None
            if len(ls_pos_series) >= 2:
                r_prev = ls_pos_series[0]
                long_share_prev = r_prev/(1.0+r_prev) if r_prev is not None and r_prev>0 else None

        delta_share_pp = None
        if long_share_now is not None and long_share_prev is not None:
            delta_share_pp = (long_share_now - long_share_prev) * 100.0  # persen poin 24h

        # normalisasi
        norm_oi = (self._normalize_pct(oi_change_pct, clamp=40.0) - 50.0)  # [-50..50]
        if delta_share_pp is None:
            norm_share = 0.0
        else:
            cl = 20.0
            v = max(-cl, min(cl, delta_share_pp))
            norm_share = (v/cl)*50.0  # [-50..50]

        # funding kontra-crowd kecil
        fbias = self._bias_from_funding(funding_rate)
        fudge = 0.0
        if fbias == "bearish_crowded": fudge += 5.0
        if fbias == "bullish_crowded": fudge -= 5.0

        # imbalance likuidasi
        liq_adj = 0.0
        if (liq_long or 0) > 0 or (liq_short or 0) > 0:
            if (liq_short or 0) > (liq_long or 0) * 1.3:
                liq_adj += 5.0
            elif (liq_long or 0) > (liq_short or 0) * 1.3:
                liq_adj -= 5.0

        flow_val = 0.6*norm_oi + 0.4*norm_share + fudge + liq_adj   # [-100..100 kira2]
        flow_score = int(round(50.0 + flow_val))
        flow_score = max(0, min(100, flow_score))
        label = "INFLOW" if flow_score >= 60 else "OUTFLOW" if flow_score <= 40 else "NEUTRAL"

        reasons = []
        if oi_change_pct is not None:
            reasons.append(f"Open Interest {oi_change_pct:+.2f}%/24h")
        if delta_share_pp is not None:
            arrow = "↑" if delta_share_pp>=0 else "↓"
            reasons.append(f"Top Trader Long Share {arrow}{abs(delta_share_pp):.1f} pp/24h")
        reasons.append(f"Funding: {fbias.replace('_',' ')}")
        if (liq_long or 0) > 0 or (liq_short or 0) > 0:
            if (liq_short or 0) > (liq_long or 0) * 1.3:
                reasons.append("Likuidasi short dominan (relief atas)")
            elif (liq_long or 0) > (liq_short or 0) * 1.3:
                reasons.append("Likuidasi long dominan (tekanan turun)")
            else:
                reasons.append("Likuidasi relatif seimbang")

        return {
            "score": flow_score,
            "label": label,
            "delta_long_share_pp": delta_share_pp,
            "components": {
                "oi_norm": norm_oi,
                "share_norm": norm_share,
                "funding_bias": fbias,
                "liq_adj": liq_adj
            },
            "reasons": reasons
        }

    # -------- composite alpha ----------
    def _compose_alpha(self, m: Dict[str, Optional[float]]):
        reasons: List[str] = []
        oi_score = self._normalize_pct(m.get("oi_change_24h_pct"), clamp=40.0)
        if m.get("oi_change_24h_pct") is not None:
            reasons.append("Open Interest naik → leverage bertambah (potensi move besar)" if m["oi_change_24h_pct"]>0 else "Open Interest turun → deleverage")

        fr = m.get("funding_rate_8h")
        bias = self._bias_from_funding(fr)
        if bias == "bullish_crowded": fund_score=40.0; reasons.append("Funding sangat positif → longs crowded")
        elif bias == "slightly_bullish": fund_score=58.0; reasons.append("Funding positif → dominasi long")
        elif bias == "slightly_bearish": fund_score=62.0; reasons.append("Funding negatif ringan → kontra crowd")
        elif bias == "bearish_crowded": fund_score=68.0; reasons.append("Funding sangat negatif → shorts crowded (squeeze risk)")
        else: fund_score=50.0; reasons.append("Funding netral")

        ls_score = (self._ratio_to_score(m.get("ls_accounts")) + self._ratio_to_score(m.get("ls_positions"))) / 2.0
        if m.get("ls_accounts") is not None or m.get("ls_positions") is not None:
            reasons.append(f"Long/Short ratio condong ke {'long' if ls_score>=52 else 'short' if ls_score<=48 else 'netral'}")

        long_usd = m.get("liq_24h_long_usd") or 0.0
        short_usd = m.get("liq_24h_short_usd") or 0.0
        liq_score = 50.0
        if long_usd or short_usd:
            if short_usd > long_usd * 1.3: liq_score=58.0; reasons.append("Likuidasi short dominan → potensi relief ke atas")
            elif long_usd > short_usd * 1.3: liq_score=42.0; reasons.append("Likuidasi long dominan → tekanan turun")
            else: reasons.append("Likuidasi relatif seimbang")

        composite = int(round(0.30*oi_score + 0.25*fund_score + 0.25*ls_score + 0.20*liq_score))
        label = "BULLISH" if composite>=60 else "BEARISH" if composite<=40 else "NEUTRAL"
        return composite, label, reasons

    # ---------------- public ----------------
    def get_alpha_for_symbol(self, symbol: str) -> Dict[str, Any]:
        base = symbol.upper()
        if "/" in base: base = base.split("/")[0]
        cache = self._get(f"alpha:{base}")
        if cache is not None: return cache

        # 1) CoinGlass
        funding = self.cg.get_funding_rate(base)
        oi = self.cg.get_open_interest_change(base)
        ls = self.cg.get_long_short_ratio(base)
        liq = self.cg.get_liquidations_24h(base)

        # 2) Fallback ke Binance
        if funding is None: funding = self.bn.get_funding_rate(base)
        if oi.get("oi_level") is None and oi.get("oi_change_24h_pct") is None:
            oi = self.bn.get_open_interest_change(base)
        if ls.get("ls_accounts") is None and ls.get("ls_positions") is None:
            ls = self.bn.get_long_short_ratio(base)
        if liq.get("liq_24h_long_usd") is None and liq.get("liq_24h_short_usd") is None:
            liq = self.bn.get_liquidations_24h(base)

        # 3) Smart-Money Flow (pakai series top trader dari Binance)
        series = self.bn.get_top_trader_pos_series(base, period="1h", limit=24)
        sm = self._smart_money_flow(
            oi_change_pct=oi.get("oi_change_24h_pct"),
            ls_pos_series=series,
            funding_rate=funding,
            liq_long=liq.get("liq_24h_long_usd"),
            liq_short=liq.get("liq_24h_short_usd"),
        )

        metrics = {
            "funding_rate_8h": funding,
            "oi_level": oi.get("oi_level"),
            "oi_change_24h_pct": oi.get("oi_change_24h_pct"),
            "ls_accounts": ls.get("ls_accounts"),
            "ls_positions": ls.get("ls_positions"),
            "liq_24h_long_usd": liq.get("liq_24h_long_usd"),
            "liq_24h_short_usd": liq.get("liq_24h_short_usd"),
        }
        score, label, reasons = self._compose_alpha(metrics)

        out = {
            "symbol": base,
            "metrics": metrics,
            "insights": reasons,
            "score": score,
            "label": label,
            "smart_money": sm
        }
        self._set(f"alpha:{base}", out)
        return out
