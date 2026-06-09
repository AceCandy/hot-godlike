# Quality Guidelines

> Code quality standards for frontend development.

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

### Mock Write APIs Must Preserve Entity Identity

When frontend UI uses mock APIs for write flows, the mock must keep enough in-memory state for the next UI action to address the entity returned by the previous action.

Required behavior:

- `create` returns a concrete entity id and inserts that entity into the mock list used by `list`.
- `update`, `enable`, `disable`, and similar mutations resolve by the requested entity id.
- Unknown entity ids return the contract error for "not found"; they must not fall back to the first mock record.
- State-changing mock modules expose a reset helper for tests so one test's writes do not affect later tests.
- UI components may still merge the write response into local state for immediate feedback, but the mock API must remain contract-faithful.

Wrong:

```typescript
const current = mockItems.find((item) => item.id === id) ?? mockItems[0];
return envelope({ ...current, enabled: false });
```

Correct:

```typescript
const index = mockItems.findIndex((item) => item.id === id);
if (index === -1) {
  return notFoundEnvelope(id);
}
const updated = { ...mockItems[index], enabled: false };
mockItems = mockItems.map((item, itemIndex) => (itemIndex === index ? updated : item));
return envelope(updated);
```

### Upstream HTML Must Be Sanitized Before Rendering

When rendering HTML captured from upstream sources, do not pass the raw string directly to `v-html`.
Route it through a project-owned sanitizer that:

- Keeps only readable content tags and safe attributes needed by the UI.
- Allows only `http` and `https` links/media URLs.
- Removes scripts, event handlers, inline styles, classes, and data attributes from upstream HTML.
- Adds safe external-link attributes such as `target="_blank"` and `rel="noopener noreferrer"`.
- Keeps plain text escaped when it is rendered through an HTML sink.

Wrong:

```vue
<div v-html="item.contentSnippet"></div>
```

Correct:

```vue
<div v-html="sanitizeRawItemHtml(item.contentSnippet || 'No summary')"></div>
```

---

## Testing Requirements

<!-- What level of testing is expected -->

- Mock write flows need regression tests for create -> list -> follow-up mutation.
- Tests that mutate module-level mock state must reset that state in `afterEach`.
- Rendering upstream HTML needs regression tests that prove readable tags/media survive and unsafe URLs, script tags, and event attributes are removed.

---

## Code Review Checklist

<!-- What reviewers should check -->

(To be filled by the team)
