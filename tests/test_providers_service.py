from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import time
import pytest
from financial_dashboard.providers import FixtureProvider, ProviderError, validate_symbol, normalize_yahoo_annual
from financial_dashboard.service import DashboardService, EndpointCache
from financial_dashboard.calculations import all_results, selected_periods
from financial_dashboard.models import Instrument

@pytest.mark.parametrize("symbol",["<script>","https://example.com","../x","A;rm","","A"*33])
def test_invalid_symbol(symbol):
    with pytest.raises(ProviderError):
        validate_symbol(symbol)

def test_symbols_suffix_and_whitespace():
    assert validate_symbol(" brk.b ")=="BRK.B"
    assert validate_symbol(" vod.l ")=="VOD.L"

def test_mapping_aliases_conflicts_no_fuzzy_or_cash_substitution():
    i=Instrument("X","X","Synthetic input")
    raw={"income":{"2024-12-31":{"Total Revenue":1e9,"TotalRevenue":2e9,"Cost Of Revenue":-600,"OperatingRevenue":9}},
         "balance":{"2024-12-31":{"CashCashEquivalentsAndShortTermInvestments":500,"TotalLiabilitiesNetMinorityInterest":999,"Current Assets":100}}}
    s=normalize_yahoo_annual(i,raw)
    assert s.obs("2024-12-31","total_revenue").status=="mapping_unresolved"
    assert s.value("2024-12-31","cost_of_revenue")==-600
    assert s.value("2024-12-31","cash_and_cash_equivalents") is None
    assert s.value("2024-12-31","current_interest_bearing_debt") is None
    assert s.value("2024-12-31","current_assets")==100
    assert all_results(s)["2024-12-31"]["gross_margin"].value is None

@pytest.mark.parametrize("symbol,assertion",[
    ("DEMO-PARTIAL",lambda s:len(selected_periods(s))==3 and s.value("2024-12-31","current_assets") is None),
    ("DEMO-TWO",lambda s:len(selected_periods(s))==2),
    ("DEMO-OPENING",lambda s:all_results(s)["2022-12-31"]["roe"].value is None),
    ("DEMO-BANK",lambda s:all_results(s)["2024-12-31"]["current_ratio"].status=="not_applicable"),
])
def test_scenarios(symbol,assertion):
    p=FixtureProvider()
    assert assertion(p.get_annual_financials(p.resolve_instrument(symbol)))

def test_isolation_no_quote_unsupported_and_invalid():
    svc=DashboardService(FixtureProvider())
    a=svc.load("DEMO-A")
    b=svc.load("DEMO-B")
    assert a.instrument.name!=b.instrument.name
    assert a.quote.data["price"]!=b.quote.data["price"]
    assert a.financials.data.value("2024-12-31","total_revenue")!=b.financials.data.value("2024-12-31","total_revenue")
    b.quote.data["price"]=0
    assert svc.load("DEMO-B").quote.data["price"]==86.4
    unknown=svc.load("AAPL")
    assert unknown.instrument is None and unknown.quote.data is None
    noquote=svc.load("DEMO-NOQUOTE")
    assert noquote.quote.data is None and noquote.financials.data
    etf=svc.load("DEMO-ETF")
    assert etf.quote.data and not etf.financials.data

class Clock:
    def __init__(self):self.now=0
    def __call__(self):return self.now
    def sleep(self,n):self.now+=n

def test_ttl_refresh_stale_partition_capacity_and_no_false_success():
    clock=Clock()
    cache=EndpointCache(clock,clock.sleep,capacity=3)
    calls=[]
    def fetch(provider="fixture-v1",symbol="A",force=False):
        return cache.fetch(provider,symbol,"quote","daily",lambda:(calls.append(1) or {"price":1}),clock()+30,force)
    assert fetch().status=="fresh"
    first=fetch()
    assert first.cache_hit
    assert fetch(force=True).status=="fresh"
    assert fetch(force=True).cache_hit
    clock.sleep(16)
    assert fetch(force=True).status=="fresh"
    clock.sleep(61)
    def outage():raise ProviderError("outage","Unavailable")
    with patch("financial_dashboard.service.random.uniform",return_value=0):
        stale=cache.fetch("fixture-v1","A","quote","daily",outage,clock()+30)
    assert stale.status=="stale" and stale.retrieved_at==first.retrieved_at
    fetch("another-provider")
    fetch(symbol="B")
    fetch(symbol="C")
    assert len(cache.entries)<=3 and len(cache.locks)<=3

@pytest.mark.parametrize("category,expected",[("validation",1),("unsupported",1),("entitlement",1),("missing",1),("transient",3),("rate_limit",3),("timeout",3)])
def test_retry_eligible_only_and_bounded(category,expected):
    clock=Clock()
    cache=EndpointCache(clock,clock.sleep)
    calls=[]
    def fail():
        calls.append(1)
        raise ProviderError(category,"Safe error")
    with pytest.raises(ProviderError):
        cache.fetch("fixture-v1","X","quote","x",fail,30)
    assert len(calls)==expected
    assert clock()<30

def test_retry_after_exceeding_deadline_not_slept():
    clock=Clock()
    cache=EndpointCache(clock,clock.sleep)
    def fail():raise ProviderError("rate_limit","Retry later",retry_after=120)
    with pytest.raises(ProviderError):
        cache.fetch("fixture-v1","X","quote","x",fail,30)
    assert clock()==0

def test_single_flight_and_deepcopy_concurrent():
    cache=EndpointCache()
    calls=[]
    def slow():
        calls.append(1)
        time.sleep(.03)
        return {"v":1}
    def run(_):return cache.fetch("fixture-v1","X","quote","x",slow,time.monotonic()+30)
    with ThreadPoolExecutor(max_workers=4) as pool:
        result=list(pool.map(run,range(4)))
    assert len(calls)==1
    result[0].data["v"]=99
    assert all(r.data["v"]==1 for r in result[1:])

def test_total_deadline_returns_available_regions():
    clock=Clock()
    class Slow(FixtureProvider):
        provider_id="yahoo-fake"
        def get_quote(self,i):
            clock.sleep(25)
            return super().get_quote(i)
    d=DashboardService(Slow(),EndpointCache(clock,clock.sleep)).load("DEMO-A")
    assert d.quote.data
    assert not d.history.data and not d.financials.data
    assert "deadline" in d.history.message

def test_yahoo_hard_timeout_and_no_raw_error_leak():
    import subprocess
    from financial_dashboard.providers import YahooPrototypeProvider
    with patch("subprocess.run",side_effect=subprocess.TimeoutExpired("hidden",9)) as run:
        with pytest.raises(ProviderError) as err:
            YahooPrototypeProvider()._call("quote","X")
        assert err.value.category=="timeout"
        assert run.call_args.kwargs["timeout"]==9

def test_shared_budget():
    clock=Clock()
    cache=EndpointCache(clock,clock.sleep)
    for n in range(60):
        cache.fetch("fixture-v1",str(n),"quote","x",lambda:1,30)
    with pytest.raises(ProviderError,match="budget"):
        cache.fetch("fixture-v1","next","quote","x",lambda:1,30)

def test_expired_stale_not_returned():
    clock=Clock()
    cache=EndpointCache(clock,clock.sleep)
    cache.fetch("fixture-v1","X","quote","x",lambda:1,30)
    clock.sleep(90000)
    def fail():raise ProviderError("entitlement","Unavailable")
    with pytest.raises(ProviderError):
        cache.fetch("fixture-v1","X","quote","x",fail,clock()+30)
