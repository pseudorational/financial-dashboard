import pytest
from financial_dashboard.providers import FixtureProvider

@pytest.fixture
def snapshot():
    p=FixtureProvider()
    return p.get_annual_financials(p.resolve_instrument("DEMO-A"))
