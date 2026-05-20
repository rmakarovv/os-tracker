#!/usr/bin/env python3
import argparse
import csv
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


# Inline repo config. Keep labels exact, including capitalization, so the query
# matches GitHub's label names. The script validates these against live labels.
REPO_CONFIG = {
    "pytorch/pytorch": {
        "labels": [
            "good first issue",
            "actionable",
            "easy",
            "OSS contribution wanted",
            "internal ramp-up task",
        ],
    },
    "jax-ml/jax": {
        "labels": [
            "good first issue",
            "help wanted",
            "contributions welcome",
        ],
    },
    "scikit-learn/scikit-learn": {
        "labels": [
            "good first issue",
            "Easy",
            "help wanted",
        ],
    },
    "scipy/scipy": {
        "labels": [
            "good first issue",
        ],
    },
    "numpy/numpy": {
        "labels": [
            "03 - Maintenance",
            "04 - Documentation",
            "05 - Testing",
            "17 - Task",
            "23 - Wish List",
        ],
    },
    "pola-rs/polars": {
        "labels": [
            "good first issue",
            "first-contribution",
            "help wanted",
        ],
    },
    "huggingface/transformers": {
        "labels": [
            "Good First Issue",
            "Good First Documentation Issue",
            "Help wanted",
            "contributions-welcome",
        ],
    },
    "huggingface/datasets": {
        "labels": [
            "good first issue",
            "help wanted",
            "dataset contribution",
        ],
    },
    "huggingface/diffusers": {
        "labels": [
            "good first issue",
            "help wanted",
            "contributions-welcome",
        ],
    },
    "huggingface/accelerate": {
        "labels": [
            "good first issue",
            "help wanted",
            "contributions-welcome",
        ],
    },
    "huggingface/peft": {
        "labels": [
            "good first issue",
            "help wanted",
            "contributions-welcome",
        ],
    },
    "huggingface/trl": {
        "labels": [
            "\U0001f476 good first issue",
        ],
    },
    "huggingface/tokenizers": {
        "labels": [
            "good first issue",
            "help wanted",
        ],
    },
    "vllm-project/vllm": {
        "labels": [
            "good first issue",
            "help wanted",
        ],
    },
    "ollama/ollama": {
        "labels": [
            "good first issue",
            "help wanted",
        ],
    },
    "ggml-org/llama.cpp": {
        "labels": [
            "good first issue",
            "help wanted",
        ],
    },
    "unslothai/unsloth": {
        "labels": [
            "good first issue",
            "help wanted",
        ],
    },
    "Lightning-AI/pytorch-lightning": {
        "labels": [
            "good first issue",
            "help wanted",
            "docs",
        ],
    },
    "mlflow/mlflow": {
        "labels": [
            "good first issue",
            "help wanted",
            "area/docs",
        ],
    },
    "ultralytics/ultralytics": {
        "labels": [
            "good first issue",
            "help wanted",
        ],
    },
    "huggingface/pytorch-image-models": {
        "labels": [
            "good first issue",
            "help wanted",
        ],
    },
    "albumentations-team/albumentations": {
        "labels": [
            "good first issue",
            "help wanted",
        ],
    },
    "DLR-RM/stable-baselines3": {
        "labels": [
            "good first issue",
            "help wanted",
        ],
    },
    "Farama-Foundation/Gymnasium": {
        "labels": [
            "good first issue",
            "help wanted",
        ],
    },
    "vwxyzjn/cleanrl": {
        "labels": [
            "good first issue",
            "help wanted",
        ],
    },
    "deepspeedai/DeepSpeed": {
        "labels": [
            "good first issue",
            "help wanted",
        ],
    },
    "open-mmlab/mmdetection": {
        "labels": [
            "good first issue",
            "community help wanted",
        ],
    },
    "Lightning-AI/torchmetrics": {
        "labels": [
            "good first issue",
            "help wanted",
        ],
    },
    "ray-project/ray": {
        "labels": [
            "good-first-issue",
            "community-contribution",
            "contribution-welcome",
            "docs",
            "rllib-docs-or-examples",
        ],
    },
    "langchain-ai/langchain": {
        "labels": [
            "help wanted",
            "documentation",
        ],
    },
    "run-llama/llama_index": {
        "labels": [
            "good first issue",
            "contributions wanted",
            "docs",
        ],
    },
    "explosion/spaCy": {
        "labels": [
            "help wanted (easy)",
            "help wanted",
            "docs",
        ],
    },
    "UKPLab/sentence-transformers": {
        "labels": [
            "good first issue",
            "help wanted",
            "documentation",
        ],
    },
    "qdrant/qdrant": {
        "labels": [
            "good first issue",
            "help wanted",
            "documentation",
        ],
    },
    "chroma-core/chroma": {
        "labels": [
            "good first issue",
            "help wanted",
            "documentation",
        ],
    },
    "gradio-app/gradio": {
        "labels": [
            "good first issue",
            "docs/website",
        ],
    },
    "keras-team/keras": {
        "labels": [
            "Good first issue",
            "stat:contributions welcome",
            "type:docs",
            "type:docs-bug",
        ],
    },
    "shap/shap": {
        "labels": [
            "good first issue",
            "help wanted",
            "documentation",
        ],
    },
    "pytorch/captum": {
        "labels": [
            "good first issue",
            "help wanted",
            "documentation",
        ],
    },
    "pymc-devs/pymc": {
        "labels": [
            "beginner friendly",
            "help wanted",
            "docs",
        ],
    },
    "pyg-team/pytorch_geometric": {
        "labels": [
            "good first issue",
            "help wanted",
            "documentation",
        ],
    },
    "sktime/sktime": {
        "labels": [
            "good first issue",
            "documentation",
        ],
    },
    "microsoft/autogen": {
        "labels": [
            "good first issue",
            "help wanted",
            "documentation",
        ],
    },
    "bentoml/BentoML": {
        "labels": [
            "good-first-issue",
            "documentation",
        ],
    },
}


DEFAULT_EXCLUDE_LABELS = [
    "duplicate",
    "fixed",
    "inactive",
    "invalid",
    "stale",
    "wontfix",
    "wont fix",
    "WIP",
]


FALLBACK_LABEL_SUBSTRINGS = [
    "good first",
    "help wanted",
    "oss contribution",
    "contribution",
    "first timer",
    "first-timer",
    "beginner",
    "newcomer",
]


GOOD_FIRST_SUBSTRINGS = [
    "good first",
    "first timer",
    "first-timer",
]


class GitHubAPIError(RuntimeError):
    def __init__(self, status, body):
        self.status = status
        self.body = body
        super().__init__(f"GitHub API error {status}: {body}")


class GitHubClient:
    def __init__(self, token):
        self.token = token

    def get_json(self, url, params=None):
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        request = urllib.request.Request(url, headers=self._headers())

        while True:
            try:
                with urllib.request.urlopen(request) as response:
                    links = self._parse_links(response.headers.get("Link", ""))
                    return json.load(response), links
            except urllib.error.HTTPError as error:
                if error.code == 403 and error.headers.get("X-RateLimit-Remaining") == "0":
                    reset_at = int(error.headers.get("X-RateLimit-Reset", "0"))
                    sleep_for = max(1, reset_at - int(time.time()) + 1)
                    print(f"Rate limited. Sleeping for {sleep_for}s...", file=sys.stderr)
                    time.sleep(sleep_for)
                    continue

                body = error.read().decode("utf-8", errors="replace")
                raise GitHubAPIError(error.code, body) from error

    def _headers(self):
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "os-tracker-newcomer-issue-finder",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    @staticmethod
    def _parse_links(header):
        links = {}
        for part in header.split(","):
            section = part.strip().split(";")
            if len(section) < 2:
                continue
            url = section[0].strip()[1:-1]
            rel = None
            for item in section[1:]:
                item = item.strip()
                if item.startswith("rel="):
                    rel = item.split("=", 1)[1].strip('"')
            if rel:
                links[rel] = url
        return links


def compact_query(query):
    return " ".join(query.split())


def parse_github_datetime(value):
    return dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)


def is_tracked_label(label):
    lowered = label.lower()
    return any(part in lowered for part in FALLBACK_LABEL_SUBSTRINGS)


def is_good_first_label(label):
    lowered = label.lower()
    return any(part in lowered for part in GOOD_FIRST_SUBSTRINGS)


def issue_label_names(issue):
    return [label["name"] for label in issue.get("labels", [])]


def issue_flags(issue, tracked_labels):
    label_names = set(issue_label_names(issue))
    return [label for label in tracked_labels if label in label_names]


def issue_has_good_first_flag(issue):
    return any(is_good_first_label(label) for label in issue_label_names(issue))


def repo_labels(client, repo_full_name):
    url = f"https://api.github.com/repos/{repo_full_name}/labels"
    params = {"per_page": 100}
    labels = []

    while url:
        data, links = client.get_json(url, params=params)
        labels.extend(label["name"] for label in data)
        url = links.get("next")
        params = None

    return labels


def actual_labels_for_repo(client, repo_full_name, configured_labels, extra_labels):
    labels = repo_labels(client, repo_full_name)
    label_names_lower = {label.lower(): label for label in labels}
    wanted_labels = configured_labels + extra_labels
    actual_labels = []

    for label in wanted_labels:
        actual_label = label_names_lower.get(label.lower())
        if actual_label and actual_label not in actual_labels:
            actual_labels.append(actual_label)
        elif not actual_label:
            print(f"  missing label: {label}", file=sys.stderr)

    if not actual_labels and not configured_labels:
        actual_labels = [label for label in labels if is_tracked_label(label)]

    return actual_labels, labels


def actual_exclude_labels(repo_labels):
    label_names_lower = {label.lower(): label for label in repo_labels}
    excludes = []
    for label in DEFAULT_EXCLUDE_LABELS:
        actual_label = label_names_lower.get(label.lower())
        if actual_label and actual_label not in excludes:
            excludes.append(actual_label)
    return excludes



def search_issues(client, repo_full_name, label, exclude_labels, cutoff):
    query = f'repo:{repo_full_name} is:issue is:open label:"{label}" -linked:pr'
    for exclude_label in exclude_labels:
        query += f' -label:"{exclude_label}"'
    if cutoff:
        query += f" created:>={cutoff.date().isoformat()}"

    url = "https://api.github.com/search/issues"
    params = {
        "q": compact_query(query),
        "sort": "created",
        "order": "desc",
        "per_page": 100,
    }

    while url:
        try:
            data, links = client.get_json(url, params=params)
        except GitHubAPIError as error:
            if error.status == 422:
                print(
                    f"  search rejected for {repo_full_name} label {label!r}; "
                    "falling back to repository issues API",
                    file=sys.stderr,
                )
                yield from repo_issues_by_label(client, repo_full_name, label, exclude_labels)
                return
            raise
        yield from data.get("items", [])
        url = links.get("next")
        params = None


def repo_issues_by_label(client, repo_full_name, label, exclude_labels):
    url = f"https://api.github.com/repos/{repo_full_name}/issues"
    params = {
        "state": "open",
        "labels": label,
        "sort": "created",
        "direction": "desc",
        "per_page": 100,
    }
    exclude_label_set = {exclude_label.lower() for exclude_label in exclude_labels}

    while url:
        data, links = client.get_json(url, params=params)
        for issue in data:
            if issue.get("pull_request"):
                continue

            issue_label_set = {name.lower() for name in issue_label_names(issue)}
            if exclude_label_set & issue_label_set:
                continue

            yield issue

        url = links.get("next")
        params = None


def issue_timeline(client, repo_full_name, issue_number):
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{issue_number}/timeline"
    params = {"per_page": 100}

    while url:
        data, links = client.get_json(url, params=params)
        yield from data
        url = links.get("next")
        params = None


def has_referencing_commit(event):
    return event.get("event") == "referenced" and event.get("commit_id")


def has_referencing_pull_request(event):
    source_issue = (event.get("source") or {}).get("issue", {})
    return event.get("event") == "cross-referenced" and bool(source_issue.get("pull_request"))


def has_blocking_reference(client, repo_full_name, issue_number, allow_commit_references, allow_pr_references):
    for event in issue_timeline(client, repo_full_name, issue_number):
        if not allow_commit_references and has_referencing_commit(event):
            return True
        if not allow_pr_references and has_referencing_pull_request(event):
            return True
    return False


def collect_issues(client, repos, extra_labels, cutoff, args):
    issues_by_key = {}
    repo_search_labels = {}
    repo_exclude_labels = {}

    for repo_full_name in repos:
        print(f"Scanning {repo_full_name}...", file=sys.stderr)
        configured_labels = REPO_CONFIG.get(repo_full_name, {}).get("labels", [])
        search_labels, labels = actual_labels_for_repo(
            client, repo_full_name, configured_labels, extra_labels
        )
        exclude_labels = actual_exclude_labels(labels)
        repo_search_labels[repo_full_name] = search_labels
        repo_exclude_labels[repo_full_name] = exclude_labels

        if not search_labels:
            print("  no tracked newcomer labels found", file=sys.stderr)
            continue

        print(f"  labels: {', '.join(search_labels)}", file=sys.stderr)
        if exclude_labels:
            print(f"  excluding: {', '.join(exclude_labels)}", file=sys.stderr)

        for label in search_labels:
            for issue in search_issues(client, repo_full_name, label, exclude_labels, cutoff):
                key = (repo_full_name, issue["number"])
                issues_by_key[key] = issue

    issues = []
    candidates = sorted(
        issues_by_key.items(),
        key=lambda item: parse_github_datetime(item[1]["created_at"]),
        reverse=True,
    )

    for repo_full_name, issue in ((key[0], issue) for key, issue in candidates):
        if cutoff and parse_github_datetime(issue["created_at"]) < cutoff:
            continue

        issue_label_set = {label.lower() for label in issue_label_names(issue)}
        if any(label.lower() in issue_label_set for label in repo_exclude_labels.get(repo_full_name, [])):
            continue

        if not args.skip_timeline_filters and has_blocking_reference(
            client,
            repo_full_name,
            issue["number"],
            allow_commit_references=args.allow_commit_references,
            allow_pr_references=args.allow_pr_references,
        ):
            continue

        flags = issue_flags(issue, repo_search_labels.get(repo_full_name, []))
        labels = issue_label_names(issue)
        created_at = parse_github_datetime(issue["created_at"])

        issues.append(
            {
                "repository": repo_full_name,
                "good_first": "yes" if issue_has_good_first_flag(issue) else "no",
                "created_at": issue["created_at"],
                "comments": issue["comments"],
                "url": issue["html_url"],
                "title": issue["title"],
                "number": issue["number"],
                "flags": "; ".join(flags),
                "labels": "; ".join(labels),
                "_created_at": created_at,
            }
        )

    issues.sort(
        key=lambda issue: (
            issue["good_first"] == "yes",
            issue["_created_at"],
            issue["number"],
        ),
        reverse=True,
    )
    return issues


def write_csv(path, issues):
    fields = [
        "repository",
        "good_first",
        "created_at",
        "comments",
        "url",
        "title",
        "number",
        "flags",
        "labels",
    ]

    with open(path, "w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for issue in issues:
            writer.writerow({field: issue[field] for field in fields})


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Collect newcomer-friendly GitHub issues across ML repos, excluding issues "
            "that already appear to have PR or commit activity."
        )
    )
    parser.add_argument(
        "--repo",
        action="append",
        dest="repos",
        default=[],
        help=(
            "Repository in owner/name form. Repeat to override the configured repo set. "
            "Known repos use REPO_CONFIG labels; unknown repos use fallback discovery."
        ),
    )
    parser.add_argument(
        "--label",
        action="append",
        dest="extra_labels",
        default=[],
        help="Extra label to include if a repository has it. Repeat as needed.",
    )
    parser.add_argument("--output", default="newcomer_issues.csv")
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=730,
        help="Skip issues older than this many days. Use 0 to disable.",
    )
    parser.add_argument(
        "--allow-commit-references",
        action="store_true",
        help="Do not filter out issues referenced by commits.",
    )
    parser.add_argument(
        "--allow-pr-references",
        action="store_true",
        help="Do not filter out issues cross-referenced by pull requests.",
    )
    parser.add_argument(
        "--skip-timeline-filters",
        action="store_true",
        help="Skip the slower PR/commit timeline filters.",
    )
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Set GITHUB_TOKEN before running this across many repositories.")

    cutoff = None
    if args.max_age_days:
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=args.max_age_days)

    repos = args.repos or list(REPO_CONFIG)
    client = GitHubClient(token=token)
    issues = collect_issues(client, repos, args.extra_labels, cutoff, args)
    write_csv(args.output, issues)

    print(f"Wrote {len(issues)} issues to {args.output}")


if __name__ == "__main__":
    main()
