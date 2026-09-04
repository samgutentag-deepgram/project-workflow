# Build ledger: project-workflow

Append-only. Never rewritten, never reordered. Corrections are new entries that say what changed.

Six tags: `decision` · `friction` · `deadend` · `surprise` · `claim` · `asset`.
Every entry carries a `Source:` line and a `Routes to:` line.

This records what a repo scan cannot recover: the dead end that was reverted, the symptom before
anyone knew the cause, the alternative that lost. Anything learnable from the repo or `git log`
belongs on the hub as a link, not here.

The design history that predates this file lives in the ledger of the repo this plugin was
extracted from, since that is where the work happened.

---

## 2026-08-07

### [decision] This repo's hub carries no file:// tiles and names nothing
The other hubs link siblings by absolute local path, which is right for a private repo on one
machine. This one is public. A `file:///Users/<name>/...` tile in a public repo is dead in every
clone and also publishes the author's disk layout, so the sibling section is empty here rather than
marked local. Same rule as the plugin's own employer-agnostic constraint, applied to paths instead
of prose: nothing in this repo should mean anything different on someone else's machine.
Source: `.hub/hub.yml` siblings (empty, with the reason inline) vs the same key in the two migrated
repos, which do use local tiles
Routes to: a note in the skill about public repos, build log post

### [friction] The board generated with no state markers at all, and looked fine
Symptom first: two freshly generated hub pages passed every link check and rendered as clean
two-column boards where no objective showed its state. Cause: `template.html` gained an SVG icon
sprite mid-session, in commit 282c1b6, after the generating session had already read it. The
generator reads the template at run time, so the new chrome was picked up and the sprite was present
in both pages, while the hand-written board markup still used the old bare `<summary>Name</summary>`
form with no `<use>` ref. Nothing referenced the sprite, so nothing rendered, and the failure looks
like a design choice rather than an error.
Fix: the generator now derives each icon from the `<details>` class instead of trusting the caller,
and asserts afterward that no row is bare and that exactly one objective is `now`.
Source: commit 282c1b6 (15:22, mid-session) · `grep -c 'ico-' index.html` returned 4, the sprite
definitions only, with 0 uses across 9 objectives
Routes to: gotchas post ("generating against a template someone else is editing"), a generation-time
assertion in the skill

### [surprise] git rm is atomic across its arguments, so one modified file cancelled all three
Not a bug. `git rm -r hub/hooks hub/events.jsonl hub/manifest.json` refused every deletion because
one of the three had uncommitted changes, and reported a single error naming only that file. The
`git mv hub .hub` that followed then carried all three into the new directory intact, so a
migration that was supposed to drop the scaffolding quietly relocated it instead, and `git status`
showed a tidy set of renames.
Worth recording because the failure composes: "delete, then move" degrades into "move everything"
whenever the delete aborts, and neither command complains.
Source: `git rm` output "error: the following file has local modifications: hub/events.jsonl" ·
the follow-up `git rm -f` against the already-moved paths
Routes to: gotchas post, any future migration script for this skill

### [decision] A migration stops at a repo another session is holding
One of the three repos to migrate had an interactive session live in it, five hours in and busy. In
the three minutes between two `git status` calls it went from 7 changed files to 29 and staged two
deletions of its own. Migrating it anyway meant running `git mv` and `git rm` against an index
another writer was staging into, which either clobbers their work or loses mine.
Rejected: doing it anyway because the changes were small, and messaging the other session to ask it
to stop. Deferred instead. Concurrent sessions on one machine share a filesystem and no lock, so a
`git status` snapshot is only true for the instant it was taken.
Source: `ListAgents` showing an interactive session in that repo, busy, started 5h prior · the same
repo's `git status` before and after
Routes to: gotchas post ("the repo moved while I was reading it"), a pre-flight check for any
skill that writes across repos

### [claim] The four deleted artifacts have not been missed
Claimed when they were cut on 2026-08-06: the commit hook, event log, generated manifest, and health
checker were scaffolding, and discipline plus two authored files would cover it. Two repos migrated
today without needing any of the four, and the one gap that did show up was a dead reference link,
which none of the deleted tools checked either. The checker's own history is the strongest evidence:
it reported a repo clean while three cited paths were stale, then needed three bug fixes in a single
day.
Not yet held, and it should not be called held for a while: a week of daily use is the test, and one
migration afternoon is not that.
Source: README "Deliberately not included" · commit b378695 (the deletion) · today's two migrations,
neither of which reached for a removed tool
Routes to: build log post, the "delete your own scaffolding" angle
