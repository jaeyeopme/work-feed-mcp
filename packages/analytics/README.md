# upwork-analytics

SQLite-backed analytics helpers for normalized Upwork job data.

The package is intentionally conditional about client analytics: it only groups
client dimensions that are present as columns in the SQLite `jobs` table. Missing
client dimensions are reported as `unknown` instead of being inferred from job
text or fabricated.
