# Source collections

Sources are grouped by type under parents named `Collection - <Group>.md`; each non-parent Source carries `source_parent` + `source_parent_id`.

- `source_parent` has **no reverse sync** — write the child side only (safe with Obsidian open). No children list on the parent; backlinks are the membership view.
- One parent per Source. A type-based axis excludes the collection → entry hierarchy; switching means replacing the axis, not adding one.
- **Cite the child, never the parent.** Parents carry no `repository`, no evidence, `confidence: unknown`.
- A parent's `source_type` is its children's dominant valid type, else `custom`. A child's type may differ.
- Parents are excluded from source counts (`source_parent.isEmpty()` finds them). Recompute counts; never trust a written figure.
