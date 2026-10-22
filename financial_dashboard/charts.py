import plotly.graph_objects as go
from .formatting import UNITS, quote_unit

COLORS = ["#49B8FF", "#536B85", "#A78BFA", "#52D3AC"]

def base(fig, height=280, unit="", percentage=False):
    fig.update_layout(template="plotly_dark", height=height, paper_bgcolor="#121923", plot_bgcolor="#121923",
        margin=dict(l=14,r=14,t=20,b=18), font=dict(family="Arial, sans-serif",size=12,color="#98A6B5"),
        legend=dict(orientation="h",y=1.14,x=0), hovermode="x unified", dragmode="zoom",
        xaxis=dict(showgrid=False, fixedrange=False),
        yaxis=dict(gridcolor="#232D3B",zeroline=True,zerolinecolor="#536B85",title=unit,
                   tickformat=".0%" if percentage else None))
    return fig

def prices(history, symbol):
    rows=history["rows"]
    fig=go.Figure(go.Scatter(x=[r["date"] for r in rows],y=[r["close"] for r in rows],mode="lines",
        line=dict(color=COLORS[0],width=2),fill="tozeroy",fillcolor="rgba(73,184,255,.06)",
        name=f"{symbol} adjusted close",connectgaps=False,hovertemplate="%{x}<br>%{y:,.4f}<extra></extra>"))
    base(fig,350,quote_unit(history["currency"]))
    values=[r["close"] for r in rows if r["close"] is not None]
    if values:
        pad=max((max(values)-min(values))*.18,abs(max(values))*.02)
        fig.update_yaxes(range=[min(values)-pad,max(values)+pad])
    return fig

def financial(s, periods, keys, names, unit):
    fig=go.Figure()
    for idx,(key,name) in enumerate(zip(keys,names)):
        fig.add_bar(x=[p.end for p in reversed(periods)],
                    y=[None if s.value(p.end,key) is None else s.value(p.end,key)/UNITS[unit] for p in reversed(periods)],
                    name=name,marker_color=COLORS[idx],hovertemplate="%{x}<br>%{y:,.2f}<extra>%{fullData.name}</extra>")
    fig.update_layout(barmode="group")
    base(fig,280,f"{s.instrument.reporting_currency} {unit.lower()}")
    fig.update_xaxes(type="category")
    return fig

def ratios(periods, results, keys, names, unit):
    fig=go.Figure()
    for idx,(key,name) in enumerate(zip(keys,names)):
        fig.add_bar(x=[p.end for p in reversed(periods)],y=[results[p.end][key].value for p in reversed(periods)],
                    name=name,marker_color=COLORS[idx],hovertemplate="%{x}<br>%{y:.4f}<extra>%{fullData.name}</extra>")
    base(fig,270,unit,unit=="%")
    fig.update_xaxes(type="category")
    return fig
