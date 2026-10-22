from dataclasses import replace
from pathlib import Path
import copy
import json
import pytest
from financial_dashboard.calculations import calculate, selected_periods, all_results, METRICS
from financial_dashboard.formatting import money, price, result_text, quote_change, quote_unit
from financial_dashboard.models import number, Period

EXPECTED=json.loads(Path(__file__).with_name("expected_metrics.json").read_text())

@pytest.mark.parametrize("end,key,num,den",[(end,k,*v) for end,rows in EXPECTED.items() for k,v in rows.items()])
def test_independent_golden_values(snapshot,end,key,num,den):
    p=next(p for p in snapshot.periods if p.end==end)
    r=calculate(snapshot,p,key)
    assert r.status=="ok"
    assert r.value==pytest.approx(num/den,abs=1e-9)
    assert r.input_ids
    assert r.input_periods

def set_value(s,key,value,end="2024-12-31"):
    s.observations[end][key].normalized_value=value

@pytest.mark.parametrize("key,value,status",[("current_liabilities",0,"invalid_denominator"),("current_liabilities",-1,"invalid_denominator"),("current_assets",-1,"mapping_unresolved"),("current_assets",None,"missing_input")])
def test_current_ratio_invalid(snapshot,key,value,status):
    set_value(snapshot,key,value)
    assert calculate(snapshot,snapshot.periods[-1],"current_ratio").status==status

@pytest.mark.parametrize("value",[0,-150_000_000])
def test_negative_or_zero_opening_equity_never_closing_only(snapshot,value):
    set_value(snapshot,"stockholders_equity",value,"2023-12-31")
    assert calculate(snapshot,snapshot.periods[-1],"roe").status=="not_meaningful"

def test_losses_negative_gross_profit_and_zero_revenue(snapshot):
    p=snapshot.periods[-1]
    set_value(snapshot,"net_income",-100_000_000)
    assert calculate(snapshot,p,"net_margin").value<0
    set_value(snapshot,"cost_of_revenue",2_000_000_000)
    assert calculate(snapshot,p,"gross_margin").value<0
    set_value(snapshot,"total_revenue",0)
    assert calculate(snapshot,p,"asset_turnover").value==0
    assert calculate(snapshot,p,"gross_margin").status=="invalid_denominator"

def test_debt_zero_absent_and_no_lease_double_count(snapshot):
    p=snapshot.periods[-1]
    for key in ("current_interest_bearing_debt","long_term_interest_bearing_debt"):
        set_value(snapshot,key,0)
    assert calculate(snapshot,p,"debt_equity").value==0
    del snapshot.observations[p.end]["current_interest_bearing_debt"]
    assert calculate(snapshot,p,"debt_equity").status=="missing_input"
    set_value(snapshot,"current_finance_lease_liabilities",100_000_000)
    snapshot.observations[p.end]["current_interest_bearing_debt"]=copy.deepcopy(snapshot.observations[p.end]["long_term_interest_bearing_debt"])
    snapshot.debt_policy="leases_included"
    assert calculate(snapshot,p,"debt_equity").value==0
    snapshot.debt_policy="unknown"
    assert calculate(snapshot,p,"debt_equity").reason=="Debt definition unresolved"

def test_quick_components_missing_and_unverified(snapshot):
    p=snapshot.periods[-1]
    del snapshot.observations[p.end]["short_term_investments"]
    assert calculate(snapshot,p,"quick_ratio").status=="missing_input"
    snapshot.quick_scope_verified=False
    assert calculate(snapshot,p,"quick_ratio").status=="mapping_unresolved"

def test_currency_scope_and_scale_mismatch(snapshot):
    p=snapshot.periods[-1]
    o=snapshot.observations[p.end]["total_revenue"]
    for field,value in [("currency","EUR"),("scope","including_nci"),("normalized_unit","millions")]:
        orig=getattr(o,field)
        setattr(o,field,value)
        assert calculate(snapshot,p,"net_margin").status=="incomparable_periods"
        setattr(o,field,orig)

def test_income_equity_scope(snapshot):
    p=snapshot.periods[-1]
    snapshot.observations[p.end]["net_income"].scope="including_nci"
    assert calculate(snapshot,p,"roe").status=="incomparable_periods"

def test_growth_loss_transitions(snapshot):
    p=snapshot.periods[-1]
    set_value(snapshot,"net_income",-40_000_000,"2023-12-31")
    r=calculate(snapshot,p,"income_yoy")
    assert r.status=="not_meaningful" and "Turned profitable" in r.note
    set_value(snapshot,"net_income",100_000_000,"2023-12-31")
    set_value(snapshot,"net_income",-40_000_000)
    r=calculate(snapshot,p,"income_yoy")
    assert r.value==pytest.approx(-1.4) and "Turned loss-making" in r.note
    set_value(snapshot,"net_income",0,"2023-12-31")
    assert calculate(snapshot,p,"income_yoy").status=="not_meaningful"

@pytest.mark.parametrize("sector",["Banks","Insurance","Financial Services","Unknown"])
def test_sector_policy(snapshot,sector):
    snapshot.instrument.sector=sector
    assert all(calculate(snapshot,snapshot.periods[-1],key).status=="not_applicable" for key in list(METRICS)[:8])

def test_missing_opening_gap_transition_and_unknown_start(snapshot):
    p=snapshot.periods[-1]
    p.start=None
    assert calculate(snapshot,p,"roe").value is None
    p.start="2024-01-01"
    snapshot.periods[-2].currency="EUR"
    assert calculate(snapshot,p,"roa").status=="incomparable_periods"
    snapshot.periods[-2].currency="USD"
    p.transition=True
    assert calculate(snapshot,p,"revenue_yoy").status=="incomparable_periods"
    p.transition=False
    snapshot.periods=[x for x in snapshot.periods if x.end!="2023-12-31"]
    assert calculate(snapshot,p,"revenue_yoy").value is None
    assert calculate(snapshot,p,"asset_turnover").value is None

def test_period_selection_dynamic_union_and_no_clock_invention(snapshot):
    assert [p.label for p in selected_periods(snapshot)]==["FY2024","FY2023","FY2022"]
    p=replace(snapshot.periods[-1],end="2025-03-31",start="2025-01-01",label="Q1",kind="quarterly")
    snapshot.periods.append(p)
    snapshot.observations[p.end]=copy.deepcopy(snapshot.observations["2024-12-31"])
    assert selected_periods(snapshot)[0].label=="FY2024"
    p.kind="annual"
    p.completed=False
    assert selected_periods(snapshot)[0].label=="FY2024"
    p.completed=True
    p.estimated=True
    assert selected_periods(snapshot)[0].label=="FY2024"
    p.estimated=False
    p.label="FY transition"
    p.transition=True
    assert selected_periods(snapshot)[0].label=="FY transition"
    snapshot.as_of="2035-01-01"
    assert len(selected_periods(snapshot))==3
    assert selected_periods(snapshot)[0].end=="2025-03-31"

def test_noncalendar_53_week_adjacency(snapshot):
    dates=[("2021-09-25","2020-09-27"),("2022-09-24","2021-09-26"),("2023-09-30","2022-09-25"),("2024-09-28","2023-10-01")]
    old_observations=snapshot.observations
    snapshot.observations={}
    for p,(end,start) in zip(snapshot.periods,dates):
        obs=old_observations[p.end]
        p.end,p.start=end,start
        for o in obs.values():
            o.period_end=end
        snapshot.observations[end]=obs
    assert calculate(snapshot,snapshot.periods[-1],"roe").value==pytest.approx(180/675)
    assert calculate(snapshot,snapshot.periods[-1],"revenue_yoy").value==pytest.approx(.25)

def test_revision_and_blank_columns(snapshot):
    duplicate=replace(snapshot.periods[-1],revision="2",notes="Restated")
    snapshot.periods.append(duplicate)
    snapshot.periods.append(Period("2025-01-01","2024-01-02","blank"))
    assert selected_periods(snapshot)[0].notes=="Restated"
    assert len(selected_periods(snapshot))==3

@pytest.mark.parametrize("unit,expected",[("Raw","1,500,000,000.00"),("Thousands","1,500,000.00"),("Millions","1,500.00"),("Billions","1.50")])
def test_units_and_rounding(unit,expected,snapshot):
    before=all_results(snapshot)
    assert money(1_500_000_000,unit)==expected
    assert result_text(before["2024-12-31"]["roe"])=="26.67%"
    assert before==all_results(snapshot)

@pytest.mark.parametrize("raw",[None,"nonsense",float("nan"),float("inf"),True])
def test_nonfinite_missing(raw):
    assert number(raw) is None
    assert money(raw)=="—"

def test_small_price_quote_subunits_and_comparison():
    assert price(.000013)!="0.00"
    assert quote_unit("GBp")=="GBp (pence)"
    q={"price":10,"previous_close":8,"currency":"GBp","previous_currency":"GBp","basis":"raw","previous_basis":"adjusted"}
    assert quote_change(q)[0] is None
    q["previous_basis"]="raw"
    assert quote_change(q)[0]==(2,.25)

def test_tiny_positive_denominator(snapshot):
    set_value(snapshot,"current_liabilities",1e-6)
    r=calculate(snapshot,snapshot.periods[-1],"current_ratio")
    assert r.value==750_000_000/1e-6 and r.note
