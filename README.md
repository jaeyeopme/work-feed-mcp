# upwork

Upwork job discovery pipeline monorepo.

This repo keeps each stage as a separate module with a narrow contract. The current implemented module is `collector`; later modules should consume the collector JSONL contract rather than reaching into collector internals.

## Modules

```text
packages/
  collector/   Upwork → normalized JSONL on stdout
  ingest/      JSONL → SQLite/Postgres with collected_at/snapshot/query metadata
  analytics/   DB → statistics and reports
  ranker/      DB/jobs → Jaeyeop-specific application value score
  report/      ranked jobs/analytics → Discord/Markdown/HTML output
```

Only `packages/collector` is implemented right now. The other package directories are placeholders for the intended boundaries.

## Current collector commands

Install the collector entrypoint after moving/cloning the monorepo:

```bash
python -m pip install -e packages/collector
```

Run local verification from the monorepo root:

```bash
make quality
make smoke
```

Run explicit live smoke with the default visitor collection size, up to 50 jobs:

```bash
make live-smoke QUERY="python"
```

Equivalent package-local commands live in `packages/collector/Makefile`.

## Pipeline contract

- `collector` owns network collection, normalization, typed errors, redaction, and JSONL stdout.
- `collector` must not own durable state, ranking, analytics, notifications, or scheduling.
- `ingest` will add durable fields such as `collected_at`, `query`, `snapshot_id`, `run_id`, hashes, and DB storage.
- `ranker` will add score fields and reasons; it must not mutate raw collector records.
- `report` owns presentation only.

See `docs/contracts/job-jsonl.md` for the shared collector output contract.
