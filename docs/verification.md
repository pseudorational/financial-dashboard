# Verification record · October 21, 2026

Tested locally on macOS with Python 3.12, Streamlit 1.66.1, Plotly 7.1.0, pandas 3.0.6, yfinance 1.7.0, and pytest 9.1.1. The complete installed runtime and development set is pinned in the requirements files. Installation, imports, AppTest execution, and the Streamlit health endpoint succeeded.

## Offline suite

`python -m pytest -q`: **109 passed**. Golden expectations are independent rational inputs/denominators from the supplied specification, with 1e-9 ratio tolerance and separate display tests. Coverage includes all ten derived metrics, invalid/missing denominators, negative equity and profit, debt/lease policy, quick-asset completeness, currency/scope/scale compatibility, noncalendar/53-week periods, reported-only selection, revisions, two-company isolation, unavailable endpoints, cache TTL/refresh/stale/capacity, shared budgets, single-flight concurrency, retry eligibility, Retry-After, snapshot deadlines, hard subprocess timeouts, units, and AppTest state/error journeys. Worker contract tests check all four provider history ranges, explicit annual frequency, adjusted daily prices, incomplete-bar omission, and separate quote/statement currencies without network access.

## Browser acceptance

The reusable `tests/browser/acceptance.cua.js` journey executed through the Codex CUA browser surface and passed **27 assertions**:

- Four tabs and prominent synthetic notice.
- Golden current ratio and ROE values in actual rendered financial tables.
- Thousands scaling changes money while preserving ratios.
- Both future tabs display their planned-release boundary.
- DEMO-B changes quote/company identity with no retained DEMO-A identity.
- Plotly zoom-in and reset controls execute successfully.
- Partial statements, bank policy, two-year history, missing opening history, unsupported instruments, and missing quotes show their specific notices while retaining all tabs.
- A real symbol in synthetic mode shows an explanatory error with all four tabs.
- At 390×844, page width equals viewport width, financial tables contain their horizontal overflow, and keyboard arrows move the table scroll position.

Desktop and mobile screenshots were visually reviewed at 1440×900 and 390×844. Controls and synthetic status remain readable. Tables retain newest-to-oldest years and scroll within their panel on mobile. Chart values have tabular equivalents. Screenshots are in `docs/screenshots/`.

## Verification boundaries

No public hosting, GitHub repository publication, live Yahoo request, paid provider subscription, or public-live data-rights review was performed. Actual-host cold start, load/concurrency limits, network restrictions, and licensed-provider mappings remain unverified. The prototype adapter is conservatively incomplete where Yahoo metadata does not establish calculation semantics; unavailable values are intentional. Its worker call configuration is checked offline with mocks. The CUA journey exercises Plotly zoom/reset; detailed pointer-hover behavior and a comprehensive screen-reader audit were not automated. Browser automation runs in Codex; the ordinary GitHub Actions job runs the offline/AppTest suite only.

This verifies the local synthetic dashboard and its documented checks, not public live-data release readiness or every operational target in the specification.
