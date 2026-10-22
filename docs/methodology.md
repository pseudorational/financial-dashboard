# Financial methodology · formula-1 / mapping-1

Periods are selected once from the union of completed, non-estimated reported annual periods with usable observations, sorted by actual fiscal end. The latest three are displayed newest first. Quarterly/YTD/TTM, future, incomplete, and empty columns are excluded. Revision metadata chooses the latest supplied revision for an end date. Income and balance rows align to the same periods; a missing statement does not remove a year. In this MVP provider revisions are latest-snapshot only; no point-in-time history is claimed.

Quick assets = cash and equivalents + eligible current short-term investments + current net receivables. Component completeness, liquidity, nonnegative values, and nonoverlap are required. No alternative inventory-subtraction convention is used.

Debt = current interest-bearing debt + noncurrent interest-bearing debt + separately identified finance leases excluded from those borrowing fields. `leases_included` prevents double counting. An unknown policy suppresses debt-to-equity. Operating leases and total liabilities are never debt substitutes.

Current ratio = current assets / positive current liabilities. Quick ratio = quick assets / positive current liabilities. Net margin = net income / positive revenue. Gross margin = (revenue − verified cost of revenue) / positive revenue. Negative profits and gross profits are preserved. A cost sign is never unconditionally converted with absolute value.

ROE = net income / average equity. ROA = net income / average assets. Asset turnover = revenue / average assets. Both balance endpoints must be positive, in compatible currencies, scales and scopes. The opening observation must close on the day immediately preceding the current period's known start. Comparable periods must have annual durations of 350–380 days with duration differences no greater than eight days, permitting 52/53-week years. Transitions or unknown continuity suppress averages and growth. Income/equity attribution mismatches suppress ROE; this conservative implementation also suppresses other scope mismatches.

Debt-to-equity = defined debt / positive closing equity. Zero debt requires explicit source values. Missing is never zero. Banks, insurers, and financial-services issuers have all eight generic ratios suppressed pending reviewed methodology; unknown sector classification is conservatively suppressed as well.

Growth = (current − previous) / previous for adjacent comparable fiscal years with a strictly positive previous value. Prior zero/negative values produce N/M; loss-to-profit and profit-to-loss transitions expose the absolute change. Positive-to-negative profit growth can validly fall below −100%.

Calculations retain full precision; rounding is presentation only. Monetary units scale only monetary aggregates. Quote currencies/subunits remain distinct from statement currencies, with no FX conversion. Missing values use —, nonmeaningful values use N/M, and sector/instrument exclusions use N/A. Hover details and the provenance panel expose reasons and input lineage.

Yahoo prototype mapping uses exact aliases only; conflicts are explicit and fuzzy matches are rejected. Combined cash/investment fields never masquerade as the required standalone cash row. Current/long-term debt, cost conventions, liquid-asset eligibility, starts, duration, and attribution need provider-specific semantic verification; uncertain derived metrics remain unavailable. Missing time metadata is Unknown. Demo observations are Synthetic, even where they represent a reported statement shape.
