# Institutional deployment and operating runbook

## Prerequisites and release gate

1. Have Connect administrators confirm R 4.5.3 is supported, or rebuild the lockfile and rerun both test suites on the approved R version. The lock records the locally tested public dependencies. The default source-job bundle reads an existing Helix pin. To include direct SQL access, set `OLSD_INCLUDE_HELIX_ADAPTER=true` when deploying, install the institution-approved `rocqi` package and record its approved version in the deployment lockfile; no institutional package or SQL is bundled here.
2. Create **separate development and pilot content**, each with distinct state, source, snapshot, and export pin namespaces. Restrict application and pin visibility to the catalog team. Keep the existing application/state pin intact during migration.
3. Configure exactly one application process and one replica. Disable scaling to additional workers and overlapping write-capable deployments. A local process lock catches extra workers on the same host, but cannot coordinate different hosts. If Connect cannot enforce this topology, keep writes disabled and use transactional storage before launch.
4. Select a designated operator, and configure admin identities separately. Only that operator can make changes, including an administrator acting as operator. Other authenticated users can view. A second browser session cannot write until the first session closes; network disconnect cleanup may take the Shiny session timeout.
5. Validate all source columns, identifiers, section delimiters, lab mappings, category identities, and vendor control columns against actual examples. The adapter expects semicolon-separated Epic sections. Ambiguous OLSD links and duplicate identities fail validation; unlinked Epic rows are retained in the source's excluded table.
6. Validate the importer’s treatment of `Test Managed By`, `Use ARUP Test Name`, blank `ARUP Test Number`, required Test Name, and category append behavior in the vendor test process. Values are read from the snapshot, not hard-coded. No real imports are automated.

Do not enable production writes merely because local checks pass. Connect identity, permission boundaries, deployment topology, service-account write access, and a supervised vendor import are acceptance gates.

## Configuration

Set these in Connect's environment settings, not an uploaded `.Renviron`:

| Variable | Purpose |
|---|---|
| `OLSD_BACKEND=connect` | Require Connect pins; no local fallback. |
| `CONNECT_SERVER` / `CONNECT_API_KEY` | Standard `pins::board_connect(auth="envvar")` configuration. Use an institutional service identity and restricted secret settings. |
| `OLSD_STATE_PIN` | A new, environment-specific catalog-state pin name. Do not point at the legacy state. |
| `OLSD_EPIC_PIN` | Environment-specific validated Epic source pin. |
| `OLSD_WRITER_USER` | Exact authenticated Connect username of the one pilot operator. |
| `OLSD_ADMIN_USERS` | Comma-separated exact admin usernames. |
| `OLSD_SINGLE_PROCESS_CONFIRMED=true` | Set only after an administrator verifies the topology above. Otherwise writes are disabled. |
| `OLSD_INITIALIZE=true` | Bootstrap an empty new state pin only. Turn off after the first durable save or candidate import. Missing state then becomes an error. |
| `OLSD_HELIX_PIN` | Source job: existing institution-provided raw Helix report pin. |
| `OLSD_HELIX_SQL` | Alternative source job input: institution-provided SQL file path. Used only when no upstream pin is configured. |

The app identity needs read access to the source pin and read/write access to its state, uploaded snapshots, and exported artifact pins. The nightly job identity needs upstream read access and source/status pin write access; it does not need editorial state write access. Do not share development and pilot write credentials unnecessarily.

Register the institutional account with `rsconnect` through your approved process. Set `OLSD_CONNECT_SERVER_NAME` and `OLSD_CONNECT_ACCOUNT` to the registered names, then from `pilot/`:

```sh
Rscript scripts/deploy.R development app
Rscript scripts/deploy.R development source-job
```

Initially keep the content private and writes disabled. Configure environment variables and access in Connect. Schedule the source job nightly in the institution’s chosen time zone, with job-failure notifications to the catalog administrator. The app checks source availability every minute while running and flags sources more than 30 hours old. A failed job preserves the last successful source; it writes a separate failure status and exits unsuccessfully.

Run `Rscript scripts/preflight.R` in the configured deployment environment. It validates dependencies and read contracts without making changes. Execute an authorized synthetic save to verify write access and persistence. Repeat deployment with `pilot` only after development acceptance; do not reuse development pins.

## Initialize or migrate

For a fresh start, an administrator previews and accepts the current OLSD export, configures shared mappings, and applies the validated Epic source. No sample records are automatically installed.

For existing real editorial content:

1. Export a restricted backup of the old state pin using the old app's approved tooling. Keep that source backup unchanged.
2. Run `Rscript scripts/migrate_preview.R legacy-backup.rds /restricted/migration-review`. Inspect `review.csv` and `candidate.rds`. Resolve unsupported schemas, duplicate mappings, and unknown categories rather than guessing.
3. While the **new** pilot app is stopped, run `Rscript scripts/import_candidate.R /restricted/migration-review/candidate.rds --app-stopped` against the new empty state pin. The importer refuses a nonempty target.
4. Start the pilot, upload a fresh OLSD snapshot, apply the real Epic source, and review preserved wording. Enabled editorial values become pending changes; disabled fields and old decisions/approvals/exports remain in `legacy_archive`. None of the old approvals authorize new files.

## Acceptance and pilot operation

Use a small agreed lab/test set. Verify correct and ambiguous identity matches, deliberate wording differences, unmapped sections, multi-field tests, group decisions, notes, deferral, approval withdrawal, and per-file confirmation. Confirm that one mismatching test does not return matching peers to review.

Test two browser sessions and two tabs. Only one session may write. Test a stale state revision and a write failure: the UI must retain unsaved choices and must not claim success. Close the writer session and confirm that another operator session can take control.

Restart and redeploy the app. Saved choices, approvals, export history, and source references must remain. Confirm that the nightly job cannot modify editorial state and that a failed refresh leaves the previous successful source available.

For the first real update, compare the approved workbook with the vendor-required template, import it manually through the existing controlled process, upload a new OLSD export, and inspect each test's result. Matching observations are dated confirmations, not proof of real-time publication.

Review Connect job errors and app error logs daily during the pilot. Monitor the displayed source date, failed-save reports, unresolved mappings, and unconfirmed exports. The administrator owns alerts and the operator owns reconciliation of downloaded files.

## Backup, restore, and rollback

Versioned pins retain historical state. Also create restricted independent backups with `Rscript scripts/backup.R /restricted/backup.rds`; include source and artifact pin retention in the institution's backup policy. Test restoration in development before the first real import.

To restore, stop the app, preserve a backup of its current state, and run `Rscript scripts/restore.R /restricted/backup.rds --app-stopped`. This validates schema, creates a new revision, and records the restore in history. Restoring a state cannot retract an Excel file already downloaded or imported: reconcile affected exports and fresh OLSD observations before resuming writes.

For a failed release, disable writes, retain the current pin versions, and redeploy the previous compatible application bundle. Do not roll back to an older schema reader against a newer incompatible state. Keep the public static prototype available as a reference; it has no authority over real state.
