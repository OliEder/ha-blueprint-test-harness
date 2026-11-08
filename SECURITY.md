# Security

## What this tool is

A development and test tool. Running it executes things: the tests you give it, the Jinja templates and actions of the blueprints you load, and, in the mutation tool, any command you put after `--`. It is not a service and it listens on no port.

## Supported versions

The latest release (0.4.0) and `main`. Versions up to 0.3.0 have the issue described under "Fixed security issues"; update to 0.4.0. A fix is published as the next patch version (see [`RELEASING.md`](RELEASING.md)).

## Reporting a vulnerability

Please do not open a public issue for a security problem.

Use GitHub's private vulnerability reporting: open the repository's **Security** tab and choose **Report a vulnerability**. The project is maintained by one person on a best-effort basis; there is no response-time promise.

Please include the version of this tool and of Home Assistant (`pip show homeassistant`), what you ran and what you expected. Leave out entity IDs, hostnames and tokens from a real installation.

## What you should know before running it

- **Treat blueprints and tests from other people as untrusted code.** Running tests runs Python. Loading a blueprint runs its templates inside Home Assistant's template sandbox, but Home Assistant reads the file with its own YAML loader first, outside any sandbox: the tags `!env_var` and `!include` read environment variables and any YAML file the user can read (absolute paths and `../` work), and what they read shows up in the recorded calls, in test output and in CI logs. Since 0.4.0 `start()` refuses a blueprint with any YAML tag other than `!input` (`BlueprintLoadError`); versions up to 0.3.0 do not. Network access is blocked by Home Assistant's test package, not by this harness. Do not run untrusted blueprints with secrets in the environment or outside a throw-away environment. `start_automation()` reads plain YAML (`yaml.safe_load`), which rejects these tags.
- **The mutation tool passes your environment on.** The command after `--` runs with the environment of the caller, minus the tool's own `HA_BLUEPRINT_TEST_HARNESS_*` variables. Secrets in that environment reach the test run. Without a command after `--` it runs `pytest` in the current directory, which loads that directory's `conftest.py`: run it only on files you have read.
- **No connection to a real instance or device.** The harness itself does not read credentials and does not talk to a Home Assistant instance or to any device (a blueprint could read environment variables and files through YAML tags before 0.4.0, see above). Services listed in `services=` are recorded, never executed. Real components you add with `components=` run for real; review one before adding it if it could open a connection.
- **Mutants are written to a temporary folder** (readable by you only) that is removed afterwards. With `--workdir` they are written there instead and stay; the folder must not hold `control.yaml` or `M001.yaml`, ... from an earlier run (the tool stops), and it never writes through a link. Give it an empty folder you created yourself.
- **YAML aliases (`*name`) may expand to at most 20 000 values, in blueprints and automation files that tests load and in files the mutation tool reads; the mutation tool also refuses files above 1 MB.** An alias is walked once for every place it is used (and written out in full for every mutant), so a few nested aliases would keep the tool or Home Assistant busy for minutes. Ordinary aliases (a list used in several places) are fine. Version 0.4.0 refused every file with an alias, which made the tool unusable for blueprints that use one; 0.4.1 fixes that.
- **Which runs count as "invalid" in a score** is decided by pytest's own failure line naming `BlueprintLoadError`; text that a test prints cannot change it. A score is still no protection against someone who may change the tests or the floor.

## In CI

`.github/workflows/ci.yaml` uses `pull_request` (not `pull_request_target`), `permissions: contents: read` and no secrets. Keep it that way: a pull request from a fork runs its own test code in the job. No checkout keeps the token (`persist-credentials: false`).

The actions are pinned to commit ids (Dependabot proposes updates), and the packages are installed from `.lock` files with hashes (`pip install --require-hashes`); the release build uses its own lock file and builds without isolation. The release workflow has write permission only in the job that creates the draft release, and only for a pushed tag; a run started by hand (the dry run) can only read. Every release comes with a `SHA256SUMS` file. There is no signed provenance (attestation) yet.

## Fixed security issues

- **0.4.0** (found by an audit on 2026-11-08): a blueprint could read environment variables and files through YAML tags (`!env_var`, `!include`), see above; the mutation tool followed links in `--workdir` and could be kept busy by nested YAML aliases (0.4.0 refused all aliases, 0.4.1 only those that expand too far); text printed by a test could change a mutation score; the workflows were not pinned.

## Out of scope

Vulnerabilities in Home Assistant itself, in the `pytest-homeassistant` or `pytest-homeassistant-custom-component` package, or in a blueprint you test belong to those projects.
