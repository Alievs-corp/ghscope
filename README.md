## ghscope

`ghscope` generates auditable activity reports for GitHub organisations and users.

It pulls commits, pull requests, issues and reviews through the GitHub GraphQL API, then aggregates them into human‑readable reports in Markdown, HTML, PDF, JSON and CSV.

The HTML export is a self‑contained dashboard with a sidebar, filters and per‑entity breakdowns; PDFs are generated from the same template for a print‑ready view.

---

### Installation

`ghscope` targets Python 3.12+.

With `uv` (recommended):

```bash
uv add ghscope
```

With `pip`:

```bash
pip install ghscope
```

---

### Authentication

`ghscope` uses a GitHub fine‑grained personal access token.

The token must have:

- **Repository access** to the repos you want to analyse (ideally “All repositories” for the organisation).
- **Scopes/permissions** that allow reading:
  - code
  - pull requests
  - issues
  - organisation members (for org‑wide reports)

You can pass the token explicitly or via environment variables.

Checked in order:

1. `--token` CLI flag
2. `GH_FINE_GRAINED_TOKEN`
3. `GITHUB_TOKEN`
4. `GH_TOKEN`

---

### CLI usage

Once installed, a `ghscope` entrypoint is available on your PATH.

Basic help:

```bash
ghscope --help
ghscope report --help
```

Generate a Markdown report for an organisation over a date range:

```bash
ghscope report \
  --org Alievs-corp \
  --since 2026-01-01 \
  --until 2026-02-28 \
  --format md \
  --output ./report.md
```

Generate an HTML dashboard:

```bash
ghscope report \
  --org Alievs-corp \
  --since 2026-01-01 \
  --until 2026-02-28 \
  --format html \
  --output ./report.html
```

Generate a JSON export suitable for further processing:

```bash
ghscope report \
  --org Alievs-corp \
  --since 2026-01-01 \
  --until 2026-02-28 \
  --format json \
  --output ./report.json
```

Generate a PDF (requires WeasyPrint and its system dependencies):

```bash
ghscope report \
  --org Alievs-corp \
  --since 2026-01-01 \
  --until 2026-02-28 \
  --format pdf \
  --output ./report.pdf
```

You can also run reports for a single user:

```bash
ghscope report \
  --user martian56 \
  --since 2026-01-01 \
  --until 2026-02-28 \
  --format html \
  --output ./user-report.html
```

`--org` and `--user` can be combined; the tool will analyse all repos visible to the token in that scope.

---

### HTML dashboard

The HTML output is a static, portable dashboard with:

- **Overview**: repository count, commit/PR/issue totals, lines changed, active/inactive contributors.
- **Contributors**: per‑user activity, sorted by total impact.
- **Repositories**: per‑repo summaries (commits, lines, PRs, issues, distinct contributors).
- **Activity timeline**: stacked bars per day (commits, PRs, issues).
- **Pull requests, commits, issues**: detailed tables with titles/messages, authors, counts and state.

There is a small filter bar at the top:

- **Focus on contributor**: pick a user to see only their work; all sections (overview, repos, timeline, PRs, commits, issues) realign to that view.
- **Filter by text**: search across titles and messages.

The page is fully static: no build step, no external assets, and it can be served from any static host or converted to PDF.

---

### Data exported

Depending on the format, `ghscope` exports:

- **Aggregates**
  - per‑user counts (commits, lines added/deleted, PRs opened/merged, issues opened/closed/assigned, reviews given/received)
  - per‑repo counts (commits, lines, PRs, issues, contributor count)
  - active vs inactive contributors
  - daily activity buckets

- **Raw entities**
  - users
  - repositories
  - commits
  - pull requests
  - issues

The JSON export contains both the aggregates and the raw entities so you can reshape the data as needed.

---

### Notes

- The reports only include repositories and members that the token can see. If you expect more data than appears in a report, check the token’s repo and organisation permissions first.
- For large organisations, keep an eye on GitHub GraphQL rate limits. `ghscope` logs remaining calls and the reset time when you run with `--verbose`.
