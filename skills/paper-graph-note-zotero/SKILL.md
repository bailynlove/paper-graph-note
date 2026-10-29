---
name: paper-graph-note-zotero
description: Create an evidence-grounded HTML research workflow map for a Zotero paper, with clickable PDF page or existing annotation links. Use when the user wants a visual paper note attached to a Zotero item or nodes that open the relevant passage in Zotero.
compatibility: Requires the sibling paper-graph-note skill and Python 3.10+. Zotero desktop must be installed for PDF links; API access is optional.
---

# Paper graph note for Zotero

This is the Zotero edition of the normal skill, not a separate renderer. Install both skill directories side by side. Read [../paper-graph-note/SKILL.md](../paper-graph-note/SKILL.md), then follow its reading, evidence, rendering, privacy, and visual QA workflow. Read [references/zotero.md](references/zotero.md) before obtaining permissions or attaching a file.

## Resolve the actual PDF

1. Identify the user-selected paper and its PDF attachment. Prefer a user-provided link from Zotero's “Copy Link” action or Better Notes. If the user provides only a title, use their existing authorized Zotero integration to find the exact item; ask if ambiguous. Never silently choose a similarly titled paper or a supplement.
2. Record the PDF attachment key and library kind. A personal-library link uses `library`; a group link uses `groups/<numeric-group-id>`. Do not confuse the parent paper key, PDF key, HTML key, local library ID, or account ID.
3. Read the actual paper and map each node to a verified physical PDF page. Existing `zotero://open-pdf/...` links can supply page and annotation IDs; preserve valid IDs after checking they belong to this PDF.
4. An ordinary `?page=N` link opens a page, not a paragraph. A copied `&annotation=KEY` link targets a specific highlight. Use existing annotations for passage precision; creating new annotations is an additional library write requiring explicit permission. If no exact annotation is available, use an honest page link, not a claim of paragraph precision.

## Generate the Zotero HTML

Use the normal JSON contract plus `zotero` as documented in [../paper-graph-note/references/format.md](../paper-graph-note/references/format.md). Add `source.annotation` only when known. Keep all source locations verified, including physical PDF page numbering.

```bash
python3 <base-skill-dir>/scripts/render.py private-map.json paper-map-zotero.html --zotero
```

Only nodes with a PDF page get a clickable body. The separate evidence expander does not navigate. Inferred nodes link to the underlying limitation or conclusion only if that passage genuinely motivates the inference; otherwise leave them unlinked. Explicitly distinguish a proposal from author-stated future work.

Test at least one page link and, if present, one annotation link in the actual Zotero library. Browser screenshots alone cannot verify protocol navigation. If the internal HTML reader blocks custom protocols, open the attachment in the system browser and accept the prompt to launch Zotero. State the fallback rather than claiming untested reader compatibility.

## Attach, without corrupting the library

The default is a generated local file plus manual attachment instructions. If the user explicitly requests attaching it, use an existing authorized Zotero integration with a supported file-import operation, or ask them to use Zotero's “Add Attachment” → “Attach Stored Copy of File” on the selected parent item. Stored copies are preferred for sync; linked files depend on local paths and do not sync through Zotero file storage.

Never edit Zotero's SQLite database, guess a storage directory, create attachment metadata without importing the bytes, or copy files into managed storage yourself. Do not request a local write key merely to generate a link. If automation is unavailable, stop at the complete HTML and explain the one manual import step.

After any automated import, read back the new attachment, confirm its parent, filename, content type, and retrievable file bytes, then open it. Partial metadata success is not a successful file attachment. Do not delete or replace an existing note, PDF, or map without explicit permission.

## Confidentiality boundary

The Zotero HTML embeds private attachment identifiers and may include group and annotation IDs. This is required for local navigation, not appropriate for a public example. Keep it out of the distributable skill repository. For a shareable version, render again **without** `--zotero`, inspect all prose for private content, and obtain permission before sharing. Never include local paths, auth responses, or API keys in JSON, HTML, logs, screenshots, or documentation.
