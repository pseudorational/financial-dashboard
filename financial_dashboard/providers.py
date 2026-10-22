"""Replaceable providers. Fixtures never pretend to be real issuer data."""
from datetime import date, timedelta
from pathlib import Path
from typing import Protocol
import copy
import json
import math
import re
import uuid
from .models import Instrument, Period, Observation, AnnualSnapshot, utcnow, number

FIELDS = {
    "total_revenue": ("TotalRevenue", "Total Revenue"),
    "cost_of_revenue": ("CostOfRevenue", "Cost Of Revenue"),
    "net_income": ("NetIncome", "Net Income"),
    "cash_and_cash_equivalents": ("CashAndCashEquivalents", "Cash And Cash Equivalents"),
    "short_term_investments": ("OtherShortTermInvestments", "Other Short Term Investments"),
    "current_receivables_net": ("AccountsReceivable", "Accounts Receivable"),
    "current_assets": ("CurrentAssets", "Current Assets"),
    "current_liabilities": ("CurrentLiabilities", "Current Liabilities"),
    "stockholders_equity": ("StockholdersEquity", "Stockholders Equity"),
    "total_assets": ("TotalAssets", "Total Assets"),
    "current_interest_bearing_debt": ("CurrentDebt", "Current Debt"),
    "long_term_interest_bearing_debt": ("LongTermDebt", "Long Term Debt"),
    "current_finance_lease_liabilities": ("CurrentCapitalLeaseObligation", "Current Capital Lease Obligation"),
    "noncurrent_finance_lease_liabilities": ("LongTermCapitalLeaseObligation", "Long Term Capital Lease Obligation"),
}
INCOME_FIELDS = {"total_revenue", "cost_of_revenue", "net_income"}
DEMO_SYMBOLS = {
    "DEMO-A": "Example Manufacturing",
    "DEMO-B": "Northstar Systems",
    "DEMO-PARTIAL": "Partial-statement scenario",
    "DEMO-BANK": "Synthetic bank scenario",
    "DEMO-OPENING": "Missing opening balance scenario",
    "DEMO-TWO": "Two-year history scenario",
    "DEMO-LOSS": "Loss transition scenario",
    "DEMO-ETF": "Unsupported instrument scenario",
    "DEMO-OUTAGE": "Provider outage scenario",
    "DEMO-NOQUOTE": "Unavailable quote scenario",
}

class ProviderError(Exception):
    def __init__(self, category, message, retry_after=None):
        super().__init__(message)
        self.category, self.public_message, self.retry_after = category, message, retry_after

def validate_symbol(symbol):
    symbol = symbol.strip().upper()
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9.^=\-]{0,31}", symbol):
        raise ProviderError("validation", "Enter a symbol of 1–32 letters, numbers, or . ^ = - punctuation.")
    return symbol

class FinancialDataProvider(Protocol):
    provider_id: str
    def resolve_instrument(self, symbol): ...
    def get_quote(self, instrument): ...
    def get_price_history(self, instrument, range_key): ...
    def get_annual_financials(self, instrument, minimum_periods=4): ...

def make_observation(inst, provider, field, raw_key, raw, p, snap, retrieved, scale=1, classification="Synthetic", status="ok", reason=""):
    value = number(raw)
    return Observation(inst.symbol, provider, field, raw_key, raw,
                       value * scale if value is not None else None, p.end, p.currency,
                       snap, retrieved, status if value is not None else "missing_input",
                       reason if value is not None else f"{field.replace('_', ' ')} unavailable",
                       source_unit=f"{scale:g} {p.currency}", classification=classification,
                       statement_type="income" if field in INCOME_FIELDS else "balance")

class FixtureProvider:
    provider_id = "fixture-v1"

    def resolve_instrument(self, symbol):
        if symbol not in DEMO_SYMBOLS:
            raise ProviderError("unknown", "Symbol not available in synthetic demo. Try DEMO-A or DEMO-B; real symbols require controlled prototype mode.")
        if symbol == "DEMO-OUTAGE":
            raise ProviderError("outage", "Synthetic provider outage. Try another demo symbol or refresh later.")
        return Instrument(symbol, symbol, DEMO_SYMBOLS[symbol],
                          instrument_type="ETF" if symbol == "DEMO-ETF" else "EQUITY",
                          sector="Banks" if symbol == "DEMO-BANK" else "Technology" if symbol == "DEMO-B" else "Industrials")

    def get_quote(self, i):
        if i.symbol == "DEMO-NOQUOTE":
            raise ProviderError("missing", "Quote unavailable in this scenario; annual financials remain available.")
        b = i.symbol == "DEMO-B"
        return {"price": 86.40 if b else 48.72, "previous_close": 85.10 if b else 48.15,
                "timestamp": "2025-03-31 16:00 America/New_York", "currency": i.quote_currency,
                "market_cap": 8_640_000_000 if b else 2_436_000_000, "market_cap_date": "2025-03-31", "market_cap_currency":"USD",
                "volume": 2_140_600 if b else 846_230, "basis": "Unadjusted daily close",
                "previous_basis": "Unadjusted daily close", "previous_currency": i.quote_currency,
                "delay": "Synthetic; historical scenario", "incomplete": False,
                "classification": "Synthetic", "label": "Latest daily close"}

    def get_price_history(self, i, range_key):
        days = {"1M": 31, "6M": 183, "1Y": 366, "5Y": 1827}[range_key]
        end = date(2025, 3, 31)
        rows = []
        b = i.symbol == "DEMO-B"
        for n in range(days, -1, -1):
            d = end - timedelta(days=n)
            if d.weekday() >= 5:
                continue
            t = (1827 - n) / 1827
            v = (21 + 24*t + 2*math.sin(n*.065) + 1.4*math.sin(n*.17)) * (1.78 if b else 1)
            rows.append({"date": d.isoformat(), "close": round(v, 4), "volume": int(700000 + 150000*math.sin(n*.15))})
        if rows:
            rows[-1]["close"] = 86.40 if b else 48.72
        return {"rows": rows, "currency": i.quote_currency, "basis": "Adjusted daily close",
                "adjustments": "Invented daily series, representing dividend/split-adjusted prices; not a total-return index.",
                "timezone": i.timezone, "incomplete_convention": "Completed synthetic weekday bars only; synthetic calendar is not an exchange calendar."}

    def get_annual_financials(self, i, minimum_periods=4):
        if i.instrument_type != "EQUITY":
            raise ProviderError("unsupported", "Unsupported instrument: annual company statements are not available for this fund.")
        raw = json.loads((Path(__file__).parent.parent / "fixtures/demo_a.json").read_text())
        raw = copy.deepcopy(raw)
        if i.symbol == "DEMO-B":
            for idx, row in enumerate(raw["periods"]):
                for k in row["values"]:
                    row["values"][k] *= 2.2 if k not in ("net_income", "cost_of_revenue") else 3.0 if k == "net_income" else 1.8
        if i.symbol in ("DEMO-OPENING", "DEMO-TWO"):
            raw["periods"] = raw["periods"][1 if i.symbol == "DEMO-OPENING" else 2:]
        if i.symbol == "DEMO-PARTIAL":
            raw["periods"][-1]["values"] = {k:v for k,v in raw["periods"][-1]["values"].items() if k in INCOME_FIELDS}
        if i.symbol == "DEMO-LOSS":
            raw["periods"][-2]["values"]["net_income"] = -40
        snap, retrieved = str(uuid.uuid4()), utcnow()
        periods, observations = [], {}
        for row in raw["periods"]:
            p = Period(row["end"], row["start"], row["label"], currency=raw["currency"])
            periods.append(p)
            observations[p.end] = {k: make_observation(i, self.provider_id, k, k, v, p, snap, retrieved, raw["source_scale"]) for k,v in row["values"].items()}
        return AnnualSnapshot(i, self.provider_id, periods, observations, snap, retrieved, raw["as_of"],
            notes=["Synthetic fixture as of 2025-04-01. Fixture dates are deliberately frozen; retrieval time is separate.",
                   "Net income and equity both use parent-stockholder scope. Finance leases explicitly zero.",
                   "Latest snapshot only; not a point-in-time backtesting dataset. Publication times unknown."])

def normalize_yahoo_annual(i, payload):
    snap, retrieved = str(uuid.uuid4()), utcnow()
    periods, observations = [], {}
    # The endpoint is explicitly annual. It does not supply starts or publication metadata.
    ends = sorted(set(payload.get("income", {})) | set(payload.get("balance", {})))
    for end in ends:
        p = Period(end, None, f"FY ended {end}", currency=i.reporting_currency,
                   notes="Provider annual classification; start, duration, continuity, and publication date unknown")
        periods.append(p)
        values = {}
        for key, aliases in FIELDS.items():
            raw = payload.get("income" if key in INCOME_FIELDS else "balance", {}).get(end, {})
            found = [(a, number(raw[a])) for a in aliases if a in raw and number(raw[a]) is not None]
            if found:
                conflict = len({v for _,v in found}) > 1
                a,v = found[0]
                o = make_observation(i, "yahoo-prototype-v1", key, a, v, p, snap, retrieved,
                                     classification="Reported via provider", status="mapping_unresolved" if conflict else "ok",
                                     reason="Conflicting source aliases" if conflict else "")
                o.source_reference = "Yahoo annual statement via yfinance; not independently verified against filing"
                values[key] = o
        observations[end] = values
    return AnnualSnapshot(i, "yahoo-prototype-v1", periods, observations, snap, retrieved, date.today().isoformat(),
        debt_policy="unresolved", quick_scope_verified=False, cost_scope_verified=False,
        notes=["Conservative prototype: debt composition, quick-asset liquidity, and cost conventions are unverified; affected ratios suppressed.",
               "Fiscal starts/durations and net-income attribution unverified. Average-balance ratios and growth are suppressed.",
               "No revision history or publication timestamps supplied. No redistribution rights established."])

class YahooPrototypeProvider:
    provider_id = "yahoo-prototype-v1"

    def _call(self, endpoint, symbol, range_key="1Y"):
        # A killable process bounds endpoints whose library API has no enforceable timeout.
        import subprocess, sys
        from threading import BoundedSemaphore
        if not _YAHOO_SLOTS.acquire(timeout=.1):
            raise ProviderError("rate_limit", "Prototype provider is busy; retry later.")
        try:
            try:
                proc = subprocess.run([sys.executable, "-m", "financial_dashboard.yahoo_worker", endpoint, symbol, range_key],
                                      capture_output=True, text=True, timeout=9, cwd=Path(__file__).resolve().parent.parent)
            except subprocess.TimeoutExpired:
                raise ProviderError("timeout", "Provider request timed out.") from None
            if proc.returncode:
                raise ProviderError("outage", "Provider request failed. No fallback data was substituted.")
            data = json.loads(proc.stdout)
            if "error" in data:
                raise ProviderError(data["error"], data["message"])
            return data
        finally:
            _YAHOO_SLOTS.release()

    def resolve_instrument(self, symbol):
        # Explicit class-share rule; exchange suffixes are preserved.
        resolved = {"BRK.B": "BRK-B", "BF.B": "BF-B"}.get(symbol, symbol)
        raw = self._call("resolve", resolved)
        return Instrument(resolved, symbol, raw["name"], raw["exchange"], raw["type"], raw["sector"],
                          raw["currency"], raw["financial_currency"], raw["timezone"],
                          f"{symbol} → {resolved}" if symbol != resolved else "None")

    def get_quote(self, i):
        return self._call("quote", i.symbol)

    def get_price_history(self, i, range_key):
        return self._call("history", i.symbol, range_key)

    def get_annual_financials(self, i, minimum_periods=4):
        if i.instrument_type != "EQUITY":
            raise ProviderError("unsupported", "Unsupported instrument: common equity statements required.")
        return normalize_yahoo_annual(i, self._call("annual", i.symbol))

from threading import BoundedSemaphore
_YAHOO_SLOTS = BoundedSemaphore(4)
