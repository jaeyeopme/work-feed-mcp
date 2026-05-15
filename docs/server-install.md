# Legacy native server install guide

This guide installs the legacy native/systemd Upwork data engine on the personal Tailscale Linux server. It is retained for non-Docker deployments and historical server operations. The primary user/runtime path is Docker Compose + MCP from `README.md`.

Target server facts:

```text
host: openclaw-0309-0402 / 100.82.127.29
user: ubuntu
repo checkout: /home/ubuntu/upwork
runtime data: /home/ubuntu/upwork-data
scheduler: systemd --user timer
```

Do not touch the existing CouchDB / `obsidian-livesync` container or its backup cron.

## 1. GitHub source of truth

Use a private GitHub repository:

```text
jaeyeopme/upwork
```

The remote URL must not contain a token. Prefer `gh auth login` / `gh auth setup-git` for credentials.

## 2. Runtime layout

On the server:

```bash
mkdir -p /home/ubuntu/upwork-data/config /home/ubuntu/upwork-data/logs
chmod 700 /home/ubuntu/upwork-data /home/ubuntu/upwork-data/config
```

Create the protected environment file:

```bash
touch /home/ubuntu/upwork-data/config/upwork.env
chmod 600 /home/ubuntu/upwork-data/config/upwork.env
```

This file may be empty for the default visitor-token bootstrap path. The service unit already sets `UPWORK_COLLECTOR_LIVE=1`.

Optional keys only; do not commit this file:

```env
# UPWORK_COLLECTOR_PROXY_URL is secret material if used.
```

Do not add proxy acquisition or bypass instructions here.

## 3. Clone and run

Install `uv` if missing, then clone the private repo after GitHub auth is configured:

```bash
cd /home/ubuntu
git clone git@github.com:jaeyeopme/upwork.git upwork
cd /home/ubuntu/upwork
uv run upwork-app --help
```

If the server uses HTTPS GitHub auth, ensure `git remote -v` does not print credentials.

## 4. Scheduled default collection

The default server one-shot command is an unfiltered/latest scan of up to 250 jobs:

```bash
UPWORK_COLLECTOR_LIVE=1 uv run upwork-app collect-scheduled \
  --db /home/ubuntu/upwork-data/upwork.db \
  --max-pages 5 \
  --page-size 50
```

Use `--queries "python,scraping"` only for manual or advanced filtered schedules. `--queries` is comma-separated: split on commas, trim whitespace, and drop empty entries. Quote the whole value when a query contains spaces.

The command records run/query summaries in SQLite. If a later explicit query fails, already completed query ingests and run history remain committed and the process exits non-zero with redacted diagnostics.

Agent-readable status:

```bash
uv run upwork-app scheduler-status --db /home/ubuntu/upwork-data/upwork.db --limit 5
```

## 5. systemd user timer

User linger is required and already verified on the target server:

```bash
loginctl show-user ubuntu -p Linger
```

Install or update unit files. Updating files in the repo does not mutate an already installed user unit; copy and reload explicitly:

```bash
mkdir -p ~/.config/systemd/user
cp /home/ubuntu/upwork/deploy/systemd/upwork-collector.service ~/.config/systemd/user/
cp /home/ubuntu/upwork/deploy/systemd/upwork-collector.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable upwork-collector.timer
systemctl --user restart upwork-collector.timer
```

Status and logs:

```bash
systemctl --user status upwork-collector.timer --no-pager
systemctl --user list-timers --all | grep upwork-collector
journalctl --user -u upwork-collector.service --no-pager -n 100
```


CLI wrapper equivalents:

```bash
cd /home/ubuntu/upwork
uv run upwork-app scheduler timer-status
uv run upwork-app scheduler restart-timer
uv run upwork-app scheduler run-now
uv run upwork-app scheduler logs --lines 100
uv run upwork-app scheduler-status --db /home/ubuntu/upwork-data/upwork.db --limit 5
```

`upwork-app scheduler` wraps `systemctl --user` and `journalctl --user`; `upwork-app scheduler-status` reads SQLite run history.

Default cadence is 60 minutes with unfiltered/latest mode and `max-pages=5`. Back-to-back runs can trigger blocking, so verify scheduler-status and journal evidence before increasing cadence, explicit query count, or pages.


## GitHub Actions deployment

CI is non-live and runs on push/pull request. Server deployment is a manual GitHub Actions workflow so production changes stay explicit and do not run live collection during CI.

Required repository secrets:

```text
UPWORK_SERVER_HOST=100.82.127.29
UPWORK_SERVER_USER=ubuntu
UPWORK_SERVER_SSH_KEY=<private key with access to the server>
```

Manual deploy workflow:

```text
Actions -> deploy-server -> Run workflow
ref: main
restart_timer: true
```

The workflow SSHes to the server, fast-forwards `/home/ubuntu/upwork`, verifies `uv run upwork-app --help`, copies `deploy/systemd/upwork-collector.{service,timer}`, reloads the user systemd manager, enables/restarts only the timer, and prints `scheduler-status` if `/home/ubuntu/upwork-data/upwork.db` already exists. It does not run `make live-smoke` or force a live collection job.

## 6. Remove scheduled collection

```bash
systemctl --user disable --now upwork-collector.timer
rm -f ~/.config/systemd/user/upwork-collector.service ~/.config/systemd/user/upwork-collector.timer
systemctl --user daemon-reload
```

This does not remove `/home/ubuntu/upwork-data`.

## 7. Verification checklist

```bash
test -d /home/ubuntu/upwork
test -d /home/ubuntu/upwork-data
stat -c %a /home/ubuntu/upwork-data/config/upwork.env
systemctl --user status upwork-collector.timer --no-pager
docker ps --format '{{.Names}} {{.Image}} {{.Status}}' | grep obsidian-livesync
crontab -l | grep couchdb-backup.sh
```

Run live collection only with explicit approval and valid credentials.
