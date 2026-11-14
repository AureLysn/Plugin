# Fiction Studio Vault Configuration (`shared/vault-config.md`)

Authoritative directory and tool path mapping for **`xuong-viet-tiep-truyen`** inside **`D:\AureLysn`** (`lane: personal`).

---

## 1. Zone & Project Paths (`05_Evasion/`)

| Logical Role | Vault Path in `D:\AureLysn` | Scope & Rule |
|---|---|---|
| **Fiction Root (`01_Oeuvre`)** | `05_Evasion/01_Oeuvre/` | Root 2 indexed area (`--include-fiction` / `-f`). |
| **Shared Fandom Canon** | `05_Evasion/01_Oeuvre/Database/Fandom/<UNIVERSE>/` | `scope: universe` (`canon_layer: official_canon` / `fandom_wiki`). **Never** write project-specific facts or project codes here (`[[04-lanes]]`). |
| **Shared Fiction Principles & Taxonomy** | `05_Evasion/01_Oeuvre/Database/Principle/` · `Database/Taxonomy/` | `scope: global`, `lane: personal`. |
| **Continuation Projects** | `05_Evasion/01_Oeuvre/Studio/Continue/<CODE>_<slug>/` | `scope: project` (`EMB`, `PPCT`, `TDTB`, `UNTCH`, `CLS`, `TRIAD`, etc.). |
| **Original Story Projects** | `05_Evasion/01_Oeuvre/Studio/Original/<CODE>_<slug>/` | `scope: project` for original fiction. |
| **Reading Library Subsystem (`Kệ Sách`)** | `05_Evasion/02_Library/` | The reading app's code and its own data. The books are in the store `library` (cards in `02_Storage/05_Library/`). No skill writes here. |
| **Genre & Trope Taxonomy** | `05_Evasion/01_Oeuvre/Database/Taxonomy/` (`Genres/`, `Tropes/`, `AU/`) | Genre maps and cross-fandom tropes (`research-genre`). A fandom's own trope map is `Database/Fandom/<UNIVERSE>/Lore/trope-fandom-<universe>.md`. |
| **Translation & Desk Subsystem (`Nexus`)** | `05_Evasion/03_Subsystems/Nexus/` | `TranslateCenter` / `Nexus` SQLite (`library.db`) and bilingual chapter sync (`push-to-translate-center`). |

---

## 2. Standard Project Internal Layout (`<CODE>_<slug>/`)

The layout below is the one on disk in all story projects and in the skeleton `Studio/<Continue|Original>/<CODE>_<slug>/`. A project folder is named `<CODE>_<slug>`, for example `EMB_ex-mafia-boss-done-with-life`.

| Subfolder | Entity `type:` | Purpose |
|---|---|---|
| `00_Overview/` | `project`, `info` | Project note (`<CODE>.md`), drop-point analysis, project rules |
| `01_Project-canon/` (`sources/`, `notes/`) | `source`, `rule` | Curated source notes (`type: source`) and the source register. Raw and extracted source files live in the store `personal-bulk` under `fiction-sources/<CODE>/`, with a card in `02_Storage/01_Personal_Archive/fiction-sources/` |
| `02_Story_Bible/` (`characters/`, `locations/`, `organizations/`, `relationships/`, `secrets/`, `world-rules/`, `style/`) | `character`, `location`, `organization`, `relationship`, `secret`, `fact`, `rule`, `style` | Project-scoped cast, places, secrets and facts. `style/` holds `targets.md`, `signature.md`, `hard-rules.md` and `ai-tells.md` (with its `gate:` block) |
| `03_Development/` (`arcs/`, `structure/`, `timeline/`, `tracker/`) | `arc`, `event`, `timeline`, `hook` | Arcs, structure notes, events and timeline, and the hook tracker |
| `04_Manuscript/` (`chapters/`) | `chapter_plan`, `scene`, `chapter`, `chapter_summary` | Chapter plans, scene cards, prose chapters (`draft` / `final`) and chapter summaries, grouped by arc |
| `05_Management/` (`crosscheck/`, `decisions/`, `questions/`, `inbox/`, `snapshots/`) | `decision`, `question`, `info`, `note` | Decisions, open questions, crosscheck records. `snapshots/` holds dated copies and is outside the index |
| `06_Alternate_Versions/` (`branches/<branch-slug>/`) | `branch` (`always_load: true` on branch) | Alternate-continuity contracts and branch-scoped notes (`[[04-lanes]]` §2.3) |

---

## 3. Authoritative Schema, Craft Rules & Templates (`01_Origine/`)

- **Schema (`01_Origine/05_Meta/Schema/`):**
  `[[01-frontmatter]]` · `[[02-entity-types]]` · `[[03-precedence]]` · `[[04-lanes]]` · `[[05-visibility]]` · `[[06-retrieval]]` · `[[07-state]]` · `[[08-impact]]` · `[[09-gates]]`
- **Writing Craft & Structure Rules (`01_Origine/02_Knowledge/Curated_Notes/writing/`):**
  - Prose craft (`11` rules): `[[one-point-of-view-per-scene]]`, `[[show-and-tell-balance]]`, `[[concrete-specific-detail]]`, `[[exposition-through-action]]`, `[[resist-the-urge-to-explain]]`, `[[said-and-action-beats]]`, `[[vary-sentence-length]]`, `[[scene-goal-conflict-outcome]]`, `[[scene-and-sequel]]`, `[[scene-must-turn]]`, `[[setup-and-payoff]]`
  - Narrative structure (`15` rules in `structure/`): `[[three-act-structure]]`, `[[save-the-cat-beat-sheet]]`, `[[seven-point-structure]]`, `[[heros-journey]]`, `[[kishotenketsu]]`, `[[braided-multiple-pov]]`, `[[frame-narrative]]`, `[[composite-novel]]`, `[[loop-narrative]]`, `[[chapter-end-hook]]`, `[[chinese-webnovel-chapter-conventions]]`, `[[japanese-web-novel-conventions]]`, `[[detective-fair-play]]`, `[[romance-central-love-story]]`, `[[ao3-ratings-and-archive-warnings]]`
- **Note Templates (`01_Origine/04_Tools/Templates/`):**
  `characters/`, `continuity/`, `project/`, `story_development/`, `world_reference/`, `writing/`

---

## 4. Deterministic Fiction CLI Tools (`01_Origine/04_Tools/VaultTool/`)

Always run from the vault root (`D:\AureLysn`):

| Script Path | Purpose |
|---|---|
| `Core/vault_doctor.py --include-fiction` | Validates frontmatter, enums, IDs, and wikilinks across Root 1 + Root 2 |
| `Core/vault_index.py --build --include-fiction` | Rebuilds Root 1 and Root 2 search indexes |
| `Core/context_resolver.py` | Resolves permitted context notes for `--scene <scene-card>` or `--project <CODE> --pov <char>` (`--role writer | planner | reviewer`) |
| `Validation/chapter_gate.py <chapter.md>` | Master chapter gate running `style_metrics`, `ai_tells_check`, and `pov_leak_check` |
| `Validation/pov_leak_check.py` | Scans chapter prose against `02_Story_Bible/secrets/` (`known_by` / `suspected_by` / `unknown_to`, `leak_terms`) |
| `Validation/ai_tells_check.py` | Checks cliché/AI-tell phrases and regex density against `02_Story_Bible/style/ai-tells.md` |
| `Validation/entity_check.py --project <CODE>` | Gate of `extract-entities`: completeness of a project's character, location, organization, secret, hook and fact notes |
| `Validation/card_check.py` | Storage cards of a store against its folders (`--store`, `--zone`, `--all`); not a story tool |
| `Reporting/style_metrics.py` | Measures sentence length distribution, dialogue ratio, and paragraph cadence (Latin + CJK) |
| `Reporting/project_table.py` | Generates the project registry table from disk |
| `Tracking/hook_ledger.py` | Audits open, overdue, and paid-off narrative hooks (`type: hook`) |
| `Tracking/giao_viec.py` | Task queue dispatcher for multi-batch extraction/audit runs |
| `Tracking/state_apply.py` | Applies `delta.yaml` state transitions upon chapter finalization (`[[07-state]]`) |
| `Utilities/plan_gate.py --project <CODE>` | Pre-flight gate before planning: the earlier stages left their notes. It reads the project, not an individual plan |
| `Scripts/tram_dich_push.py` | Syncs finalized chapters to `05_Evasion/03_Subsystems/Nexus/` (`TranslateCenter`) |
