# Maintainer Setup

Managed repositories are created and administered from `py-lib-starter`.
Ordinary contributor bootstrap is documented in [SETUP.md](../SETUP.md), and the
normal development workflow is in [CONTRIBUTING.md](../CONTRIBUTING.md).

## Target State

- `dev` is the default branch and normal pull-request target.
- `main` is the protected release branch.
- Pull requests to `main` come only from this repository's `dev` branch.
- Full CI runs on `dev` pushes and pull requests to `dev` or `main`.
- Release and template-sync commits use `betabitplus-py-lib-automation`.
- Public and private repositories use the same workflow and credential topology.

## Managed Onboarding

From an up-to-date `py-lib-starter` checkout, create or resume the repository
with:

```bash
scripts/platform/create_managed_repository.sh <repository-name>
```

The command creates the GitHub repository, `dev` and `main`, default branch,
merge settings, GitHub App credentials, standard `main` ruleset, registry
change, protected pull requests, CI, template sync, Repo Doctor, and Fleet
Doctor checks.

Do not repeat these operations in the GitHub UI. The only normal manual actions
are reviewing and merging the protected pull requests. Rerun the same command
after each merge.

## Automation Identity

`betabitplus-py-lib-automation` must remain installed in `All repositories` mode
with:

- `Contents: Read and write`
- `Pull requests: Read and write`
- `Workflows: Read and write`

Repository Actions values are:

```text
Variable: PY_LIB_AUTOMATION_APP_ID
Variable: PY_LIB_AUTOMATION_CLIENT_ID
Secret:   PY_LIB_AUTOMATION_PRIVATE_KEY
```

Never commit the private key or add PAT fallback credentials. Generated local
reusable CI workflows create scoped App tokens only for trusted operations;
fork pull requests do not receive App credentials or repository secrets.

## Protection and Verification

`main` requires pull requests, an up-to-date branch, squash merge, and only
`ci/merge-gate`; force pushes and deletion remain blocked. Only the automation
App receives the narrow release and synchronization bypass.

For missing credentials, installation access, workflow permissions, ruleset
rejection, key rotation, repository transfer, or visibility changes, rerun the
onboarding command or follow the authoritative policy:

```text
https://github.com/betabitplus/py-lib-starter/blob/dev/docs/platform-ops/github-app-automation-policy.md
```
