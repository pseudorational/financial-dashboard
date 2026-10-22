# Implementation decisions

## October 21, 2026

- Preserve the confirmed Python, Streamlit, and Plotly architecture. Sites hosting does not run this Python process, so deliver a local Streamlit app with deployment preparation. No Site registration, repository publication, or external account creation is necessary to build it.
- Use the spec's project-owned synthetic golden fixture as the default. Freeze its as-of date at 2025-04-01. Never advance reported financial years merely because today's date changes. Use a second distinct synthetic company and clearly named edge-case symbols.
- Consolidate the suggested module tree into a small Python package with the same provider/domain/service/UI boundaries. No API server, database, account, or LLM is added.
- Use per-session selection and synchronous Streamlit script orchestration. There is no background UI completion callback that can overwrite a newer ticker request. Previous data is cleared before loading a new request. Shared cache objects contain copies rather than a mutable global selected ticker.
- Use a single bounded 128-entry endpoint cache, single-flight locks with reference tracking, a shared 60-request/minute provider budget, endpoint TTLs from the spec, and per-session/shared refresh cooldowns of 15 seconds. Monetary units are not a cache dimension. Keys include provider, symbol/exchange, endpoint, request range/frequency/adjustment, schema, mapping, and entitlement category.
- Yahoo APIs lacking cancellable timeouts are isolated in subprocesses with a hard nine-second timeout and four shared process slots. Retry at most twice for transient categories, with jitter and a 30-second snapshot deadline. Resolve and region calls are sequential, so a slow early endpoint may exhaust the budget for later regions; those regions return explicit deadline states. The worker does not expose raw exception text, stderr, authenticated URLs, or secrets.
- Yahoo's annual response does not establish fiscal start, duration, attribution, or component coverage. Preserve unknown metadata and suppress affected calculations. Do not assume the candidate field aliases alone establish semantics. More complete live-data mapping requires explicit provider validation rather than guessed results. Tests use invented provider-shaped payloads, not captured Yahoo data.
- Four tab containers compute eagerly using the pinned Streamlit release. Shared data is fetched before the tabs, once per snapshot. Switching tabs or units does not initiate retrieval.
- Use bars for three-observation financial trends. Missing periods are not connected or smoothed. Keep percentage charts separate from multiple charts. Scope future tabs exactly to the spec's planned panels.
- Unknown sector classifications are conservatively suppressed for all eight generic ratios. This is stricter than selective suppression and is documented to avoid implying a methodology review.
- Public-live mode fails closed until a licensed adapter and rights review exist. No deployment readiness claim is based on a passing synthetic test suite.

Remaining limits: real-host cold-start, concurrent load limits, exchange/provider entitlements, actual Yahoo schema behavior, and public-live licensing have not been verified. A repository owner and hosting audience have not been selected. These do not block the local synthetic demonstration.
