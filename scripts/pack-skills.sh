#!/usr/bin/env bash
# Regenerate every skills/<name>.skill archive from its source folder.
# The .skill files are the upload format for claude.ai / Claude Desktop.
# Run this after editing any skill and before cutting a release, so the
# committed zips never drift from the source folders.
#
# Note: zip embeds file mtimes, so re-running churns bytes even with no
# content change. Run it intentionally (on skill edits / releases), not on
# every commit.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skills_dir="$repo_root/skills"
count=0

for dir in "$skills_dir"/*/; do
  name="$(basename "$dir")"
  if [ ! -f "$skills_dir/$name/SKILL.md" ]; then
    echo "skip: $name (no SKILL.md)"
    continue
  fi
  archive="$skills_dir/$name.skill"
  rm -f "$archive"
  # Zip from inside skills/ so the archive's internal path is <name>/...
  # -X drops extra platform attributes; exclude macOS cruft.
  ( cd "$skills_dir" && zip -q -X -r "$name.skill" "$name" -x '*.DS_Store' )
  echo "packed: $name"
  count=$((count + 1))
done

echo "done: $count skill archive(s) regenerated"
