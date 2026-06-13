# Security Policy

## Supported versions

| Version | Support status |
|---|---|
| v5.0.x | Supported for security fixes and release-readiness updates |
| Earlier preview builds | Best-effort only; please upgrade to v5.0.x before reporting unless the issue affects current `main` |

## Reporting a vulnerability

Please do not open a public issue for vulnerabilities, leaked credentials, or exploit details.

Report privately to the maintainer with:

- A concise description of the issue and affected version or commit.
- Steps to reproduce in a local or sandbox environment.
- Impact assessment, including whether secrets, dashboard access, worker execution, or SQLite data may be exposed.
- Any logs or screenshots with tokens, paths, user data, and private prompts removed.

The maintainer will acknowledge the report when possible, investigate, and coordinate a fix or disclosure timeline appropriate to the severity.

## Dashboard exposure warning

The dashboard and API are intended to be local-first unless you add your own network controls. Binding `hermes-collab server` or sandbox scripts to public interfaces can expose run metadata, logs, worker status, model names, and task content.

Before exposing the dashboard beyond `127.0.0.1`:

- Put it behind authentication and transport security.
- Review reverse proxy, firewall, and access-log retention settings.
- Avoid sending private prompts, customer data, credentials, or proprietary source code to demo instances.
- Confirm sandbox runs use isolated demo databases and workspaces.

## Secrets policy

This repository must not contain real runtime secrets or private state:

- No API keys, tokens, auth JSON, session cookies, or private model gateway URLs.
- No real Hermes or Claude configuration copied from a developer machine.
- No production SQLite files, including `data/*.sqlite3`.
- No private logs, prompts, customer data, or generated worker output that cannot be published.

Use `.example` files, empty templates, environment variables, or local config outside the repository. If you accidentally commit a secret, rotate it immediately and report the incident privately.

## Security boundaries for contributions

Security-sensitive changes should be small and explicit. Document any change that affects worker execution, tool allowlists, subprocess handling, dashboard/API exposure, sandbox real execution, database paths, or cleanup behavior. Prefer safe defaults and local-only examples.
