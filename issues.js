const state = {
  issues: [],
  filtered: [],
  includeTags: new Set(),
  excludeTags: new Set(),
  search: "",
  goodFirst: "all",
  repo: "",
  sort: "good-new",
};

const els = {
  summary: document.querySelector("#summary"),
  searchInput: document.querySelector("#searchInput"),
  repoSelect: document.querySelector("#repoSelect"),
  sortSelect: document.querySelector("#sortSelect"),
  includeSelect: document.querySelector("#includeSelect"),
  excludeSelect: document.querySelector("#excludeSelect"),
  includeChips: document.querySelector("#includeChips"),
  excludeChips: document.querySelector("#excludeChips"),
  issuesBody: document.querySelector("#issuesBody"),
  emptyState: document.querySelector("#emptyState"),
};

init();

async function init() {
  wireEvents();

  try {
    const response = await fetch("newcomer_issues.csv", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`CSV request failed with ${response.status}`);
    }
    loadCsv(await response.text());
  } catch (error) {
    els.summary.textContent = "Could not load newcomer_issues.csv.";
    console.warn(error);
  }
}

function wireEvents() {
  els.searchInput.addEventListener("input", () => {
    state.search = els.searchInput.value.trim().toLowerCase();
    render();
  });

  document.querySelectorAll('input[name="goodFirst"]').forEach((input) => {
    input.addEventListener("change", () => {
      state.goodFirst = input.value;
      render();
    });
  });

  els.repoSelect.addEventListener("change", () => {
    state.repo = els.repoSelect.value;
    render();
  });

  els.sortSelect.addEventListener("change", () => {
    state.sort = els.sortSelect.value;
    render();
  });

  els.includeSelect.addEventListener("change", () => addTag("include"));
  els.excludeSelect.addEventListener("change", () => addTag("exclude"));
}

function loadCsv(text) {
  const rows = parseCsv(text);
  const [header, ...records] = rows;
  const fields = header.map((field) => field.trim());

  state.issues = records
    .filter((record) => record.length && record.some(Boolean))
    .map((record) => rowToIssue(fields, record))
    .filter((issue) => issue.url && issue.title);

  resetFilters(false);
  populateControls();
  render();
}

function rowToIssue(fields, record) {
  const raw = {};
  fields.forEach((field, index) => {
    raw[field] = record[index] ?? "";
  });

  const flags = splitTags(raw.flags);
  const labels = splitTags(raw.labels);
  const tagSet = new Set([...flags, ...labels]);
  const createdAt = new Date(raw.created_at);
  const number = Number.parseInt(raw.number, 10) || 0;

  return {
    repository: raw.repository,
    goodFirst: raw.good_first.toLowerCase() === "yes",
    createdAt,
    createdAtRaw: raw.created_at,
    comments: Number.parseInt(raw.comments, 10) || 0,
    url: raw.url,
    title: raw.title,
    number,
    flags,
    labels,
    tags: [...tagSet].sort((a, b) => a.localeCompare(b)),
    searchText: [
      raw.repository,
      raw.good_first,
      raw.created_at,
      raw.comments,
      raw.url,
      raw.title,
      raw.number,
      raw.flags,
      raw.labels,
    ]
      .join(" ")
      .toLowerCase(),
  };
}

function splitTags(value) {
  return String(value || "")
    .split(";")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    const next = text[i + 1];

    if (char === '"') {
      if (inQuotes && next === '"') {
        field += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (char === "," && !inQuotes) {
      row.push(field);
      field = "";
    } else if ((char === "\n" || char === "\r") && !inQuotes) {
      if (char === "\r" && next === "\n") {
        i += 1;
      }
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
    } else {
      field += char;
    }
  }

  if (field || row.length) {
    row.push(field);
    rows.push(row);
  }

  return rows;
}

function populateControls() {
  const repos = [...new Set(state.issues.map((issue) => issue.repository))]
    .filter(Boolean)
    .sort((a, b) => a.localeCompare(b));
  const tags = [...new Set(state.issues.flatMap((issue) => issue.tags))]
    .filter(Boolean)
    .sort((a, b) => a.localeCompare(b));

  replaceOptions(els.repoSelect, [["", "All repositories"], ...repos.map((repo) => [repo, repo])]);
  replaceOptions(els.includeSelect, [["", "Choose tag"], ...tags.map((tag) => [tag, tag])]);
  replaceOptions(els.excludeSelect, [["", "Choose tag"], ...tags.map((tag) => [tag, tag])]);
}

function replaceOptions(select, options) {
  select.replaceChildren(
    ...options.map(([value, label]) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      return option;
    }),
  );
}

function addTag(kind) {
  const select = kind === "include" ? els.includeSelect : els.excludeSelect;
  const tag = select.value;
  if (!tag) {
    return;
  }

  if (kind === "include") {
    state.includeTags.add(tag);
    state.excludeTags.delete(tag);
  } else {
    state.excludeTags.add(tag);
    state.includeTags.delete(tag);
  }

  select.value = "";
  render();
}

function resetFilters(shouldRender = true) {
  state.includeTags.clear();
  state.excludeTags.clear();
  state.search = "";
  state.goodFirst = "all";
  state.repo = "";
  state.sort = "good-new";

  els.searchInput.value = "";
  els.repoSelect.value = "";
  els.sortSelect.value = "good-new";
  document.querySelector('input[name="goodFirst"][value="all"]').checked = true;

  if (shouldRender) {
    render();
  }
}

function render() {
  state.filtered = state.issues.filter(matchesFilters).sort(compareIssues);
  renderSummary();
  renderChips();
  renderRows();
}

function matchesFilters(issue) {
  if (state.search && !issue.searchText.includes(state.search)) {
    return false;
  }

  if (state.goodFirst === "yes" && !issue.goodFirst) {
    return false;
  }

  if (state.goodFirst === "no" && issue.goodFirst) {
    return false;
  }

  if (state.repo && issue.repository !== state.repo) {
    return false;
  }

  const tags = new Set(issue.tags);
  if (state.includeTags.size) {
    let hasIncludedTag = false;
    for (const tag of state.includeTags) {
      if (tags.has(tag)) {
        hasIncludedTag = true;
        break;
      }
    }
    if (!hasIncludedTag) {
      return false;
    }
  }

  for (const tag of state.excludeTags) {
    if (tags.has(tag)) {
      return false;
    }
  }

  return true;
}

function compareIssues(a, b) {
  if (state.sort === "good-new") {
    return (
      Number(b.goodFirst) - Number(a.goodFirst) ||
      b.createdAt - a.createdAt ||
      b.number - a.number
    );
  }

  if (state.sort === "new") {
    return b.createdAt - a.createdAt || b.number - a.number;
  }

  if (state.sort === "comments-desc") {
    return b.comments - a.comments || b.createdAt - a.createdAt;
  }

  if (state.sort === "comments-asc") {
    return a.comments - b.comments || b.createdAt - a.createdAt;
  }

  if (state.sort === "repo") {
    return a.repository.localeCompare(b.repository) || b.createdAt - a.createdAt;
  }

  return 0;
}

function renderSummary() {
  const total = state.issues.length;
  const shown = state.filtered.length;
  const goodFirst = state.filtered.filter((issue) => issue.goodFirst).length;
  const repos = new Set(state.filtered.map((issue) => issue.repository)).size;

  els.summary.textContent = `Showing ${shown} of ${total} issues across ${repos} repositories. ${goodFirst} marked good first.`;
}

function renderChips() {
  renderChipSet(els.includeChips, state.includeTags, "include");
  renderChipSet(els.excludeChips, state.excludeTags, "exclude");
}

function renderChipSet(container, tags, kind) {
  if (!tags.size) {
    const empty = document.createElement("span");
    empty.className = "issue-meta";
    empty.textContent = "None";
    container.replaceChildren(empty);
    return;
  }

  container.replaceChildren(
    ...[...tags].sort((a, b) => a.localeCompare(b)).map((tag) => {
      const chip = document.createElement("span");
      chip.className = "chip";
      chip.textContent = tag;

      const button = document.createElement("button");
      button.type = "button";
      button.textContent = "x";
      button.title = `Remove ${tag}`;
      button.addEventListener("click", () => {
        const target = kind === "include" ? state.includeTags : state.excludeTags;
        target.delete(tag);
        render();
      });

      chip.append(button);
      return chip;
    }),
  );
}

function renderRows() {
  els.emptyState.hidden = state.filtered.length > 0;

  const rows = state.filtered.map((issue) => {
    const tr = document.createElement("tr");
    tr.append(
      issueCell(issue),
      textCell(issue.repository, "repo-cell"),
      goodFirstCell(issue),
      textCell(formatDate(issue.createdAt)),
      textCell(issue.comments.toLocaleString()),
      tagsCell(issue),
    );
    return tr;
  });

  els.issuesBody.replaceChildren(...rows);
}

function issueCell(issue) {
  const td = document.createElement("td");
  const link = document.createElement("a");
  link.className = "issue-link";
  link.href = issue.url;
  link.target = "_blank";
  link.rel = "noreferrer";
  link.textContent = issue.title;

  const meta = document.createElement("div");
  meta.className = "issue-meta";
  meta.textContent = `#${issue.number}`;

  td.append(link, meta);
  return td;
}

function textCell(text, className = "") {
  const td = document.createElement("td");
  if (className) {
    td.className = className;
  }
  td.textContent = text;
  return td;
}

function goodFirstCell(issue) {
  const td = document.createElement("td");
  const status = document.createElement("span");
  status.className = `status ${issue.goodFirst ? "yes" : "no"}`;
  status.textContent = issue.goodFirst ? "Yes" : "No";
  td.append(status);
  return td;
}

function tagsCell(issue) {
  const td = document.createElement("td");
  const list = document.createElement("div");
  list.className = "tag-list";

  const flagSet = new Set(issue.flags);
  const visibleTags = issue.tags.slice(0, 12);
  visibleTags.forEach((tag) => {
    const tagEl = document.createElement("span");
    tagEl.className = `tag ${flagSet.has(tag) ? "flag" : ""}`;
    tagEl.textContent = tag;
    list.append(tagEl);
  });

  if (issue.tags.length > visibleTags.length) {
    const more = document.createElement("span");
    more.className = "tag";
    more.textContent = `+${issue.tags.length - visibleTags.length}`;
    more.title = issue.tags.slice(visibleTags.length).join("; ");
    list.append(more);
  }

  td.append(list);
  return td;
}

function formatDate(date) {
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  }).format(date);
}
