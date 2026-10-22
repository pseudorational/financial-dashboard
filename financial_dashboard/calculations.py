"""Pure arithmetic over canonical observations; no Streamlit or provider imports."""
from datetime import date, timedelta
from .models import AnnualSnapshot, Result

METRICS = {
    "current_ratio": ("Current ratio", "x", "Current assets / current liabilities"),
    "quick_ratio": ("Quick ratio", "x", "(Cash + eligible short-term investments + net current receivables) / current liabilities"),
    "net_margin": ("Net profit margin", "%", "Net income / total revenue"),
    "gross_margin": ("Gross profit margin", "%", "(Revenue − cost of revenue) / revenue"),
    "roe": ("Return on equity", "%", "Net income / average of adjacent opening and closing stockholders’ equity"),
    "roa": ("Return on assets", "%", "Net income / average of adjacent opening and closing assets"),
    "debt_equity": ("Debt-to-equity", "x", "Interest-bearing debt including qualifying finance leases, once / closing equity"),
    "asset_turnover": ("Asset turnover", "x", "Revenue / average of adjacent opening and closing assets"),
    "revenue_yoy": ("Revenue YoY growth", "%", "(Revenue − comparable prior revenue) / positive prior revenue"),
    "income_yoy": ("Net income YoY growth", "%", "(Net income − comparable prior net income) / positive prior net income"),
}

def eligible_periods(s: AnnualSnapshot):
    import re
    def revision_key(value):
        return tuple((0,int(v)) if v.isdigit() else (1,v) for v in re.split(r"(\d+)",value))
    latest = {}
    for p in s.periods:
        if (p.kind != "annual" or not p.reported or not p.completed or p.estimated
                or p.end > s.as_of or not any(o.normalized_value is not None for o in s.observations.get(p.end, {}).values())):
            continue
        if p.end not in latest or revision_key(p.revision) > revision_key(latest[p.end].revision):
            latest[p.end] = p
    return sorted(latest.values(), key=lambda p: p.end, reverse=True)

def selected_periods(s):
    return eligible_periods(s)[:3]

def previous_period(s, p):
    if p.start is None:
        return None
    opening_end = (date.fromisoformat(p.start) - timedelta(days=1)).isoformat()
    return next((q for q in eligible_periods(s) if q.end == opening_end), None)

def comparable(p, q):
    if not p or not q or p.start is None or q.start is None:
        return False
    if p.currency != q.currency or p.scope != q.scope or p.transition or q.transition:
        return False
    days = lambda x: (date.fromisoformat(x.end) - date.fromisoformat(x.start)).days + 1
    return 350 <= days(p) <= 380 and 350 <= days(q) <= 380 and abs(days(p) - days(q)) <= 8

def calculate(s, p, key):
    unit = METRICS[key][1]
    inputs = []
    def result(value=None, status="ok", reason="", note=""):
        return Result(key, value, unit, status, reason, [o.id for o in inputs],
                      sorted(set(o.period_end for o in inputs)), note=note)
    inst = s.instrument
    if inst.instrument_type != "EQUITY":
        return result(status="not_applicable", reason="Unsupported instrument")
    if inst.sector in ("Banks", "Insurance", "Financial Services") and key not in ("revenue_yoy", "income_yoy"):
        return result(status="not_applicable", reason="Financial-institution methodology not enabled")
    if inst.sector == "Unknown" and key not in ("revenue_yoy", "income_yoy"):
        return result(status="not_applicable", reason="Sector classification unknown; applicability unverified")
    if p.currency in ("Unknown", "", None):
        return result(status="incomparable_periods", reason="Reporting currency unknown")

    def get(field, period=p):
        o = s.obs(period.end, field)
        if o:
            inputs.append(o)
        if o and o.status != "ok":
            raise ValueError((o.status, o.reason_code))
        if not o or o.normalized_value is None:
            raise ValueError(("missing_input", f"{field.replace('_', ' ').capitalize()} unavailable"))
        if o.currency != p.currency or o.normalized_unit != "base currency" or o.scope != p.scope:
            raise ValueError(("incomparable_periods", "Currency, scale, or consolidation scope mismatch"))
        return o.normalized_value

    def positive(n, reason, nm=False):
        if n <= 0:
            raise ValueError(("not_meaningful" if nm else "invalid_denominator", reason))
        return n

    def nonnegative(n, name):
        if n < 0:
            raise ValueError(("mapping_unresolved", f"Negative {name}; source definition unresolved"))
        return n

    try:
        if key in ("current_ratio", "quick_ratio"):
            den = positive(get("current_liabilities"), "Current liabilities must be strictly positive")
            if key == "current_ratio":
                num = nonnegative(get("current_assets"), "current assets")
            else:
                if not s.quick_scope_verified:
                    return result(status="mapping_unresolved", reason="Quick-asset liquidity/composition unresolved")
                num = sum(nonnegative(get(k), k) for k in ("cash_and_cash_equivalents", "short_term_investments", "current_receivables_net"))
        elif key in ("net_margin", "gross_margin"):
            den = positive(get("total_revenue"), "Revenue must be strictly positive")
            if key == "net_margin":
                num = get("net_income")
            else:
                if not s.cost_scope_verified:
                    return result(status="mapping_unresolved", reason="Cost sign and scope unverified")
                num = den - get("cost_of_revenue")
        elif key == "debt_equity":
            den = positive(get("stockholders_equity"), "Nonpositive closing equity", True)
            if s.debt_policy not in ("separate_finance_leases", "leases_included"):
                return result(status="mapping_unresolved", reason="Debt definition unresolved")
            fields = ["current_interest_bearing_debt", "long_term_interest_bearing_debt"]
            if s.debt_policy == "separate_finance_leases":
                fields += ["current_finance_lease_liabilities", "noncurrent_finance_lease_liabilities"]
            num = sum(nonnegative(get(k), "debt") for k in fields)
        elif key in ("roe", "roa", "asset_turnover"):
            prior = previous_period(s, p)
            if prior is None:
                return result(status="missing_input", reason="Opening balance unavailable; adjacent period not established")
            if not comparable(p, prior):
                return result(status="incomparable_periods", reason="No comparable prior fiscal year; duration, currency, or scope mismatch")
            field = "stockholders_equity" if key == "roe" else "total_assets"
            close, opening = get(field), get(field, prior)
            positive(close, f"Nonpositive closing {field.replace('_', ' ')}", key == "roe")
            positive(opening, f"Nonpositive opening {field.replace('_', ' ')}", key == "roe")
            den = (close + opening) / 2
            num = get("total_revenue" if key == "asset_turnover" else "net_income")
            if key == "asset_turnover":
                nonnegative(num, "revenue")
        else:
            prior = previous_period(s, p)
            if prior is None or not comparable(p, prior):
                return result(status="incomparable_periods", reason="No comparable prior fiscal year")
            field = "total_revenue" if key == "revenue_yoy" else "net_income"
            current, den = get(field), get(field, prior)
            note = ""
            if field == "net_income":
                if den < 0 < current:
                    note = f"Turned profitable; absolute change {current-den:,.2f} {p.currency}"
                elif den > 0 > current:
                    note = f"Turned loss-making; absolute change {current-den:,.2f} {p.currency}"
            if den <= 0:
                return result(status="not_meaningful", reason="Nonpositive growth baseline", note=note)
            return result((current - den) / den, note=note)
        value = num / den
        import math
        if not math.isfinite(value):
            return result(status="not_meaningful", reason="Result outside finite numeric range")
        note = "Very small denominator; interpret extreme result with care" if 0 < abs(den) < 1 else ""
        return result(value, note=note)
    except ValueError as exc:
        status, reason = exc.args[0]
        return result(status=status, reason=reason)

def all_results(s):
    return {p.end: {k: calculate(s, p, k) for k in METRICS} for p in selected_periods(s)}
