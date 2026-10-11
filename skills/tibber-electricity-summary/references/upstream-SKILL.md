---
name: tibber-electricity-summary
description: Use when checking Tibber electricity costs and prices.
version: 0.1.0
author: Mehdi Shahdoost
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [tibber, electricity, costs, cache, mcp]
---

# Tibber electricity summary

Use the authenticated Tibber MCP to report month-to-date electricity cost, last month's electricity cost, year-to-date electricity cost, and today's cheapest and most expensive price periods. Cache historical observations in `~/.hera/tibber.data` (this exact path, not `~/.hermes/`). Do not estimate consumption costs by multiplying spot prices by guessed usage.

## When to Use

Use for a Tibber electricity dashboard, monthly/year-to-date consumption costs, or today's cheapest and most expensive electricity periods. Do not use for final invoice reconciliation without invoice data.

## Prerequisites

The Tibber MCP tools must be available. Load their schemas with `tool_describe` before invocation through `tool_call`:

- `mcp__tibber__tibber_account`: `{}`; authenticated user and homes.
- `mcp__tibber__tibber_home`: `{ "homeId": "..." }`; home details.
- `mcp__tibber__tibber_prices`: `{ "homeId": "..." }`; current, today and available tomorrow prices.
- `mcp__tibber__tibber_history`: `{ "homeId": "...", "from": "ISO-8601 with offset", "to": "ISO-8601 with offset", "type": "consumption", "resolution": "DAILY" }`; maximum 31 days per request.

If schemas change, use the live schemas rather than guessing parameters. If Tibber MCP is unavailable, use the installation instructions for `tibber-mcp-server` at https://www.npmjs.com/package/tibber-mcp-server to install and configure it. Before modifying Hermes configuration, load the `hermes-agent` and `native-mcp` skills and follow their setup workflows. Read the package's current instructions rather than guessing installation commands or credential requirements. Verify that the Tibber MCP tools are available after setup. If authentication or tools remain unavailable, report the blocker; never invent figures.

## Procedure

1. Obtain current time using `terminal` or Python via `execute_code`, and compute calendar boundaries in the home's timezone with `zoneinfo`. Do not use the conversation date as a live clock. Discover homes with the account tool. Default to the user's primary home at Kempenlaan 11, 1066PW Amsterdam, Netherlands; match the returned address, never assume the first home is primary. If it cannot be matched uniquely, ask the user. Get home details and use its timezone, defaulting to `Europe/Amsterdam` only for the confirmed Amsterdam home. Retain the verified home ID and timezone in the cache.
2. Read the existing cache with `read_file` if present. A missing file means an empty cache. Reject unsupported schemas or malformed data rather than silently overwriting it. Preserve unrelated homes. Load cached history before planning any history queries.
3. Calculate these local calendar ranges: this month from its first day to now; last month from its first day to this month's first day; this year from January 1 to now. Build a single union of required daily intervals so overlapping month and year requests are not duplicated. Account for January's previous-year last month. Compute timezone-aware boundaries, including daylight-saving changes, rather than assuming a day is always 24 hours.
4. Query only missing or provisional history, partitioning requests into at most 31 calendar days, and also obeying the API's elapsed-time limit across DST transitions. Set `type=consumption` and `resolution=DAILY` explicitly. Interpret response timestamps and returned structure from actual tool output. Filter observations into the desired half-open ranges `[start, end)` and deduplicate by home ID and interval start/end; API boundary semantics must not cause double counting. Inspect pagination/completeness indicators if returned. If data is missing or null, mark it unavailable, not zero.
5. Sum returned consumption `cost` fields with Python `Decimal`, preserving currency. Report what Tibber consumption cost represents; do not call it a final invoice or add guessed fixed charges, taxes, grid fees or credits. Separately show the latest included history timestamp. Month/year-to-date may exclude today or lag meter reporting; clearly state this. Never mix currencies. Calculate totals from daily records rather than adding overlapping month/year totals.
6. Fetch today's prices fresh with the prices tool. Select intervals by their timestamps in the home's local date, using the returned total electricity price per kWh and currency. Do not substitute the energy-only component when a total price is available. Find minimum and maximum with Python, not mental arithmetic. Preserve the API's actual interval resolution (hourly, quarter-hourly, etc.). Derive interval ends from the next timestamp or an explicit end/resolution; do not invent an hourly duration. Merge adjacent equally priced extreme intervals, and report every tied disjoint period. If a complete local day is unavailable, label extremes as covering only available prices. Include past periods: the default is the whole day, not only the remaining day. If the user requests a longer cheapest block, calculate a duration-weighted average over that duration and label it as a separate calculation.
7. Persist fetched history according to the cache rules below, then verify that cached records and coverage match actual MCP output. Render the report with local dates, timezone, currency and units, plus freshness and missing-data warnings.

## Cache format and policy

Store UTF-8 JSON in the file `~/.hera/tibber.data`, despite its `.data` extension. Use this schema:

    {"schema_version":1,"homes":{"HOME_ID":{"address":"...","timezone":"Europe/Amsterdam","currency":"EUR","history":{"INTERVAL_START":{"from":"...","to":"...","cost":"decimal string or null","consumption":"decimal string or null","currency":"EUR","fetched_at":"ISO timestamp","status":"complete or provisional"}},"coverage":[],"prices":{"local_date":"YYYY-MM-DD","fetched_at":"ISO timestamp","intervals":[]}}}}

Populate records only from real tool output. `coverage` contains confirmed fully populated ranges, not merely requested ranges. Cached prices are optional and must not replace a fresh price query by default.

- Reuse complete historical daily records indefinitely; do not query past covered intervals each time. Recompute totals locally. Never cache only aggregate totals: daily records allow reuse across year/month boundaries.
- Today and the previous two local days remain provisional, even when returned with costs. Requery them on subsequent runs to capture reporting delays. Older records become complete only when valid cost and interval fields exist and the interval has ended; missing/null records remain retryable. This stabilization policy is a heuristic, not an API guarantee. Explicit requests to refresh or reconcile historical bills override cache reuse.
- Do not mark empty responses, partial ranges, null costs or future days as covered. Never treat absence as zero. If older cached data is suspected stale, say so and offer an explicit refresh rather than secretly fetching all history.
- Store decimals as strings and timestamps with offsets; isolate all records by home ID. Keep raw interval identity for deduplication.
- Create the parent directory only as needed. Write atomically using a temporary sibling file and `os.replace` through Python, restricting the file to owner read/write where supported. Read and merge immediately before replacement to avoid losing existing data; use a lock for concurrent writers. Never put tokens or credentials in this cache. Use `write_file` for initial creation or an atomic Python merge for updates; obey existing-file read-before-write requirements.
- On malformed cache, preserve the original, report the problem and ask before resetting. On MCP failure, leave good cache intact and distinguish cached historical totals from unavailable live prices.

## Output

    Home: verified address — timezone
    This month (date range): currency amount — reported consumption cost
    Last month (date range): currency amount — reported consumption cost
    This year to date (date range): currency amount — reported consumption cost
    Today cheapest: local start–end, currency amount/kWh
    Today most expensive: local start–end, currency amount/kWh
    Data through: latest included history interval; today's prices fetched at timestamp
    Notes: missing/provisional data and any cached historical results

Round displayed monetary totals to currency precision and prices to sufficient precision to distinguish intervals; retain unrounded values for calculations. Do not report an incomplete subtotal as a complete monthly or yearly cost. Provide the available subtotal with the missing range explicitly identified.

## Pitfalls

The price per kWh and total consumption cost are different measures. Negative prices are valid. DST days may have repeated or absent local hours: include offsets when times are ambiguous. A price interval is not necessarily one hour. Month-to-date and year-to-date normally reflect reported history rather than real-time spend. Historical records can be revised by the provider, so an explicit refresh remains available.

## Verification

Before responding, confirm the primary home match, timezone-aware date boundaries, history request limits, no duplicated intervals, no fabricated zero costs, consistent currency, and minimum/maximum over all available intervals for today's local date. Calculate with Python. Validate the written JSON and that no credentials were stored. On a second run, complete covered historical intervals must cause no history queries; only missing/provisional records may be fetched. State any unverified or unavailable information plainly.
