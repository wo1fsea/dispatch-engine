---
language: en-US
audience: mixed
doc_type: spec
---

# Issue Evidence Capability Preflight Product Spec

## Summary

Plans that ask a worker to inspect GitHub issues must grant an appropriate
capability or record a local-only evidence strategy before dispatch. A worker
should not discover during execution that issue evidence requires network
access that its capability profile denies.

This spec covers GitHub issue #26.

## Goals / Non-goals

- Goal: Detect issue-evidence workstreams whose scope or validation asks for
  GitHub issue reads while `network_access` is `none`.
- Goal: Require a pre-dispatch decision, capability escalation, or local-only
  evidence note before the worker starts.
- Goal: Keep GitHub writes separately governed by `github_issue_create`.
- Non-goal: Grant network access automatically.
- Non-goal: Make the runtime understand every possible external tracker.

## Behavior Invariants

1. A workstream mentioning GitHub issue evidence with denied network access
   receives a warning or blocker before dispatch.
2. Coordinator guidance must inspect `validation_warnings` and capability
   mismatches before launching the worker.
3. The operator can choose between read-only public issue access, local-only
   evidence, or blocking the workstream.
4. A worker that uses `gh issue view` without a matching grant remains a
   capability overreach.

## States And Edge Cases

- Public read-only issue inspection: requires explicit read-only network
  capability or decision.
- Local-only issue evidence: worker documents that GitHub was not read and
  relies on locally available issue text.
- GitHub issue creation/commenting: remains out of scope unless
  `github_issue_create` is explicitly granted.

## Open Questions

- Should this heuristic be GitHub-specific first, or generalized as
  `external_tracker_evidence`?
