#!/usr/bin/env bash

py_lib_project_config_python() {
  if command -v python3 >/dev/null 2>&1; then
    printf '%s\n' "python3"
    return 0
  fi

  if command -v python >/dev/null 2>&1; then
    printf '%s\n' "python"
    return 0
  fi

  return 1
}

py_lib_read_project_env_config() {
  local repo_root="$1"
  local python_bin
  python_bin="$(py_lib_project_config_python)" || return 1

  "$python_bin" - "$repo_root/pyproject.toml" <<'PY'
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

pyproject_path = Path(sys.argv[1])
with pyproject_path.open("rb") as pyproject_file:
    pyproject = tomllib.load(pyproject_file)

tooling = pyproject["tool"]["py_lib_starter"]
env_prefix = tooling["env_prefix"].strip()
env_file_default = tooling["env_file_default"].strip()

if not re.fullmatch(r"[A-Z][A-Z0-9_]*", env_prefix):
    msg = "[tool.py_lib_starter].env_prefix must be an uppercase env-var prefix."
    raise SystemExit(msg)
if not env_file_default or "\n" in env_file_default or "\r" in env_file_default:
    msg = "[tool.py_lib_starter].env_file_default must be a one-line string."
    raise SystemExit(msg)

print(env_prefix)
print(f"{env_prefix}_ENV_FILE")
print(env_file_default)
PY
}

py_lib_expand_env_file_path() {
  local env_file_path="$1"

  case "$env_file_path" in
    \~)
      printf '%s\n' "$HOME"
      ;;
    \~/*)
      printf '%s/%s\n' "$HOME" "${env_file_path#"~/"}"
      ;;
    \$HOME*)
      printf '%s%s\n' "$HOME" "${env_file_path#\$HOME}"
      ;;
    \$\{HOME\}*)
      printf '%s%s\n' "$HOME" "${env_file_path#\$\{HOME\}}"
      ;;
    *)
      printf '%s\n' "$env_file_path"
      ;;
  esac
}

py_lib_load_project_env_config() {
  local repo_root="${1:-$(pwd)}"
  local config_lines
  local configured_env_file
  mapfile -t config_lines < <(py_lib_read_project_env_config "$repo_root") || return 1

  if [ "${#config_lines[@]}" -ne 3 ]; then
    return 1
  fi

  PY_LIB_PROJECT_ENV_PREFIX="${config_lines[0]}"
  PY_LIB_PROJECT_ENV_FILE_VAR="${config_lines[1]}"
  PY_LIB_PROJECT_ENV_FILE_DEFAULT="${config_lines[2]}"
  configured_env_file="${!PY_LIB_PROJECT_ENV_FILE_VAR:-$PY_LIB_PROJECT_ENV_FILE_DEFAULT}"
  PY_LIB_PROJECT_ENV_FILE="$(py_lib_expand_env_file_path "$configured_env_file")"

  export PY_LIB_PROJECT_ENV_PREFIX
  export PY_LIB_PROJECT_ENV_FILE_VAR
  export PY_LIB_PROJECT_ENV_FILE_DEFAULT
  export PY_LIB_PROJECT_ENV_FILE
  export "${PY_LIB_PROJECT_ENV_FILE_VAR}=${PY_LIB_PROJECT_ENV_FILE}"
}
