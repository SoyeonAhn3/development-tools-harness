---
name: harness-github-push
description: >-
  For the development-tools-harness repository, review the Git working tree, protect secrets, stage the intended changes, draft or use an approved commit message, commit, and safely push to a GitHub remote; initialize Git and configure origin when needed, and optionally record a compatible dev-log entry after success. Use when the user asks to upload changes to GitHub, run git push, commit and push, publish the current repository, configure a GitHub remote, or says "깃허브에 올려줘", "git push해줘", "변경사항 올려줘", "커밋해줘", or "커밋하고 푸시해줘".
---

# GitHub Push — development-tools-harness

Inspect, commit, and push repository changes with an explicit, auditable scope. Use Git CLI commands and adapt their syntax to the active shell.

## Project scope

- This skill belongs to the repository containing this file. Resolve that root from `.agents/skills/harness-github-push/SKILL.md` and verify it with `git rev-parse --show-toplevel`; do not operate on a different project from this skill.
- Expected GitHub repository: `https://github.com/SoyeonAhn3/development-tools-harness.git`. HTTPS and SSH URLs for the same owner/repository are equivalent. Read the actual remotes every time; do not silently create, replace or redirect a remote based on this reference. Explain an unexpected destination before publishing.
- The Git workflow is a user-invoked development operation. It does not grant the harness Planner, Developer or Reviewer permission to perform Git writes.
- Requests to install or edit this skill do not authorize staging, committing or pushing product changes.

## Preserve user work and credentials

- Never discard, overwrite, reset, amend, rebase, merge, or clean existing work unless the user explicitly requests that exact operation.
- Never change an existing remote URL, branch name, or upstream without explaining the change and receiving approval.
- Never run `git push --force`. Use `--force-with-lease` only when the user explicitly requests history rewriting after reviewing the affected commits.
- Never bypass hooks with `--no-verify` unless explicitly requested.
- Never ask the user to paste a password or Personal Access Token into chat. Prefer Git Credential Manager, `gh auth login`, or SSH authentication.
- Treat a commit-only request as authorization to commit, not to push. Push only when the user requests publishing, uploading, or pushing.

## 1. Locate or initialize the repository

Run `git rev-parse --show-toplevel` from the requested working directory. Use the returned root for every subsequent command.

If the directory is not a Git worktree:

1. Confirm from the request and directory contents that this is the intended project root. Ask only if the target is ambiguous.
2. Review the existing `.gitignore`; create or extend it without replacing project-specific rules.
3. Ensure actual secret files are ignored, including `.env`, `.env.*`, `*.env`, `api.env`, `.claude/api.env`, private keys, and credential files. Preserve intentional templates with exceptions such as `!.env.example`, `!.env.sample`, and `!.env.template` where appropriate.
4. Do not add generic `logs/`, `archive/`, or `output/` rules unless project conventions require them. Ignore `logs/` when the compatible dev-log integration below is active.
5. Initialize with `git init -b main` when supported; otherwise use `git init` followed by `git branch -M main`.

Inspect remotes with `git remote -v`. If no push remote exists, request the GitHub or GitHub Enterprise repository URL, then add it with `git remote add origin <url>`. Do not silently replace an existing `origin`.

## 2. Inspect the full change set

Run at minimum:

```text
git status --short --branch
git diff --stat
git diff --cached --stat
git diff
git diff --cached
```

Also inspect relevant untracked files because ordinary diffs omit them. Review recent commit subjects with `git log -5 --pretty=format:%s` so the proposed message follows repository conventions.

If there are no relevant changes, report that there is nothing to commit or push and stop without creating an empty commit.

Before staging:

- Identify which files belong to the user's request and leave unrelated changes untouched.
- Check suspicious filenames and changed content for tokens, passwords, private keys, connection strings, personal data, or generated secrets. Use an installed secret scanner when available.
- Check whether sensitive paths are already tracked; `.gitignore` does not untrack them. If a likely secret is found, stop and report only its path and remediation, never its value.
- Note submodules, large binaries, generated artifacts, and unexpected deletions for the user when they materially affect the commit.

## 3. Stage only the reviewed scope

Stage explicit paths with `git add -- <paths>`. Use `git add -A` only when the user requested all changes and every listed change was reviewed.

Validate the exact staged snapshot:

```text
git diff --cached --check
git diff --cached --name-status
git diff --cached --stat
git diff --cached
```

If validation exposes an unintended or sensitive file, unstage only that path with `git restore --staged -- <path>` and resolve the issue. Do not alter its working-tree contents.

## 4. Draft and confirm the commit

Draft a concise subject, preferably at most 50 characters when the repository has no stronger convention. Use an imperative summary and add a short body only when it clarifies intent or important implementation details.

Before committing, present:

- the staged file list and concise change summary;
- the proposed subject and optional body;
- the current branch and selected push remote when a push was requested.

Ask for confirmation of the commit message and scope. Treat an exact message plus an explicit commit/push instruction already supplied by the user as confirmation; do not ask redundantly.

Create the commit without bypassing hooks. If a hook fails or modifies files, inspect the resulting worktree and staged snapshot again. Do not automatically retry with broader staging.

## 5. Push safely

Skip this section for commit-only requests.

1. Refuse to push from a detached `HEAD` until the user selects or creates a branch.
2. Re-read `git status --short --branch`, the current branch, remotes, and upstream after committing.
3. Fetch the selected remote before pushing when practical, then inspect ahead/behind state. Fetching must not be followed by an automatic merge or rebase.
4. If an upstream exists, run `git push`. If it does not, run `git push -u <remote> HEAD`; default to `origin` only when it is the intended GitHub remote.
5. Verify that the upstream tip equals local `HEAD` after a successful push.

On a non-fast-forward rejection, run `git fetch <remote>` and show the divergent commits. Ask the user whether to merge, rebase, or stop. Never resolve all conflicts with `-X ours`, merge unrelated histories, or force-push automatically.

On authentication failure, stop and recommend the applicable credential flow (`gh auth login`, Git Credential Manager, or SSH setup). Do not solicit credentials in chat or embed them in a remote URL.

## 6. Record a compatible dev-log entry

After a successful push, perform this step automatically only when the repository contains `.claude/skills/dev-log/references/schema.md` or `.codex/skills/dev-log/references/schema.md`. Also perform it when the user explicitly requests development logging.

Read the repository's schema first and append one JSONL entry to its prescribed path. Use `module: "github-push"`, `event_type: "INFO"`, the commit subject as `message`, and include the commit hash, branch, sanitized remote URL, changed-file count, and full commit message in `data`. Never record credentials or URL user-info. Ensure the log path is ignored if the repository convention requires it.

Logging occurs after the push and must not amend or create another commit. If logging fails, preserve the successful push result and report the logging warning separately.

## 7. Report the result

Report the operation performed, commit subject and short hash, branch, sanitized remote, number of committed files, and whether the upstream matches `HEAD`. Include a GitHub repository or commit link when it can be derived safely. Mention any remaining unstaged or untracked changes without implying they were pushed.

For failures, lead with the exact failed stage and next safe action. Distinguish clearly between a successful commit with a failed push and a completed push with a failed optional log entry.
