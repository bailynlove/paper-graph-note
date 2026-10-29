#!/usr/bin/env python3
"""Render a paper map offline using only the Python standard library."""
import argparse
import base64
import hashlib
import html
import json
from pathlib import Path
import re
from urllib.parse import urlencode

LANES = (
    ("questions", "Research questions", "What needs answering?"),
    ("related", "Related work", "Where existing work stops"),
    ("method", "Method", "How the paper responds"),
    ("experiments", "Experiments", "What the evidence supports"),
    ("future", "Future work", "What remains open"),
)
ID = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")
KEY = re.compile(r"[A-Z0-9]{8}\Z")


def text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonempty text")
    return value


def positive_int(value, field):
    if type(value) is not int or value < 1:
        raise ValueError(f"{field} must be a positive integer")
    return value


def validate(data, zotero=False):
    if not isinstance(data, dict):
        raise ValueError("input must be an object")
    text(data.get("title"), "title")
    for field in ("subtitle", "citation"):
        if field in data:
            text(data[field], field)
    lanes = data.get("lanes")
    if not isinstance(lanes, list) or len(lanes) != 5:
        raise ValueError("provide exactly five lanes")
    if any(not isinstance(lane, dict) for lane in lanes):
        raise ValueError("each lane must be an object")
    if [lane.get("id") for lane in lanes] != [lane[0] for lane in LANES]:
        raise ValueError("lane order: questions, related, method, experiments, future")
    ids = set()
    for lane in lanes:
        nodes = lane.get("nodes")
        if not isinstance(nodes, list) or not 1 <= len(nodes) <= 8:
            raise ValueError("each lane needs 1 to 8 nodes")
        for node in nodes:
            if not isinstance(node, dict):
                raise ValueError("each node must be an object")
            ident = node.get("id")
            if not isinstance(ident, str) or not ID.fullmatch(ident) or ident in ids:
                raise ValueError("node IDs must be unique lowercase slugs")
            ids.add(ident)
            text(node.get("title"), "node.title")
            text(node.get("summary"), "node.summary")
            if type(node.get("inferred", False)) is not bool:
                raise ValueError("inferred must be a boolean")
            details = node.get("details", [])
            if not isinstance(details, list):
                raise ValueError("details must be a list of plain-text strings")
            for detail in details:
                text(detail, "detail")
            source = node.get("source")
            if source is not None:
                if not isinstance(source, dict):
                    raise ValueError("source must be an object")
                text(source.get("section"), "source.section")
                if "page" in source:
                    positive_int(source["page"], "source.page")
                if "annotation" in source and (
                    not isinstance(source["annotation"], str)
                    or not KEY.fullmatch(source["annotation"])
                ):
                    raise ValueError("annotation must be an eight-character Zotero key")
                if "annotation" in source and "page" not in source:
                    raise ValueError("annotation requires a PDF page")
    edges = data.get("edges", [])
    if not isinstance(edges, list) or len(edges) > 80:
        raise ValueError("edges must be a list of at most 80 connections")
    for edge in edges:
        if not isinstance(edge, dict) or any(
            not isinstance(edge.get(side), str) or edge[side] not in ids
            for side in ("from", "to")
        ):
            raise ValueError("edge endpoints must reference existing nodes")
        if edge["from"] == edge["to"]:
            raise ValueError("self connections are not supported")
        text(edge.get("label"), "edge.label")
    if zotero:
        z = data.get("zotero")
        if not isinstance(z, dict) or z.get("library") not in ("personal", "group"):
            raise ValueError("Zotero mode needs zotero.library: personal or group")
        if not isinstance(z.get("attachment"), str) or not KEY.fullmatch(z["attachment"]):
            raise ValueError("zotero.attachment must be the eight-character PDF attachment key")
        if z["library"] == "group":
            positive_int(z.get("group_id"), "zotero.group_id")


def pdf_link(z, source):
    if not source or "page" not in source:
        return None
    library = "library" if z["library"] == "personal" else f"groups/{z['group_id']}"
    params = {"page": source["page"]}
    if "annotation" in source:
        params["annotation"] = source["annotation"]
    return f"zotero://open-pdf/{library}/items/{z['attachment']}?{urlencode(params)}"


def render(data, zotero=False):
    validate(data, zotero)
    esc = html.escape
    node_map = {n["id"]: n for lane in data["lanes"] for n in lane["nodes"]}
    columns = []
    for i, (lane, (_, title, caption)) in enumerate(zip(data["lanes"], LANES), 1):
        cards = []
        for node in lane["nodes"]:
            inferred = node.get("inferred", False)
            source = node.get("source")
            location = "No source location supplied"
            if source:
                location = source["section"]
                if "page" in source:
                    location += f" · p. {source['page']}"
            badge = '<span class="badge">Inferred</span>' if inferred else ""
            href = pdf_link(data["zotero"], source) if zotero else None
            content = (
                f'<span class="node-top"><span class="node-id">{esc(node["id"])}</span>{badge}</span>'
                f'<h3>{esc(node["title"])}</h3><p>{esc(node["summary"])}</p>'
                f'<span class="source">{esc(location)}'
                + ('<span class="open-mark" aria-hidden="true">↗</span>' if href else "")
                + '</span>'
            )
            if href:
                precision = "annotation" if "annotation" in source else "page"
                body = f'<a class="node-body" href="{esc(href)}" title="Open PDF {precision} in Zotero">{content}</a>'
            else:
                body = f'<div class="node-body">{content}</div>'
            details = ""
            if node.get("details"):
                bullets = "".join(f"<li>{esc(d)}</li>" for d in node["details"])
                details = f'<details class="node-details"><summary>Evidence &amp; details</summary><ul>{bullets}</ul></details>'
            cards.append(f'<article class="node{" inferred" if inferred else ""}" id="n-{node["id"]}" tabindex="0">{body}{details}</article>')
        columns.append(
            f'<section class="lane lane-{i}" aria-labelledby="lane-{i}">'
            f'<header class="lane-head"><span class="lane-number">0{i}</span>'
            f'<div><h2 id="lane-{i}">{title}</h2><p>{caption}</p></div></header>'
            f'<div class="node-stack">{"".join(cards)}</div></section>'
        )
    paths, connections = [], []
    for edge in data.get("edges", []):
        start, end = edge["from"], edge["to"]
        inferred = node_map[end].get("inferred", False)
        paths.append(
            f'<path class="connection{" hypothesis" if inferred else ""}" data-from="n-{start}" data-to="n-{end}" marker-end="url(#arrow)">'
            f'<title>{esc(edge["label"])}</title></path>'
        )
        connections.append(
            f'<li><a href="#n-{start}">{esc(node_map[start]["title"])}</a>'
            f'<span>{esc(edge["label"])}</span><a href="#n-{end}">{esc(node_map[end]["title"])}</a></li>'
        )
    template = (Path(__file__).resolve().parent.parent / "assets" / "map.html").read_text(encoding="utf-8")
    script = re.search(r"<script>(.*?)</script>", template, re.S).group(1)
    digest = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    replacements = {
        "TITLE": esc(data["title"]),
        "SUBTITLE": esc(data.get("subtitle", "A reading path from research question to open problem.")),
        "CITATION": esc(data.get("citation", "")),
        "MODE": "Zotero edition" if zotero else "Research map",
        "HINT": (
            "Click a node to open its PDF page in Zotero. Annotation links, when supplied, target a highlight."
            if zotero else "Follow the connections. Expand a node for evidence and reading notes."
        ),
        "LANES": "".join(columns),
        "PATHS": "".join(paths),
        "CONNECTIONS": "".join(connections) or "<li>No explicit connections supplied.</li>",
        "SCRIPT_HASH": digest,
    }
    return re.sub(r"@@([A-Z_]+)@@", lambda m: replacements[m.group(1)], template)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Evidence-grounded map JSON")
    parser.add_argument("output", type=Path, help="Self-contained HTML file (must not exist)")
    parser.add_argument("--zotero", action="store_true", help="Include Zotero PDF links")
    args = parser.parse_args()
    try:
        result = render(json.loads(args.input.read_text(encoding="utf-8")), args.zotero)
        with args.output.open("x", encoding="utf-8") as out:
            out.write(result)
    except (ValueError, TypeError, OSError) as error:
        parser.exit(1, f"error: {error}\n")
    print(f"Created {args.output.name}")


if __name__ == "__main__":
    main()
