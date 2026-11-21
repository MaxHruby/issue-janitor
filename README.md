# Issue Janitor

A persistent Devin Bot that watches a public GitHub repo and handles incoming issues.

**Status: early design. Nothing here is built yet except the classifier prompt and rules below.**
Everything marked "planned" is a target, not a result.

## What it does (planned)

1. A new issue arrives.
2. The bot classifies it: **bug**, **question**, or **unclear**.
3. **Clear bug** -> bot reproduces it, opens a fix pull request, links it to the issue.
4. **Question** -> bot answers from the README/docs, or points to the right file.
5. **Unclear** -> bot asks the reporter ONE clarifying question and waits.
6. Weekly digest: what was closed, what is waiting, what the bot gave up on.

## Why a persistent bot (not a one-off script)

- It remembers which fix patterns were merged and which were rejected, and stops repeating rejected ones.
- It remembers per-reporter context (was the question already asked? did they reply?).
- It keeps a running list of known-flaky areas of the codebase.

## Classifier rules (v0)

See [classifier_prompt.md](classifier_prompt.md) for the full prompt. Hard rules:

- Never close an issue without a linked PR or an explicit answer.
- Never push to the default branch. Pull requests only.
- Max 1 clarifying question per issue.
- If a fix needs more than ~50 changed lines or touches CI/config, stop and tag a human.
- Budget cap per issue (target: $1 of compute). Over budget -> stop and tag a human.

## Proof plan (all public in this repo)

- Week 1: classifier prompt + a labelled set of 20 sample issues in /examples, with expected labels.
- Week 2: Devin Bot wired to this repo; first bot-opened PRs visible in the PR tab.
- Week 3: weekly digest posted as a GitHub Discussion.

## Success metric (target, not a result)

On the labelled sample set, >= 85% correct classification; of issues labelled "clear bug", >= 50% get a PR that passes CI.
