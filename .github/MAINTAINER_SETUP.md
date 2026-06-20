# Maintainer Setup

Use this file for one-time GitHub and repository administration. It is for
repository maintainers, not for ordinary local contributor bootstrap. Use
[SETUP.md](../SETUP.md) for local environment setup and
[CONTRIBUTING.md](../CONTRIBUTING.md) for the normal development workflow.

This playbook was rechecked against GitHub Docs on May 13, 2026. It matches
this repository's current release flow: `dev` is the default integration
branch, `main` is the protected release branch, and GitHub Actions uses
`PAT_TOKEN` when configured, otherwise `github.token`, to publish the release
bump commit, tag, and GitHub Release. Strict starter-template sync requires
`PAT_TOKEN`. CI uses `PY_LIB_PRIVATE_GIT_TOKEN` when private shared py-lib package sources must be read. Renovate runs through the hosted GitHub App.

## Target state

- `dev` is the default branch and normal PR target.
- `main` is the protected release branch.
- Pull requests targeting `main` must come from the same repository's `dev` branch.
- Full CI runs on `dev` pushes and on pull requests targeting `dev` or `main`.
- A push to `main` runs Release only, not full CI.
- The release workflow bumps version and changelog, pushes the bump commit and
  tag, creates the GitHub Release, and synchronizes `dev` to the final `main`
  commit.
- The `Sync Starter Template` workflow accepts starter release dispatches,
  updates template-owned files on `dev`, and creates or reuses the `dev` ->
  `main` PR.
- CI can resolve private Git sources for shared py-lib packages, and Renovate is installed for dependency update PRs.

## 1. Set the default branch

On GitHub, open the repository and go to `Settings -> Branches -> Default branch`, then set the default branch to `dev`.

Keep `main` non-default so ordinary work lands on `dev`.

## 2. Create the release token

Prefer a fine-grained personal access token once branch protection is enabled.
For an unprotected bootstrap repository, the workflow can run with
`github.token`.

On GitHub, go to `Profile -> Settings -> Developer settings -> Personal access tokens -> Fine-grained tokens -> Generate new token`, then use:

- Resource owner: the owner of this repository
- Repository access: `Only select repositories` -> this repository plus
  `py-lib-starter` when it is private
- Repository permissions:
  - `Contents: Read and write`
  - `Pull requests: Read and write`
  - `Workflows: Read and write`
- Expiration: use a finite lifetime unless policy requires something else

If the organization requires approval for fine-grained tokens, wait until the
token is approved before using it.

The current workflow does not use a GitHub App. A PAT can only do what its
owner can already do, so the token owner must already have the repository
access needed to push the release bump commit, push tags, create releases, push
starter-template sync commits to `dev`, and let `PAT_TOKEN` create or reuse
sync PRs. The workflow permission is required because starter-template syncs
can legitimately update files under `.github/workflows/`.

## 3. Store `PAT_TOKEN`

On GitHub, go to `Settings -> Secrets and variables -> Actions -> New repository secret`, then create:

- Name: `PAT_TOKEN`
- Value: the fine-grained token created above

Keep GitHub Actions enabled for the repository. The expected workflows are
`ci.yml`, `release.yml`, `sync-starter-template.yml`, and the optional manual
`build-ci-image.yml`.

If `PAT_TOKEN` is not set, the release workflow falls back to `github.token`.
Use `PAT_TOKEN` when protected branch rules require a token owner with an
explicit bypass path.

The `Sync Starter Template` workflow intentionally requires `PAT_TOKEN`. Do not
replace it with `github.token`: sync commits must trigger CI immediately after
the starter repository dispatches an update, and repository settings can block
the default token from creating pull requests.

## 4. Store `PY_LIB_PRIVATE_GIT_TOKEN` For Private Shared Packages

Generated repositories depend on shared py-lib packages from the private
`py-lib-starter` Git repository. Store the read token as an Actions secret when CI or template sync must read private shared package sources. Renovate runs through the hosted GitHub App and does not use Dependabot secrets.

Create a fine-grained token with read-only `Contents` access to
`py-lib-starter`. For one repository, go to `Settings -> Secrets and variables -> Actions -> New repository secret`. For a fleet, prefer organization secrets shared with the selected generated repositories. Create:

- Name: `PY_LIB_PRIVATE_GIT_TOKEN`
- Value: the read-only token

The generated CI workflow uses this token before falling back to `PAT_TOKEN` or `github.token`. The generated `renovate.json5` is handled by the hosted Renovate GitHub App. If private Git dependency resolution fails despite the app being installed on both repositories, switch only the runner to self-hosted Renovate with a GitHub token that can read `py-lib-starter` and write PRs to targets.

## 5. Protect `main`

Prefer `Settings -> Rules -> Rulesets -> New branch ruleset` and target
`main`.

Keep these rules enabled:

- require a pull request before merging
- require status checks before merging
- require branches to be up to date before merging
- require only the `ci/merge-gate` status
- allow only squash merges into `main`
- block force pushes
- block branch deletion
- do not enable merge queue

Keep the release path compatible with the `PAT_TOKEN` owner. If your ruleset
would block the workflow's push back to `main`, either give the token owner a
valid bypass path through the ruleset model or move the release automation to a
GitHub App.

If you also protect `dev`, do not break the documented contributor flow in
[CONTRIBUTING.md](../CONTRIBUTING.md), which relies on local fast-forward merges
back into `dev`. The release workflow may also need to move `dev` to `main`
with an exact force-with-lease after a rebase merge that produced the same
patch with different commit SHAs. Either leave `dev` unprotected or give the
automation token a narrow bypass for that update.

## 6. Configure required checks

Required checks should use the stable merge-gate context from
[`workflows/ci.yml`](workflows/ci.yml):

- `ci/merge-gate`

The merge gate checks the individual CI jobs internally, so branch protection
does not need to change when the workflow splits or renames implementation
jobs.

## 7. Verify the setup

Check the full path once after setup:

1. Confirm `dev` is the default branch.
2. Open a same-repository `dev` -> `main` PR and confirm the single required `ci/merge-gate` check is enforced against the PR test-merge tree.
3. Squash-merge the `dev` -> `main` PR, confirm no full CI push run starts on `main`, and confirm the `Release` workflow starts.
4. Confirm the workflow can:
   - run `cz bump --changelog --yes`
   - push the bump commit to `main`
   - push the tag
   - create the GitHub Release
   - synchronize `dev` to `main`, or create `dev` from `main` during initial
     bootstrap
   - accept tree-equivalent squash merges with an exact lease
   - refuse to move `dev` if it contains real commits not represented on
     `main`
5. From the starter repository or the manual workflow button, confirm
   `Sync Starter Template` can:
   - run `uv run py-lib-template-update`
   - run `uv run py-lib-template-check`
   - push a sync commit to `dev`
   - create or reuse the `dev` -> `main` PR
6. Trigger or wait for a Renovate run, confirm the Dependency Dashboard appears, and close stale Dependabot PRs after the first successful Renovate run.

If `dev` has real commits missing from `main`, or its final tree does not match
the squashed `main` content, the final synchronization step fails by design.
