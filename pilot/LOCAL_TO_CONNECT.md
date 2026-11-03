# Local development → institutional Git → Posit Connect

This workflow is supported. Start from the supplied source archive: the `production/posit-connect-pilot` branch was committed in the cloud workspace, but has not been pushed to the public GitHub repository. Extract the archive and copy `pilot/` into your institutional repository. Keep development content and pins separate from any existing live app.

## 1. Restore locally

Use the R version in `renv.lock` (currently 4.5.3), or update the lock and rerun the checks on your institution's supported version. From `pilot/`, in R:

```r
install.packages("renv") # if needed
renv::restore(prompt = FALSE)
renv::load()
```

Install the DBI driver/authentication packages approved for your warehouse into this project library. After changing the adapter, update the lockfile with `renv::snapshot(type = "all", prompt = FALSE)`. Connect must be able to install those package versions and access any required system driver or DSN.

## 2. Replace the warehouse adapter

Edit `jobs/helix_direct.R`. Keep its function named `read_helix_sql()` so the existing source job can call it. Replace the `rocqi` calls with your institution's connection/query code, reading connection settings from `Sys.getenv()` and closing the connection even on errors. Use a read-only warehouse identity.

The function must return a data frame with these exact columns:

- `Procedure ID`: unique Epic procedure identity.
- `Test Menu Links`: link containing `/Tests/<numeric OLSD ID>`.
- `Procedure Display Name`: proposed name.
- `Authorized Lab Sections`: semicolon-separated section identifiers used by the shared mappings.

Alias your warehouse result columns to these names. Keep the actual query in the institutional repository or a provisioned file. Records with no OLSD link are excluded and retained for inspection; duplicate identities or multiple OLSD links fail validation. If your warehouse cannot provide that link, implement and validate an explicit identity crosswalk rather than matching by test name.

Leave `OLSD_HELIX_PIN` unset/empty for direct warehouse access; a nonempty value takes precedence over the adapter. Existing `HELIX` names are configuration labels and do not require the database to be Helix. Put your query in `pilot/sql/warehouse_catalog.sql`. The adapter reads that path relative to the project root; no SQL-path environment variable is needed.

The alternative CLI uploader, `scripts/deploy.R`, contains a `rocqi` dependency check for the original direct adapter. If you use that uploader, update its check for your warehouse driver. The Git/manifest route below does not invoke that script.

## 3. Configure local credentials and test

Store development credentials in your user-level `~/.Renviron`, an institutional secret manager, or your shell environment. Choose the exact variable names in your adapter, for example `WAREHOUSE_USER` and `WAREHOUSE_PASSWORD`. Restart R after changing `.Renviron`. Do not commit that file, credentials, real snapshots, generated Excel files, or local pin data.

For local tests, leave `CONNECT_SERVER`, `CONNECT_API_KEY`, `POSIT_PRODUCT`, and `RSTUDIO_PRODUCT` unset, and set:

```r
Sys.setenv(OLSD_BACKEND = "folder", OLSD_DATA_DIR = "/path/to/private/local-pins")
```

Test the connection and output contract before publishing a source snapshot:

```r
source("R/core.R")
source("R/sources.R")
source("jobs/helix_direct.R")
validated <- normalize_helix(read_helix_sql())
stopifnot(nrow(validated$rows) > 0)
```

Inspect IDs, names, sections, and excluded rows against known tests. Do not print connection objects or passwords into shared logs. Then run the source job against local folder pins:

```r
source("source_job.R")
shiny::runApp(".")
```

In the app, upload an OLSD export, review its preview, accept it, and configure the lab mappings. Test review/save/approve/download using development data. Run automated checks:

```sh
Rscript -e 'renv::load();source("tests/run.R")'
OLSD_USE_RENV=true python tests/run_browser.py
```

The browser checks require Python Playwright, Chromium, and openpyxl. They create an isolated synthetic app and do not query the warehouse. Passing them does not validate the real connection.

## 4. Build two manifest directories

A Connect content item has one entry point. Stage the Shiny app and scheduled R job into separate directories in your institutional repository, then create one manifest in each. From `pilot/` in R, after restoring and loading renv:

```r
app <- "../connect-build/app"
job <- "../connect-build/source-job"
stopifnot(!dir.exists(app), !dir.exists(job)) # use fresh directories each build
for (dest in c(app, job)) {
  dir.create(dest, recursive = TRUE)
  stopifnot(file.copy("renv.lock", dest))
  stopifnot(file.copy("R", dest, recursive = TRUE))
}
stopifnot(file.copy("app.R", app))
stopifnot(file.copy("www", app, recursive = TRUE))
dir.create(file.path(job, "jobs"))
stopifnot(file.copy("source_job.R", job))
stopifnot(all(file.copy(c("jobs/refresh_epic.R", "jobs/helix_direct.R"),
                       file.path(job, "jobs"))))
dir.create(file.path(job, "sql"))
stopifnot(file.copy("sql/warehouse_catalog.sql", file.path(job, "sql")))
rsconnect::writeManifest(appDir = app, appPrimaryDoc = "app.R", appMode = "shiny")
rsconnect::writeManifest(appDir = job, appPrimaryDoc = "source_job.R", appMode = "r")
```

The allowlist deliberately omits `.Renviron`, local pins, real data, tests, and credentials. Inspect both generated directories and manifests before committing. Commit their code/assets, `manifest.json`, and `renv.lock` alongside the maintained `pilot/` source. Regenerate both build directories/manifests after source or dependency changes. Archive or remove the previous generated directories before rebuilding; do not reuse stale files.

## 5. Deploy from institutional Git

If your Connect installation enables Git-backed deployment and can access the institutional Git host, create two private content items from the same branch:

| Content | Repository subdirectory | Entry point |
|---|---|---|
| Development app | `connect-build/app` | `app.R` |
| Development nightly source job | `connect-build/source-job` | `source_job.R` |

Use your Connect administrator's deployment method if Git-backed deployment is unavailable. A local Git push does not automatically redeploy unless that integration/polling is configured; verify the deployed commit/build in Connect. Confirm the content stays restricted before enabling real data.

## 6. Configure runtime variables in Connect

Local environment variables are not carried into a Git deployment. Configure them separately on each Connect content item before running it.

**Both items:** `OLSD_BACKEND=connect`, `CONNECT_SERVER`, `CONNECT_API_KEY`, and the same environment-specific `OLSD_EPIC_PIN`. Use the institutional approved secret mechanism. Service identities must have the relevant pin access; the database credentials and the Connect API key serve different purposes.

**Source job only:** your warehouse credential variables and an empty/unset `OLSD_HELIX_PIN`. The job needs warehouse network access, installed drivers/DSNs, warehouse permissions, and source/status pin write access. Run it once manually and inspect the published rows and status before scheduling it nightly (for example, 5:00 AM America/New_York).

**App only:** a new `OLSD_STATE_PIN`, `OLSD_WRITER_USER`, `OLSD_ADMIN_USERS`, and initially `OLSD_INITIALIZE=true`. The app needs source pin read access and state/snapshot/export pin read/write access. It does not need warehouse credentials when reading the job's source pin.

Have administrators enforce one application process and one replica before setting `OLSD_SINGLE_PROCESS_CONFIRMED=true`. The environment variable is an acknowledgement, not a server scaling control. Only the designated operator can write, even when another user is an administrator.

Open the app and complete the first durable save, then disable `OLSD_INITIALIZE` so a missing pin becomes an error. If migrating existing editorial content, follow `DEPLOYMENT.md` instead of initializing over an existing pin. Validate authenticated identity, a second session's write block, restart persistence, and a supervised Excel import/reconciliation cycle before expanding the pilot.

Deploy the pilot as separate content with separate pins after development acceptance. Never put database passwords or Connect API keys in `manifest.json`: manifests describe code/dependencies, not runtime secrets.
