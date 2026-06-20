# Scripts

Repo-local scripts live here only when the implementation is specific to this
repository. Shared development commands come from `py-lib-tooling` console
scripts.

## Shared Repo Config

`py_lib_tooling.get_project_tooling_config` is the single reader for repo-local tooling
metadata in `[tool.py_lib_starter]` in `pyproject.toml`.

- Use it when behavior depends on the distribution name, the primary package,
  the package list, repo-scoped env vars, or the repo's optional env-file
  default.
- Do not hardcode project package names in reusable checks, smokes, or shared
  test support; read them from `[tool.py_lib_starter]`.
- When the template is rendered or updated for another library, keep
  `[project].name` and `[tool.py_lib_starter]` in `pyproject.toml` accurate; the
  shared checks and smoke commands should then follow that config.
- `package_names` supports future multi-package repos; `primary_package`
  remains the default import/smoke target.
- Keep this helper out of runtime package code under `src/`; it is only for
  repository tooling and test support.

Example:

```python
from py_lib_tooling import get_project_tooling_config

project_config = get_project_tooling_config()
package_name = project_config.primary_package
package_names = project_config.package_names
env_file_var = project_config.env_file_var
env_file_default = project_config.env_file_default
```

## Local Scripts

- `env/`
  Local contributor environment setup and health checks. `project_config.sh`
  reads `[tool.py_lib_starter]` from `pyproject.toml` for `.envrc` and
  `env/doctor.sh`.
- `ci/`
  Optional `act` entrypoints for terminal-only GitHub workflow debugging.

Use shared smoke commands directly:

```bash
uv run py-lib-smoke-installed-artifact
uv run py-lib-smoke-public-api
```

Run the GitHub CI workflow locally with:

```bash
scripts/ci/local_ci.sh
```

This is a debug dry run. Protected merges are gated by the GitHub Actions
`ci/merge-gate` job on the configured runner backend.

Check and apply starter template and shared package updates through the shared
commands:

```bash
uv run py-lib-template-check
uv run py-lib-template-update
```

Run cleanup, structural, and artifact checks directly when needed:

```bash
uv run py-lib-check-legacy-support-cleanup
uv run py-lib-check-project-docs-structure
uv run py-lib-smoke-built-artifacts
```

Use the running-loop diagnostic helper only for real workbench modules:

```bash
uv run py-lib-reproduce-running-loop workbench.reddit_scraper.<module>
```
