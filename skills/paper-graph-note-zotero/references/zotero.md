# Zotero links, attachments, and permissions

## No API key is needed to make or open links

A personal-library PDF page link looks like this (fake example):

```text
zotero://open-pdf/library/items/DEMO0001?page=4
```

An existing highlight can be targeted with:

```text
zotero://open-pdf/library/items/DEMO0001?page=4&annotation=DEMO0002
```

A group-library link uses the numeric group ID, not an account or local database ID:

```text
zotero://open-pdf/groups/123456/items/DEMO0001?page=4
```

Get a real link using the PDF reader's “Copy Link” action when available, an annotation's copied link, or Better Notes' link-copy features. Menu labels vary by version. Better Notes is optional; it supplies navigation links, not this skill's renderer. Do not install it merely to draw the map.

The target PDF must exist in the viewer's Zotero library. Zotero must be registered as the `zotero://` protocol handler. A browser may ask permission to open Zotero; approve only expected links. An ordinary page link is not a text search, text fragment, or paragraph anchor. Annotation IDs are the route to exact passages.

## Manual attachment (recommended, no API authorization)

Select the parent paper in Zotero, choose “Add Attachment” → “Attach Stored Copy of File”, and select the generated `.html` file. Confirm that the attachment is a child of the paper, not a new standalone item. Open it to verify the file was imported. Use a stored copy if you want file sync, subject to your account's storage settings and quota.

Generating HTML and manually importing it do not require enabling the local API, creating a Web API key, or granting an agent library-write access.

## Optional automated local discovery

With Zotero desktop running, enable Settings → Advanced → “Allow other applications on this computer to communicate with Zotero” if your version provides that option. The local API normally listens at `http://127.0.0.1:23119/api`. Use your integration's version-specific setup; do not expose this port to the network.

Local reads are available on Zotero 7+ without a Web API key when enabled. Some integrations introduce their own permission prompts. Grant only the access needed to locate the parent and PDF attachment.

## Optional automated writes

Zotero 10+ supports separately authorized local writes. A compatible integration requests local authorization; Zotero shows a permission dialog. “Allow” and “Always Allow” may have different persistence behavior. Local keys are distinct from zotero.org Web API keys. The integration must discover and send the current `Zotero-Server-ID` and handle version preconditions. Never hardcode a server ID, key, or previously read item version. Do not repeatedly prompt after a denial.

For older Zotero versions, unavailable upload support, or denied access, use manual attachment instead. Do not work around missing permissions by editing SQLite or managed storage. File import must include the actual bytes through a supported importer or upload API, not just attachment metadata.

## Optional remote Web API

Remote automation is not needed by these skills. If explicitly requested, use a supported client and a key scoped to the intended personal or group library:

| Operation | Access needed |
|---|---|
| Locate metadata | Read access to that library |
| Fetch private PDFs | Read access including files |
| Create an HTML child attachment and upload bytes | Library write access and appropriate file access; group role must allow it |
| Read or modify notes/annotations | Relevant notes/read or write permissions, only if this extra operation is requested |

Check the current permission labels in Zotero's key settings; do not grant all libraries by default. Store keys in a credential manager or environment variable such as `ZOTERO_API_KEY`, never in a map or skill file. Local authorization uses a separate key; if an integration needs environment configuration, document its variable name without its value. Revocation and retention are controlled by Zotero and the integration, not by the HTML renderer.

## What to report

Distinguish: HTML rendered; attachment metadata created; bytes imported; file opened; page link tested; annotation link tested. Report only stages actually verified. A synced attachment may reveal the note to other users of a shared library; check the library's audience before import.

## References

- [Zotero local API](https://www.zotero.org/support/dev/web_api/v3/local_api)
- [Zotero Web API](https://www.zotero.org/support/dev/web_api/v3/start)
- [Stored and linked files](https://www.zotero.org/support/attaching_files)
- [File upload protocol](https://www.zotero.org/support/dev/web_api/v3/file_upload)
