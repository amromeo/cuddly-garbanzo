# Updates for an institutional repository with app.R at its root

Use `upstream/production/posit-connect-pilot-root`. This delivery branch has the same root layout as your institutional application: `app.R`, `R/`, `jobs/`, `sql/`, and `renv.lock` are directly at the top level. Do not merge the public nested-layout branch into this repository.

## One-time history alignment

Your original corporate commit was created from the downloaded archive, independently of the public Git history. The delivery branch includes an archive baseline with the original files. First link that baseline using an `ours` **strategy** merge, which records ancestry without changing any of your working files. Then perform a normal merge of the newer delivery branch to receive updates.

With a clean working tree on institutional `main`, and the public remote named `upstream`:

```sh
git branch backup/before-public-updates
git fetch upstream
git merge --allow-unrelated-histories -s ours 627c2113268f0120bdde575a8c587facaa304bd4 -m "Link original pilot archive history"
git merge --no-commit --no-ff upstream/production/posit-connect-pilot-root
```

The second merge applies the real updates; the first merge intentionally does not. Use the `ours` strategy only for that baseline alignment, not for future updates.

If the merge conflicts in `jobs/helix_direct.R`, preserve your committed institutional warehouse adapter:

```sh
git restore --source=HEAD --staged --worktree jobs/helix_direct.R
```

Inspect `git status` for any remaining conflicts, resolve them, and inspect the staged diff before committing:

```sh
git status
git diff --cached --stat
git diff --cached -- jobs/helix_direct.R sql/
git commit -m "Integrate public pilot updates"
```

The adapter/SQL diff should be empty if you preserved them unchanged. Do not commit while any other file still has conflict markers. If unsure, `git merge --abort` cancels the current update merge; the separate backup branch retains your original state.

Your private SQL file is not present in the public branch, so it is retained. If it is already committed in institutional GitHub, the new ignore rule does not untrack it.

Reload the updated R functions and validate your warehouse result:

```r
source("R/core.R")
source("R/sources.R")
source("jobs/helix_direct.R")
validated <- normalize_helix(read_helix_sql())
```

Run the automated checks and review the one-to-many entries in the local app. Push to institutional GitHub after validation:

```sh
git push origin main
```

## Future updates

Commit your institutional changes first. With a clean working tree:

```sh
git fetch upstream
git merge upstream/production/posit-connect-pilot-root
```

Resolve overlapping edits normally, test, regenerate the deployment manifests, and push `origin main`. Keep `upstream` push-disabled and `origin` pointed at corporate GitHub.

The deployment guide's `pilot/` working directory now means your repository root. Build staging directories inside your institutional repository (for example `connect-build/app` and `connect-build/source-job`) rather than copying files outside it. Preserve the SQL in the private source-job bundle as described in that guide.
