# `design-review` — Design & Portfolio Audit

Plugin for reviewing design work in **`03_Atelier/`** and **`04_Portfolio/`** against the Style DNA (`[[core]]`, `[[palette-core]]`, the work modes) and WCAG 2.2 AA contrast.
It holds design work that does not belong to vault administration (`vault-ops`); `art-auditor` moved here from `quan-ly-he-thong` on 2026-11-23 when the plugins were renamed.

---

## 1. Components

| Type | Name | Path | Role |
|---|---|---|---|
| **Subagent** | `art-auditor` | `agents/art-auditor.md` | Read-only design and portfolio auditor (`sonnet`, `medium` effort): case study narratives, design tokens, colour contrast and layout specifications. Zero write permissions |

Design skills (for example a case-study or token check procedure) belong in this plugin when they are written.
