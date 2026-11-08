# Security

Ditoo Control runs a small HTTP server so its window, hooks and your scripts can talk to it.

- It listens on **127.0.0.1 only** – nothing on your network can reach it.
- Requests with a foreign `Host` header are rejected (protects against DNS rebinding).
- Browser requests coming from other websites (`Sec-Fetch-Site: cross-site`) are rejected, and state-changing calls require a JSON body, so a web page you visit cannot control the app.
- Static files are served only from the bundled `ui` folder and the app's media folder; "open" actions use a fixed allow-list (Windows Bluetooth / sound settings, the project's pages).
- Settings are validated against known keys and types.
- Integrations edit `~/.claude/settings.json` and `~/.codex/config.toml` only on request, always after a timestamped backup, and only touch Ditoo Control's own entries.

## Reporting a vulnerability

Please open a [private security advisory](https://github.com/kantaon/ditoo-control/security/advisories/new) instead of a public issue. You'll get an answer as soon as possible.
