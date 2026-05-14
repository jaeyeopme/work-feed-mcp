# Server install guide

This guide installs the CLI-first Upwork data engine on the personal Tailscale Linux server.

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

## 4. Scheduled multi-query collection

The one-shot command is:

```bash
UPWORK_COLLECTOR_LIVE=1 uv run upwork-app collect-scheduled \
  --db /home/ubuntu/upwork-data/upwork.db \
  --queries "python,scraping" \
  --max-pages 1 \
  --page-size 50
```

`--queries` is comma-separated: split on commas, trim whitespace, and drop empty entries. Quote the whole value when a query contains spaces.

The command is fail-fast: if a later query fails, already completed query ingests remain committed and the process exits non-zero with redacted diagnostics.

## 5. systemd user timer

User linger is required and already verified on the target server:

```bash
loginctl show-user ubuntu -p Linger
```

Install unit files:

```bash
mkdir -p ~/.config/systemd/user
cp /home/ubuntu/upwork/deploy/systemd/upwork-collector.service ~/.config/systemd/user/
cp /home/ubuntu/upwork/deploy/systemd/upwork-collector.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now upwork-collector.timer
```

Status and logs:

```bash
systemctl --user status upwork-collector.timer --no-pager
systemctl --user list-timers --all | grep upwork-collector
journalctl --user -u upwork-collector.service --no-pager -n 100
```

Default cadence is 15 minutes with `max-pages=1`. If rate-limit/block evidence appears, switch the timer to 30 minutes before increasing query count or pages.

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
