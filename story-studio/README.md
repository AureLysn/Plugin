# `story-studio` — Fiction Continuation & Original Story Studio

End-to-end plugin for **`05_Evasion/01_Oeuvre/`** (`Studio/Continue/`, `Studio/Original/`, and `Database/Fandom/`), beside **`05_Evasion/02_Library/`** (the `Kệ Sách` reading app; no skill writes there) and connected to **`05_Evasion/03_Subsystems/Nexus/`** (`TranslateCenter`).

---

## 1. Architecture (`v0.20.0`)

- **2 Shared Configuration Files (`shared/`):**
  - `shared/vault-config.md` — Authoritative path mappings for `D:\AureLysn` (`05_Evasion/01_Oeuvre/`, `01_Origine/05_Meta/Schema/`, `01_Origine/02_Knowledge/Curated_Notes/writing/`, and `01_Origine/04_Tools/VaultTool/`).
  - `shared/working-standard.md` — Provenance rules, POV firewall (`[[05-visibility]]`), reading ledger requirement (`[[reading-ledger-rule]]`), the two writing gates, and the format of audit findings (§5, since 0.19.0: a finding counts only with its quotation, checked by `Validation/finding_check.py`).
- **2 Subagents (`agents/`):**
  - `agents/xuong-lam.md` (`opus`, `high` effort) — Single-role execution subagent (bound to a specific skill passed in the prompt: `extract-entities`, `plan-continuation`, or `write-chapter`).
  - `agents/xuong-kiem.md` (`sonnet`, `medium` effort) — Read-only blind verification subagent (`check-continuity`, `check-conflicts`, `check-style`, `review-plan`).
- **27 Skills (`skills/`):**
  1. **Setup & Source Ingestion (`4`):** `init-project`, `ingest-sources`, `doi-chieu-thu-vien`, `extract-entities`
  2. **Analysis & Canon (`4`):** `analyze-style`, `analyze-tropes`, `analyze-drop-point`, `crosscheck-canon`
  3. **Original & Special Contracts (`5`):** `brainstorm-premise`, `research-genre`, `worldbuild-original`, `crossover-contract`, `watch-frame-contract`
  4. **Planning & Drafting (`4`):** `plan-continuation`, `review-plan`, `write-chapter`, `viet-ba-model` *(Claude plans, DeepSeek writes, GPT reviews, Claude checks last — Aurel 2026-11-15)*
  5. **Verification & Finalization (`5`):** `check-continuity`, `check-conflicts`, `check-style`, `finalize-chapter`, `push-to-translate-center`. Since 0.19.0 `chapter_gate.py` also stops on broken model output (`Validation/degeneration.py`); since 0.20.0 it runs `style_metrics`, `ai_tells_check` and `pov_leak_check` as `[[07-state]]` §3 says, and the queue checks POV leaks
  6. **Project Management & Creative Support (`5`):** `project-status`, `dieu-phoi-hang-doi`, `summarize-run`, `persona`, `fanart-prompt`
