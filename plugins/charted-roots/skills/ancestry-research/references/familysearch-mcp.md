# FamilySearch MCP: connected research tools

Read if the FamilySearch MCP is connected in the environment or the user asks to set it up. Use a suitable connection straight away within the task and access rights, once the user has authorised web work for this task (`privacy-and-safety.md`, section 0); no separate mode needs switching on. Without it, continue with browser search and with the material in hand.

**Scope in this vault: read only.** Where the vault has an upstream master (core model § GEDCOM), that hosted tree is the master; vault changes reach the tree only through `gedcom-sync` and upstream edits by the user (`CLAUDE.md` § GEDCOM and any upstream-tree convention). Writing to a FamilySearch tree through the MCP — adding or changing persons, facts, relationships, sources or Memories — is outside the scope of this skill.

## 1. Connection and purpose

Discover the real tools and read the schemas of the operations needed. If authorisation diagnostics are available, check the account, environment and rights; the absence of a tool with a specific name such as `auth_status` does not by itself block the operations that are available.

Results go into the vault's own notes (`SKILL.md` § Where things live). The connection does not change that: having FamilySearch available does not move results there. Distinguish the production environment from the test one: a successful read in Beta says nothing about production.

## 2. Search and reading

Structured search, reading a profile and viewing an archival image have different capabilities. Check the supported filters and pagination; do not pass DGS, dates or parents as though every server accepts them. If the needed filter or viewer is missing, choose the browser route per `familysearch-indexes.md` and `field-lessons.md`.

An empty or truncated response does not establish that the record is absent: assess coverage and loading per `search-result-validation.md`. An unavailable viewer does not mean there is no document and does not stop other routes.

Record stable FamilySearch IDs/ARKs, the query, time of reading, original fields, links and the scope actually viewed in the `Survey -` note; a record worth keeping goes through `add-archive-record`. The FamilySearch tree and its hints are leads, not evidence: assess claims, identity resolution, every kinship edge and the dependence of copies per `evidence-protocol.md`. A source description or a Memory does not replace reading the document itself. Never treat the FamilySearch tree and the upstream hosted tree as independent when one may copy the other.

## 3. Changes to the FamilySearch tree

Outside scope (see above). If the research shows that a FamilySearch tree entry is wrong or incomplete, record the finding and its evidence in the relevant `Hypothesis -` or `Search Plan -` note; making the change is the user's decision and action. Never use a write tool "for technical success", and never invent a living status, rights or missing details.

## 4. Access, privacy and setup

The user performs authorisation through the connection's standard method. Do not extract cookies or tokens and do not get around protection; login procedure and real restrictions — `browser-and-captcha.md`. A connected server does not override the source's terms, limits or access to a specific image.

Handle living people's data, private files and publication per `privacy-and-safety.md`. Do not pass vault contents to the server beyond the search terms the query needs. Do not assume Memories or public-tree entries are private by default: consider the actual visibility of the chosen operation separately from citing it. Never upload files.

Do setup on the user's request and per the documentation of the chosen client and server, keeping the existing settings and limiting access to the task. Having an MCP does not require installing a particular third-party implementation or switching browsers. Do not suggest extracting the browser session or disguising the client as a way to connect or to get around a refusal.

In the report, separate what was actually read and verified from proposals and blocked steps.
