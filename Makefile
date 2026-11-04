.DEFAULT_GOAL := help

## Show available targets
help:
	@grep -B1 '^[a-z][a-z_-]*:' $(MAKEFILE_LIST) \
		| grep -A1 '^##' \
		| awk '/^##/{d=substr($$0,4)} /^[a-z]/{split($$0,a,":"); printf "  %-20s %s\n", a[1], d}'

# Fail early with an actionable message when a required tool is missing, rather
# than letting a recipe die halfway with a cryptic "command not found". Each
# target lists the binaries it assumes as `guard-<tool>` order-only prereqs.
guard-%:
	@command -v $* >/dev/null 2>&1 || { \
		printf 'error: required tool %s not found on PATH.\n' '$*' >&2; \
		printf 'See CONTRIBUTING.md > Prerequisites for how to install it.\n' >&2; \
		exit 1; \
	}

## Run both test layers (conformance and support scripts)
test: test_conformance test_scripts

# Each layer is one call into .scripts/run-tests.py, which composes the `uvx`
# invocation in Python. Doing that here in `$(shell ...)` would make `make` and a
# POSIX shell prerequisites of running the tests at all; the script runs the same
# on Windows, where make usually is not installed.

## Check that every skill and rule is shaped the way akit discovers one (fast, offline)
test_conformance: | guard-uv
	uv run .scripts/run-tests.py conformance

## Test the Python under .scripts/ and inside the skills (installs what the scripts declare)
test_scripts: | guard-uv
	uv run .scripts/run-tests.py scripts

## Record evidence for one kit against your own assistant (KIT=<name>)
record_evidence: | guard-uv
	@test -n "$(KIT)" || { printf 'usage: make record_evidence KIT=<name>\n' >&2; exit 1; }
	uv run --script .scripts/record_evidence.py $(KIT) $(RECORD_ARGS)

## Run the full pre-commit guard suite against all files
check: | guard-uvx
	uvx prek run --all-files

## Install the pre-commit hooks into this clone
bootstrap: | guard-git guard-uvx
	uvx prek install

.PHONY: help test test_conformance test_scripts record_evidence check bootstrap
