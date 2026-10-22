"""Run with: streamlit run app.py"""
import os
import time
import streamlit as st
from financial_dashboard.models import Dashboard
from financial_dashboard.providers import FixtureProvider, YahooPrototypeProvider
from financial_dashboard.service import DashboardService, EndpointCache
from financial_dashboard.formatting import UNITS
from financial_dashboard import ui

st.set_page_config(page_title="Financial Dashboard", page_icon="▥", layout="wide",initial_sidebar_state="collapsed")
st.markdown(ui.CSS,unsafe_allow_html=True)
st.markdown('<div class="masthead"><div class="brand"><b>▥</b> Financial Dashboard <span style="color:#667C91;font-size:12px;margin-left:12px">EQUITY RESEARCH</span></div><span class="badge">ANNUAL FUNDAMENTALS / v0.1</span></div>',unsafe_allow_html=True)
mode=os.environ.get("DASHBOARD_MODE","demo")
if mode not in ("demo","prototype"):
    st.error("Public live data is not configured. A licensed provider and rights review are required. Set DASHBOARD_MODE=demo for the synthetic demonstration.")
    tabs=st.tabs(["Overview","Financials","Valuation","Comparisons"])
    for tab in tabs:
        with tab:
            st.info("No provider enabled. Public-live mode fails closed.")
    st.stop()

@st.cache_resource
def services():
    cache=EndpointCache()
    return {"demo":DashboardService(FixtureProvider(),cache),"prototype":DashboardService(YahooPrototypeProvider(),cache)}

service=services()[mode]
if mode=="demo":
    st.markdown('<div class="notice"><strong>SYNTHETIC DEMO</strong> · Invented companies and market data, frozen as of April 1, 2025. No live financial data. Try <strong>DEMO-A</strong> or <strong>DEMO-B</strong>.</div>',unsafe_allow_html=True)
else:
    st.warning("Yahoo prototype · Controlled research only. Redistribution rights have not been established. Do not expose this mode as a public live-data service.")

if "active_mode" not in st.session_state or st.session_state.active_mode != mode:
    st.session_state.active_mode=mode
    st.session_state.dashboard=None
    st.session_state.ticker_input="DEMO-A" if mode=="demo" else ""
    st.session_state.range_loaded="1Y"
    st.session_state.refreshes={}

t,u,h,r=st.columns([3.5,1.7,2.6,1])
with t:
    with st.form("ticker_form",border=False):
        ticker_col,submit_col=st.columns([3,1])
        with ticker_col:
            symbol=st.text_input("Stock symbol",key="ticker_input",placeholder="Enter a ticker",max_chars=32)
        with submit_col:
            st.markdown('<div style="height:28px"></div>',unsafe_allow_html=True)
            submit=st.form_submit_button("Load",width="stretch",type="primary")
with u:
    unit=st.selectbox("Monetary units",list(UNITS),index=2,key="money_units")
with h:
    range_key=st.radio("Price history range",["1M","6M","1Y","5Y"],index=2,horizontal=True,key="price_range")
with r:
    st.markdown('<div style="height:28px"></div>',unsafe_allow_html=True)
    refresh=st.button("↻ Refresh",width="stretch")

initial = st.session_state.dashboard is None and mode=="demo"
old=st.session_state.dashboard
range_changed=old is not None and st.session_state.range_loaded!=range_key
refresh_allowed=True
if refresh and old:
    last=st.session_state.refreshes.get(old.requested_symbol,-1000)
    if time.monotonic()-last<15:
        st.info("Refresh cooldown: wait 15 seconds between refreshes for this instrument.")
        refresh_allowed=False
    else:
        st.session_state.refreshes[old.requested_symbol]=time.monotonic()

if submit or initial or (refresh and refresh_allowed and old) or range_changed:
    requested=symbol if submit or initial else old.requested_symbol
    # Old values are removed before the new request starts. Streamlit serializes a session's script runs.
    st.session_state.dashboard=Dashboard(requested)
    with st.spinner(f"Loading {requested or 'symbol'}…"):
        st.session_state.dashboard=service.load(requested,range_key,force=refresh and refresh_allowed)
    st.session_state.range_loaded=range_key

d=st.session_state.dashboard or Dashboard("",error="Enter a stock symbol and press Load.")
ui.identity(d,mode)
overview,financials,valuation,comparisons=st.tabs(["Overview","Financials","Valuation","Comparisons"])
with overview:
    ui.overview(d,unit)
with financials:
    ui.financials(d,unit)
with valuation:
    ui.planned(d,"Valuation")
with comparisons:
    ui.planned(d,"Comparisons")
ui.methodology(d)
st.caption("Financial Dashboard · Synthetic demonstration / controlled prototype · Financial statement exploration · No investment recommendations")
