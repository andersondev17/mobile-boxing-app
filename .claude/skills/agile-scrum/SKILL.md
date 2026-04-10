---
name: agile-scrum
description: Apply this skill when planning sprints, defining tasks, or tracking development progress for the boxing app. Contains the sprint structure, Definition of Done, and backlog conventions. Trigger on: "sprint planning", "sprint", "backlog", "user story", "tasks for this week", "what's left", "sprint review", "definition of done", "next sprint", "prioritize", "plan the work".
---

# Agile/Scrum — mobile-boxing-app

## Team size
Small team: 1 tech lead (Federico) + AI subagents as co-developers.
Sprint duration: 1 week.

## Sprint Structure

### Sprint 1 (Foundation) — feature/sprint1-mongodb-migration
**Goal**: Stable infrastructure, clean codebase, no critical violations

| Task | Owner | Status |
|------|-------|--------|
| MongoDB migration (Beanie ODM) | backend-builder | ✅ Done (already using MongoDB) |
| Kafka folder rename kakfa→kafka | kafka-data-eng | ✅ Staged |
| Fix Kafka partition key (device_id→user_id) | kafka-data-eng | ⚠️ Pending |
| Docker Compose single-node Kafka | devops-engineer | ✅ Done |
| Consent routes (Ley 1581) | backend-builder | ✅ Done |
| Mobile residual cleanup (Appwrite, TMDB) | mobile-dev | ❌ Pending |

### Sprint 2 (Landmark Pipeline)
**Goal**: Mobile sends landmarks (not base64) to backend

| Task | Owner |
|------|-------|
| TFLite on-device landmark extraction | mobile-dev |
| Migrate realtimePoseService.ts to landmarks | mobile-dev |
| Mobile consent UI (3 consent screens) | mobile-dev + legal-expert |
| Backend WebSocket cleanup (remove legacy base64) | backend-builder |

### Sprint 3 (ML Pipeline)
**Goal**: DTW scorer working end-to-end

| Task | Owner |
|------|-------|
| window_buffer.py (Redis 30-frame) | ml-researcher |
| dtw_scorer.py (dtaidistance) | ml-researcher + boxing-domain-expert |
| feature_extractor.py expansion | ml-researcher |
| punch_classifier.py (SVM/RF) | ml-researcher |

### Sprint 4 (Polish)
**Goal**: Production-ready MVP

| Task | Owner |
|------|-------|
| CORS restriction | backend-builder |
| DELETE /user/{id} (right to erasure Ley 1581) | backend-builder + legal-expert |
| Schema alignment backend↔mobile | backend-builder + mobile-dev |
| Test coverage ≥ 75% | all |

## Definition of Done (DoD)

A task is DONE when:
1. Code is written and reviewed by code-reviewer
2. No violations of the 6 permanent restrictions
3. All public functions have docstrings
4. Docker Compose still starts without errors
5. Tests pass (no regressions)
6. PR is merged to main

## Backlog Priority Rules

**P0 — Block everything**: Permanent restriction violations (C-01 to C-06)
**P1 — Sprint this week**: Core functionality for the current sprint goal
**P2 — Next sprint**: Important but not blocking current goal
**P3 — Eventually**: Nice to have, no specific sprint assignment

## Task description format

```markdown
**[P1] Fix Kafka partition key**

Owner: kafka-data-eng
File: apps/backend/app/kafka/smartwatch_producer.py:83
Restriction: C-02

Current: key = message["device_id"]
Required: key = message["user_id"]

Notes: Also check technique_producer.py and round_producer.py when created.
```

## Sprint review format

At end of each sprint:
```
SPRINT N REVIEW
==============
Completed: [list with PR numbers]
Not completed: [list with reason]
Unexpected findings: [what we discovered during the sprint]
Needs user decision: [things that require Federico's input]
Next sprint start: [date]
```
