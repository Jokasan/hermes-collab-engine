# Roadmap

Hermes Collab Engine v5.0 is the first public release line. The roadmap below highlights contributor-friendly milestones after v5.0. It is not a promise of dates or scope; issues and pull requests should stay small and reviewable.

## v5.0.x release hardening

- Keep installation, sandbox startup, and dashboard documentation current across `README.md`, `README.en.md`, and `README.ja.md`.
- Add targeted regression tests for dashboard payloads, sandbox cleanup, and CLI status commands.
- Improve issue templates and contributor guidance based on first external reports.
- Preserve safe defaults for local-only dashboard and mock sandbox demos.

## Contributor experience

- Document common development tasks and narrow verification commands.
- Expand examples for custom Agent Backend implementations.
- Add clearer troubleshooting for missing CLI dependencies, model configuration, and sandbox ports.
- Track localization gaps so English, Japanese, and Chinese docs remain aligned.

## Collaboration engine capabilities

- Improve WBS node observability and run-detail summaries without exposing unnecessary runtime data.
- Add more focused verification helpers for release checks.
- Refine Leader feedback notebook export formats.
- Explore safer extension points for skills and tool profiles.

## Security and operations

- Strengthen dashboard deployment guidance for authenticated, non-local environments.
- Add more checks that prevent committing runtime SQLite files, logs, and secrets.
- Keep sandbox real execution isolated from production data and clearly labeled.
- Review tool permission defaults before adding new write-capable integrations.

## How to propose roadmap changes

Open a feature request with the user workflow, safety impact, and a minimal first step. Large ideas are welcome, but the preferred implementation path is a sequence of small PRs with clear verification.
