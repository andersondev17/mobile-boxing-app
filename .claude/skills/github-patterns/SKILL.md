---
name: github-patterns
description: Apply this skill for git commits, branch naming, PR creation, and code review in the boxing-api monorepo. Trigger on: "commit", "git commit", "branch name", "create PR", "pull request", "merge", "git", "changelog", "semantic commit", "conventional commit", "review PR".
---

# GitHub Patterns — boxing-api

## Repository
Monorepo: `boxing-api/` with two packages: `apps/backend/` and `apps/mobile/`

## Branch Naming

```
feature/<scope>-<short-description>
bugfix/<scope>-<short-description>
chore/<scope>-<short-description>
hotfix/<scope>-<short-description>
```

Scopes: `backend`, `mobile`, `ml`, `kafka`, `infra`, `auth`, `sprint1`, `sprint2`

Examples:
```
feature/ml-dtw-scorer
feature/mobile-tflite-frame-processor
bugfix/kafka-user-id-partition-key
chore/infra-mongodb-migration
feature/backend-consent-endpoint
```

Current branch: `feature/sprint1-mongodb-migration`

## Semantic Commit Messages

Format: `type(scope): short description`

```
feat(ml): implement DTW scorer with dtaidistance
feat(mobile): add TFLite on-device landmark extraction
fix(kafka): change partition key from device_id to user_id
fix(ws): respond to client before publishing to Kafka
chore(infra): update docker-compose to single-node Kafka KRaft
refactor(backend): migrate routes to Beanie ODM from SQLAlchemy
docs(agents): add boxing-domain-expert subagent definition
test(ml): add pytest fixtures for 30-frame landmark windows
```

Types: `feat` `fix` `refactor` `chore` `docs` `test` `perf` `ci`

## PR Checklist (must pass before merge)

- [ ] No violations of the 6 permanent restrictions
- [ ] All public functions have docstrings (Google-style Python or JSDoc TypeScript)
- [ ] `user_id` is the Kafka partition key in any new producer
- [ ] No base64 image bytes stored or sent over WebSocket
- [ ] Consent check present before any biometric data persistence
- [ ] Docker Compose still works after changes (`docker-compose up`)
- [ ] No hardcoded credentials (use `.env` + `settings`)
- [ ] `.env.example` updated if new env vars were added
- [ ] TypeScript interfaces in `interfaces.d.ts` match Pydantic schemas

## PR Description Template

```markdown
## Summary
Brief description of what this PR does.

## Changes
- `apps/backend/app/kafka/...` — description
- `apps/mobile/services/...` — description

## Restrictions Check
- [ ] C-01: No video/image bytes stored
- [ ] C-02: Kafka key is user_id
- [ ] C-03: Window size is exactly 30 frames
- [ ] C-06: WebSocket responds < 100ms

## Testing
How to test manually:
1. Start in technique mode: `docker-compose up mongodb redis backend`
2. Connect to WebSocket, verify...

## Notes
Anything the reviewer should know.
```

## Sprint Branch Strategy

Each sprint gets its own branch from `main`:
```bash
git checkout main && git pull
git checkout -b feature/sprint1-mongodb-migration
# work...
git push -u origin feature/sprint1-mongodb-migration
# PR → main
```

## Common Git Commands

```bash
# Check what's changed
git status
git diff --staged

# Stage specific files (never use git add -A or git add . blindly)
git add apps/backend/app/kafka/smartwatch_producer.py

# Commit with message
git commit -m "fix(kafka): change partition key from device_id to user_id"

# Push current branch
git push

# Create PR (using gh CLI)
gh pr create --title "fix(kafka): partition key correction" --body "..."
```

## Files to never commit
- `.env` (any environment file with real credentials)
- `*.parquet` files with real user data
- `apps/backend/app/ml_service/models/*.task` (large binary model files — use Git LFS)
- `node_modules/`, `__pycache__/`, `.expo/`
