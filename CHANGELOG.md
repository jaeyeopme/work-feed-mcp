# Changelog

This file records user-visible changes.

The format follows Keep a Changelog style. Version tags such as `v0.1.0`
identify GitHub Releases and GHCR images.

## [Unreleased]

### Added

- Lightweight open-source maintenance files: license, contributing guide,
  security policy, changelog, issue templates, and PR template.
- Dependabot configuration for conservative GitHub Actions and Python dependency update checks.
- Documentation contract coverage for the public maintenance surface.

### Changed

- Release guidance now includes a first-release checklist and keeps GHCR as the
  primary distribution surface while PyPI remains deferred.

## [0.1.0] - TBD

### Added

- Initial public Docker/MCP-first Upwork job discovery data engine baseline.
- Streamable HTTP MCP tools for collected job lookup, collector status, and safe queued control.
- Docker worker runtime for recurring collection into SQLite.
