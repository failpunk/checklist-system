#!/usr/bin/env python3
"""
Linear API wrapper for the checklist system.

Reads the Linear API key from $LINEAR_API_KEY, the macOS Keychain (service
"linear-checklist"), or ~/.config/checklist/api-key (in that order).

Subcommands:

  # Issue / slice
  linear.py whoami                                          # the authenticated Linear user (id, name)
  linear.py get-issue <issue-key>
  linear.py append-checkbox <issue-key> <text...>
  linear.py check-item <issue-key> <text...>
  linear.py uncheck-item <issue-key> <text...>
  linear.py create-issue <team-name> <project-name> <title> <label-name>
  linear.py mark-done <issue-key>
  linear.py set-state <issue-key> <state-name>
  linear.py archive-issue <issue-key>                       # hard-archive (Free plan 250-issue cap; archived issues do not count)
  linear.py unarchive-issue <issue-key>                     # restore an archived issue
  linear.py set-body <issue-key> <markdown-text>            # body passed inline
  linear.py set-body <issue-key> -                          # body read from stdin
  linear.py set-title <issue-key> <title...>                # rename an issue ('-' reads stdin)
  linear.py create-milestone <team> <project> <name...>     # create a project milestone (idempotent)
  linear.py set-milestone <issue-key> <milestone-name...>   # assign an issue to a project milestone
  linear.py create-comment <issue-key> <markdown | ->       # post a comment ('-' reads stdin)
  linear.py delete-comment <comment-id>                     # delete a comment by id
  linear.py get-comments <issue-key>                        # read the issue's comments

  # Team / project / label
  linear.py list-projects <team-name>
  linear.py get-project-content <team-name> <project-name>
  linear.py list-labels <team-name>
  linear.py list-open-slices <team-name> <project-name>
  linear.py audit-projects <team-name>
  linear.py create-project <team-name> <project-name> <description|->
  linear.py update-project <team-name> <project-name> [--description <text|->] [--content <markdown|->] [--status <name>]
  linear.py add-project-resource <team-name> <project-name> <url> <label...>
  linear.py post-project-update <team-name> <project-name> <body|-> [--health onTrack|atRisk|offTrack]
  linear.py create-label <team-name> <label-name>

  # Initiative
  linear.py get-initiative <initiative-name>
  linear.py get-initiative-content <initiative-name>
  linear.py add-project-to-initiative <initiative-name> <project-name>

  # Document
  linear.py list-initiative-documents <initiative-name>
  linear.py get-document <document-id>
  linear.py get-document-content <document-id>
  linear.py create-document <initiative-name> <title> <markdown | ->
  linear.py update-document <document-id> <markdown | ->

Output is JSON for queries / creates, plain text for content fetches.
All errors exit non-zero with a clear message.
"""

import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

LABEL_PALETTE = [
    "#5e6ad2",  # blue
    "#0f7b6c",  # green
    "#bc4f01",  # orange
    "#bb87fc",  # purple
    "#eb5757",  # red
    "#f2c94c",  # yellow
    "#26b5ce",  # cyan
    "#4cb782",  # light green
    "#ee7ab9",  # pink
    "#95a2b3",  # gray
]


def _next_label_color(team_id: str) -> str:
    """Pick the palette color used least often by labels already in the team.

    First-tie wins, so the palette order acts as the preference order when
    multiple colors are equally underused.
    """
    q = """
    query LabelColors($teamId: ID!) {
      teams(filter: { id: { eq: $teamId } }, first: 1) {
        nodes {
          labels(first: 250) { nodes { color } }
        }
      }
    }
    """
    result = gql(q, {"teamId": team_id})
    teams = (result.get("teams") or {}).get("nodes") or []
    used = []
    if teams:
        used = [
            (l.get("color") or "").lower()
            for l in (teams[0].get("labels") or {}).get("nodes") or []
        ]
    counts = {c: used.count(c.lower()) for c in LABEL_PALETTE}
    # Stable: use the first palette color among those tied for least-used
    min_count = min(counts.values())
    for c in LABEL_PALETTE:
        if counts[c] == min_count:
            return c
    return LABEL_PALETTE[0]

LINEAR_API_URL = "https://api.linear.app/graphql"

# Failpunk Linear color scheme by entity type (see the "Cross-entity references"
# spec doc). Override per-call with `--color <hex>` on the relevant subcommand.
DEFAULT_DOC_COLOR = "#f2994a"  # documents: orange
DEFAULT_PROJECT_COLOR = "#26b5ce"  # projects: blue
DEFAULT_INITIATIVE_COLOR = "#eb5757"  # initiatives: red


def get_api_key() -> str:
    # Env var (generic first; *_FAILPUNK_* kept for back-compat with the maintainer's setup).
    for var in ("LINEAR_API_KEY", "LINEAR_FAILPUNK_API_KEY"):
        env_key = os.environ.get(var)
        if env_key:
            return env_key.strip()
    # macOS Keychain (generic service first, then back-compat).
    try:
        import subprocess

        for service in ("linear-checklist", "linear-failpunk"):
            out = subprocess.run(
                ["security", "find-generic-password", "-w", "-s", service],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if out.returncode == 0 and out.stdout.strip():
                return out.stdout.strip()
    except Exception:
        pass
    key_file = Path.home() / ".config" / "checklist" / "api-key"
    if not key_file.exists():
        sys.exit(
            "error: no Linear API key found. Provide one of:\n"
            "  - env var LINEAR_API_KEY\n"
            "  - macOS Keychain: security add-generic-password -U -s linear-checklist -a \"$USER\" -w\n"
            "  - file ~/.config/checklist/api-key (mode 600)\n"
            "Create a key at https://linear.app/settings/api"
        )
    return key_file.read_text().strip()


def gql(query: str, variables: dict | None = None) -> dict:
    payload = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        LINEAR_API_URL,
        data=payload,
        headers={
            "Authorization": get_api_key(),
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"error: Linear API returned HTTP {e.code}: {e.read().decode()}")
    except urllib.error.URLError as e:
        sys.exit(f"error: failed to reach Linear API: {e.reason}")

    if "errors" in data:
        sys.exit(
            "error: Linear GraphQL errors:\n"
            + json.dumps(data["errors"], indent=2)
        )
    return data.get("data") or {}


def cmd_get_issue(args: list[str]) -> None:
    if len(args) != 1:
        sys.exit("usage: linear.py get-issue <issue-key>")
    issue_key = args[0]

    query = """
    query GetIssue($id: String!) {
      issue(id: $id) {
        id
        identifier
        title
        url
        description
        state { id name type }
        project { id name }
        labels { nodes { id name } }
        team {
          id
          states { nodes { id name type } }
        }
      }
    }
    """
    result = gql(query, {"id": issue_key})
    issue = result.get("issue")
    if not issue:
        sys.exit(f"error: issue not found: {issue_key}")

    # Auto-transition: Todo → In Progress when at least one checkbox is marked done.
    # Idempotent: skipped if state isn't Todo or no `- [x]` lines exist.
    if (issue.get("state") or {}).get("name", "").lower() == "todo":
        body = issue.get("description") or ""
        has_checked = bool(re.search(r"^\s*- \[[xX]\] ", body, re.MULTILINE))
        if has_checked:
            team_states = ((issue.get("team") or {}).get("states") or {}).get("nodes") or []
            target = next(
                (s for s in team_states if s["name"].lower() == "in progress"),
                None,
            )
            if not target:
                target = next(
                    (s for s in team_states if s["type"] == "started"), None
                )
            if target and target["id"] != issue["state"]["id"]:
                update = """
                mutation AutoProgress($id: String!, $stateId: String!) {
                  issueUpdate(id: $id, input: { stateId: $stateId }) {
                    success
                    issue { state { id name type } }
                  }
                }
                """
                upd = gql(update, {"id": issue["id"], "stateId": target["id"]})
                if ((upd.get("issueUpdate") or {}).get("success")):
                    issue["state"] = {"id": target["id"], "name": target["name"], "type": target["type"]}
                    promoted = _maybe_promote_project(issue["identifier"])
                    if promoted:
                        issue["project_promoted"] = promoted

    issue.pop("team", None)  # internal-only field for auto-transition lookup
    print(json.dumps(issue, indent=2))


def _insert_checkbox(body: str, text: str) -> str:
    """Insert `- [ ] text` at the end of the top contiguous checkbox block.

    - Empty body → return `- [ ] text\\n`.
    - Top of body has a checkbox block (allowing leading/internal blank lines)
      → insert after the last checkbox in that block.
    - Top of body has non-checkbox content → prepend `- [ ] text` followed by
      a `---` separator and the existing body, establishing the convention.
    """
    new_line = f"- [ ] {text}"
    if not body.strip():
        return new_line + "\n"

    lines = body.split("\n")
    last_checkbox_idx = -1
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("- [ ]") or stripped.lower().startswith("- [x]"):
            last_checkbox_idx = i
        elif line.strip() == "":
            continue
        else:
            break

    if last_checkbox_idx >= 0:
        lines.insert(last_checkbox_idx + 1, new_line)
        return "\n".join(lines)

    return f"{new_line}\n\n---\n\n{body}"


def _count_checkboxes(body: str) -> tuple[int, int]:
    """Count (done, total) checkboxes in the TOP contiguous checkbox block only.

    Mirrors `_insert_checkbox`'s boundary: scan from the top, counting checkbox
    lines (blank lines allowed within the block) and stop at the first non-blank,
    non-checkbox line — i.e. the `# ` plan/overview heading or `---` separator.
    Embedded spec/plan checkboxes below the boundary never count.
    """
    done = total = 0
    for line in body.split("\n"):
        low = line.lstrip().lower()
        if low.startswith("- [ ]"):
            total += 1
        elif low.startswith("- [x]"):
            total += 1
            done += 1
        elif line.strip() == "":
            continue
        else:
            break
    return done, total


def _find_governing_checklist_dir(issue_identifier: str) -> "Path | None":
    """Walk up from CWD (to $HOME) for a `.checklist.json` whose
    `current_slice_issue` matches `issue_identifier`. Returns the containing dir,
    or None — including when the nearest `.checklist.json` governs a different slice."""
    home = os.path.realpath(os.path.expanduser("~"))
    d = Path.cwd()
    while True:
        cfg = d / ".checklist.json"
        if cfg.is_file():
            try:
                data = json.loads(cfg.read_text())
            except (OSError, ValueError):
                data = {}
            if (data.get("current_slice_issue") or "") == issue_identifier:
                return d
            return None
        if os.path.realpath(str(d)) == home or d.parent == d:
            break
        d = d.parent
    return None


def _write_slice_state(directory: "Path", slice_id: str, done: int, total: int) -> None:
    """Write `.checklist.state.json` beside the governing `.checklist.json`. Best-effort."""
    try:
        state = {
            "slice": slice_id,
            "done": done,
            "total": total,
            "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        (directory / ".checklist.state.json").write_text(json.dumps(state) + "\n")
    except OSError:
        pass


def _sync_slice_state(issue_identifier: str, body: str) -> None:
    """After a body-mutating op, refresh the statusline cache for the governing
    project. Silent no-op if this CWD isn't inside the matching checklist project,
    and never raises (must not break the mutating command)."""
    try:
        directory = _find_governing_checklist_dir(issue_identifier)
        if directory is None:
            return
        done, total = _count_checkboxes(body)
        _write_slice_state(directory, issue_identifier, done, total)
    except Exception:
        pass


def cmd_append_checkbox(args: list[str]) -> None:
    if len(args) < 2:
        sys.exit("usage: linear.py append-checkbox <issue-key> <text...>")
    issue_key = args[0]
    text = " ".join(args[1:])

    fetch = """
    query GetForAppend($id: String!) {
      issue(id: $id) {
        id
        identifier
        description
      }
    }
    """
    result = gql(fetch, {"id": issue_key})
    issue = result.get("issue")
    if not issue:
        sys.exit(f"error: issue not found: {issue_key}")

    current = issue.get("description") or ""
    new_desc = _insert_checkbox(current, text)

    update = """
    mutation UpdateDesc($id: String!, $description: String!) {
      issueUpdate(id: $id, input: { description: $description }) {
        success
        issue { identifier }
      }
    }
    """
    result = gql(update, {"id": issue["id"], "description": new_desc})
    update_result = result.get("issueUpdate") or {}
    if not update_result.get("success"):
        sys.exit(f"error: failed to update issue {issue_key}")
    _sync_slice_state(update_result["issue"]["identifier"], new_desc)
    print(f"appended to {update_result['issue']['identifier']}: {text}")


def _toggle_checkbox(body: str, text: str, checked: bool) -> str:
    """Flip a single checkbox to the requested state.

    `checked=True`: find `- [ ] text` → `- [x] text`.
    `checked=False`: find `- [x] text` (or `- [X] text`) → `- [ ] text`.

    Match is on the trimmed text after the marker. Raises ValueError on
    0 or 2+ matches; the message includes candidate items so the caller
    can disambiguate.
    """
    if checked:
        line_re = re.compile(r"^(?P<indent>\s*)- \[ \](?P<spaces> +)(?P<text>.*?)\s*$")
        target_marker = "[x]"
        kind = "unchecked"
    else:
        line_re = re.compile(r"^(?P<indent>\s*)- \[[xX]\](?P<spaces> +)(?P<text>.*?)\s*$")
        target_marker = "[ ]"
        kind = "checked"

    target_text = text.strip()
    lines = body.split("\n")
    matches: list[tuple[int, re.Match]] = []
    candidates: list[str] = []
    for i, line in enumerate(lines):
        m = line_re.match(line)
        if m:
            item_text = m.group("text")
            candidates.append(item_text)
            if item_text == target_text:
                matches.append((i, m))

    if not matches:
        if candidates:
            raise ValueError(
                f"no {kind} item matched '{target_text}'. {kind.capitalize()} items:\n  - "
                + "\n  - ".join(candidates)
            )
        raise ValueError(f"no {kind} items in body")

    if len(matches) > 1:
        raise ValueError(
            f"{len(matches)} items matched '{target_text}' — be more specific."
        )

    i, m = matches[0]
    lines[i] = f"{m.group('indent')}- {target_marker}{m.group('spaces')}{m.group('text')}"
    return "\n".join(lines)


def _compute_target_state(
    body: str, current_state: dict, team_states: list[dict]
) -> dict | None:
    """Return the team state to transition to after a check/uncheck, or None.

    Lifecycle:
      - All items checked (and ≥1 item) → Done
      - Mixed → In Progress
      - All items unchecked (and ≥1 item) → Todo

    Returns None when there are no checkbox items, when the requested target
    state can't be found in the team, or when already in the target state.
    """
    open_count = len(re.findall(r"^\s*- \[ \]", body, re.MULTILINE))
    closed_count = len(re.findall(r"^\s*- \[[xX]\]", body, re.MULTILINE))
    if open_count + closed_count == 0:
        return None

    if open_count == 0:
        target_name, target_type = "done", "completed"
    elif closed_count == 0:
        target_name, target_type = "todo", "unstarted"
    else:
        target_name, target_type = "in progress", "started"

    target = next(
        (s for s in team_states if s["name"].lower() == target_name), None
    )
    if not target:
        target = next((s for s in team_states if s["type"] == target_type), None)
    if not target or target["id"] == current_state["id"]:
        return None
    return target


def _toggle_item(issue_key: str, text: str, checked: bool) -> None:
    fetch = """
    query GetForToggle($id: String!) {
      issue(id: $id) {
        id
        identifier
        description
        state { id name type }
        team {
          id
          states { nodes { id name type } }
        }
      }
    }
    """
    result = gql(fetch, {"id": issue_key})
    issue = result.get("issue")
    if not issue:
        sys.exit(f"error: issue not found: {issue_key}")

    current_body = issue.get("description") or ""
    try:
        new_body = _toggle_checkbox(current_body, text, checked)
    except ValueError as e:
        sys.exit(f"error: {e}")

    team_states = ((issue.get("team") or {}).get("states") or {}).get("nodes") or []
    target_state = _compute_target_state(new_body, issue["state"], team_states)

    if target_state:
        update = """
        mutation ToggleItem($id: String!, $description: String!, $stateId: String!) {
          issueUpdate(id: $id, input: { description: $description, stateId: $stateId }) {
            success
            issue { identifier state { name } }
          }
        }
        """
        result = gql(
            update,
            {
                "id": issue["id"],
                "description": new_body,
                "stateId": target_state["id"],
            },
        )
    else:
        update = """
        mutation ToggleItemNoState($id: String!, $description: String!) {
          issueUpdate(id: $id, input: { description: $description }) {
            success
            issue { identifier state { name } }
          }
        }
        """
        result = gql(update, {"id": issue["id"], "description": new_body})

    update_result = result.get("issueUpdate") or {}
    if not update_result.get("success"):
        sys.exit(f"error: failed to update issue {issue_key}")

    out = update_result["issue"]
    _sync_slice_state(out["identifier"], new_body)
    payload = {
        "identifier": out["identifier"],
        "state": out["state"]["name"],
        "action": "checked" if checked else "unchecked",
        "item": text.strip(),
    }
    promoted = _maybe_promote_project(out["identifier"])
    if promoted:
        payload["project_promoted"] = promoted
    print(json.dumps(payload))


def cmd_check_item(args: list[str]) -> None:
    if len(args) < 2:
        sys.exit("usage: linear.py check-item <issue-key> <text...>")
    _toggle_item(args[0], " ".join(args[1:]), checked=True)


def cmd_uncheck_item(args: list[str]) -> None:
    if len(args) < 2:
        sys.exit("usage: linear.py uncheck-item <issue-key> <text...>")
    _toggle_item(args[0], " ".join(args[1:]), checked=False)


def cmd_create_issue(args: list[str]) -> None:
    if len(args) not in (3, 4):
        sys.exit(
            "usage: linear.py create-issue <team-name> <project-name> <title> [label-name]\n"
            "       (label optional; pass '-' or omit for no label)"
        )
    team_name, project_name, title = args[0], args[1], args[2]
    label_name = args[3] if len(args) == 4 else None

    lookup = """
    query Lookup($teamName: String!) {
      teams(filter: { name: { eq: $teamName } }, first: 1) {
        nodes {
          id
          name
          states { nodes { id name type } }
          labels(first: 100) { nodes { id name } }
          projects(first: 100) { nodes { id name } }
        }
      }
    }
    """
    result = gql(lookup, {"teamName": team_name})
    teams = (result.get("teams") or {}).get("nodes") or []
    if not teams:
        sys.exit(f"error: team not found: {team_name}")
    team = teams[0]

    project = next(
        (p for p in team["projects"]["nodes"] if p["name"] == project_name), None
    )
    if not project:
        sys.exit(
            f"error: project '{project_name}' not found in team '{team_name}'. "
            "Create it in Linear UI first."
        )

    label = None
    if label_name and label_name != "-":
        label = next(
            (l for l in team["labels"]["nodes"] if l["name"] == label_name), None
        )
        if not label:
            sys.exit(
                f"error: label '{label_name}' not found in team '{team_name}'. "
                "Create it in Linear UI first, or omit the label."
            )

    state = next(
        (s for s in team["states"]["nodes"] if s["name"].lower() == "todo"), None
    )
    if not state:
        state = next(
            (s for s in team["states"]["nodes"] if s["type"] == "unstarted"), None
        )
    if not state:
        sys.exit(f"error: no Todo/unstarted state found in team '{team_name}'")

    create = """
    mutation CreateIssue($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue { id identifier title }
      }
    }
    """
    create_input = {
        "teamId": team["id"],
        "title": title,
        "projectId": project["id"],
        "labelIds": [label["id"]] if label else [],
        "stateId": state["id"],
    }
    result = gql(create, {"input": create_input})
    create_result = result.get("issueCreate") or {}
    if not create_result.get("success"):
        sys.exit(f"error: failed to create issue")
    issue = create_result["issue"]
    print(
        json.dumps(
            {
                "identifier": issue["identifier"],
                "id": issue["id"],
                "title": issue["title"],
            }
        )
    )


def _get_team_id(team_name: str) -> str:
    lookup = """
    query GetTeam($teamName: String!) {
      teams(filter: { name: { eq: $teamName } }, first: 1) {
        nodes { id name }
      }
    }
    """
    result = gql(lookup, {"teamName": team_name})
    teams = (result.get("teams") or {}).get("nodes") or []
    if not teams:
        sys.exit(f"error: team not found: {team_name}")
    return teams[0]["id"]


def _get_project_id(team_name: str, project_name: str) -> str:
    team_id = _get_team_id(team_name)
    query = """
    query ProjectsOfTeam($teamId: String!) {
      team(id: $teamId) { projects(first: 250) { nodes { id name } } }
    }
    """
    team = gql(query, {"teamId": team_id}).get("team") or {}
    nodes = (team.get("projects") or {}).get("nodes") or []
    for p in nodes:
        if (p.get("name") or "").lower() == project_name.lower():
            return p["id"]
    sys.exit(f"error: project not found in {team_name}: {project_name}")


def _get_org_project_statuses() -> list[dict]:
    query = "query { organization { projectStatuses { id name type } } }"
    org = gql(query).get("organization") or {}
    return org.get("projectStatuses") or []


MACHINE_HUB_RE = re.compile(r"machine hub", re.IGNORECASE)


def _maybe_promote_project(issue_key: str) -> dict | None:
    """Promote-only project roll-up (Project hygiene spec).

    When the slice is in a started/completed state and its project still sits
    in a backlog/planned status, promote the project to the started status.
    Never demotes, never completes, and skips machine-hub projects (declared
    by the words "machine hub" in the project description).
    """
    fetch = """
    query IssueProjectStatus($id: String!) {
      issue(id: $id) {
        state { type }
        project { id name description status { id name type } }
      }
    }
    """
    issue = (gql(fetch, {"id": issue_key}) or {}).get("issue") or {}
    if (issue.get("state") or {}).get("type") not in ("started", "completed"):
        return None
    project = issue.get("project")
    if not project:
        return None
    if (project.get("status") or {}).get("type") not in ("backlog", "planned"):
        return None
    if MACHINE_HUB_RE.search(project.get("description") or ""):
        return None
    started = next(
        (s for s in _get_org_project_statuses() if s["type"] == "started"), None
    )
    if not started:
        return None
    update = """
    mutation PromoteProject($id: String!, $statusId: String!) {
      projectUpdate(id: $id, input: { statusId: $statusId }) {
        success
        project { name status { name } }
      }
    }
    """
    res = (gql(update, {"id": project["id"], "statusId": started["id"]}) or {}).get(
        "projectUpdate"
    ) or {}
    if not res.get("success"):
        return None
    return {
        "project": res["project"]["name"],
        "status": res["project"]["status"]["name"],
    }


def cmd_get_project_content(args: list[str]) -> None:
    if len(args) != 2:
        sys.exit("usage: linear.py get-project-content <team-name> <project-name>")
    project_id = _get_project_id(args[0], args[1])
    query = """
    query ProjectContent($id: String!) {
      project(id: $id) { content }
    }
    """
    proj = gql(query, {"id": project_id}).get("project") or {}
    print(proj.get("content") or "")


def cmd_list_projects(args: list[str]) -> None:
    if len(args) != 1:
        sys.exit("usage: linear.py list-projects <team-name>")
    team_name = args[0]

    query = """
    query ListProjects($teamName: String!) {
      teams(filter: { name: { eq: $teamName } }, first: 1) {
        nodes {
          id
          projects(first: 100) {
            nodes { id name state }
          }
        }
      }
    }
    """
    result = gql(query, {"teamName": team_name})
    teams = (result.get("teams") or {}).get("nodes") or []
    if not teams:
        sys.exit(f"error: team not found: {team_name}")
    print(json.dumps(teams[0]["projects"]["nodes"], indent=2))


def cmd_list_labels(args: list[str]) -> None:
    if len(args) != 1:
        sys.exit("usage: linear.py list-labels <team-name>")
    team_name = args[0]

    query = """
    query ListLabels($teamName: String!) {
      teams(filter: { name: { eq: $teamName } }, first: 1) {
        nodes {
          id
          labels(first: 100) {
            nodes { id name color }
          }
        }
      }
    }
    """
    result = gql(query, {"teamName": team_name})
    teams = (result.get("teams") or {}).get("nodes") or []
    if not teams:
        sys.exit(f"error: team not found: {team_name}")
    print(json.dumps(teams[0]["labels"]["nodes"], indent=2))


def cmd_mark_done(args: list[str]) -> None:
    if len(args) != 1:
        sys.exit("usage: linear.py mark-done <issue-key>")
    issue_key = args[0]

    fetch = """
    query GetForMarkDone($id: String!) {
      issue(id: $id) {
        id
        identifier
        state { id name type }
        team {
          id
          states { nodes { id name type } }
        }
      }
    }
    """
    result = gql(fetch, {"id": issue_key})
    issue = result.get("issue")
    if not issue:
        sys.exit(f"error: issue not found: {issue_key}")

    if issue["state"]["type"] == "completed":
        print(json.dumps({"identifier": issue["identifier"], "state": issue["state"]["name"], "already_done": True}))
        return

    done_state = next(
        (s for s in issue["team"]["states"]["nodes"] if s["type"] == "completed"),
        None,
    )
    if not done_state:
        sys.exit("error: no 'completed' state found in team")

    update = """
    mutation MarkDone($id: String!, $stateId: String!) {
      issueUpdate(id: $id, input: { stateId: $stateId }) {
        success
        issue { identifier state { name } }
      }
    }
    """
    result = gql(update, {"id": issue["id"], "stateId": done_state["id"]})
    update_result = result.get("issueUpdate") or {}
    if not update_result.get("success"):
        sys.exit(f"error: failed to mark issue done")
    out = update_result["issue"]
    payload = {"identifier": out["identifier"], "state": out["state"]["name"]}
    promoted = _maybe_promote_project(out["identifier"])
    if promoted:
        payload["project_promoted"] = promoted
    print(json.dumps(payload))


def cmd_set_state(args: list[str]) -> None:
    if len(args) != 2:
        sys.exit("usage: linear.py set-state <issue-key> <state-name>")
    issue_key, state_name = args

    fetch = """
    query GetForSetState($id: String!) {
      issue(id: $id) {
        id
        identifier
        state { id name type }
        team {
          id
          states { nodes { id name type } }
        }
      }
    }
    """
    result = gql(fetch, {"id": issue_key})
    issue = result.get("issue")
    if not issue:
        sys.exit(f"error: issue not found: {issue_key}")

    target = next(
        (s for s in issue["team"]["states"]["nodes"]
         if s["name"].lower() == state_name.lower()),
        None,
    )
    if not target:
        available = ", ".join(s["name"] for s in issue["team"]["states"]["nodes"])
        sys.exit(f"error: state '{state_name}' not found. Available: {available}")

    if issue["state"]["id"] == target["id"]:
        print(json.dumps({"identifier": issue["identifier"], "state": target["name"], "unchanged": True}))
        return

    update = """
    mutation SetState($id: String!, $stateId: String!) {
      issueUpdate(id: $id, input: { stateId: $stateId }) {
        success
        issue { identifier state { name } }
      }
    }
    """
    result = gql(update, {"id": issue["id"], "stateId": target["id"]})
    update_result = result.get("issueUpdate") or {}
    if not update_result.get("success"):
        sys.exit("error: failed to update state")
    out = update_result["issue"]
    payload = {"identifier": out["identifier"], "state": out["state"]["name"]}
    promoted = _maybe_promote_project(out["identifier"])
    if promoted:
        payload["project_promoted"] = promoted
    print(json.dumps(payload))


def cmd_set_body(args: list[str]) -> None:
    if len(args) < 2:
        sys.exit(
            "usage: linear.py set-body <issue-key> <markdown-text>\n"
            "       linear.py set-body <issue-key> -    (body read from stdin)"
        )
    issue_key = args[0]
    rest = args[1:]
    if rest == ["-"]:
        body = sys.stdin.read()
    else:
        body = " ".join(rest)

    fetch = """
    query GetForSetBody($id: String!) {
      issue(id: $id) { id identifier }
    }
    """
    result = gql(fetch, {"id": issue_key})
    issue = result.get("issue")
    if not issue:
        sys.exit(f"error: issue not found: {issue_key}")

    update = """
    mutation SetBody($id: String!, $description: String!) {
      issueUpdate(id: $id, input: { description: $description }) {
        success
        issue { identifier }
      }
    }
    """
    result = gql(update, {"id": issue["id"], "description": body})
    update_result = result.get("issueUpdate") or {}
    if not update_result.get("success"):
        sys.exit("error: failed to set body")
    _sync_slice_state(update_result["issue"]["identifier"], body)
    print(json.dumps({"identifier": update_result["issue"]["identifier"], "bytes": len(body)}))


def cmd_set_title(args: list[str]) -> None:
    if len(args) < 2:
        sys.exit(
            "usage: linear.py set-title <issue-key> <title...>\n"
            "       linear.py set-title <issue-key> -    (title read from stdin)"
        )
    issue_key = args[0]
    rest = args[1:]
    title = sys.stdin.read().strip() if rest == ["-"] else " ".join(rest)
    if not title:
        sys.exit("error: empty title")

    fetch = """
    query GetForSetTitle($id: String!) {
      issue(id: $id) { id identifier }
    }
    """
    result = gql(fetch, {"id": issue_key})
    issue = result.get("issue")
    if not issue:
        sys.exit(f"error: issue not found: {issue_key}")

    update = """
    mutation SetTitle($id: String!, $title: String!) {
      issueUpdate(id: $id, input: { title: $title }) {
        success
        issue { identifier title }
      }
    }
    """
    result = gql(update, {"id": issue["id"], "title": title})
    update_result = result.get("issueUpdate") or {}
    if not update_result.get("success"):
        sys.exit("error: failed to set title")
    print(json.dumps({
        "identifier": update_result["issue"]["identifier"],
        "title": update_result["issue"]["title"],
    }))


def _resolve_project(team_name: str, project_name: str):
    lookup = """
    query LookupProj($teamName: String!) {
      teams(filter: { name: { eq: $teamName } }, first: 1) {
        nodes { id name projects(first: 100) { nodes { id name } } }
      }
    }
    """
    result = gql(lookup, {"teamName": team_name})
    teams = (result.get("teams") or {}).get("nodes") or []
    if not teams:
        sys.exit(f"error: team not found: {team_name}")
    team = teams[0]
    project = next((p for p in team["projects"]["nodes"] if p["name"] == project_name), None)
    if not project:
        sys.exit(f"error: project '{project_name}' not found in team '{team_name}'.")
    return team, project


def _project_milestones(project_id: str):
    q = """
    query PM($id: String!) {
      project(id: $id) { projectMilestones(first: 250) { nodes { id name } } }
    }
    """
    result = gql(q, {"id": project_id})
    return ((result.get("project") or {}).get("projectMilestones") or {}).get("nodes") or []


def cmd_create_milestone(args: list[str]) -> None:
    if len(args) < 3:
        sys.exit("usage: linear.py create-milestone <team-name> <project-name> <milestone-name...>")
    team_name, project_name = args[0], args[1]
    name = " ".join(args[2:])
    _, project = _resolve_project(team_name, project_name)
    existing = next((m for m in _project_milestones(project["id"]) if m["name"] == name), None)
    if existing:  # idempotent: re-running just returns the existing milestone
        print(json.dumps({"id": existing["id"], "name": existing["name"], "created": False}))
        return
    create = """
    mutation CreateMS($input: ProjectMilestoneCreateInput!) {
      projectMilestoneCreate(input: $input) { success projectMilestone { id name } }
    }
    """
    result = gql(create, {"input": {"name": name, "projectId": project["id"]}})
    cr = result.get("projectMilestoneCreate") or {}
    if not cr.get("success"):
        sys.exit("error: failed to create milestone")
    ms = cr["projectMilestone"]
    print(json.dumps({"id": ms["id"], "name": ms["name"], "created": True}))


def cmd_set_milestone(args: list[str]) -> None:
    if len(args) < 2:
        sys.exit("usage: linear.py set-milestone <issue-key> <milestone-name...>")
    issue_key = args[0]
    name = " ".join(args[1:])
    fetch = """
    query GetForMS($id: String!) {
      issue(id: $id) { id identifier project { id name } }
    }
    """
    result = gql(fetch, {"id": issue_key})
    issue = result.get("issue")
    if not issue:
        sys.exit(f"error: issue not found: {issue_key}")
    project = issue.get("project")
    if not project:
        sys.exit(f"error: {issue_key} is not in a project (project milestones require a project)")
    ms = next((m for m in _project_milestones(project["id"]) if m["name"] == name), None)
    if not ms:
        sys.exit(f"error: milestone '{name}' not found in project '{project['name']}'. "
                 f"create it: linear.py create-milestone <team> '{project['name']}' '{name}'")
    update = """
    mutation SetMS($id: String!, $milestoneId: String!) {
      issueUpdate(id: $id, input: { projectMilestoneId: $milestoneId }) {
        success issue { identifier projectMilestone { name } }
      }
    }
    """
    result = gql(update, {"id": issue["id"], "milestoneId": ms["id"]})
    ur = result.get("issueUpdate") or {}
    if not ur.get("success"):
        sys.exit("error: failed to set milestone")
    print(json.dumps({"identifier": ur["issue"]["identifier"],
                      "milestone": (ur["issue"].get("projectMilestone") or {}).get("name")}))


def cmd_create_comment(args: list[str]) -> None:
    """Post a comment on an issue (non-destructive; never overwrites the body).

    `body` inline, or '-' to read from stdin. Resolves the issue key to its id,
    then runs the GraphQL `commentCreate` mutation.
    """
    if len(args) < 2:
        sys.exit(
            "usage: linear.py create-comment <issue-key> <markdown-text>\n"
            "       linear.py create-comment <issue-key> -    (body read from stdin)"
        )
    issue_key = args[0]
    rest = args[1:]
    body = sys.stdin.read() if rest == ["-"] else " ".join(rest)
    if not body.strip():
        sys.exit("error: comment body must not be empty")

    fetch = """
    query GetForComment($id: String!) {
      issue(id: $id) { id identifier }
    }
    """
    issue = (gql(fetch, {"id": issue_key}) or {}).get("issue")
    if not issue:
        sys.exit(f"error: issue not found: {issue_key}")

    mutation = """
    mutation CreateComment($input: CommentCreateInput!) {
      commentCreate(input: $input) {
        success
        comment { id url createdAt }
      }
    }
    """
    result = gql(mutation, {"input": {"issueId": issue["id"], "body": body}})
    create_result = result.get("commentCreate") or {}
    if not create_result.get("success"):
        sys.exit(f"error: failed to create comment on {issue_key}")
    comment = create_result["comment"]
    print(json.dumps({
        "identifier": issue["identifier"],
        "comment_id": comment["id"],
        "url": comment.get("url"),
        "createdAt": comment.get("createdAt"),
    }))


def cmd_get_comments(args: list[str]) -> None:
    """Read an issue's comments via the root `comments` connection.

    Returns author display name, createdAt, and body for each comment, oldest
    first. (Inline/description-pinned comments live on a separate connection and
    may not appear here — that's acceptable per the comment-based write design.)
    """
    if len(args) != 1:
        sys.exit("usage: linear.py get-comments <issue-key>")
    issue_key = args[0]

    query = """
    query GetComments($id: String!) {
      issue(id: $id) {
        id
        identifier
        comments(first: 100) {
          nodes {
            id
            body
            createdAt
            user { name displayName }
          }
        }
      }
    }
    """
    issue = (gql(query, {"id": issue_key}) or {}).get("issue")
    if not issue:
        sys.exit(f"error: issue not found: {issue_key}")
    nodes = (issue.get("comments") or {}).get("nodes") or []
    nodes.sort(key=lambda c: c.get("createdAt") or "")
    out = [
        {
            "id": c["id"],
            "author": (c.get("user") or {}).get("displayName")
            or (c.get("user") or {}).get("name")
            or "(unknown)",
            "createdAt": c.get("createdAt"),
            "body": c.get("body") or "",
        }
        for c in nodes
    ]
    print(json.dumps(out, indent=2))


def cmd_sync_slice_state(args: list[str]) -> None:
    """sync-slice-state <issue-key> [dir]

    Fetch the issue body, count top-block checkboxes, and write
    `<dir>/.checklist.state.json` (the statusline progress cache). `dir` defaults
    to the governing dir found by walking up from CWD. Used by the SessionStart
    hook to seed the cache so the status bar is correct from the first render."""
    if not (1 <= len(args) <= 2):
        sys.exit("usage: linear.py sync-slice-state <issue-key> [dir]")
    issue_key = args[0]
    fetch = """
    query GetForState($id: String!) {
      issue(id: $id) { identifier description }
    }
    """
    issue = (gql(fetch, {"id": issue_key}) or {}).get("issue")
    if not issue:
        sys.exit(f"error: issue not found: {issue_key}")
    identifier = issue["identifier"]
    done, total = _count_checkboxes(issue.get("description") or "")
    if len(args) == 2:
        directory = Path(args[1])
    else:
        directory = _find_governing_checklist_dir(identifier)
        if directory is None:
            sys.exit(f"error: no governing .checklist.json found for {identifier}")
    _write_slice_state(directory, identifier, done, total)
    payload = {"slice": identifier, "done": done, "total": total, "dir": str(directory)}
    promoted = _maybe_promote_project(identifier)
    if promoted:
        payload["project_promoted"] = promoted
    print(json.dumps(payload))


def cmd_list_open_slices(args: list[str]) -> None:
    if len(args) != 2:
        sys.exit("usage: linear.py list-open-slices <team-name> <project-name>")
    team_name, project_name = args

    query = """
    query ListOpenSlices($teamName: String!, $projectName: String!) {
      issues(
        filter: {
          team: { name: { eq: $teamName } }
          project: { name: { eq: $projectName } }
          state: { type: { neq: "completed" } }
        }
        first: 100
      ) {
        nodes {
          id
          identifier
          title
          state { name type }
          sortOrder
        }
      }
    }
    """
    result = gql(query, {"teamName": team_name, "projectName": project_name})
    issues = (result.get("issues") or {}).get("nodes") or []
    # Sort by Linear's manual sortOrder (matches the UI's top-to-bottom priority order).
    issues.sort(key=lambda i: i.get("sortOrder") if i.get("sortOrder") is not None else float("inf"))
    for i in issues:
        i.pop("sortOrder", None)
    print(json.dumps(issues, indent=2))


def cmd_audit_projects(args: list[str]) -> None:
    """Read-only project-hygiene audit for a whole team (Project hygiene spec).

    Returns one record per project with the facts the hygiene bar needs, plus
    deterministic flags. The only flag that should trigger a WRITE is
    `needs_promotion` (promote-only status roll-up); every other flag is for an
    agent or human to judge and report, never to auto-act on. Two GraphQL
    queries total, regardless of project count.
    """
    if len(args) != 1:
        sys.exit("usage: linear.py audit-projects <team-name>")
    team_name = args[0]

    projects_q = """
    query AuditProjects($teamName: String!) {
      teams(filter: { name: { eq: $teamName } }, first: 1) {
        nodes {
          id
          projects(first: 100) {
            nodes {
              id
              name
              description
              status { name type }
              documents(first: 1) { nodes { id } }
              externalLinks(first: 1) { nodes { id } }
            }
          }
        }
      }
    }
    """
    teams = (gql(projects_q, {"teamName": team_name}).get("teams") or {}).get("nodes") or []
    if not teams:
        sys.exit(f"error: team not found: {team_name}")
    projects = (teams[0].get("projects") or {}).get("nodes") or []

    # One query for all non-completed issues in the team; group by project name.
    slices_q = """
    query AuditSlices($teamName: String!) {
      issues(
        filter: {
          team: { name: { eq: $teamName } }
          state: { type: { neq: "completed" } }
        }
        first: 250
      ) {
        nodes { identifier state { name type } project { name } }
      }
    }
    """
    issues = (gql(slices_q, {"teamName": team_name}).get("issues") or {}).get("nodes") or []
    by_project: dict[str, list[dict]] = {}
    for i in issues:
        pname = (i.get("project") or {}).get("name")
        if pname:
            by_project.setdefault(pname, []).append(
                {"identifier": i["identifier"],
                 "state": (i.get("state") or {}).get("name"),
                 "type": (i.get("state") or {}).get("type")}
            )

    records = []
    for p in projects:
        desc = (p.get("description") or "").strip()
        status = p.get("status") or {}
        status_type = status.get("type")
        is_hub = bool(MACHINE_HUB_RE.search(desc))
        open_slices = by_project.get(p["name"], [])
        has_active_slice = any(s["type"] == "started" for s in open_slices)
        has_resources = bool(
            (p.get("documents") or {}).get("nodes")
            or (p.get("externalLinks") or {}).get("nodes")
        )
        records.append({
            "name": p["name"],
            "status": status.get("name"),
            "status_type": status_type,
            "is_machine_hub": is_hub,
            "description_chars": len(desc),
            "open_slices": open_slices,
            # The ONLY write-trigger: backlog/planned project with an active slice.
            "needs_promotion": (
                status_type in ("backlog", "planned")
                and has_active_slice
                and not is_hub
            ),
            # Judgment flags — report, never auto-act:
            "missing_description": not desc,
            "missing_resources": not has_resources and not is_hub,
            "status_possibly_stale": status_type == "started" and not has_active_slice,
        })
    records.sort(key=lambda r: r["name"])
    print(json.dumps(records, indent=2))


def cmd_create_project(args: list[str]) -> None:
    args, color = _pop_color(args)
    if len(args) != 3:
        sys.exit(
            "usage: linear.py create-project <team-name> <project-name> <description|-> [--color <hex>]\n"
            "       (description is required per the Project hygiene spec; '-' reads it from stdin.\n"
            "        Say what this is, where it lives on disk, and how to pick it up cold.)\n"
            f"       (color defaults to {DEFAULT_PROJECT_COLOR})"
        )
    team_name, project_name, description = args
    if description == "-":
        description = sys.stdin.read().strip()
    if not description.strip():
        sys.exit("error: description must not be empty (Project hygiene spec)")
    if len(description) > 255:
        sys.exit(
            f"error: Linear caps project descriptions at 255 chars (got {len(description)})."
        )
    team_id = _get_team_id(team_name)

    create = """
    mutation CreateProject($input: ProjectCreateInput!) {
      projectCreate(input: $input) {
        success
        project { id name color }
      }
    }
    """
    result = gql(
        create,
        {
            "input": {
                "name": project_name,
                "teamIds": [team_id],
                "description": description,
                "color": color or DEFAULT_PROJECT_COLOR,
            }
        },
    )
    create_result = result.get("projectCreate") or {}
    if not create_result.get("success"):
        sys.exit("error: failed to create project")
    print(json.dumps(create_result["project"]))


def _pop_flag(args: list[str], flag: str) -> tuple[list[str], str | None]:
    """Remove `--flag value` from args; return (remaining, value or None)."""
    if flag in args:
        i = args.index(flag)
        if i + 1 >= len(args):
            sys.exit(f"error: {flag} requires a value")
        value = args[i + 1]
        return args[:i] + args[i + 2 :], value
    return args, None


def cmd_update_project(args: list[str]) -> None:
    args, description = _pop_flag(args, "--description")
    args, content = _pop_flag(args, "--content")
    args, status_name = _pop_flag(args, "--status")
    if len(args) != 2 or not (description or content or status_name):
        sys.exit(
            "usage: linear.py update-project <team-name> <project-name>\n"
            "         [--description <text|->] [--content <markdown|->] [--status <name>]\n"
            "       (at least one flag required; '-' reads that value from stdin;\n"
            "        description = short list-view text, content = overview body)"
        )
    team_name, project_name = args
    if [description, content].count("-") > 1:
        sys.exit("error: only one of --description/--content may read from stdin")
    if description == "-":
        description = sys.stdin.read().strip()
    if content == "-":
        content = sys.stdin.read()
    if description is not None and len(description) > 255:
        sys.exit(
            f"error: Linear caps project descriptions at 255 chars (got {len(description)}). "
            "Put the overflow in --content."
        )

    project_id = _get_project_id(team_name, project_name)
    input_obj: dict = {}
    if description is not None:
        input_obj["description"] = description
    if content is not None:
        input_obj["content"] = content
    if status_name is not None:
        statuses = _get_org_project_statuses()
        target = next(
            (s for s in statuses if s["name"].lower() == status_name.lower()), None
        )
        if not target:
            available = ", ".join(s["name"] for s in statuses)
            sys.exit(
                f"error: project status '{status_name}' not found. Available: {available}"
            )
        input_obj["statusId"] = target["id"]

    update = """
    mutation UpdateProjectFields($id: String!, $input: ProjectUpdateInput!) {
      projectUpdate(id: $id, input: $input) {
        success
        project { id name status { name } }
      }
    }
    """
    res = (gql(update, {"id": project_id, "input": input_obj}) or {}).get(
        "projectUpdate"
    ) or {}
    if not res.get("success"):
        sys.exit("error: failed to update project")
    out = res["project"]
    print(
        json.dumps(
            {
                "project": out["name"],
                "status": out["status"]["name"],
                "updated": sorted(
                    k for k in ("description", "content", "statusId") if k in input_obj
                ),
            }
        )
    )


def cmd_add_project_resource(args: list[str]) -> None:
    if len(args) < 4:
        sys.exit(
            "usage: linear.py add-project-resource <team-name> <project-name> <url> <label...>"
        )
    team_name, project_name, url = args[0], args[1], args[2]
    label = " ".join(args[3:])
    project_id = _get_project_id(team_name, project_name)
    create = """
    mutation AddProjectResource($input: EntityExternalLinkCreateInput!) {
      entityExternalLinkCreate(input: $input) {
        success
        entityExternalLink { id url label }
      }
    }
    """
    res = (
        gql(create, {"input": {"projectId": project_id, "url": url, "label": label}})
        or {}
    ).get("entityExternalLinkCreate") or {}
    if not res.get("success"):
        sys.exit("error: failed to add project resource")
    print(json.dumps(res["entityExternalLink"]))


VALID_HEALTH = ("onTrack", "atRisk", "offTrack")


def cmd_post_project_update(args: list[str]) -> None:
    args, health = _pop_flag(args, "--health")
    if len(args) < 3:
        sys.exit(
            "usage: linear.py post-project-update <team-name> <project-name> <body|-> [--health onTrack|atRisk|offTrack]\n"
            "       (health defaults to onTrack)"
        )
    team_name, project_name = args[0], args[1]
    rest = args[2:]
    body = sys.stdin.read() if rest == ["-"] else " ".join(rest)
    if not body.strip():
        sys.exit("error: update body must not be empty")
    health = health or "onTrack"
    if health not in VALID_HEALTH:
        sys.exit(f"error: invalid health '{health}'. Valid: {', '.join(VALID_HEALTH)}")
    project_id = _get_project_id(team_name, project_name)
    create = """
    mutation PostProjectUpdate($input: ProjectUpdateCreateInput!) {
      projectUpdateCreate(input: $input) {
        success
        projectUpdate { id url health }
      }
    }
    """
    res = (
        gql(create, {"input": {"projectId": project_id, "body": body, "health": health}})
        or {}
    ).get("projectUpdateCreate") or {}
    if not res.get("success"):
        sys.exit("error: failed to post project update")
    print(json.dumps(res["projectUpdate"]))


def cmd_create_label(args: list[str]) -> None:
    if len(args) != 2:
        sys.exit("usage: linear.py create-label <team-name> <label-name>")
    team_name, label_name = args
    team_id = _get_team_id(team_name)
    color = _next_label_color(team_id)

    create = """
    mutation CreateLabel($input: IssueLabelCreateInput!) {
      issueLabelCreate(input: $input) {
        success
        issueLabel { id name color }
      }
    }
    """
    result = gql(
        create,
        {"input": {"name": label_name, "teamId": team_id, "color": color}},
    )
    create_result = result.get("issueLabelCreate") or {}
    if not create_result.get("success"):
        sys.exit("error: failed to create label")
    print(json.dumps(create_result["issueLabel"]))


def cmd_add_label(args: list[str]) -> None:
    """add-label <issue-key> <label-name> — add a team label to an existing issue.

    Idempotent: re-adding a label the issue already has is a no-op. Resolves the
    label by name within the issue's team (case-insensitive)."""
    if len(args) != 2:
        sys.exit("usage: linear.py add-label <issue-key> <label-name>")
    issue_key, label_name = args
    fetch = """
    query GetForAddLabel($id: String!) {
      issue(id: $id) {
        id
        identifier
        labels { nodes { id name } }
        team { id labels(first: 250) { nodes { id name } } }
      }
    }
    """
    issue = (gql(fetch, {"id": issue_key}) or {}).get("issue")
    if not issue:
        sys.exit(f"error: issue not found: {issue_key}")
    team_labels = ((issue.get("team") or {}).get("labels") or {}).get("nodes") or []
    target = next((l for l in team_labels if l["name"].lower() == label_name.lower()), None)
    if not target:
        available = ", ".join(l["name"] for l in team_labels)
        sys.exit(f"error: label '{label_name}' not found in team. Available: {available}")
    current = [l["id"] for l in (issue.get("labels") or {}).get("nodes") or []]
    if target["id"] in current:
        print(json.dumps({"identifier": issue["identifier"], "label": target["name"], "added": False}))
        return
    update = """
    mutation AddLabel($id: String!, $labelIds: [String!]!) {
      issueUpdate(id: $id, input: { labelIds: $labelIds }) {
        success
        issue { identifier labels { nodes { name } } }
      }
    }
    """
    res = (gql(update, {"id": issue["id"], "labelIds": current + [target["id"]]}) or {}).get("issueUpdate") or {}
    if not res.get("success"):
        sys.exit("error: failed to add label")
    out = res["issue"]
    print(json.dumps({
        "identifier": out["identifier"],
        "label": target["name"],
        "added": True,
        "labels": [l["name"] for l in (out.get("labels") or {}).get("nodes") or []],
    }))


def _get_initiative(name: str) -> dict:
    lookup = """
    query GetInitiative($name: String!) {
      initiatives(filter: { name: { eq: $name } }, first: 1) {
        nodes { id name url description content slugId }
      }
    }
    """
    result = gql(lookup, {"name": name})
    inits = (result.get("initiatives") or {}).get("nodes") or []
    if not inits:
        sys.exit(f"error: initiative not found: {name}")
    return inits[0]


def cmd_get_initiative(args: list[str]) -> None:
    if len(args) != 1:
        sys.exit("usage: linear.py get-initiative <name>")
    init = _get_initiative(args[0])
    # Don't print content (can be large); include length as a hint
    summary = {k: v for k, v in init.items() if k != "content"}
    summary["contentLength"] = len(init.get("content") or "")
    print(json.dumps(summary, indent=2))


def cmd_get_initiative_content(args: list[str]) -> None:
    if len(args) != 1:
        sys.exit("usage: linear.py get-initiative-content <name>")
    init = _get_initiative(args[0])
    sys.stdout.write(init.get("content") or "")


def cmd_create_initiative(args: list[str]) -> None:
    args, color = _pop_color(args)
    description = None
    if "--description" in args:
        i = args.index("--description")
        if i + 1 >= len(args):
            sys.exit("error: --description requires a value")
        description = args[i + 1]
        args = args[:i] + args[i + 2 :]
    if len(args) != 1:
        sys.exit(
            "usage: linear.py create-initiative <name> [--color <hex>] [--description <text>]\n"
            f"       (color defaults to {DEFAULT_INITIATIVE_COLOR})"
        )
    init_input = {"name": args[0], "color": color or DEFAULT_INITIATIVE_COLOR}
    if description is not None:
        init_input["description"] = description

    mutation = """
    mutation CreateInitiative($input: InitiativeCreateInput!) {
      initiativeCreate(input: $input) {
        success
        initiative { id name url color }
      }
    }
    """
    result = gql(mutation, {"input": init_input})
    create_result = result.get("initiativeCreate") or {}
    if not create_result.get("success"):
        sys.exit("error: failed to create initiative")
    print(json.dumps(create_result["initiative"], indent=2))


def cmd_update_initiative(args: list[str]) -> None:
    args, color = _pop_color(args)
    if len(args) < 2:
        sys.exit(
            "usage: linear.py update-initiative <name> <markdown-text>\n"
            "       linear.py update-initiative <name> -    (content read from stdin)\n"
            "       (optional: --color <hex>)"
        )
    name = args[0]
    rest = args[1:]
    content = sys.stdin.read() if rest == ["-"] else " ".join(rest)
    init = _get_initiative(name)
    upd_input = {"content": content}
    if color is not None:
        upd_input["color"] = color

    mutation = """
    mutation UpdateInitiative($id: String!, $input: InitiativeUpdateInput!) {
      initiativeUpdate(id: $id, input: $input) {
        success
        initiative { id name url color }
      }
    }
    """
    result = gql(mutation, {"id": init["id"], "input": upd_input})
    update_result = result.get("initiativeUpdate") or {}
    if not update_result.get("success"):
        sys.exit("error: failed to update initiative")
    print(json.dumps(update_result["initiative"], indent=2))


def cmd_add_project_to_initiative(args: list[str]) -> None:
    if len(args) != 2:
        sys.exit(
            "usage: linear.py add-project-to-initiative <initiative-name> <project-name>"
        )
    initiative_name, project_name = args
    init = _get_initiative(initiative_name)

    # Resolve project by name (across all teams the user has access to)
    project_lookup = """
    query GetProject($name: String!) {
      projects(filter: { name: { eq: $name } }, first: 1) {
        nodes { id name }
      }
    }
    """
    result = gql(project_lookup, {"name": project_name})
    projects = (result.get("projects") or {}).get("nodes") or []
    if not projects:
        sys.exit(f"error: project not found: {project_name}")
    project = projects[0]

    mutation = """
    mutation Link($input: InitiativeToProjectCreateInput!) {
      initiativeToProjectCreate(input: $input) {
        success
        initiativeToProject {
          id
          initiative { name }
          project { name }
        }
      }
    }
    """
    try:
        result = gql(
            mutation,
            {"input": {"initiativeId": init["id"], "projectId": project["id"]}},
        )
    except SystemExit as e:
        # Idempotent: a "project nesting conflict" means the link already exists.
        if "project nesting conflict" in str(e):
            print(
                json.dumps(
                    {
                        "alreadyLinked": True,
                        "initiative": initiative_name,
                        "project": project_name,
                    },
                    indent=2,
                )
            )
            return
        raise
    create_result = result.get("initiativeToProjectCreate") or {}
    if not create_result.get("success"):
        sys.exit("error: failed to link project to initiative")
    print(json.dumps(create_result["initiativeToProject"], indent=2))


def cmd_list_initiative_documents(args: list[str]) -> None:
    if len(args) != 1:
        sys.exit("usage: linear.py list-initiative-documents <initiative-name>")
    init = _get_initiative(args[0])
    query = """
    query GetDocs($id: String!) {
      initiative(id: $id) {
        documents(first: 100) {
          nodes { id title url slugId updatedAt }
        }
      }
    }
    """
    result = gql(query, {"id": init["id"]})
    docs = (result.get("initiative") or {}).get("documents", {}).get("nodes") or []
    print(json.dumps(docs, indent=2))


def cmd_get_document(args: list[str]) -> None:
    if len(args) != 1:
        sys.exit("usage: linear.py get-document <document-id>")
    ident = args[0]
    query = """
    query GetDoc($id: String!) {
      document(id: $id) {
        id title url slugId content
        initiative { id name }
        updatedAt
      }
    }
    """
    result = gql(query, {"id": ident})
    doc = result.get("document")
    if not doc:
        sys.exit(f"error: document not found: {ident}")
    print(json.dumps(doc, indent=2))


def cmd_get_document_content(args: list[str]) -> None:
    if len(args) != 1:
        sys.exit("usage: linear.py get-document-content <document-id>")
    ident = args[0]
    query = """
    query GetDoc($id: String!) {
      document(id: $id) { content }
    }
    """
    result = gql(query, {"id": ident})
    doc = result.get("document")
    if not doc:
        sys.exit(f"error: document not found: {ident}")
    sys.stdout.write(doc.get("content") or "")


def cmd_list_project_documents(args: list[str]) -> None:
    if len(args) != 2:
        sys.exit("usage: linear.py list-project-documents <team> <project>")
    project_id = _get_project_id(args[0], args[1])
    query = """
    query ProjectDocs($id: String!) {
      project(id: $id) {
        documents(first: 250) { nodes { id title url color updatedAt } }
      }
    }
    """
    project = gql(query, {"id": project_id}).get("project") or {}
    docs = (project.get("documents") or {}).get("nodes") or []
    print(json.dumps(docs, indent=2))


def cmd_create_project_document(args: list[str]) -> None:
    args, color = _pop_color(args)
    if len(args) < 4:
        sys.exit(
            "usage: linear.py create-project-document <team> <project> <title> <markdown|-> [--color <hex>]\n"
            f"       (color defaults to {DEFAULT_DOC_COLOR})"
        )
    team_name, project_name, title = args[0], args[1], args[2]
    rest = args[3:]
    content = sys.stdin.read() if rest == ["-"] else " ".join(rest)
    project_id = _get_project_id(team_name, project_name)

    mutation = """
    mutation CreateProjectDoc($input: DocumentCreateInput!) {
      documentCreate(input: $input) {
        success
        document { id title url slugId color }
      }
    }
    """
    result = gql(
        mutation,
        {"input": {
            "title": title,
            "content": content,
            "projectId": project_id,
            "color": color or DEFAULT_DOC_COLOR,
        }},
    )
    create_result = result.get("documentCreate") or {}
    if not create_result.get("success"):
        sys.exit("error: failed to create project document")
    print(json.dumps(create_result["document"], indent=2))


def cmd_create_team_document(args: list[str]) -> None:
    args, color = _pop_color(args)
    if len(args) < 3:
        sys.exit(
            "usage: linear.py create-team-document <team-name> <title> <markdown|-> [--color <hex>]\n"
            f"       (color defaults to {DEFAULT_DOC_COLOR})"
        )
    team_name, title = args[0], args[1]
    rest = args[2:]
    content = sys.stdin.read() if rest == ["-"] else " ".join(rest)
    team_id = _get_team_id(team_name)

    mutation = """
    mutation CreateTeamDoc($input: DocumentCreateInput!) {
      documentCreate(input: $input) {
        success
        document { id title url slugId color }
      }
    }
    """
    result = gql(
        mutation,
        {"input": {
            "title": title,
            "content": content,
            "teamId": team_id,
            "color": color or DEFAULT_DOC_COLOR,
        }},
    )
    create_result = result.get("documentCreate") or {}
    if not create_result.get("success"):
        sys.exit("error: failed to create team document")
    print(json.dumps(create_result["document"], indent=2))


def cmd_list_team_documents(args: list[str]) -> None:
    if len(args) != 1:
        sys.exit("usage: linear.py list-team-documents <team-name>")
    team_id = _get_team_id(args[0])
    query = """
    query TeamDocs($id: ID!) {
      documents(filter: { team: { id: { eq: $id } } }, first: 250) {
        nodes { id title url slugId color updatedAt }
      }
    }
    """
    result = gql(query, {"id": team_id})
    docs = (result.get("documents") or {}).get("nodes") or []
    print(json.dumps(docs, indent=2))


def cmd_move_document(args: list[str]) -> None:
    if len(args) != 3 or args[1] != "--to-team":
        sys.exit("usage: linear.py move-document <document-id> --to-team <team-name>")
    doc_id, team_name = args[0], args[2]
    team_id = _get_team_id(team_name)

    mutation = """
    mutation MoveDoc($id: String!, $input: DocumentUpdateInput!) {
      documentUpdate(id: $id, input: $input) {
        success
        document { id title url team { name } initiative { name } project { name } }
      }
    }
    """
    result = gql(
        mutation,
        {"id": doc_id, "input": {
            "teamId": team_id,
            "initiativeId": None,
            "projectId": None,
        }},
    )
    update_result = result.get("documentUpdate") or {}
    if not update_result.get("success"):
        sys.exit("error: failed to move document")
    print(json.dumps(update_result["document"], indent=2))


def _splice_doc_index(content: str, block: str) -> str:
    """Replace the managed '## Documentation' section in `content` with `block`
    (from the heading line up to the next top-level '## ' heading or EOF).
    Append the block if the section isn't present. Preserves all other content."""
    heading = "## Documentation"
    lines = (content or "").split("\n")
    start = next((i for i, ln in enumerate(lines) if ln.strip() == heading), None)
    if start is None:
        base = (content or "").rstrip()
        return (base + "\n\n" + block + "\n") if base else (block + "\n")
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    tail = lines[end:]
    new_lines = lines[:start] + block.split("\n") + ([""] + tail if tail else [])
    return "\n".join(new_lines)


def cmd_update_doc_index(args: list[str]) -> None:
    if len(args) != 2:
        sys.exit("usage: linear.py update-doc-index <team> <project>")
    project_id = _get_project_id(args[0], args[1])
    query = """
    query DocIndex($id: String!) {
      project(id: $id) {
        content
        documents(first: 250) { nodes { title url } }
      }
    }
    """
    proj = gql(query, {"id": project_id}).get("project") or {}
    docs = sorted(
        (proj.get("documents") or {}).get("nodes") or [],
        key=lambda d: (d.get("title") or "").lower(),
    )
    if docs:
        body = "\n".join(f"- [{d['title']}]({d['url']})" for d in docs)
        block = f"## Documentation\n\n{body}\n\n_Living Docs — maintained by the [Documentation System](https://linear.app/failpunkllc/initiative/documentation-system-75b5f0c34e5a)._"
    else:
        block = "## Documentation\n\n_No Living Docs yet._"
    new_content = _splice_doc_index(proj.get("content") or "", block)

    mutation = """
    mutation UpdateProjectContent($id: String!, $content: String!) {
      projectUpdate(id: $id, input: { content: $content }) {
        success
        project { id name }
      }
    }
    """
    result = gql(mutation, {"id": project_id, "content": new_content})
    if not (result.get("projectUpdate") or {}).get("success"):
        sys.exit("error: failed to update project doc index")
    print(json.dumps({"project": args[1], "docs_indexed": len(docs)}))


def _pop_color(args: list[str]) -> tuple[list[str], str | None]:
    """Pull an optional `--color <hex>` flag out of args, returning (remaining, color)."""
    if "--color" in args:
        i = args.index("--color")
        if i + 1 >= len(args):
            sys.exit("error: --color requires a hex value, e.g. --color '#f2994a'")
        color = args[i + 1]
        return args[:i] + args[i + 2 :], color
    return args, None


def cmd_create_document(args: list[str]) -> None:
    args, color = _pop_color(args)
    if len(args) < 3:
        sys.exit(
            "usage: linear.py create-document <initiative-name> <title> <markdown-text> [--color <hex>]\n"
            "       linear.py create-document <initiative-name> <title> -    (content read from stdin)\n"
            f"       (color defaults to {DEFAULT_DOC_COLOR})"
        )
    initiative_name = args[0]
    title = args[1]
    rest = args[2:]
    if rest == ["-"]:
        content = sys.stdin.read()
    else:
        content = " ".join(rest)

    init = _get_initiative(initiative_name)

    mutation = """
    mutation CreateDoc($input: DocumentCreateInput!) {
      documentCreate(input: $input) {
        success
        document { id title url slugId color }
      }
    }
    """
    result = gql(
        mutation,
        {
            "input": {
                "title": title,
                "content": content,
                "initiativeId": init["id"],
                "color": color or DEFAULT_DOC_COLOR,
            }
        },
    )
    create_result = result.get("documentCreate") or {}
    if not create_result.get("success"):
        sys.exit("error: failed to create document")
    print(json.dumps(create_result["document"], indent=2))


def cmd_update_document(args: list[str]) -> None:
    args, color = _pop_color(args)
    if len(args) < 2:
        sys.exit(
            "usage: linear.py update-document <document-id> <markdown-text> [--color <hex>]\n"
            "       linear.py update-document <document-id> -    (content read from stdin)"
        )
    doc_id = args[0]
    rest = args[1:]
    if rest == ["-"]:
        content = sys.stdin.read()
    else:
        content = " ".join(rest)

    doc_input = {"content": content}
    if color is not None:
        doc_input["color"] = color

    mutation = """
    mutation UpdateDoc($id: String!, $input: DocumentUpdateInput!) {
      documentUpdate(id: $id, input: $input) {
        success
        document { id title url color }
      }
    }
    """
    result = gql(mutation, {"id": doc_id, "input": doc_input})
    update_result = result.get("documentUpdate") or {}
    if not update_result.get("success"):
        sys.exit("error: failed to update document")
    print(json.dumps(update_result["document"], indent=2))


def cmd_delete_document(args: list[str]) -> None:
    if len(args) != 1:
        sys.exit("usage: linear.py delete-document <document-id>")
    mutation = """
    mutation DeleteDoc($id: String!) {
      documentDelete(id: $id) { success }
    }
    """
    result = gql(mutation, {"id": args[0]})
    if not (result.get("documentDelete") or {}).get("success"):
        sys.exit("error: failed to delete document")
    print(json.dumps({"deleted": args[0]}))


def cmd_archive_issue(args: list[str]) -> None:
    if len(args) != 1:
        sys.exit("usage: linear.py archive-issue <issue-key>")
    issue_key = args[0]
    fetch = """
    query GetForArchive($id: String!) {
      issue(id: $id) { id identifier state { name } }
    }
    """
    issue = (gql(fetch, {"id": issue_key}) or {}).get("issue")
    if not issue:
        sys.exit(f"error: issue not found: {issue_key}")
    mutation = """
    mutation ArchiveIssue($id: String!) {
      issueArchive(id: $id) { success }
    }
    """
    res = (gql(mutation, {"id": issue["id"]}) or {}).get("issueArchive") or {}
    if not res.get("success"):
        sys.exit("error: failed to archive issue")
    print(json.dumps({"identifier": issue["identifier"], "archived": True, "was_state": issue["state"]["name"]}))


def cmd_unarchive_issue(args: list[str]) -> None:
    if len(args) != 1:
        sys.exit("usage: linear.py unarchive-issue <issue-key>")
    issue_key = args[0]
    fetch = """
    query GetForUnarchive($id: String!) {
      issue(id: $id) { id identifier }
    }
    """
    issue = (gql(fetch, {"id": issue_key}) or {}).get("issue")
    if not issue:
        sys.exit(f"error: issue not found: {issue_key}")
    mutation = """
    mutation UnarchiveIssue($id: String!) {
      issueUnarchive(id: $id) { success }
    }
    """
    res = (gql(mutation, {"id": issue["id"]}) or {}).get("issueUnarchive") or {}
    if not res.get("success"):
        sys.exit("error: failed to unarchive issue")
    print(json.dumps({"identifier": issue["identifier"], "unarchived": True}))


def cmd_delete_comment(args: list[str]) -> None:
    if len(args) != 1:
        sys.exit("usage: linear.py delete-comment <comment-id>")
    comment_id = args[0]
    mutation = """
    mutation DeleteComment($id: String!) {
      commentDelete(id: $id) { success }
    }
    """
    res = (gql(mutation, {"id": comment_id}) or {}).get("commentDelete") or {}
    if not res.get("success"):
        sys.exit("error: failed to delete comment")
    print(json.dumps({"deleted_comment": comment_id}))


def cmd_whoami(args: list[str]) -> None:
    q = "query { viewer { id name displayName email } }"
    v = (gql(q) or {}).get("viewer") or {}
    print(json.dumps(v))


HANDLERS = {
    "whoami": cmd_whoami,
    "get-issue": cmd_get_issue,
    "append-checkbox": cmd_append_checkbox,
    "check-item": cmd_check_item,
    "uncheck-item": cmd_uncheck_item,
    "sync-slice-state": cmd_sync_slice_state,
    "create-issue": cmd_create_issue,
    "mark-done": cmd_mark_done,
    "set-state": cmd_set_state,
    "archive-issue": cmd_archive_issue,
    "unarchive-issue": cmd_unarchive_issue,
    "set-body": cmd_set_body,
    "set-title": cmd_set_title,
    "create-milestone": cmd_create_milestone,
    "set-milestone": cmd_set_milestone,
    "create-comment": cmd_create_comment,
    "delete-comment": cmd_delete_comment,
    "get-comments": cmd_get_comments,
    "list-projects": cmd_list_projects,
    "get-project-content": cmd_get_project_content,
    "list-labels": cmd_list_labels,
    "list-open-slices": cmd_list_open_slices,
    "audit-projects": cmd_audit_projects,
    "create-project": cmd_create_project,
    "update-project": cmd_update_project,
    "add-project-resource": cmd_add_project_resource,
    "post-project-update": cmd_post_project_update,
    "create-label": cmd_create_label,
    "add-label": cmd_add_label,
    "get-initiative": cmd_get_initiative,
    "get-initiative-content": cmd_get_initiative_content,
    "create-initiative": cmd_create_initiative,
    "update-initiative": cmd_update_initiative,
    "add-project-to-initiative": cmd_add_project_to_initiative,
    "list-initiative-documents": cmd_list_initiative_documents,
    "get-document": cmd_get_document,
    "get-document-content": cmd_get_document_content,
    "create-document": cmd_create_document,
    "update-document": cmd_update_document,
    "delete-document": cmd_delete_document,
    "list-project-documents": cmd_list_project_documents,
    "create-project-document": cmd_create_project_document,
    "create-team-document": cmd_create_team_document,
    "list-team-documents": cmd_list_team_documents,
    "move-document": cmd_move_document,
    "update-doc-index": cmd_update_doc_index,
}


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd, *args = sys.argv[1:]
    handler = HANDLERS.get(cmd)
    if not handler:
        sys.exit(
            f"unknown subcommand: {cmd}\nAvailable: {', '.join(HANDLERS)}"
        )
    handler(args)


if __name__ == "__main__":
    main()
