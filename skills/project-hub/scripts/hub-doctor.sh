#!/usr/bin/env bash
#
# hub-doctor.sh - is this repo's build record keeping up with its build?
#
# Called two ways:
#   --brief   one line, or nothing at all when healthy. This is what the
#             SessionStart hook uses, so silence is the common case.
#   (no args) the full report, for when you actually want to look.
#
# WHY THIS EXISTS
# A ledger is only worth having if it was written while the work was hot.
# Nothing about a repo forces that, and a skill only runs when invoked, so a
# project can reach forty commits before anyone notices there is no record of
# how it got there. By then the perishable half - the symptom, the dead end,
# the thing that surprised you - is gone. This is the one thing that runs
# unbidden, so it is the only place that check can live.
#
# It nags about absence and staleness. It never nags about content.
#
# Opt out per repo with a .nohub file at the root. Forks, vendored SDKs and
# scratch directories should have one.
#
# SAFETY: this script does not protect the session against its own failures.
# The caller does. ~/.claude/hooks/project-hub-check.sh invokes it with
# `2>/dev/null || true` and ends with its own `exit 0`, so any failure here,
# including a nonzero exit, is swallowed before it can touch session start.
# Do not reintroduce a blanket `trap ... ERR`: it also fires on ordinary
# command-substitution misses (a grep with no match, a date parse that
# fails), and one here previously converted every such miss into a silent,
# empty exit before the healthy report could print at all. Guard individual
# commands with `|| true` where a miss is expected instead.

set -uo pipefail

BRIEF=0
[ "${1:-}" = "--brief" ] && BRIEF=1

# --- thresholds -------------------------------------------------------------
# Low enough to catch a project while its early decisions are still recoverable,
# high enough that scaffolding a repo does not trip it.
NO_HUB_AFTER=3       # commits with no .hub/ at all, and with .hub/ but no ledger.md
EMPTY_AFTER=5        # commits with a .hub/ but zero ledger entries
STALE_AFTER=10       # commits since the newest ledger entry

# --- locate the repo --------------------------------------------------------
root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
[ -n "$root" ] || exit 0

# Opt-out marker, checked before anything else.
[ -f "$root/.nohub" ] && exit 0

# A repo with no commits yet has nothing to be behind on.
commits=$(git -C "$root" rev-list --count HEAD 2>/dev/null) || exit 0
[ "${commits:-0}" -gt 0 ] || exit 0

name=$(basename "$root")
hub="$root/.hub"
ledger="$hub/ledger.md"

# --- check 1: no hub at all -------------------------------------------------
if [ ! -d "$hub" ]; then
  if [ "$commits" -ge "$NO_HUB_AFTER" ]; then
    echo "hub: $name has $commits commits and no build ledger. /project-hub init starts one, or touch .nohub to silence."
  fi
  exit 0
fi

# --- check 2: hub exists, ledger does not -----------------------------------
if [ ! -f "$ledger" ]; then
  if [ "$commits" -ge "$NO_HUB_AFTER" ]; then
    echo "hub: $name has .hub/ but no ledger.md. /project-hub init will add it."
  fi
  exit 0
fi

# --- check 3: ledger exists but holds nothing -------------------------------
# An entry is a "### [tag] title" line. Day headings alone do not count.
# grep -c prints 0 AND exits 1 when nothing matches, so `|| echo 0` would append
# a second zero. Swallow the status instead and let grep's own count stand.
entries=$(grep -c '^### \[' "$ledger" 2>/dev/null || true)
entries=${entries:-0}
if [ "$entries" -eq 0 ] && [ "$commits" -ge "$EMPTY_AFTER" ]; then
  echo "hub: $name has $commits commits and an empty ledger. Capture the decisions while you still remember them."
  exit 0
fi

# --- check 4: ledger has fallen behind the build ----------------------------
# Newest day heading in the file. The ledger is append-only with the newest day
# at the bottom, so take the last one rather than sorting. `|| true` keeps a
# no-match from failing the assignment: last_day is simply empty then, and the
# guard below skips this check instead of the whole script dying.
last_day=$(grep -oE '^## [0-9]{4}-[0-9]{2}-[0-9]{2}' "$ledger" 2>/dev/null | tail -1 | awk '{print $2}') || true

if [ -n "${last_day:-}" ]; then
  # Commits landed strictly after the last recorded day. --since is inclusive of
  # that date, so step forward one day to avoid counting the day itself.
  # Same `|| true` guard: a regex-valid but calendar-invalid date (2026-13-45)
  # fails both the BSD and GNU branches, and that must not take the script
  # down with it.
  next_day=$(date -j -v+1d -f %Y-%m-%d "$last_day" +%Y-%m-%d 2>/dev/null \
             || date -d "$last_day + 1 day" +%Y-%m-%d 2>/dev/null) || true
  if [ -n "${next_day:-}" ]; then
    since=$(git -C "$root" rev-list --count --since="$next_day" HEAD 2>/dev/null || echo 0)
    if [ "${since:-0}" -ge "$STALE_AFTER" ]; then
      echo "hub: $name has $since commits since the last ledger entry ($last_day). The friction from those is the perishable part."
      exit 0
    fi
  fi
fi

# --- healthy ----------------------------------------------------------------
# --brief says nothing at all. This is the common case and it must stay quiet.
if [ "$BRIEF" = "0" ]; then
  echo "hub: $name looks current. $entries ledger entries, $commits commits, last entry ${last_day:-unknown}."
fi

exit 0
