# Privacy, consent and safe boundaries

Read this file when working with living people, the user's own documents, DNA, adoption or repression, and before preparing anything to be passed to third parties.

## 0. Vault rule (overrides everything below)

The vault holds data on living people. Check `enablePrivacyProtection` in `data.json`: when it is `false`, the plugin redacts nothing automatically, and even when it is on, it does not cover what you write into a search query, a letter or a report (core model § Working conventions, Privacy).

- **No web search, portal lookup, upload or e-mail without the user's explicit instruction for this task.** An instruction for one task does not carry over to the next.
- **Never paste vault contents** — notes, transcriptions, scans, names and dates of living people — into external services (search engines, translation or OCR services, image tools, forums, AI services, archive web forms) unless the user has explicitly instructed it for that item. Search queries contain only the historical data the query needs.
- Reading local scans and vault notes, and local processing (cropping, OCR, translation with local tools), needs no authorisation.

## 1. Data minimisation

Collect only the data the research question needs. Once the user has authorised the task (including web work, if they have), it covers reading the materials provided, searching public historical sources, keeping evidence in the vault and ordinary local processing; do not ask permission for every search, scan or extracted fact within that scope. Permissions already given apply within their stated limits.

## 2. Living people

For a person who is clearly or probably alive:

- confine the search to the family-history task;
- use the already known connection to the family and the materials provided; mark what is unknown without guessing, and continue with the historical part of the search that is available;
- do not look for a current address, phone number, personal e-mail, workplace, movements, accounts or financial information;
- do not publish a full date of birth, document numbers or other identifiers;
- use public historical records and the user's materials only to the extent needed;
- if the purpose turns intrusive, stop that part of the search.

## 3. Minors

Do not trace minors on the web and do not include their personal data in any output, beyond the minimal fact of a relationship that the user provided directly and the task requires.

## 4. The user's documents

- Work on copies; never alter originals.
- Do not pass private documents, family photos or DNA data to new external services without explicit consent. Until it is given, use the local tools available and continue the other checks.
- Do not publish passport data, signatures, addresses, recent-period act-record numbers or other unnecessary identifiers.
- When preparing a version for sharing, redact living people's data (section 8).
- Do not apply face recognition or reverse image search to pictures of living people. Further restrictions on photographs — `photo-search.md`.

## 5. Sensitive findings

These include possible adoption, misattributed paternity, DNA matches, repression, criminal cases, deportation, captivity, ethnic and religious affiliation, and medical information.

Rules:

1. report them neutrally and only if they bear directly on the research question;
2. keep the text of the record separate from its interpretation;
3. draw no psychological, moral or biological conclusions beyond the source;
4. mark uncertainty;
5. minimise data on living relatives;
6. do not recommend sudden contact with a potential relative as an automatic next step.

## 6. DNA

- Analyse only results the user has provided.
- Do not upload raw data or match lists to third-party databases without separate consent.
- Do not treat match size as the sole proof of an exact relationship.
- Take endogamy, multiple relationship paths and incomplete trees into account.
- Phrase conclusions about biological relationship cautiously and with alternatives.
- For assessing DNA as evidence, independence groups and working in DNA-service accounts, see the [evidence protocol, section "DNA"](evidence-protocol.md#dna).

## 7. Forbidden sources and methods

Do not use:

- leaks, dumped databases, stolen documents;
- current-address/phone aggregators to identify living people;
- hacked accounts and other people's sessions;
- a false cover story to join closed communities;
- circumvention of paywalls, geoblocking, CAPTCHA mechanisms or rate limits; the permitted single attempt through the normal interface and the hand-over to the user are described in `browser-and-captcha.md`, sections 5–5a;
- bulk harvesting of social-media profiles.

## 8. Report to the user and a version for sharing

The working report goes to the user in the conversation (`SKILL.md` § Workflow, step 9); findings live in the vault's own notes. Prepare a redacted version only when the user explicitly asks for something to be shared outside the vault. In that version:

- replace living people with initials or `P-xxxx`;
- remove current contacts, exact addresses and identifiers;
- cut down sensitive attachments;
- keep the references to historical sources and the method;
- state that some data has been withheld for privacy.

When updating a version for sharing, compare its content with the available previous version. Information removed from a table may remain in a retelling, an interview transcript, a caption or an image. Apply the restrictions recorded in the vault (the Person notes, `private` flags) to the actual content of the version, including for people whose living status is unknown. If it is confirmed that a previous version containing such information was passed on, tell the user. Where only a copy survives and there is no record of it being sent, note that the transfer is not confirmed.

## 9. Contacting people and institutions

Messages to people and institutions, applications and publications are the user's to send. The agent drafts; it never sends, submits or publishes, whatever tools are connected. Draft the text and leave sending as a step waiting on the user (in the `Search Plan -` note), carrying on with the research.

For requests to institutions use [correspondence.md](correspondence.md): choosing the recipient, the official channel, the letter's contents, recording it in the letters folder and the letters index, and handling the reply. Access to a mailbox gives no permission to correspond; the bans and permissions of the specific task apply regardless of what the tools can do.

Consent to an interview with a relative, the option to skip sensitive topics, and the terms on which what was told may be passed on — per `relatives-interview.md`.
