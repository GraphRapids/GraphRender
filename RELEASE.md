# Release Process

This project uses semantic versioning (`MAJOR.MINOR.PATCH`).

## 1. Prepare Release Branch/PR

1. Ensure `main` is green (CI, tests, gitleaks).
2. Update `CHANGELOG.md`:
   - Move entries from `[Unreleased]` to a new version section.
   - Add the release date.
3. Update version in `pyproject.toml`.
4. Open a PR and get approval.

## 2. Tag and Publish

After merge to `main`:

```bash
git checkout main
git pull --ff-only
git tag vX.Y.Z
git push origin vX.Y.Z
```

Create a GitHub Release from tag `vX.Y.Z` and include changelog highlights.

## 3. Post-Release

1. Add a new empty `[Unreleased]` section at the top of `CHANGELOG.md`.
2. Verify package/build artifacts if distribution is planned.
3. Announce release notes.
