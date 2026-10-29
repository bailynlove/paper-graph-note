# Paper graph note

Two agent skills for turning a research paper into a readable, evidence-grounded workflow map. The output is a single offline HTML file drawn with native HTML, CSS, JavaScript, and SVG. No Mermaid, Pele, CDN, browser extension, API key, or build step is required to render it.

| Skill | Output | Use it when |
|---|---|---|
| `paper-graph-note` | Standalone research map, no Zotero links | You want a visual reading note you can open in any modern browser. |
| `paper-graph-note-zotero` | The same map with clickable Zotero PDF links | You want to jump from a claim to its PDF page or an existing highlight. |

The Zotero edition extends the normal skill; install both directories together. It does not require Better Notes and does not assume that Zotero item notes can render JavaScript.

## Contents

- [What the map shows](#what-the-map-shows)
- [Requirements](#requirements)
- [Install](#install)
  - [Pi package](#pi-package)
  - [Manual install](#manual-install)
- [Use with an agent](#use-with-an-agent)
  - [Normal edition](#normal-edition)
  - [Zotero edition](#zotero-edition)
- [Zotero permissions](#zotero-permissions)
- [Render without an agent](#render-without-an-agent)
- [Privacy and trust](#privacy-and-trust)
- [Test](#test)
- [Files](#files)

## What the map shows

Five lanes connect **research questions → related work → methods → experiments → future work**. Short node summaries stay visible; evidence and qualifications expand on demand. Inferred proposals have badges and dashed borders. A connection index records why nodes are related, including when JavaScript is disabled.

The visual treatment uses paper-like surfaces, large editorial headings, distinct lane colors, curved connections, keyboard focus highlighting, automatic light/dark themes, adjustable node width, horizontal scrolling, and print styles. It is a fixed five-lane reading map, not an unrestricted graph editor.

Open [`examples/demo.html`](examples/demo.html) for a rendered example. Its content and page references are explicitly fictional; it contains no real paper, private library information, or experimental results.

## Requirements

- A skill-capable agent to read the paper and compose the map.
- Python 3.10 or newer, standard library only, to render the HTML.
- A modern browser to view it. JavaScript draws connectors and adds controls; content, native evidence expanders, the connection index, and Zotero links remain usable without it.
- Zotero desktop only if you want Zotero navigation. The normal edition works independently.

The renderer is not a PDF parser or an LLM service. Your agent provides the paper-reading and synthesis capabilities it already has.

## Install

### Pi package

Install both skills from npm:

```bash
pi install npm:paper-graph-note
```

Alternatively, install from a local checkout:

```bash
pi install /absolute/path/to/paper-graph-note
```

Then start a new Pi session or use `/reload`. This package declares only skills, not extensions, tools, providers, or startup scripts. Do not add it to your installation until you have reviewed the skill and renderer files.

### Manual install

Copy both folders into your agent's skill directory, preserving the layout:

```text
<agent-skills-dir>/
  paper-graph-note/
    SKILL.md
    scripts/render.py
    assets/map.html
    references/format.md
  paper-graph-note-zotero/
    SKILL.md
    references/zotero.md
```

For Pi, the user-level skill directory is `~/.pi/agent/skills/`; project-only skills can go in `.pi/skills/`. Other agents may use `~/.agents/skills/`, `~/.claude/skills/`, or another documented location. Use the directory supported by your agent, and restart or reload it after copying. These are agent instructions plus a local script, not a Zotero plugin.

## Use with an agent

### Normal edition

In Pi:

```text
/skill:paper-graph-note Read this paper and make an HTML research map. Save it in the paper's attachments folder.
```

Or ask in natural language:

> Use paper-graph-note on the attached PDF. Show the research questions, related work, methods, experiments, and future work in one diagram. Clearly distinguish author claims from your inferences. Do not include Zotero links.

Provide the full paper, not just its abstract. The skill verifies source sections and physical PDF pages, preserves qualifications, and labels inferred future directions. It does not overwrite existing user notes by default.

### Zotero edition

```text
/skill:paper-graph-note-zotero Create a clickable research map for this Zotero PDF. Use verified page links; use existing annotation links where available. Save the HTML first, then tell me how to attach it.
```

Provide the PDF or its location plus a copied Zotero PDF link. A title alone may require an authorized integration to locate the correct item. You can paste links copied by Zotero or Better Notes; no plugin is needed for the diagram itself.

A page link opens a PDF page. An annotation link can target a specific highlighted passage. The skill must not claim paragraph-level navigation when it only knows the page, and must not create annotations silently.

To attach the file manually: select the parent paper in Zotero, choose **Add Attachment → Attach Stored Copy of File**, and select the HTML. Stored copies support Zotero file sync subject to your account settings and storage quota. Linked files depend on a local path and do not sync through Zotero file storage. If Zotero's internal HTML viewer blocks the links, open the file in the system browser and allow it to launch Zotero.

## Zotero permissions

**Generating a map, opening Zotero links, and manually attaching HTML require no API key.** Grant API access only if you separately want an agent to discover items or import files automatically.

| Workflow | Permission/setup |
|---|---|
| Normal map | None from Zotero. |
| Render Zotero map from a supplied PDF and copied link | None from Zotero; Zotero desktop and its protocol handler are needed to open the link. |
| Attach HTML yourself | Your normal access to the destination library. No agent/API authorization. |
| Local API discovery | Zotero desktop running, local API enabled under Settings → Advanced → “Allow other applications on this computer to communicate with Zotero”, where supported. Local reads are available in Zotero 7+. |
| Automated local writes | Zotero 10+ and a compatible integration with separately approved local authorization. File import support is also required. Deny or revoke access when not needed. |
| Remote private-library discovery/download | Explicitly configured Web API client; API key scoped to the intended library, with read/file access as needed. |
| Remote attachment upload | Explicit write authorization and appropriate file access; group libraries also require a role allowed to write. |

Local write keys and zotero.org Web API keys are different. Never put either in the map JSON, HTML, a skill, a prompt example, or Git. Use a credential manager or the integration's documented environment variables, such as `ZOTERO_API_KEY` for a Web API client. The renderer never reads credentials.

No importer is bundled. If your integration cannot import the actual file bytes safely, use manual attachment. Do not edit Zotero's database, guess storage paths, or treat a metadata-only attachment as a completed upload. Creating or replacing notes and annotations is outside this workflow unless explicitly requested.

More details and official references: [Zotero integration](skills/paper-graph-note-zotero/references/zotero.md).

## Render without an agent

The checked-in sample can be rendered with one command from the repository root:

```bash
python3 skills/paper-graph-note/scripts/render.py examples/demo.json /tmp/paper-map-demo.html
```

Open `/tmp/paper-map-demo.html` in your browser. The output path must not already exist; use a fresh filename for a revision.

To create your own map, follow [the JSON format](skills/paper-graph-note/references/format.md). It accepts plain text, exactly five lanes, unique node IDs, verified source locations, and labeled connections. HTML in text fields is escaped.

For a private Zotero map, add the `zotero` object described in that reference and run:

```bash
python3 skills/paper-graph-note/scripts/render.py private-map.json /tmp/paper-map-zotero.html --zotero
```

Only this flag enables Zotero links. Without it, Zotero configuration and annotation IDs are not emitted. That is **not** general content redaction: titles, summaries, and details are reproduced, so inspect them before sharing.

## Privacy and trust

- This repository contains only reusable instructions, rendering code, and a synthetic example. Keep actual papers, private maps, library identifiers, annotations, and generated personal notes elsewhere.
- Generated HTML makes no network requests and uses no remote fonts or scripts. It has a restrictive content security policy. Clicking a Zotero link deliberately invokes the local application.
- Offline rendering does not mean local-only AI processing: your agent may send paper text to its configured model. Follow the paper's confidentiality requirements before using a hosted model.
- Paper text is untrusted input, never an instruction to run commands, request permissions, or upload files. Rendering treats all text fields as text.
- Zotero maps contain attachment IDs and may contain group/annotation IDs. Do not publish them. Render a normal edition and inspect the prose if you need a shareable copy.
- This package does not install itself, request Zotero permissions, publish files, upload paper content, or modify library storage.

## Test

```bash
python3 -m unittest discover -s tests -v
```

Tests cover valid rendering, normal/Zotero separation, personal/group links, annotation handling, escaped text, input rejection, no-overwrite behavior, offline assets, and package privacy. Browser visual inspection and real Zotero navigation remain separate checks; unit tests do not prove a link opens your private PDF.

## Files

```text
skills/paper-graph-note/          Main skill, schema, renderer, native HTML template
skills/paper-graph-note-zotero/   Zotero workflow and permission guidance
examples/                       Synthetic JSON and generated HTML preview
tests/                          Standard-library checks
package.json                    Pi skills package manifest
```
