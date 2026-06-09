# Quality Guidelines

> Code quality standards for backend development.

---

## Overview

<!--
Document your project's quality standards here.

Questions to answer:
- What patterns are forbidden?
- What linting rules do you enforce?
- What are your testing requirements?
- What code review standards apply?
-->

(To be filled by the team)

---

## Forbidden Patterns

<!-- Patterns that should never be used and why -->

(To be filled by the team)

---

## Required Patterns

<!-- Patterns that must always be used -->

### External Feed Smoke Inputs Must Pass SSRFGuard

When running a real RSS, AI HOT RSS, or RSSHub smoke test, validate the candidate
URL through `SSRFGuard` before using it in UI or API smoke flows. In this local
environment, some public-looking hosts can resolve to reserved ranges such as
`198.18.0.0/15`; those must stay blocked and should be recorded as an expected
`SOURCE_SSRF_BLOCKED` result, not worked around with a silent bypass.

Good:

```bash
PYTHONPATH=backend backend/.venv/bin/python - <<'PY'
from app.services.ssrf import SSRFGuard

SSRFGuard().validate_url("https://github.blog/feed/")
PY
```

Bad:

```python
# Do not disable or bypass SSRF validation to make a live smoke source work.
SourcePreviewer(guard=None)
```

The smoke source must still use the normal `/api/sources/preview` or
`/api/sources/{sourceId}/fetch` path so envelope, trace, fetch run, raw item,
and source health behavior are verified together.

### Backend Package Discovery Must Exclude Non-Package Folders

The backend uses a flat layout with `app/` for importable code and
`migrations/` for SQL artifacts. `pyproject.toml` must explicitly configure
setuptools package discovery so editable installs include `app*` and exclude
`migrations*`.

Good:

```toml
[tool.setuptools.packages.find]
include = ["app*"]
exclude = ["migrations*"]
```

Bad:

```toml
# Relying on automatic discovery fails once app/ and migrations/ both exist.
```

Before considering backend environment setup healthy, verify:

```bash
backend/.venv/bin/python -m pip install -e 'backend[dev]'
```

---

## Testing Requirements

<!-- What level of testing is expected -->

- Real feed smoke tests must verify the candidate URL is not rejected by
  `SSRFGuard` before driving the browser UI.
- If the guard rejects a candidate, assert or record the concrete blocked reason
  and switch to another candidate source instead of weakening the guard.
- Backend packaging changes must keep editable install green with
  `backend/.venv/bin/python -m pip install -e 'backend[dev]'`.

---

## Code Review Checklist

<!-- What reviewers should check -->

(To be filled by the team)
