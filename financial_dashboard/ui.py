from dataclasses import asdict
from html import escape
import pandas as pd
import streamlit as st
from .calculations import METRICS, selected_periods, all_results, previous_period
from .formatting import UNITS, money, price, result_text, quote_unit, quote_change
from . import charts

REPORTED = {
    "total_revenue":"Total revenue", "cost_of_revenue":"Cost of revenue", "net_income":"Net income",
    "cash_and_cash_equivalents":"Cash and cash equivalents", "current_assets":"Total current assets",
    "current_liabilities":"Total current liabilities", "stockholders_equity":"Total stockholders’ equity",
}
SUPPORT = {
    "short_term_investments":"Short-term investments", "current_receivables_net":"Current net receivables",
    "total_assets":"Total assets", "current_interest_bearing_debt":"Current interest-bearing debt",
    "long_term_interest_bearing_debt":"Noncurrent interest-bearing debt",
    "current_finance_lease_liabilities":"Current finance leases", "noncurrent_finance_lease_liabilities":"Noncurrent finance leases",
}

CSS = """
<style>
.stApp {background:#0B0F14;}
.block-container {max-width:1540px;padding-top:3.8rem;padding-bottom:2rem;}
h1,h2,h3 {letter-spacing:-.025em;} h1 {font-size:2rem!important;} h3 {font-size:1.05rem!important;}
[data-testid="stCaptionContainer"] {color:#98A6B5;font-size:12px;}
.eyebrow {font:600 11px monospace;letter-spacing:.16em;color:#49B8FF;margin:0 0 5px;}
.masthead {display:flex;align-items:center;justify-content:space-between;gap:15px;border-bottom:1px solid #263140;padding-bottom:14px;margin-bottom:12px;}
.brand {font-size:17px;font-weight:650;letter-spacing:-.03em;}.brand b {color:#49B8FF;margin-right:9px;}
.badge {display:inline-block;border:1px solid #2C4251;background:#10212B;color:#8BCDF5;padding:4px 9px;border-radius:4px;font:11px monospace;}
.notice {padding:9px 13px;border:1px solid #314359;border-left:3px solid #49B8FF;background:#101B27;color:#AEC3D8;font-size:12px;margin:8px 0 16px;}
.identity {display:flex;gap:15px;align-items:center;margin:16px 0 9px;}.monogram {background:#172B3C;color:#76C9FF;font:600 20px monospace;border:1px solid #29465F;border-radius:9px;padding:13px;}
.company {font-size:25px;font-weight:650;letter-spacing:-.035em;}.meta {font-size:12px;color:#98A6B5;margin-top:3px;}
.metric-card {height:122px;background:#121923;border:1px solid #253040;border-radius:7px;padding:14px 15px;margin-bottom:8px;}
.metric-label {font-size:12px;color:#98A6B5;}.metric-value {font-size:26px;font-weight:600;letter-spacing:-.035em;font-variant-numeric:tabular-nums;margin:5px 0;white-space:nowrap;}
.metric-note {font-size:11px;color:#98A6B5;}.positive {color:#52D3AC;}.negative {color:#F58B92;}
.section-kicker {font-size:10px;letter-spacing:.15em;color:#74889D;font-weight:600;margin:18px 0 4px;}
.table-scroll {overflow:auto;border:1px solid #253040;border-radius:7px;margin:7px 0 16px;}
table.fin {width:100%;min-width:670px;table-layout:fixed;border-collapse:collapse;font-size:13px;background:#101720;}
table.fin caption {text-align:left;padding:11px 14px;color:#98A6B5;font-size:11px;}
table.fin th {background:#151F2B;color:#A4B4C5;font-size:11px;font-weight:500;padding:11px 14px;white-space:nowrap;text-align:right;border-bottom:1px solid #2B3747;}
table.fin th:first-child {text-align:left;width:245px;}
table.fin td {padding:10px 14px;border-bottom:1px solid #1E2936;text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;}
table.fin td:first-child {text-align:left;color:#C6D2E0;}.fin tr:last-child td {border-bottom:none;}.fin tr:hover td {background:#182331;}
.fin small {color:#72869A;font-size:10px;margin-left:7px;}.fin .emphasis td {font-weight:650;color:#E6EDF3;background:#131F2B;}
.planned {border:1px solid #293647;border-radius:8px;background:#121923;padding:35px;max-width:800px;margin:24px 0;}
.planned h2 {font-size:25px;}.planned p {color:#98A6B5;font-size:14px;line-height:1.7;}
[data-baseweb="tab-list"] {gap:25px;border-bottom:1px solid #253040;overflow-x:auto;}
[data-baseweb="tab"] {font-size:13px;height:45px;white-space:nowrap;}
[data-testid="stMetricValue"] {font-variant-numeric:tabular-nums;}
@media(max-width:650px){.block-container{padding:3.8rem .8rem 1rem;} .company{font-size:20px;}.masthead{align-items:flex-start;flex-wrap:wrap;}.badge{font-size:9px;}.metric-card{height:115px;}.metric-value{font-size:23px;}[data-baseweb="tab-list"]{gap:18px;} .planned{padding:20px;}}
</style>
"""

def card(label, value, note="", tone=""):
    st.markdown(f'<div class="metric-card"><div class="metric-label">{escape(label)}</div><div class="metric-value {escape(tone)}">{escape(value)}</div><div class="metric-note">{escape(note)}</div></div>', unsafe_allow_html=True)

def section(kicker, title):
    st.markdown(f'<div class="section-kicker">{escape(kicker)}</div>',unsafe_allow_html=True)
    st.subheader(title)

def table(s, periods, rows, unit, results=None, caption=""):
    head = "".join(f'<th scope="col">{escape(p.label)}<br><span style="color:#72869A">{escape(p.end)}</span></th>' for p in periods)
    body=[]
    for key,label in rows.items():
        cells=[]
        for p in periods:
            if results is not None:
                r = results[p.end][key]
                text = result_text(r)
                detail = f"Derived · {METRICS[key][2]} · {r.reason or 'Valid inputs'} · {r.note} · {r.formula_version}"
            else:
                o=s.obs(p.end,key)
                text=money(s.value(p.end,key),unit)
                detail = (f"{o.classification} · {o.raw_field_key} · raw {o.raw_value} {o.source_unit} · {o.reason_code or 'Available'}" if o else "Missing input; not reported in this snapshot")
            cells.append(f'<td title="{escape(detail,quote=True)}">{escape(text)}</td>')
        badge="D" if results is not None else "S" if s.provider_id.startswith("fixture") else "R"
        body.append(f'<tr class="{"emphasis" if key in ("total_revenue","net_income") else ""}"><td>{escape(label)} <small>{badge}</small></td>{"".join(cells)}</tr>')
    st.markdown(f'<div class="table-scroll" tabindex="0" aria-label="Scrollable financial table"><table class="fin"><caption>{escape(caption)}</caption><thead><tr><th scope="col">Metric</th>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>',unsafe_allow_html=True)

def plot(fig, key):
    st.plotly_chart(fig, width="stretch", key=key, config={"displaylogo":False,"scrollZoom":False,"modeBarButtonsToRemove":["toImage"]})

def show_region_status(region, name):
    if region.data is None:
        st.warning(f"{name}: {region.message or 'Unavailable'}")
    elif region.status == "stale":
        st.warning(f"{name}: {region.message} Last successful retrieval: {region.retrieved_at}")

def identity(d, mode):
    if not d.instrument:
        st.error(f"{d.requested_symbol or 'No symbol selected'} · {d.error or 'Enter a ticker to begin.'}")
        st.caption(f"Request reference: {d.correlation_id or '—'}")
        return
    i=d.instrument
    s=d.financials.data
    periods=selected_periods(s) if s else []
    st.markdown(f'<div class="identity"><div class="monogram">{escape(i.symbol.removeprefix("DEMO-")[:2])}</div><div><div class="eyebrow">{escape(i.symbol)} / {escape(i.exchange)}</div><div class="company">{escape(i.name)}</div><div class="meta">{escape(i.sector)} · {escape(i.instrument_type)} · Quote {escape(quote_unit(i.quote_currency))} · Statements {escape(i.reporting_currency)}</div></div></div>',unsafe_allow_html=True)
    if i.transformation != "None":
        st.caption(f"Symbol transformation: {i.transformation}")
    q=d.quote.data or {}
    st.caption(f"Quote/bar: {q.get('timestamp','Unknown')}  ·  Newest fiscal end: {periods[0].end if periods else 'Unavailable'}  ·  {q.get('delay','Delay unknown')}")
    retrieved = max((r.retrieved_at for r in (d.quote,d.history,d.financials) if r.retrieved_at), default="Unknown")
    st.caption(f"Provider: {'Project-owned synthetic fixtures' if mode=='demo' else 'Yahoo / yfinance prototype'}  ·  Last successful retrieval: {retrieved}  ·  " + " / ".join(f"{label} {r.status}" for label,r in [("Quote",d.quote),("History",d.history),("Annual",d.financials)]))

def overview(d, unit):
    if not d.instrument:
        st.info("Load a supported symbol to see price history and financial context.")
        return
    q=d.quote.data or {}
    s=d.financials.data
    periods=selected_periods(s) if s else []
    latest=periods[0] if periods else None
    currency=quote_unit(q.get("currency",d.instrument.quote_currency))
    change, reason=quote_change(q)
    cols=st.columns(4)
    with cols[0]:
        card(q.get("label","Latest available price"),f"{price(q.get('price'))} {currency}",q.get("timestamp","Unknown quote time"))
    with cols[1]:
        card("Change vs previous close",f"{change[0]:+.2f} / {change[1]*100:+.2f}%" if change else "—","Derived · "+reason,"positive" if change and change[0]>=0 else "negative" if change else "")
    with cols[2]:
        # Market capitalization is a monetary aggregate in ISO currency, not quote subunits.
        cap_currency=q.get("market_cap_currency","Unknown")
        card("Market capitalization",money(q.get("market_cap"),unit),q.get("market_cap_note") or f"{cap_currency} {unit.lower()} · provider date {q.get('market_cap_date','Unknown')}")
    with cols[3]:
        vol=q.get("volume")
        card("Trading volume",f"{vol:,.0f}" if vol is not None else "—",f"Shares · {'session may be incomplete' if q.get('incomplete') else 'completed daily session'}")
    show_region_status(d.quote,"Market data")
    left,right=st.columns([3,1])
    with left:
        section("MARKET HISTORY", "Adjusted daily close")
        if d.history.data and d.history.data["rows"]:
            plot(charts.prices(d.history.data,d.instrument.symbol),"price_history")
            st.caption(f"{d.history.data['adjustments']} {d.history.data['incomplete_convention']}")
            with st.expander("Price data · tabular equivalent"):
                st.dataframe(pd.DataFrame(d.history.data["rows"]),hide_index=True,width="stretch")
        else:
            show_region_status(d.history,"Price history")
            if d.history.data:
                st.info("No daily bars in this selected range.")
    with right:
        section("ANNUAL SNAPSHOT",latest.label if latest else "Financial context")
        card("Total revenue",money(s.value(latest.end,"total_revenue") if latest else None,unit),f"{d.instrument.reporting_currency} {unit.lower()} · annual")
        card("Net income",money(s.value(latest.end,"net_income") if latest else None,unit),f"{d.instrument.reporting_currency} {unit.lower()} · annual")
        if latest:
            results=all_results(s)[latest.end]
            card("Net profit margin",result_text(results["net_margin"]),"Derived from annual statements")
    show_region_status(d.financials,"Annual statements")
    if d.history.status == "stale":
        show_region_status(d.history,"Price history")

def financials(d, unit):
    s=d.financials.data
    if not s:
        show_region_status(d.financials,"Annual statements")
        return
    periods=selected_periods(s)
    if not periods:
        st.info("No usable completed reported annual fiscal periods were returned.")
        return
    results=all_results(s)
    section("REPORTED ANNUAL PERIODS", "Financial statements")
    st.caption(f"{s.instrument.reporting_currency} {unit.lower()} · newest fiscal year first · S Synthetic / R Reported via provider / D Derived · — unavailable / N/M not meaningful / N/A not applicable")
    if len(periods)<3:
        st.info(f"Only {len(periods)} reported annual years available. No additional years have been invented.")
    if any(p.transition for p in periods):
        st.warning("Short transition fiscal period present. Values are not annualized; incomparable growth and averages are suppressed.")
    if any(s.value(p.end,k) is None for p in periods for k in REPORTED):
        st.warning("Partial annual data: missing statement cells retain their fiscal year. See cell details and methodology for reasons.")
    if s.instrument.sector in ("Banks","Insurance","Financial Services","Unknown"):
        st.info("Standard industrial-company ratios are suppressed under the sector applicability policy.")
    table(s,periods,{k:v for k,v in REPORTED.items() if k in ("total_revenue","cost_of_revenue","net_income")},unit,caption="Income statement · annual flows")
    table(s,periods,{k:v for k,v in REPORTED.items() if k not in ("total_revenue","cost_of_revenue","net_income")},unit,caption="Balance sheet · fiscal year-end balances")
    section("DERIVED LOCALLY", "Ratios & growth")
    table(s,periods,{k:METRICS[k][0] for k in list(METRICS)[:8]},unit,results,caption="Eight financial ratios · full-precision inputs; rounded display")
    table(s,periods,{k:METRICS[k][0] for k in ("revenue_yoy","income_yoy")},unit,results,caption="Comparable consecutive fiscal years · positive prior-value convention")
    issues=[{"Period":p.label,"Metric":METRICS[k][0],"Status":r.status,"Reason / context":r.reason or r.note} for p in periods for k,r in results[p.end].items() if r.status!="ok" or r.note]
    if issues:
        with st.expander(f"Calculation notes · {len(issues)} unavailable or contextual results"):
            st.dataframe(pd.DataFrame(issues),hide_index=True,width="stretch")
    with st.expander("Supporting inputs & opening balances"):
        table(s,periods,SUPPORT,unit,caption=f"Supporting reported inputs · {s.instrument.reporting_currency} {unit.lower()}")
        openings=[]
        for p in periods:
            prior=previous_period(s,p)
            openings.append({"Fiscal year":p.label,"Opening balance date":prior.end if prior else "Unknown / unavailable",
                             "Opening equity":money(s.value(prior.end,"stockholders_equity") if prior else None,unit),
                             "Opening assets":money(s.value(prior.end,"total_assets") if prior else None,unit),
                             "Prior revenue":money(s.value(prior.end,"total_revenue") if prior else None,unit),
                             "Prior net income":money(s.value(prior.end,"net_income") if prior else None,unit)})
        st.dataframe(pd.DataFrame(openings),hide_index=True,width="stretch")
    section("HISTORICAL TRENDS", "Three fiscal years, one consistent dataset")
    l,r=st.columns(2)
    with l:
        st.caption("Revenue & cost of revenue")
        plot(charts.financial(s,periods,["total_revenue","cost_of_revenue"],["Revenue","Cost of revenue"],unit),"revenue_cost")
    with r:
        st.caption("Net income · losses remain below zero")
        plot(charts.financial(s,periods,["net_income"],["Net income"],unit),"net_income")
    l,r=st.columns(2)
    with l:
        st.caption("Year-over-year growth")
        plot(charts.ratios(periods,results,["revenue_yoy","income_yoy"],["Revenue YoY","Net income YoY"],"%"),"growth")
    with r:
        chosen=st.selectbox("Ratio trend",list(METRICS)[:8],format_func=lambda k:METRICS[k][0],key="ratio_trend")
        plot(charts.ratios(periods,results,[chosen],[METRICS[chosen][0]],METRICS[chosen][1]),"ratio")
    st.caption("Chart values are also available in the statement, ratio, and growth tables above. Bars preserve missing observations and do not interpolate missing fiscal years.")

def planned(d, name):
    symbol=d.instrument.symbol if d.instrument else d.requested_symbol or "No company selected"
    text = ("Valuation metrics need approved definitions for price dates, fiscal or forward periods, share basis, enterprise-value debt/cash scope, currency alignment, and treatment of losses. No fair value or recommendation is calculated in this release."
            if name=="Valuation" else "A future comparison view will use explicitly selected peers and reviewed rules for fiscal periods, currencies, accounting scope, and sector applicability. Peer selection and benchmark definitions remain open.")
    st.markdown(f'<div class="planned"><div class="eyebrow">{escape(symbol)} / {escape(name.upper())}</div><h2>More perspective, next.</h2><span class="badge">Planned — not included in this release</span><p>{escape(text)}</p></div>',unsafe_allow_html=True)

def methodology(d):
    s=d.financials.data
    with st.expander("Methodology, provenance & data status"):
        st.markdown("**Calculation policy:** quick assets include cash, eligible current investments, and net current receivables. Interest-bearing debt includes finance leases once and excludes operating leases. ROE/ROA/turnover use adjacent opening and closing balances. Growth requires a comparable, positive prior-year baseline. No FX conversion is performed.")
        st.caption("Percentages are stored as ratios. Display scaling never changes calculations. Publication time and provider update time are Unknown unless explicitly supplied. This is a latest-available snapshot, not a historical backtest dataset.")
        st.dataframe(pd.DataFrame([{"Region":label,"Freshness":r.status,"Last successful retrieval UTC":r.retrieved_at or "Unknown","Note":r.message} for label,r in [("Quote",d.quote),("Daily history",d.history),("Annual financials",d.financials)]]),hide_index=True,width="stretch")
        if d.quote.data:
            st.markdown("**Market observations · quote currency, previous close, timestamp, and adjustment basis**")
            st.json(d.quote.data,expanded=False)
        if d.history.data:
            st.json({k:v for k,v in d.history.data.items() if k!="rows"},expanded=False)
        if s:
            for note in s.notes:
                st.caption(note)
            st.caption(f"Snapshot: {s.snapshot_id} · Provider: {s.provider_id} · Mapping: mapping-1 · Formulas: formula-1 · Net-income attribution: {s.periods[0].scope if s.provider_id.startswith('fixture') else 'Unverified; ROE suppressed'}")
            st.markdown("**Fiscal period metadata**")
            st.dataframe(pd.DataFrame([asdict(p) for p in s.periods]),hide_index=True,width="stretch")
            end=st.selectbox("Inspect fiscal period",[p.end for p in selected_periods(s)],key="audit_period") if selected_periods(s) else None
            if end:
                st.markdown("**Source observations · original field, raw value, scale, currency, and snapshot**")
                st.dataframe(pd.DataFrame([asdict(o)|{"observation_id":o.id} for o in s.observations.get(end,{}).values()]),hide_index=True,width="stretch")
                st.markdown("**Derived results · unrounded values and input observation IDs**")
                st.dataframe(pd.DataFrame([asdict(r)|{"formula":METRICS[k][2]} for k,r in all_results(s)[end].items()]),hide_index=True,width="stretch")
