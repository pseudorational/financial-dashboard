# Data rights status

As of October 21, 2026, the deployable default is **demo**. Its invented fixtures and generated price series are project-owned and explicitly synthetic. No original real-company filings or raw restricted provider captures are included.

The Yahoo adapter is for controlled prototyping. No agreement, public display entitlement, redistribution right, or commercial-use right has been reviewed or established. A software package license is not a data license. Do not publicly expose this mode based on this project's existence. Yahoo requests were not used for mandatory testing.

**Public live-data release: disabled.** A licensed provider and accountable rights owner remain unselected. `public_live` fails closed and never falls back to Yahoo or synthetic data under a real symbol.

Before implementing and enabling that mode, record the provider/product/plan, agreement version, review date and owner, evidence location, public-display and derived-data rights, audience/exchanges/territories, cache and storage limits, retention and termination policy, export/redistribution rights, attribution and delay requirements, entitlement conditions, and request budgets. Implement the selected adapter and real-host operational checks against those actual terms.

The prototype uses bounded in-memory caches and no raw disk captures. Stale fallback is restricted to the fixture provider because Yahoo retention/display rights are not established. Built-in Streamlit data viewers are for controlled inspection; no public data-export feature is implemented. Revisit all viewer/export surfaces before any live-data launch.
