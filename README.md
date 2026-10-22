# Financial Dashboard

A compact dark Python / Streamlit / Plotly dashboard built from the accompanying financial-dashboard specification. Overview and Financials are functional; Valuation and Comparisons deliberately remain labeled roadmap panels.

**Default: synthetic demo.** All demo companies, annual figures, prices, and volumes are invented. The financial fixture is frozen as of **2025-04-01**. Retrieval time is the actual retrieval time, not the fixture's market date. This application does not require an LLM, account, API key, database, or live network connection in demo mode.

## Run locally

Use Python **3.12**. From this directory:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
streamlit run app.py
```

Open the URL printed by Streamlit. For the already installed environment, `./run_dashboard.command` launches the app on 127.0.0.1:8501. On macOS you can also open that executable file in Finder. Settings use the supported Streamlit dark theme with limited CSS for layout and financial tables. The configured file watcher is disabled: restart the server after code changes.

## Explore

- Enter `DEMO-A` (Example Manufacturing) or `DEMO-B` (Northstar Systems), then press Enter or Load. Real symbols are unavailable in demo mode.
- Select Raw, Thousands, Millions, or Billions. Ratios, per-share quotes, share counts, currencies, and raw values do not change.
- Select 1M, 6M, 1Y, or 5Y adjusted daily history; use Plotly's zoom, pan, and reset controls.
- Financials shows the newest three reported annual periods, supporting inputs, eight ratios, two growth measures, and chronological charts.
- Expand Methodology, provenance & data status for the unrounded results, formulas, source observations, dates, input IDs, mapping version, and snapshot ID. Financial tables provide hover details and keyboard-focusable horizontal scrolling. Chart values have tabular equivalents.

Scenario symbols: `DEMO-PARTIAL`, `DEMO-BANK`, `DEMO-OPENING`, `DEMO-TWO`, `DEMO-LOSS`, `DEMO-ETF`, `DEMO-OUTAGE`, and `DEMO-NOQUOTE`. Each is visibly synthetic. See [fixture declarations](fixtures/README.md).

## Controlled Yahoo prototype

```sh
DASHBOARD_MODE=prototype .venv/bin/streamlit run app.py
```

This mode starts with an empty ticker field. Enter a real provider-supported ticker and Load. It uses explicit annual endpoints and `auto_adjust=True` daily history. Provider calls run in killable subprocesses, with bounded endpoint retries, shared budgets, and an overall 30-second load deadline. No live Yahoo requests were made for the delivered offline test suite.

Yahoo fields do not establish their semantic scope merely by having plausible names. Consequently this adapter conservatively withholds quick ratio, gross margin, debt-to-equity, average-balance ratios, and growth when field definitions or fiscal metadata cannot be verified. It preserves available reported rows and explains unavailable calculations. It does not guess fiscal starts or substitute liabilities for debt. An empty result does not prove a symbol is invalid.

**Prototype access is not redistribution permission.** Do not publicly deploy prototype mode without the applicable data rights and a reviewed adapter. `DASHBOARD_MODE=public_live` fails closed; a licensed adapter has not been selected or implemented. No silent provider fallback exists. See [data rights](docs/data_rights.md).

## Tests

```sh
.venv/bin/python -m pytest -q
```

The deterministic offline suite covers independent golden calculations, missing/negative/zero inputs, sector applicability, fiscal-period selection, 52/53-week adjacency, transition periods, alias conflicts, currency/scope/scale mismatches, ticker isolation, endpoint failures, retries, deadlines, TTLs, refresh cooldown, coalescing, stale handling, and Streamlit widget/error journeys. It uses no live provider secrets. Exact expectations are specified independently in `tests/expected_metrics.json`.

Browser journeys use the Codex browser testing surface. The reusable assertions are in `tests/browser/acceptance.cua.js`; run within that surface with a connected `tab`, `browser`, and `nodeRepl`. Browser results and screenshots are recorded in [verification](docs/verification.md). This complements AppTest, which does not establish responsive rendering or Plotly interaction.

## Structure

`app.py` owns session selection. `financial_dashboard/providers.py` owns fixtures and Yahoo mapping; `yahoo_worker.py` isolates network requests. `models.py` defines canonical observations. `calculations.py` contains pure arithmetic and period alignment. `service.py` owns caching and retrieval. `formatting.py`, `charts.py`, and `ui.py` handle presentation.

Source repository: [pseudorational/financial-dashboard](https://github.com/pseudorational/financial-dashboard) (private). For Streamlit Community Cloud, select this repository, branch `main`, entrypoint `app.py`, and Python 3.12. No secrets are required for demo mode. Set app sharing to public if you want an address anyone can view; the source repository can remain private.

See [methodology](docs/methodology.md), [implementation decisions](docs/decisions.md), and [deployment and rollback](docs/deployment.md). The Streamlit app has not yet been deployed. The original spec remains in the parent directory; it is not modified by the application.
