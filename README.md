# OS Tracker

A static browser for newcomer-friendly ML and AI open-source issues.

The site is just:

- `index.html`
- `issues.css`
- `issues.js`
- `newcomer_issues.csv`

## Run Locally

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Open:

```text
http://127.0.0.1:8000/
```

Stop the server with `Ctrl+C`.

## Refresh Data

```bash
GITHUB_TOKEN=your_token_here python3 list_newcomer_issues.py --output newcomer_issues.csv
```

## Publish

Enable GitHub Pages for the repository:

1. Settings -> Pages
2. Source: deploy from branch
3. Branch: `main`
4. Folder: `/root`

The included GitHub Actions workflow can refresh `newcomer_issues.csv` daily.
