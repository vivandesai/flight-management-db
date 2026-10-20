# Free hosting options

Checked against provider documentation on 21 October 2026. These are recommendations, not deployed or cloud-verified environments. Free plans and availability can change.

The project is one Flask application: Jinja renders the frontend on the backend server, and Bootstrap assets are bundled locally. Host the whole app as a Python web service plus a MySQL database. A static-only website host is not sufficient for its forms and reports.

| Provider | Suitable use | Free-plan limits / tradeoffs |
| --- | --- | --- |
| [Render](https://render.com/docs/free) | Flask application, including frontend | Free web services sleep after 15 idle minutes, with 750 instance hours per workspace per month. Render's free managed database is PostgreSQL, so use an external MySQL service for this project. |
| [Aiven](https://aiven.io/free-mysql-database) | Managed MySQL database | Free MySQL includes 1 GB storage and 1 GB RAM without a credit card. Inactive services can be powered off after notification. |
| [Oracle Cloud Always Free](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm) | A VM hosting the app and your own MySQL server | More setup and server maintenance; signup normally requires a card. Always Free resources have limits, regional capacity constraints and possible idle-instance reclamation. Select explicitly eligible resources rather than temporary paid trial resources. |

**Suggested starting combination: Render for Flask and Aiven for MySQL.** These fit the current stack without migrating SQL to a different database engine. No cloud instance has been provisioned or charged as part of this recommendation.

## Project-specific requirements before deployment

1. Preserve SQL case compatibility. The original trigger script refers to `airline` while the table is declared `Airline`. Aiven's [advanced MySQL parameters](https://aiven.io/docs/products/mysql/reference/advanced-params) support `mysql.lower_case_table_names=1`, which must be chosen **when creating the service** and cannot be changed afterward. Ensure this is available on the selected free service before importing the unchanged scripts. A self-managed MySQL server can likewise be initialized with case-insensitive table handling.
2. Use the hosting platform's public HTTP binding and assigned port. The current `python run.py` intentionally listens only on `127.0.0.1` for local use. For Render, the existing Waitress dependency can be started with `waitress-serve --listen=0.0.0.0:$PORT run:app`; see [Render's port-binding requirements](https://render.com/docs/web-services#port-binding). Do not change the local default merely to research hosting.
3. Configure database TLS with the provider's CA certificate and certificate verification. The current connection helper does not expose provider-specific TLS/CA configuration through `.env`; add that configuration before using a cloud database. Store credentials and a stable SECRET_KEY as provider environment secrets.
4. Protect write access before publishing. The app currently has no login, by design for local use. Public visitors would otherwise be able to use DBA edits/deletions, management forms and fixed transaction demos. Add authentication or a hosting access gate covering those operations before making a public deployment.
5. Initialize deliberately using the original scripts in documented order and then install the views. Verify all twelve triggers and seven views on the cloud database, along with account privileges; never initialize or reseed on web-service startup.

The original SQL files need no edits for these requirements. Hosting preparation belongs in server configuration and the application deployment layer.

[PythonAnywhere's current free accounts](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/) are a poor fit for a new deployment of this project: new free accounts no longer include MySQL, and free accounts have restricted outbound access. Its [database guide](https://help.pythonanywhere.com/pages/KindsOfDatabases/) explains external database restrictions.
