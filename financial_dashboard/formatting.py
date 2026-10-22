import math
from .models import number

UNITS = {"Raw":1, "Thousands":1000, "Millions":1000000, "Billions":1000000000}

def money(value, unit="Millions"):
    n = number(value)
    return "—" if n is None else f"{n / UNITS[unit]:,.2f}"

def price(value):
    n = number(value)
    if n is None:
        return "—"
    return f"{n:,.2f}" if n == 0 or abs(n) >= .01 else f"{n:.6g}"

def result_text(r):
    if r.value is None:
        return {"not_meaningful":"N/M", "not_applicable":"N/A"}.get(r.status, "—")
    return f"{r.value*100:,.2f}%" if r.unit == "%" else f"{r.value:,.2f}x"

def quote_unit(code):
    return {"GBp":"GBp (pence)", "GBX":"GBX (pence)", "ZAc":"ZAc (cents)"}.get(code, code)

def quote_change(q):
    a, b = number(q.get("price")), number(q.get("previous_close"))
    if a is None or b is None or b <= 0:
        return None, "Previous comparable positive close unavailable"
    if q.get("basis") != q.get("previous_basis") or q.get("currency") != q.get("previous_currency"):
        return None, "Currency, unit, or adjustment basis mismatch"
    return (a-b, (a-b)/b), "Versus previous close"
