# Agent Notes for buildkit Repository

## GitHub Actions Preferences
- Workflows should use a `build-release` concurrency group to cancel in-progress runs when a new build starts.
- Build wheels on `ubuntu-latest` for Python 3.12 and 3.13 using a virtual environment per job.
- Package all produced wheels into a single zip artifact for easy download.
- Publish every successful build to the `latest` GitHub Release, attaching both the individual wheel files and the bundled zip.
- Keep workflow triggers limited to pushes on `main`, semantic version tags (`v*.*.*`), and manual dispatches.
- Ensure workflows request `contents: write` permissions so release uploads succeed.
- Prefer the newest stable `uses:` versions for GitHub-maintained actions in workflows.
