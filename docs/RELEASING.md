# Releasing

This repository publishes GitHub Releases and GHCR container images from version tags.

## First release checklist

Before pushing the first public release tag:

1. confirm `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, and `CHANGELOG.md` are present;
2. update `CHANGELOG.md` so the release section describes the shipped user-facing changes;
3. run `make quality`, `make smoke`, and `make e2e-smoke`;
4. keep live collection evidence out of the release gate unless a maintainer explicitly requests it, and report any live evidence separately;
5. verify the tag points at the commit intended for GHCR publication.

GHCR is the primary package distribution surface. PyPI publishing is deferred until Python package installation becomes a user-facing goal.

## Release trigger

Create and push a semantic version tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The `.github/workflows/release.yml` workflow then:

1. checks out the tagged commit;
2. builds the Docker image;
3. publishes image tags to GitHub Container Registry:
   - `ghcr.io/jaeyeopme/work-feed-mcp:v0.1.0`
   - `ghcr.io/jaeyeopme/work-feed-mcp:0.1.0`
   - `ghcr.io/jaeyeopme/work-feed-mcp:latest`
4. creates a GitHub Release for the tag.

Manual dispatch is also available for an existing tag if the release job needs to be rerun.

## Versioning

Use `vMAJOR.MINOR.PATCH` tags. Pre-release suffixes such as `v0.2.0-rc.1` are accepted by the workflow.

## What this does not do

- It does not publish to PyPI.
- It does not run live Upwork collection.
- It does not deploy to Oracle Cloud; deployment remains in `.github/workflows/ci-cd.yml`.

The project is Docker/MCP-first, so GHCR is the primary package distribution surface for now. PyPI can be added later if `pip install work-feed-mcp` becomes a user-facing goal.
