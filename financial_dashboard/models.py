from dataclasses import dataclass, field
from datetime import date, datetime, timezone
import math

SCHEMA = "canonical-1"
MAPPING = "mapping-1"
FORMULA = "formula-1"

def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def number(value):
    if isinstance(value, bool):
        return None
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (ValueError, TypeError, OverflowError):
        return None

@dataclass
class Instrument:
    symbol: str
    requested_symbol: str
    name: str
    exchange: str = "DEMO"
    instrument_type: str = "EQUITY"
    sector: str = "Industrials"
    quote_currency: str = "USD"
    reporting_currency: str = "USD"
    timezone: str = "America/New_York"
    transformation: str = "None"

@dataclass
class Period:
    end: str
    start: str | None
    label: str
    kind: str = "annual"
    reported: bool = True
    completed: bool = True
    estimated: bool = False
    revision: str = "1"
    publication_time: str | None = None
    currency: str = "USD"
    scope: str = "parent"
    transition: bool = False
    notes: str = ""

    @property
    def heading(self):
        return f"{self.label} · ended {self.end}"

@dataclass
class Observation:
    instrument_id: str
    provider_id: str
    canonical_field: str
    raw_field_key: str
    raw_value: object
    normalized_value: float | None
    period_end: str
    currency: str
    snapshot_id: str
    retrieved_at_utc: str
    status: str = "ok"
    reason_code: str = ""
    source_unit: str = "base currency"
    normalized_unit: str = "base currency"
    classification: str = "Synthetic"
    scope: str = "parent"
    mapping_version: str = MAPPING
    statement_type: str = "balance"
    source_reference: str = "project-owned fixture"

    @property
    def id(self):
        return f"{self.snapshot_id}:{self.period_end}:{self.canonical_field}"

@dataclass
class AnnualSnapshot:
    instrument: Instrument
    provider_id: str
    periods: list[Period]
    observations: dict[str, dict[str, Observation]]
    snapshot_id: str
    retrieved_at: str
    as_of: str
    debt_policy: str = "separate_finance_leases"
    quick_scope_verified: bool = True
    cost_scope_verified: bool = True
    notes: list[str] = field(default_factory=list)

    def obs(self, end, key):
        return self.observations.get(end, {}).get(key)

    def value(self, end, key):
        o = self.obs(end, key)
        return o.normalized_value if o and o.status == "ok" else None

@dataclass
class Result:
    metric_id: str
    value: float | None
    unit: str
    status: str = "ok"
    reason: str = ""
    input_ids: list[str] = field(default_factory=list)
    input_periods: list[str] = field(default_factory=list)
    formula_version: str = FORMULA
    note: str = ""

@dataclass
class Region:
    data: object = None
    retrieved_at: str | None = None
    status: str = "unavailable"
    message: str = ""
    cache_hit: bool = False

@dataclass
class Dashboard:
    requested_symbol: str
    instrument: Instrument | None = None
    quote: Region = field(default_factory=Region)
    history: Region = field(default_factory=Region)
    financials: Region = field(default_factory=Region)
    error: str = ""
    correlation_id: str = ""
