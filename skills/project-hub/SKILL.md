---
name: project-hub
description: Use when the user wants the one page that links everything in a project, or wants the build record kept so it can later become a blog post, video, and social thread. Maintains <repo>/.hub/ with index.html (reference tiles), hub.yml, and an append-only ledger.md. Progress and status live in Asana, not here. Triggers include "make a project hub", "regenerate the hub", "log this to the ledger", or "/project-hub".
---

# Project Hub

Four things in one hidden directory per repo:

```
.hub/
  index.html    derived    the tiles. one page linking everything in the project
  hub.yml       authored   config and links. no status, no progress, no objectives
  ledger.md     authored   append-only build record
  assets/       captured   terminal sessions, logs, diffs, screenshots
```

Nothing else goes in `.hub/`. Committed by default, and one `.gitignore` line if that ever changes.

## Why this exists

**Build freely; the hub captures everything; later the ledger becomes the story.** The output is
a blog post, a video, and social posts about what was actually built. So the ledger is not
housekeeping, it is the raw material for content that has to be true.

That sets the priority when in doubt: **capture generously.** The harvest step trims. A detail you
skipped because it felt minor is not recoverable next month, and an over-full ledger costs nothing.

## Format follows audience

**HTML for what a person reads. Markdown for what Claude reads.**

Do not spend styling effort on a file that only ever gets parsed, and do not hand the user raw markdown
for something they are meant to look at. `index.html` is styled because a person opens it. `ledger.md` and
`hub.yml` are plain because they are read by a machine. The same test decides where project docs go:
a guide a person reads is `docs/thing.html`; notes Claude consumes are `docs/thing.md`.

## Verbs

No argument regenerates `index.html`. Otherwise: `init`, `capture`.

**This skill does not track work.** Asana does, and that is the whole point: a board in a
gitignored local HTML file is invisible to everyone but its author, and the reason to track anything is
so someone else can see it. The objectives column was removed on 2026-08-26 for exactly that
reason. Never reintroduce it, never add a `status:` or `progress:` key to `hub.yml`, and never
answer "what state is this project in" from anything in `.hub/`.

What `.hub/` still owns is what Asana is bad at: an append-only record of what actually happened
while it happened, and one page that links every artifact in the project.

### `init`

**Idempotent. Safe to re-run on a repo that already has a hub.** Re-running never destroys
authored content: it creates only what is missing, leaves everything else exactly as it found it,
and reports which is which.

1. **`ledger.md` is never touched if it exists.** Not rewritten, not appended to, not "refreshed",
   not even if it is empty or malformed. Check for `.hub/ledger.md` before creating anything. If it
   exists, leave it byte-for-byte alone and move to the next check.
2. **`hub.yml` is not clobbered either.** If it exists, read it and leave the authored fields alone.
   Links and prose the user wrote stay as written. Only add a key that is missing outright; never
   overwrite a value that is already set.
3. **Create only what is missing.** Check `.hub/`, `hub.yml`, `ledger.md`, and `assets/`
   independently:
   - `.hub/` missing: create it.
   - `hub.yml` missing: write it from the repo scan. Ask only for the lede if the README does not
     make the project obvious. Never ask for status or progress; that is Asana's.
   - `ledger.md` missing: create it with the header and tag legend, zero entries.
   - `capture-plan.md` missing: create it from the generic scaffold, questions only, no answers.
     See the capture plan section below. Never overwrite one that exists.
   - `assets/` missing: create it.
   A repo with `hub.yml` but no `assets/` gets `assets/` and nothing else. A repo with everything
   already in place gets nothing new.
4. **`index.html` is the one exception, and may be regenerated freely.** Unlike the other three
   files it is derived, not authored, so there is nothing to lose by rebuilding it. Generate it now
   the same way the no-argument verb does.
5. **Wire the repo to Asana.** Everything above must be on disk before this step starts. If any
   Asana call below fails, the repo already has a complete, working hub; report the failure plainly
   and stop, and do not undo or redo the file work above because of it.

   **Idempotency check first.** Read `hub.yml`. If `asana.project` is already set there:
   - Fetch that project by gid to confirm it is still reachable. If it resolves, report that the
     Asana project already exists, give its URL, and move on to the rest of `init`. Do not create a
     second project.
   - If it does not resolve, report that plainly, name the stale gid, and stop rather than quietly
     creating a replacement. A silent second project is how a repo ends up with two, and the old gid
     may still be referenced elsewhere.

   Otherwise, in order:
   a. **Create the project.** Name it the repo's directory name. Team: the gid in `hub.yml`
      under `asana.team` if one is set; otherwise list the workspace's teams, ask which one, and
      record the answer there. Never bake a team gid into this skill. For `notes`, write a short description of what the repo is,
      taken from the README if the repo has one; leave `notes` blank rather than guessing if it
      does not.
   b. **Scaffold four starter tasks**, in this order, on the project:
      - `Build the thing`: the actual work.
      - `Keep the ledger`: capture decisions, friction, and dead ends as they happen, not at
        wrap-up.
      - `Capture the first time it works`: points at `.hub/capture-plan.md`. The first time
        happens once.
      - `Decide: promote or drop`: an explicit task, on purpose. A kill is a decision someone
        makes, not something that happens by a project going quiet.

      These four are the exploration spine, deliberately not content deliverables: at this stage
      nobody has decided the thing is content yet. That decision, and the deliverable tasks that
      follow from it, belong to `advocacy-intake` later, not to `init`.

      **Ask for a check-back date on `Build the thing`, right after creating it.** Use
      `AskUserQuestion` with a small set of concrete options, never an open prompt:

      - One week from today, marked as the default.
      - A shorter option, three days out, for something the user expects to resolve fast.
      - A longer option, three weeks out, for something that will clearly take a while.
      - No date yet, for when they genuinely do not know.

      Set whatever comes back as `due_on` on `Build the thing` only. `Keep the ledger`,
      `Capture the first time it works`, and `Decide: promote or drop` stay undated: they are
      ongoing or event-triggered, not a point to check back on.

      **This is a check-back date, not a build estimate, and that distinction is the whole
      point.** "How long will this take" is unanswerable on day one, nobody knows yet. "When
      should this either be working or be dropped" is answerable immediately, because it does
      not require knowing the future, only committing to a moment to look again. A date on the
      task is what makes a three-week stall visible instead of indistinguishable from a project
      started yesterday, which is the entire early-kill-signal this design rests on.

      **Why one week is the default.** A tinker toy touched on evenings will not be done in
      three days, so a three-day date is overdue almost immediately, and a date that is always
      overdue is noise you learn to ignore. A week is long enough to mean something and short
      enough to actually catch a stall.

      **What an overdue check-back date means.** Not a reason to feel behind. It is a prompt:
      look at the project again and decide, promote it, give it a new check-back date, or drop
      it. "Drop" is a real, correct answer to a check-back, not a failure of one.
   c. **Write the result into `hub.yml`**, under a new top-level `asana` key (see the `hub.yml`
      section below for the exact shape). This is the only key `init` ever writes into `hub.yml`
      on its own initiative rather than leaving for the user to author.

   **Why this exists at all.** A repo gets an Asana project the moment it gets a hub, before anyone
   has decided the thing is worth anything. Someone seeing it early can give the kill sign cheaply,
   and a project that was tried and dropped is evidence worth showing, not a failure to hide.

   **Report every partial failure, by name.** If the project is created but the task scaffold
   fails partway, say exactly that: the project exists, give its URL, and name which of the four
   tasks were created and which were not. Silent partial success is the failure mode that has cost the most in this project already;
   never report "Asana wiring done" when part of it did not happen.
6. **Report what it found and what it did.** Say plainly which of `hub.yml`, `ledger.md`, and
   `assets/` already existed and were left untouched, and which were created, plus the outcome of
   the Asana wiring: created and fully wired, already existed and verified reachable, or partially
   wired with the failing part named. On a repo that already has a full hub with a working Asana
   project, the correct output is an acknowledgment that both already exist plus that checklist, not
   silence and not a fresh scaffold.
7. Open it once in the browser: `open .hub/index.html` on macOS, `xdg-open .hub/index.html` on
   Linux. Never again after that; say "refresh the tab" instead. Duplicate windows across monitors are worse than a stale tab.

### (no argument): regenerate `index.html`

1. Scan the repo for linkable artifacts: `README*`, `docs/*`, any root-level docs, entry points.
2. Read `hub.yml` for what a scan cannot find: external links, local ports, the reference groups.
3. Copy `template.html` **verbatim**. Fill only the title, eyebrow, `<h1>`, lede, the region between
   `TILES START/END`, the region between `BOARD LINK START/END`, and the foot stamp. The
   `BOARD LINK` region is filled when `hub.yml` has `asana.url` and removed outright, not left with
   placeholders, when it does not.

   `${CLAUDE_PLUGIN_ROOT}/skills/project-hub/scripts/render_board.py <hub.yml> reference` emits the reference sections, which are a
   mechanical transform of `hub.yml` and should not cost a model anything. The project-specific
   tiles above them are authored by hand, because deciding what to link and how to mark it is the
   judgment this verb exists for.
4. Check the links. Every path is relative to `.hub/`, so repo files are `../<path>`. Getting the
   prefix wrong produces a page of dead links that still looks correct.
5. **The Asana banner.** If `hub.yml` has `asana.url` set, render the `.board-link` block
   directly under the lede: the link text is `hub.yml`'s `title`, the `href` is `asana.url`.
   If `asana.url` is absent, omit the block entirely.

   **`hub.yml` owns this value; there is nothing else to read.** `init` writes `asana.project`
   and `asana.url` once, at the moment the Asana project is created (see the `init` verb above).
   Every verb after that, including this one, reads the value back from `hub.yml` and never calls
   the Asana API. project-hub does not talk to Asana except at `init`.

   **The banner and every external tile open in a new tab.** `target="_blank" rel="noopener"`,
   without exception. The hub is opened from a `file://` URL in a tab the user closes and reopens, so a
   same-tab navigation does not just leave the page, it loses it.

   **Malformed value, same as absent.** If `asana.url` is present but empty or does not look like
   a URL, omit the block entirely, exactly as if the key were not there. Never emit a literal
   `ASANA_URL`, an empty `href`, or a placeholder project name.

Tile marking, which is about honesty rather than tidiness:

| Case | Marking |
|---|---|
| Target does not exist yet | `class="pending"` |
| Only resolves on this machine (`file://`, `localhost`) | `class="local"` |
| Gitignored with a committed counterpart | link the counterpart instead |
| Gitignored build output, no counterpart | `class="local"`, and say it only exists after a run |
| External URL | `class="ext"` plus `target="_blank" rel="noopener"` |

Never link a gitignored file unmarked. Check with `git check-ignore -q <path>`. It exists on this
disk and is absent from every clone, so it looks like a working tile and is not one.

`.hub/capture-plan.md` belongs in the Capture tile group, alongside the ledger and the assets
directory, but only when the file exists. It is written conditionally (see "The capture plan"
below), so unlike the ledger it is not a permanent fixture of the group: add the tile when the
scan finds the file, and leave the group without it when the file has not been written yet. Do
not mark it `pending` for its absence; a plan that may never get written is not a tile that will
ever resolve.

### The capture plan

`.hub/capture-plan.md`. **Scaffolded at `init`, filled in before the first irreversible success,
and never rewritten after it.**

`init` writes the generic half, which is the same for every project and is mostly questions:

- What has to be in frame, and why a screen recording will not do if the thing is physical.
- What has to be running so the terminal output is a file and not a memory.
- Record the failed attempts, in order, narrating what changed between them. Those clips are worth
  more than the success clip, because everyone has seen a demo that works.
- **If it works first try, say so. Do not manufacture struggle.**

Scaffolding it at `init` rather than waiting is deliberate. A prompt that fires late might not fire
at all, and the specifics are cheap to add once you know them. What is expensive is discovering on
the day that nobody wrote down what to point the camera at.

**The specifics get filled in when the one-time event comes into view.** When work in this session
turns to something whose name describes a first, like "First over the air turn" or "first time it
answers the dog for real", and `.hub/capture-plan.md` is still only the generic scaffold, say once:

> "<the thing> reads as a one-time event. Worth filling in `.hub/capture-plan.md` before it happens?"

Ongoing work is not a trigger. Take no for an answer and do not ask again for that event.

**Why this lives in project-hub and not in advocacy-intake.** The first time
something works happens once, and it is usually long before anyone decides the
project is content. A capture plan created at intake is created too late. This
is the same reason the ledger lives here.

### `capture`: append to the ledger

Append entries as things happen. Do it unprompted, in the same turn, especially for friction. Do not
save it for wrap-up: the symptom is the perishable part and it is gone by tomorrow.

Six tags:

| Tag | What it records |
|---|---|
| `decision` | The choice, what lost, and why |
| `friction` | Symptom first, then cause, then fix |
| `deadend` | Tried and reverted. Leaves zero trace in git |
| `surprise` | Behaved differently than expected, not a bug |
| `claim` | A falsifiable claim and whether it held |
| `asset` | A captured artifact, by path |

Two required lines on every entry:

- `Source:` a path, a `path:line-range`, a command plus output, an asset file, or a URL. A number
  without a source cannot be used in a post, so this is what makes the ledger publishable.
- `Routes to:` where this lands. A repo fix, an upstream issue, a specific piece of content.

```markdown
## 2026-08-06

### [friction] The uploader silently truncates files over 100 MB
Symptom first: large uploads reported success and arrived incomplete, no error anywhere. Cause: the
client streams into a fixed buffer and stops at capacity instead of erroring. Fix: compare the
returned byte count to the local size and fail loudly on mismatch.
Source: src/upload.py:41-58 · repro `make upload FILE=fixtures/large.bin`
Routes to: upstream issue, gotchas post
```

**Rules:**

- **Read the whole ledger before appending. Never `Write` over it.** Another session may have
  appended since you last looked. Append-only is a rule about the file, not about your intentions,
  and a full-file write is how it breaks. Anchor an edit to the last entry.
- **Symptom before cause** on every `friction` entry. The symptom is what the next person searches
  for; the cause is what you only knew afterward.
- **Corrections are new entries.** If a cited path moves, append an entry naming the new path. Never
  edit an existing entry, including to fix a broken citation.
- **`asset` entries must point at a file that already exists.** A terminal session nobody captured
  cannot be honestly re-staged, so record the gap instead of reenacting it.

## Lab repos and the public flip

**New projects are built in a private `-lab` repo and, if they ship, snapshotted once into a
separate public repo.** `thing-lab` private, `thing` public. Nothing in `.hub/` or `advocacy/`
ever reaches the public one.

The suffix is a fact about visibility, not a label: in `~/LABS`, `-lab` means private and a bare
name means public. Every private repo carries it. Repos that predate the convention have no lab
twin: do not propose creating one to make old work look like it followed the rule. A lab repo is
only real if the work actually happened in it.

**The one case where a twin IS created after the fact** is a pre-convention repo that went public
with `.hub/` tracked. There the twin is a rescue, not a fabrication: copy the real history into a
private `<thing>-lab`, keep the hub there, untrack `.hub/` upstream. Say plainly that untracking
does not unpublish: the ledger stays in the public repo's history until someone rewrites it, and
that rewrite is the user's call.

Both halves live in `~/LABS/`, side by side, because writing the build-log post means reading the
lab ledger with the public repo open beside it. If work and personal repos commit as different
identities, drive that from `includeIf` blocks in `~/.gitconfig` keyed on directory, so a repo-local
`user.email` never has to be set.

Because both halves share a directory, **the suffix is the only privacy signal**. Keep it accurate,
and check `gh repo view <name> --json visibility` before committing anything quotable. A `.hub/`
pushed to a public repo cannot be recalled.

The flip is one way and terminal:

- History is **rewritten into build order** before the public push, so the commit log reads as a
  tutorial. Deciding the chapters is the user's judgment call, not this skill's. Budget an hour.
- `.hub/` and `advocacy/` are stripped from **every commit**, not just the tip. A `.gitignore`
  line does not do this and leaves them in history.
- After the flip the public repo is the repo of record. The lab repo is never worked in again
  except to write content from its ledger, and is never deleted, because the ledger is the only
  source for the build-log post.
- PRs on the public repo are applied by hand in the lab repo and arrive in a later snapshot.
  Nothing is merged back from public to lab. Two-way sync is how this model dies.

Record the public repo in `hub.yml` as `public_repo:` once it exists, so the hub can link out to
it. Before that field is set, this project has not flipped and every tile is internal.

## hub.yml

Only what a repo scan cannot find.

```yaml
wordmark: acme                  # accent word in the eyebrow. the org, or the repo for personal work
title: Widget Pipeline          # <h1> becomes "<title> · Project Hub"
eyebrow: ingest + render demo
lede: One line on what this is and where to start.

# There is no objectives key, and adding one back is a bug. Status lives in Asana.
# Hubs written before 2026-08-26 carry their old board at .hub/objectives-archive.md,
# which is a frozen document and not read by anything.

asana:                          # written once by `init`, not authored by hand. project-hub
                                  # reads this back for the banner and never calls Asana again.
  project: "1200000000000001"   # quoted: Asana gids overflow a YAML/JSON float
  team: "1200000000000000"      # the team the project was created in. asked once, then reused
  url: https://app.asana.com/0/1200000000000001

public_repo: https://github.com/org/thing   # set only after the flip. absent = still private

local:                          # rendered class="local"
  app_url: http://localhost:8000

suppress:                       # tiles the scan finds that should not appear
  - docs/scratch.md

reference:                      # grouped into "Reference: <group>" sections
  Vendor docs:
    - name: 📗 API reference
      url: https://example.com/docs/api
      desc: Endpoints, auth, rate limits.
```

## Rules

- **Copy `template.html` verbatim.** The chrome, tokens, toggle, and script are canonical. Never
  restyle or re-derive them from memory. Brand tokens stay in the one `:root` block so a palette
  change is a single edit.
- **Never hand-edit `.hub/index.html`.** Change the repo or `hub.yml`, then regenerate.
- **Never rewrite `.hub/ledger.md`.** Append only, corrections included.
- **`init` never destroys authored content, and the only file any verb may overwrite is
  `index.html`.**
- **Colorblind-safe.** Nothing on this page may carry meaning by
  color alone: a tile's state is carried by its label and its `pending` / `local` / `ext` marking,
  never by hue.
- **No status on this page.** No objectives, no percentages, no "in progress" pills, no burndown.
  If a question is "how is this going", the answer is the Asana link at the top.
- No em dashes. `&middot;` is the separator in the title.
- Prose is direct and plain: no preamble, no marketing verbs, no AI-isms.
- Open the page once, on creation. After that, "refresh the tab".

## What this does not own

| Artifact | Owner |
|---|---|
| `.claude/handoffs/` | session handoff notes, git state, local per clone |
| `docs/` | nobody. Project documentation, HTML or Markdown per the audience rule |
| Status, progress, what is next | **Asana.** Not this skill, not `hub.yml`, not `index.html` |

There is no roadmap file, no `PROGRESS.md`, and no Notion. **If a project needs a status page it is
the Asana project, and this page links to it.** That is a reversal: until 2026-08-26 the objectives
board here was the status page, and it was the wrong place because a gitignored local HTML file is
visible to exactly one person. Tracking exists so someone else can see it.
