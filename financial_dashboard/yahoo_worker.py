"""One isolated request. stdout is machine data; no upstream exception text escapes."""
import json
import sys
from datetime import datetime, timezone

def main():
    import yfinance as yf
    from .models import number
    endpoint, symbol, range_key = sys.argv[1:]
    t = yf.Ticker(symbol)
    if endpoint in ("resolve", "quote"):
        info = t.get_info()
        if not info or not info.get("quoteType"):
            return {"error":"unknown", "message":"Provider returned no instrument metadata; symbol validity is unconfirmed."}
        if endpoint == "resolve":
            sector = info.get("sector", "Unknown")
            industry = info.get("industry", "").lower()
            if "bank" in industry:
                sector = "Banks"
            elif "insurance" in industry:
                sector = "Insurance"
            return {"name":info.get("longName", info.get("shortName", symbol)), "exchange":info.get("exchange", "Unknown"),
                    "type":info["quoteType"], "sector":sector, "currency":info.get("currency", "Unknown"),
                    "financial_currency":info.get("financialCurrency", "Unknown"),
                    "timezone":info.get("exchangeTimezoneName", "Unknown")}
        stamp = info.get("regularMarketTime")
        cap_currency=info.get("currency", "Unknown")
        cap_known=cap_currency not in ("GBp","GBX","ZAc","Unknown")
        return {"price":number(info.get("regularMarketPrice")), "previous_close":number(info.get("regularMarketPreviousClose")),
                "timestamp":datetime.fromtimestamp(stamp, timezone.utc).isoformat() if stamp else "Unknown",
                "currency":info.get("currency", "Unknown"), "previous_currency":info.get("currency", "Unknown"),
                "market_cap":number(info.get("marketCap")) if cap_known else None, "market_cap_date":"Unknown",
                "market_cap_currency":cap_currency if cap_known else "Unknown", "market_cap_note":"" if cap_known else "Aggregate currency unverified for subunit quotation",
                "volume":number(info.get("regularMarketVolume")), "delay":"Delay unknown", "incomplete":True,
                "basis":"Provider regular-market quote", "previous_basis":"Provider regular-market quote",
                "classification":"Provider metric", "label":"Latest available price"}
    if endpoint == "history":
        period={"1M":"1mo","6M":"6mo","1Y":"1y","5Y":"5y"}[range_key]
        df = t.history(period=period, interval="1d", auto_adjust=True, timeout=8, raise_errors=True)
        rows = []
        today = datetime.now(df.index.tz).date() if df.index.tz else datetime.now(timezone.utc).date()
        for index, row in df.iterrows():
            if index.date() >= today:
                continue
            rows.append({"date":index.date().isoformat(), "close":number(row.get("Close")), "volume":number(row.get("Volume"))})
        meta = t.get_history_metadata()
        return {"rows":rows, "currency":meta.get("currency", "Unknown"), "basis":"Adjusted daily close",
                "timezone":str(df.index.tz), "adjustments":"yfinance auto_adjust=True; vendor dividend and split adjustments, not a total-return index.",
                "incomplete_convention":"Today's exchange-local daily bar omitted."}
    if endpoint == "annual":
        def serialize(df):
            return {col.date().isoformat():{str(k):number(v) for k,v in df[col].items()} for col in df.columns}
        return {"income":serialize(t.get_income_stmt(freq="yearly", pretty=False)),
                "balance":serialize(t.get_balance_sheet(freq="yearly", pretty=False))}
    return {"error":"validation", "message":"Unknown endpoint"}

if __name__ == "__main__":
    try:
        data = main()
    except Exception as exc:
        name = type(exc).__name__
        category = "rate_limit" if "RateLimit" in name else "timeout" if "Timeout" in name else "outage"
        data = {"error":category, "message":"Provider request unavailable; retry later."}
    print(json.dumps(data, allow_nan=False))
