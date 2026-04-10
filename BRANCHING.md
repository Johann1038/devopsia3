# Git Branching Strategy — Prestige Motors Luxury Car Showroom

## Overview

This project follows the **Git Flow** branching model, adapted for a Jenkins CI/CD
pipeline. Every code change follows a strict branch → PR → merge path that ensures
`main` is always deployable and production-ready.

---

## Branch Hierarchy

```
main  ←──────────────────────────── stable, production-ready releases
 │
develop  ←───────────────────────── integration branch (pre-prod)
 │
 ├── feature/<ticket>-<short-desc>  new features
 ├── fix/<ticket>-<short-desc>      bug fixes
 ├── hotfix/<ticket>-<short-desc>   critical production patches
 └── release/<version>             release preparation
```

---

## Branch Definitions

### `main`
- Represents **production**.
- Only receives merges from `release/*` or `hotfix/*` via pull request.
- Every merge is **tagged** with a semantic version (`v1.0.0`, `v1.1.0`, …).
- Direct commits are **forbidden** — protected branch rules enforce this.

### `develop`
- Living integration branch; all features merge here first.
- Jenkins runs the full CI pipeline on every push.

### `feature/<ticket>-<short-desc>`
- Created from `develop` (e.g. `feature/18-car-detail-page`).
- Merged back via **pull request** after code review + CI green.
- Deleted after merge.

### `fix/<ticket>-<short-desc>`
- Non-critical bug fixes branched from `develop`.

### `hotfix/<ticket>-<short-desc>`
- **Urgent production patches** branched from `main`.
- Merged into both `main` **and** `develop`.
- Tagged on `main` after merge.

### `release/<version>`
- Created from `develop` when a sprint is complete.
- Bug-fix only; no new features.
- Merged into `main` (and back into `develop`) when UAT passes.

---

## Workflow: Feature Development

```bash
# 1. Start from an up-to-date develop branch
git checkout develop
git pull origin develop

# 2. Create a feature branch
git checkout -b feature/18-car-detail-page

# 3. Commit using Conventional Commits format
git add templates/car_detail.html app/app.py app/tests/test_app.py
git commit -m "feat(ui): add car detail page with PayPal purchase (#18)"

# 4. Keep in sync with develop (rebase preferred)
git fetch origin
git rebase origin/develop

# 5. Push and open a pull request → develop
git push origin feature/18-car-detail-page
```

---

## Workflow: Hotfix

```bash
# 1. Branch from main
git checkout main && git pull origin main
git checkout -b hotfix/55-fix-hpa-cpu-threshold

# 2. Fix, commit, push
git commit -m "fix(k8s): correct HPA CPU threshold to 60 (#55)"
git push origin hotfix/55-fix-hpa-cpu-threshold

# 3. PR → main; after merge, back-merge into develop
git checkout develop
git merge --no-ff hotfix/55-fix-hpa-cpu-threshold
git push origin develop
```

---

## Commit Message Convention (Conventional Commits)

```
<type>(<scope>): <summary> (#<issue>)

Types:
  feat     — new feature
  fix      — bug fix
  docs     — documentation only
  style    — formatting, no logic change
  refactor — code change, not a fix/feature
  test     — adding/updating tests
  ci       — CI/CD pipeline changes
  chore    — build, tooling, dependencies

Examples:
  feat(ui): add hero banner with animated stats (#5)
  feat(api): add car filter by fuel_type and brand (#8)
  fix(k8s): correct LoadBalancer port mapping (#23)
  ci(jenkins): publish JUnit test results (#31)
  feat(paypal): integrate payment microservice (#15)
```

---

## Pull Request Rules

| Rule | Detail |
|------|--------|
| Minimum reviewers | 1 approval required |
| CI must pass | All Jenkins stages (Build → Test → Push) green |
| No direct push to `main` / `develop` | Enforced via branch protection |
| Delete branch after merge | Enforced automatically |

---

## Jenkins Pipeline Triggers per Branch

| Branch pattern | Stages that run |
|---------------|-----------------|
| `main` | All 5 stages → deploy to production |
| `develop` | All 5 stages → deploy to staging |
| `feature/*`, `fix/*` | Stages 1–3 only (Build + Test, no push/deploy) |
| `hotfix/*` | All 5 stages (emergency deploy path) |
| `release/*` | All 5 stages → deploy to staging for UAT |

---

## Visual Branch Diagram

```
main:     ──●──────────────────────────────────────●── (v1.1.0)
              \                                   /
release:       ●──●──●──────────────────────────●
                                                /
develop:  ──●──●────────────────────────────────●──●──
              \                       \           /
feature:       ●──●──●──●──────────────●         |
               (feat/18-car-detail)    ↑merged    |
fix:                                              ●──●
                                                 (fix/55)
```

---

## Tagging Releases

```bash
git checkout main && git pull origin main
git tag -a v1.1.0 -m "Release v1.1.0: car detail page + PayPal integration"
git push origin v1.1.0
```

GitHub Releases are created from tags with a changelog.
