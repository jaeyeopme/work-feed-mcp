# Upwork collection scheduler plan

Status: implementation planning / server install reference.

## Responsibility boundary

The app does **not** run a long-lived internal scheduler daemon. Scheduled execution is handled by the OS scheduler, which calls a one-shot CLI command.

Recommended one-shot command for the default server schedule:

```bash
UPWORK_COLLECTOR_LIVE=1 uv run upwork-app collect-scheduled \
  --db /home/ubuntu/upwork-data/upwork.db \
  --max-pages 5 \
  --page-size 50
```

This is an unfiltered/latest scan of up to 250 jobs per run. Use `--queries "python,scraping"` only for manual or advanced filtered schedules.

Agent-readable status:

```bash
uv run upwork-app scheduler-status --db /home/ubuntu/upwork-data/upwork.db --limit 5
```

## Linux server recommendation

For the target Ubuntu/Tailscale server, use a `systemd --user` timer.

Why:
- visible status through `systemctl --user status`
- logs through `journalctl --user`
- works after logout because `ubuntu` has `Linger=yes`
- no app-native daemon or cron mutation needed

Default:

```text
repo: /home/ubuntu/upwork
runtime: /home/ubuntu/upwork-data
env file: /home/ubuntu/upwork-data/config/upwork.env
cadence: every 60 minutes
query mode: unfiltered/latest by default
max pages: 5
page size: 50
```

See `docs/server-install.md` and `deploy/systemd/` for concrete unit files.

## macOS / cron note

macOS `launchd` and cron can still call the same one-shot CLI, but they are not the first-pass server target. Prefer Linux `systemd --user` for the current server install.

## Safety notes

- Live collection remains explicit opt-in through `UPWORK_COLLECTOR_LIVE=1`.
- Proxy/token material must stay outside git and logs.
- Do not document proxy acquisition or access-control bypass.
- Keep the default cadence at 60 minutes. If rate-limit/block evidence appears, reduce pages or split explicit query schedules before increasing cadence.
