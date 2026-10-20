# Interface verification

## Integrated view navigation — 21 October 2026

- Full regression suite: **131 passed in 68.95 seconds**, against the isolated MySQL 8.4.13 test server.
- All seven views appear in the same card grid and search as the 54 original reports, under their relevant business categories. All reports contains 61 entries; there is no SQL views sidebar item or separate listing page.
- View details retain live SELECT results and source definitions, highlight the correct category, and link back to that category. Existing `/views` bookmarks redirect to All reports; all seven direct view URLs remain valid.
- Tests check category membership, combined counts, all 61 link targets, V1–V7/database-name search, view-only results, empty searches, legacy navigation, and missing-view guidance without blocking original features.
- Desktop 1366 × 900 and mobile 390 × 844 browser checks passed for category cards, opening a view, returning to its category and shared search. Mobile page width matches client width; temporary viewport overrides were reset.
- No SQL file or hash-manifest changes were made. Hosting recommendations were researched from official provider documentation and recorded separately; no cloud deployment or account creation was performed.

## DBA panel and seven views — 20 October 2026

Verified against a newly provisioned, isolated Windows MySQL Community Server **8.4.13**, bound to `127.0.0.1:33317`, with the required disposable-server marker. No existing user database was used or reset.

- Final complete regression run: **129 passed in 56.45 seconds**. The 98 existing checks still pass; 31 additional checks cover the new catalogues, DBA workflows and views.
- All seven entity updates persist and preserve immutable relationships. Invalid dates/email, duplicate codes/passports/seats, invalid fares, baggage limits and capacity reductions are rejected without stored changes.
- Concurrent edits from the same original snapshot produce exactly one successful commit; the other is rejected as stale. Tampered, cross-record, wrong-operation and expired row tokens are rejected.
- Individual deletion succeeds for each of the seven entities after dependencies are removed separately. Referenced records remain blocked. Booking creation/cancellation audits survive deletion of their original booking.
- Flight edits reject invalid timing and aircraft overlap; the original arrived-status lock and status-only edits to past flights work as intended.
- All seven installed views execute with INVOKER security. Checks verify seed totals, zero-activity rows, one row per booking, correct revenue/baggage aggregates and immediate edit/deletion results.
- Missing-view screens show setup instructions without creating objects or blocking original reports. Repeated `install-views` preserves base rows, including after a partial installation.
- Browser verification at desktop 1366 × 900 and mobile 390 × 844 covered DBA lists, edit forms, blocked-deletion previews, view cards and view-definition disclosure. A browser-submitted airline edit appeared immediately in the airline-performance view. No browser warnings/errors were logged; mobile page width matched client width.
- Dependency checks and Python compilation passed. All eight original SQL blobs and the existing hash manifest remain unchanged. The newer upstream README commit was incorporated before adding documentation.
- The disposable database finished with the original seed: 29 bookings, fare total 271,300.00, and seven installed views. Temporary browser viewport overrides were reset.

See [DBA and views setup and walkthrough](dba-and-views.md).

## Original implementation — 7 October 2026

Verified on 7 October 2026 using Python 3.13.15 and a separate Windows MySQL Community Server 8.4.9 instance bound to localhost on port 33317. The test server was created under the local temporary directory, outside the repository. The app itself requires only Python and an existing MySQL installation.

## Results

- Full initial test suite: **96 passed in 41.52 seconds**.
- Final focused checks after adding HTTP workflow/evidence cases: **5 passed in 9.58 seconds**. These include two new tests; the final suite contains 98 distinct tests.
- All 54 report statements execute against the unchanged seeded database; every report page renders.
- All 10 original transaction examples execute separately on fresh fixtures. Checks verify commits, full rollback, savepoint rollback, trigger rejection, retained pre-transaction cancellation and audit effects.
- All 12 trigger demos preserve stored rows after rollback and show real rule errors or audit rows.
- Management workflows pass through both direct adapters and HTTP forms; failed baggage/rebooking operations restore data and audit rows.
- Initialization refuses an existing database; missing triggers produce setup guidance; unavailable MySQL produces a connection page.
- `pip check`: no broken requirements. Python source compilation passes.

## Browser checks

- Desktop dashboard inspected at a 1366 × 900 viewport.
- Mobile dashboard inspected at a 390 × 844 viewport; page scroll width equals its client width. Wide result tables scroll inside their own containers.
- Report catalogue search narrows to the requested report.
- Mumbai → Delhi on 5 October 2026 returns Flight 1 through the browser form.
- Booking submitted through the browser creates its optional baggage and the AFTER INSERT audit record. Audit evidence shows passenger 15, Flight 7, seat 45A and fare 9,000.00.
- Final inspected page has no browser error or warning logs.
- Temporary viewport overrides were reset after testing. The disposable database was returned to the original seed after tests.

## SQL preservation

Original repository baseline: `12d62b3fd57e0a4fa3cff16774d6ac585ff171f1`.

All eight original SQL files have zero Git diff against that baseline. The content manifest in `tests/sql-hashes.json` verifies SHA-256 hashes, allowing only operating-system checkout line endings. No original statement, table, trigger, transaction, literal or sample date was edited.

See [setup and test instructions](interface.md) for reproducing the checks on a separate disposable MySQL server.

## Visual refresh

The interface now uses charcoal, warm cream and burnt orange, with local SVG icons, a compact flight board, clearer status badges and consistent report cards and forms. Styling assets remain bundled locally.

- Read-only rendering checks passed for **99 pages**, including all 54 reports with valid inputs, all management forms, transaction and trigger pages, and record views.
- Browser checks covered report search, the Mumbai-to-Delhi flight filter, original SQL disclosure, booking form and database demonstrations.
- Dashboard and booking form were inspected at desktop and mobile sizes; mobile page width matches client width and wide tables remain inside scroll containers.
- Catalogue and original SQL hash checks passed. Python backend files and original SQL files have no changes in this refresh.
- No database writes were made during this visual verification.
