# project-workflow

A Claude Code plugin. Gives every repo the same small, predictable structure so you can build
freely, walk away, come back, and see where you are in one glance.

Employer-agnostic on purpose. Nothing here names a product or a company.

## What it does

One hidden directory per repo, four things in it:

```
.hub/
  index.html    derived    reference tiles left, objectives board right. the page you open
  hub.yml       authored   config, links, and the objectives with their states
  ledger.md     authored   append-only build record
  assets/       captured   terminal sessions, logs, diffs, screenshots
```

**The board** is the checklist. One objective is marked `now`, each has a collapsible detail block,
and Claude updates it as work lands so the first thing you read on returning is where you are.

**The ledger** is append-only and exists for one purpose: you build freely, it captures everything,
and later it becomes a blog post, a video, and social posts about what you actually built. That is
why it records what a repo scan can never recover, the dead end that was tried and reverted, the
symptom before anyone knew the cause, and the alternative that lost. Dead ends leave zero trace in
git, so this is their only home.

When in doubt it captures generously. The harvest step trims; a detail skipped today is gone next
month.

## Format follows audience

**HTML for what you read. Markdown for what Claude reads.** No styling effort on files that only
get parsed, no raw markdown for pages you look at. `index.html` is styled; `ledger.md` and `hub.yml`
are plain.

## Install

This repo is both the plugin and its own marketplace.

```
/plugin marketplace add samgutentag-deepgram/project-workflow
/plugin install project-workflow@project-workflow
```

From a local clone, to test a branch before it merges:

```
/plugin marketplace add ./project-workflow
/plugin install project-workflow@project-workflow
```

## Verbs

| Verb | Use |
|---|---|
| `init` | Create `.hub/`, ask for the objectives, generate the page, open it once |
| (none) | Regenerate `index.html` from the repo and `hub.yml` |
| `board` | Flip an objective's state and rewrite the stamp. Run after every turn that moves the work |
| `capture` | Append a ledger entry. Runs unprompted when something breaks |

## Ledger entries

Six tags: `decision`, `friction`, `deadend`, `surprise`, `claim`, `asset`. Every entry carries a
`Source:` line and a `Routes to:` line. A number without a source cannot go in a post, which is what
makes the ledger publishable rather than just a diary.

## Packaging for claude.ai

`scripts/pack-skills.sh` builds a `.skill` archive per skill folder, the upload format for claude.ai
and Claude Desktop. Run it after editing a skill, not on every commit: zip embeds mtimes, so it
churns bytes even with no content change.

## Pairs with advocacy-workflow

When a build is done, [advocacy-workflow](https://github.com/samgutentag-deepgram/advocacy-workflow)
turns the ledger this plugin keeps into a content campaign: blog posts, derivatives, style variants
and videos, through review gates tracked in Asana. It reads `.hub/ledger.md` and `hub.yml`
directly, which is why the ledger captures generously. Install it alongside this plugin only
when a project is heading for publication.

## License

MIT.
