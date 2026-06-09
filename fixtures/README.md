# /fixtures — recorded JSON shared across the seam

The single source of recorded data that keeps the frontend and backend honest
with each other (ADR 0003). Both sides assert against the **same files**; when a
shape changes, regenerate here (`make fixtures`) and both test suites feel it.

**Provenance rule:** fixtures are *recorded or generated*, never hand-edited.
Each subdirectory documents its generator.

Planned contents (by phase):

| Dir | Contents | Generator | Phase |
|---|---|---|---|
| `seam/` | `IntelligenceService` request/response pairs per method | recorded from the FastAPI service | P4–P5 |
| `jira/` | recorded Jira issue/comment JSON for connector mapping tests | recorded from a real board (scrubbed) | P4 |
| `seed/` | the 52-week simulation scenario exported as offline demo data | `make fixtures` ← sim harness | P2/P8 |

Nothing here yet — directories appear with their phases.
