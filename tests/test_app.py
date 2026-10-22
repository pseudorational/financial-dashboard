from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from financial_dashboard.calculations import all_results

APP=str(Path(__file__).parent.parent/"app.py")

def start():
    app=AppTest.from_file(APP).run(timeout=30)
    assert not app.exception
    return app

def load(app,symbol):
    app.text_input(key="ticker_input").set_value(symbol)
    app.button[0].click().run(timeout=30)
    assert not app.exception

def test_start_tabs_synthetic_golden_units_and_no_refetch():
    app=start()
    assert [t.label for t in app.tabs]==["Overview","Financials","Valuation","Comparisons"]
    assert any("SYNTHETIC DEMO" in m.value for m in app.markdown)
    d=app.session_state.dashboard
    assert d.instrument.symbol=="DEMO-A"
    assert all_results(d.financials.data)["2024-12-31"]["current_ratio"].value==2.5
    snap=d.financials.data.snapshot_id
    app.selectbox(key="money_units").select("Thousands").run()
    assert not app.exception
    assert app.session_state.dashboard.financials.data.snapshot_id==snap
    assert any("1,500,000.00" in m.value for m in app.markdown)
    assert sum("Planned — not included in this release" in m.value for m in app.markdown)==2

@pytest.mark.parametrize("symbol",["DEMO-B","DEMO-PARTIAL","DEMO-BANK","DEMO-OPENING","DEMO-TWO","DEMO-LOSS","DEMO-ETF","DEMO-NOQUOTE","DEMO-OUTAGE","AAPL","<script>"])
def test_scenarios_and_error_tabs(symbol):
    app=start()
    load(app,symbol)
    assert len(app.tabs)==4
    d=app.session_state.dashboard
    if symbol in ("AAPL","<script>","DEMO-OUTAGE"):
        assert d.instrument is None and d.financials.data is None
    else:
        assert d.instrument.symbol==symbol
    if symbol=="DEMO-B":
        assert d.quote.data["price"]==86.4
        assert not any("Example Manufacturing" in m.value for m in app.markdown)

def test_public_live_fails_closed(monkeypatch):
    monkeypatch.setenv("DASHBOARD_MODE","public_live")
    app=start()
    assert len(app.tabs)==4
    assert any("not configured" in e.value for e in app.error)

def test_prototype_starts_empty_without_network(monkeypatch):
    monkeypatch.setenv("DASHBOARD_MODE","prototype")
    app=start()
    assert app.text_input[0].value==""
    assert app.session_state.dashboard is None
