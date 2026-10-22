"""No network: validate the actual installed adapter entrypoint using fake clients."""
from types import SimpleNamespace
from unittest.mock import Mock, patch
import pandas as pd
import pytest
from financial_dashboard import yahoo_worker
from financial_dashboard.models import Instrument
from financial_dashboard.providers import normalize_yahoo_annual

@pytest.mark.parametrize("requested,period",[("1M","1mo"),("6M","6mo"),("1Y","1y"),("5Y","5y")])
def test_history_explicit_range_adjustment_timeout_and_current_bar_omission(requested,period):
    df=pd.DataFrame({"Close":[10.,12.],"Volume":[100,200]},index=pd.DatetimeIndex(["2025-03-31","2099-01-01"],tz="America/New_York"))
    client=Mock()
    client.history.return_value=df
    client.get_history_metadata.return_value={"currency":"GBp"}
    with patch("yfinance.Ticker",return_value=client),patch("sys.argv",["worker","history","TEST",requested]):
        result=yahoo_worker.main()
    client.history.assert_called_once_with(period=period,interval="1d",auto_adjust=True,timeout=8,raise_errors=True)
    assert result["rows"]==[{"date":"2025-03-31","close":10.,"volume":100.}]
    assert result["currency"]=="GBp"

def test_annual_endpoint_contract_no_quarterly_or_ttm():
    df=pd.DataFrame({pd.Timestamp("2024-09-28"):{"TotalRevenue":1500.}})
    client=Mock()
    client.get_income_stmt.return_value=df
    client.get_balance_sheet.return_value=df
    with patch("yfinance.Ticker",return_value=client),patch("sys.argv",["worker","annual","TEST","1Y"]):
        result=yahoo_worker.main()
    client.get_income_stmt.assert_called_once_with(freq="yearly",pretty=False)
    client.get_balance_sheet.assert_called_once_with(freq="yearly",pretty=False)
    assert result["income"]["2024-09-28"]["TotalRevenue"]==1500.

def test_quote_subunits_do_not_guess_aggregate_currency():
    client=Mock()
    client.get_info.return_value={"quoteType":"EQUITY","currency":"GBp","regularMarketPrice":125,"regularMarketPreviousClose":120,"marketCap":1000000}
    with patch("yfinance.Ticker",return_value=client),patch("sys.argv",["worker","quote","TEST","1Y"]):
        result=yahoo_worker.main()
    assert result["price"]==125 and result["currency"]=="GBp"
    assert result["market_cap"] is None and result["market_cap_currency"]=="Unknown"
    assert result["timestamp"]=="Unknown"

def test_distinct_quote_and_statement_currencies():
    i=Instrument("TEST","TEST","Synthetic cross-currency input",quote_currency="GBp",reporting_currency="USD")
    s=normalize_yahoo_annual(i,{"income":{"2024-09-28":{"TotalRevenue":1000}},"balance":{}})
    assert s.value("2024-09-28","total_revenue")==1000
    assert s.obs("2024-09-28","total_revenue").currency=="USD"
    assert s.instrument.quote_currency=="GBp"
