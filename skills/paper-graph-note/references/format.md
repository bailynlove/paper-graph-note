# Map data format

The JSON is a writing interface, not an extraction result. The agent must read and verify the paper before filling it in. Text fields are plain text, not HTML or Markdown. The renderer escapes them and never executes content from the paper.

## Root

| Field | Required | Meaning |
|---|---|---|
| `title` | Yes | Paper title or short descriptive title. |
| `subtitle` | No | One sentence framing the central question. |
| `citation` | No | Verified bibliographic string; plain text, not a URL. |
| `lanes` | Yes | Exactly five lane objects in the order below. |
| `edges` | No | List of `{ "from": "node-id", "to": "other-id", "label": "why connected" }`. |
| `zotero` | Zotero mode only | Link configuration, never required for normal output. |

Each lane has `id` and `nodes`. Lane IDs in order: `questions`, `related`, `method`, `experiments`, `future`. Each needs 1 to 8 nodes; aim for 2 to 4. If a lane has no source evidence, use a node explaining the absence. Edges are limited to 80 for legibility; do not add self-loops. Duplicate node IDs and dangling edges are rejected. Backward edges are allowed, but dense or cyclic graphs may be clearer in the connection index. The layout is a five-lane reading map, not a general graph-layout engine.

## Node

```json
{
  "id": "method-retrieve",
  "title": "Retrieve supporting evidence",
  "summary": "Fetch candidate passages before making a decision.",
  "details": [
    "Preserve an exact formula or result here when it matters.",
    "Qualify what the experiment does and does not show."
  ],
  "source": { "section": "3.1 Retrieval", "page": 4 },
  "inferred": false
}
```

`id`, `title`, and `summary` are required. IDs start with a lowercase letter and contain lowercase letters, numbers, and single or repeated hyphens, up to 64 characters. Use short semantic IDs. `details` is an optional list of plain-text bullets. `inferred` defaults to false; set true for your reconstruction or proposal, not for a reported result. The renderer shows an inferred badge, dashed node border, and dashed incoming edges.

`source` is optional; if present, `section` is required and `page` is an optional positive integer. Page means the physical PDF page, starting at 1. Prefer a source on every factual node. A node spanning several locations should link to its most relevant passage, with other locations described in details. An absent location is shown honestly rather than guessed.

## Zotero edition

Supply this root object only in private, per-paper input; these values below are deliberately fake:

```json
{
  "zotero": {
    "library": "personal",
    "attachment": "DEMO0001"
  }
}
```

For a group library, use `"library": "group"` and a positive numeric `"group_id"`. `attachment` is the **PDF attachment's** eight-character item key, not the parent bibliographic item, HTML attachment, user ID, or filename.

A node with a verified `source.page` gets a link in Zotero mode. For a paragraph-exact link, optionally add `"annotation": "DEMO0002"` to its source, copied from an existing annotation on that PDF. An annotation requires a page. Never fabricate annotation keys or create annotations silently. A node lacking a page stays unlinked.

```bash
python3 <base-skill-dir>/scripts/render.py private-map.json paper-map-zotero.html --zotero
```

Normal mode emits no Zotero links and discards the Zotero configuration and annotation keys even if they occur in the input. It does not redact other text: do not put private information in the title, summary, or details and expect automatic removal.
