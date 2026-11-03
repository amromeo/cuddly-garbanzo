# Pull public updates; push institutional changes

Use one local working copy with two remotes:

- `upstream`: public source code maintained by the assistant.
- `origin`: your institutional repository, including institution-specific code and SQL.

Keep your warehouse adapter and SQL committed on the institutional branch. Git merges public changes into those commits; do not replace the whole folder with a new ZIP after setting this up.

## One-time setup

First run `git remote -v` in your existing local working copy.

If `origin` currently points to the public `amromeo/cuddly-garbanzo` repository:

```sh
git remote rename origin upstream
git remote add origin YOUR_INSTITUTIONAL_REPOSITORY_URL
```

If `origin` already points to your institutional repository, keep it and add the public remote:

```sh
git remote add upstream https://github.com/amromeo/cuddly-garbanzo.git
```

Then configure pushes to go to institutional GitHub:

```sh
git remote set-url --push upstream DISABLED
git config remote.pushDefault origin
git config push.default simple
```

`DISABLED` intentionally makes a push through `upstream` fail. You can still fetch or pull from it. Keep this setting on your workstation; it is not stored in the repository's committed files.

The simplest starting history is a clone of the public pilot branch. If you downloaded a ZIP and created an unrelated institutional repository, do not force an unrelated-history merge. Instead, clone the public pilot branch into a new folder, configure the two remotes there, and copy your institutional changes into that working copy. If your institutional repository already has history that must be preserved, agree on the initial history integration before replacing any branch.

## Commit institutional files privately

The public repository ignores `*.sql` and `.Renviron` files. Ignored files remain on disk when you pull updates. Because the public repository does not track your SQL filename, public merges will not replace it.

For Git-backed Connect deployment, the institutional repository must contain the SQL query (or Connect must provision it separately). After verifying `origin` is your institutional repository, explicitly track the query there:

```sh
git add -f pilot/sql/warehouse_catalog.sql
git add pilot/jobs/helix_direct.R pilot/renv.lock
git commit -m "Configure institutional warehouse source"
git push -u origin YOUR_WORKING_BRANCH
```

Use your actual working branch name; it can be `production/posit-connect-pilot` if you kept that branch. Do not commit credentials. Configure local credentials through your user-level `.Renviron` or secret manager, and runtime credentials through Connect settings.

Once SQL is tracked in your institutional branch, Git continues tracking it despite the public ignore rule. `.gitignore` prevents accidental additions; it does not prevent publishing a tracked private file. Keep the public remote push-disabled.

## Each update cycle

Save and commit your institutional changes first, so the working tree is clean. Then:

```sh
git fetch upstream
git merge upstream/production/posit-connect-pilot
```

Equivalently, `git pull --no-rebase upstream production/posit-connect-pilot` fetches and merges in one command. Your private SQL stays on your branch. If both sides changed the warehouse adapter, Git may ask you to resolve a merge conflict: preserve your warehouse connection and incorporate the relevant upstream changes. Do not blindly choose one whole file.

Run the R and browser checks, plus a real read-only warehouse query. Rebuild both deployment directories and manifests using `LOCAL_TO_CONNECT.md`. The ignore rule also covers SQL copied into generated deployment directories, so explicitly include the source job's SQL in the institutional commit:

```sh
git add pilot connect-build
git add -f connect-build/source-job/sql/warehouse_catalog.sql
git commit -m "Integrate upstream changes and refresh deployment bundles"
git push origin YOUR_WORKING_BRANCH
```

Connect pulls from the institutional branch and the appropriate `connect-build` subdirectory. Trigger or verify redeployment according to your installation's Git deployment configuration, then test there. Public source code updates do not automatically change the institutional repository or Connect deployment.
