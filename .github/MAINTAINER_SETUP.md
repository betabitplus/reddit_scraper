# Maintainer Setup

Use this file for one-time GitHub and repository administration. It is for
repository maintainers, not for ordinary local contributor bootstrap. Use
[SETUP.md](../SETUP.md) for local environment setup and
[CONTRIBUTING.md](../CONTRIBUTING.md) for the normal development workflow.

This repository uses `betabitplus-py-lib-automation` for release writes,
starter-template synchronization, pull-request automation, and private shared
Git reads. Normal repository-local read-only CI continues to use
`GITHUB_TOKEN`.

## Target state

- `dev` is the default branch and normal PR target.
- `main` is the protected release branch.
- Pull requests targeting `main` must come from this repository's `dev` branch.
- Full CI runs on `dev` pushes and on pull requests targeting `dev` or `main`.
- Release and template-sync commits are attributed to the App bot identity.
- The same workflow and credential names work while this repository or
  `py-lib-starter` is public or private.

## 1. Set the default branch

Set `dev` as the default branch in `Settings -> Branches -> Default branch`.

## 2. Install the automation App

Install the GitHub App `betabitplus-py-lib-automation` on this repository and
keep it installed across visibility changes. Confirm these repository
permissions are approved:

- `Contents: Read and write`
- `Pull requests: Read and write`
- `Workflows: Read and write`

`All repositories` makes the GitHub App installation available to a new
repository, but it does not create repository Actions variables or secrets and
does not register the repository in the managed py-lib fleet. Before enabling
fleet workflows for a new managed repository, register it in the fleet manifest
and run the onboarding helper from `py-lib-starter`:

```bash
scripts/platform/onboard_github_app_repository.sh \
    betabitplus/new_repo \
    "$HOME/.config/py-lib-platform/github-app.pem"
```

The authoritative fleet runbook is:

```text
https://github.com/betabitplus/py-lib-starter/blob/dev/docs/platform-ops/github-app-automation-guide.md
```

## 3. Store App credentials

Expose these Actions values:

```text
Variable: PY_LIB_AUTOMATION_APP_ID      numeric App ID used for ruleset bypass
Variable: PY_LIB_AUTOMATION_CLIENT_ID   Client ID used by actions/create-github-app-token
Secret:   PY_LIB_AUTOMATION_PRIVATE_KEY private-key secret used by actions/create-github-app-token
```

Keep both variables. The App ID remains numeric for ruleset bypass; workflows use the Client ID to create installation tokens. Store the full current private-key PEM as the secret. Never commit it.

## 4. Protect `main`

Keep the existing human path unchanged:

- require pull requests into `main`
- require branches to be up to date
- require only `ci/merge-gate`
- allow squash merging only
- block force pushes and deletion
- do not enable merge queue

Add only `betabitplus-py-lib-automation` to the bypass list where the existing
release flow pushes a generated release commit or synchronizes protected
branches. If `dev` is protected, allow the App's template-sync push there too.

## 5. Configure required checks

Required checks must use the stable context:

- `ci/merge-gate`

Do not require implementation-job names separately.

## 6. Verify the setup

1. Run normal CI and confirm shared Git dependencies resolve.
2. Run Release and confirm the bump commit, tag, and GitHub Release are created
   by the App identity.
3. Run Sync Starter Template and confirm it can update workflow files, push to
   `dev`, and create or refresh the `dev` -> `main` pull request.
4. Repeat the relevant checks with this repository public, private, and public
   again without editing workflow files or replacing credentials.
5. Verify the mixed case where this repository and `py-lib-starter` have
   different visibility.

For missing credentials, malformed keys, missing installation access, workflow
permission failures, ruleset rejection, key rotation, or repository transfer,
follow the authoritative fleet runbook above.
