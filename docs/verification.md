# Interface verification

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
