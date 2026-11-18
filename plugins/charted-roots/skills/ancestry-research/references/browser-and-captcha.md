# Browser, dynamic sites and CAPTCHA

Read this file when using the agent's built-in browser, downloading material, or meeting blocks, CAPTCHAs, logins and rate limits.

**Precondition.** Browsing, web search, portal lookups and downloads happen only once the user has explicitly authorised web work for this task (`privacy-and-safety.md`; `SKILL.md` § Rules that win). Reading local scans and vault notes needs no authorisation.

## 1. Establish capabilities

Choose among the available search, page viewing, APIs, HTTP requests and local tools according to the task. A missing browser or a missing feature does not stop work on other sources or on material already obtained. Never claim an action the tool did not actually perform.

## 2. Normal browsing cycle

1. Open the original page.
2. Check the owner, title, date and a stable identifier.
3. Go on to the original record if the result is a snippet or an index.
4. Record the query and the URL (in the `Survey -` note).
5. Keep the minimum necessary fragment and its provenance.
6. Respect the site's pauses, limits and rules; no bulk harvesting.

### Loading frames and indexes

After moving to a frame, match its number against the image or cards actually shown. If the viewer still shows the previous content or an empty panel, wait for it to refresh with the viewing means available and check the needed fragment again. After zooming in, make sure the parts of the image needed for reading have loaded. Go by the content of the selected frame and the legibility of the area you need.

On signs of a transient failure you may reopen the frame within the source's rules. On a CAPTCHA, a block or `429`, follow sections 5 and 7. Record a persistent failure and the resume point per section 8, carrying on with other available checks. Leave cards or image areas that did not load as unchecked. Check the completeness of an index result per `search-result-validation.md`.

## 3. Documents and scans

On signs of an incomplete PDF transfer, check the tool's messages, the expected size of the same copy in a comparable representation, and whether the needed pages open in an available PDF tool. The HTTP status, file signature and hash record the response and the bytes received; check the completeness of the file and the legibility of the pages separately. If reading failed, state the failure observed and leave the cause unknown until it is established. The number of PDF pages may differ from the printed pagination.

Record the state of the transfer, what the copy contains and the pages actually read. If another permitted copy is available, check its provenance and give its actual address. Usable fragments may be used with their bounds stated. Limit any negative result to the pages read, per section 8.

- For PDFs of scans, look at the relevant pages visually.
- Use OCR only as an auxiliary layer.
- Evidentiary copies and fragments that the source's rules allow you to keep go into the vault through `add-archive-record` (scan in the archive folder, `.jpg` or `.pdf` only — PNG converted with `sips`, per `archive.md` § Scan files). No separate question per file is needed once web work is authorised. Working downloads that are not yet records stay in the session scratchpad, never in the skill folder.
- If copying is unavailable or forbidden by the source, carry on viewing and record the URL, frame/page and archival reference in the Survey note (and on the Source, if one is created).
- If the source delivers a file as one large PDF (e.g. Wikimedia Commons) and page-by-page viewing is slow, you may download the whole file under the source's rules and extract the embedded images, keeping the original encoding where supported (e.g. `pdfimages -j` for JPEG, or `pdfimages -all` from poppler). A contributor observed on 29–30.10.2026 that PDFs of 0.2–0.7 GB downloaded from Commons in a few minutes and yielded original JPEGs of about 530 ppi, whereas page rendering through the API took 4 to 60 s per page, was capped at 960–1280 px width and drew `429` during continuous viewing. Thumbnails can help find the cover and the table of contents; check illegible text at full resolution. Tie the extracted images to the source PDF (its URL in the Survey note) and keep the page-to-image mapping, e.g. via `pdfimages -list` or page numbers in the filenames (`pdfimages -p`); on `429`, follow section 7. Keep the extracted set in the scratchpad; only the pages that become records enter the vault.
- Local cropping, enlarging, OCR and translation are part of the research. Passing private material to external services — per `privacy-and-safety.md`, section 4.

## 4. Login and authorisation

You may use a lawful session the user already has open, within the scope of the task. Forbidden:

- guessing or brute-forcing a password;
- using someone else's cookies or tokens;
- creating a false identity to gain access;
- getting around an invitation requirement or a closed group;
- accepting legally binding terms on the user's behalf without explicit permission;
- extracting data beyond the family-history purpose.

## 5. CAPTCHA: acceptable behaviour

Check the page's actual response: do not hand an ordinary search to the user merely because this site has shown a CAPTCHA before.

1. When a CAPTCHA actually appears, make **one attempt** to pass it with the page's normal visible controls in the agent's built-in browser, if one is available and the tools and the site's rules allow it. No additional permission is needed for that attempt within authorised research. Note the attempt in the Survey note and check the result; if access is granted, continue the research in that session.
2. If the attempt fails, a repeat CAPTCHA appears, or no suitable method is available, hand this step to the user. Do not start a new cycle of attempts after reloading the page or switching tabs. Phone, ID-document, biometric and payment checks go straight to the user.
3. When the user's participation is needed, open or show them the exact blocked tab in the built-in browser, if the environment supports it. Keep the relevant page and query; do not open duplicate copies of the same tab. If there is no browser or no tab the user can reach, give the URL and state this limitation plainly; do not claim the tab is open.
4. Give the user the resume point once (section 8), record the route in the `Search Plan -` note as a step blocked on the user, and carry on with other sources and with analysing material without waiting for a reply. Once the user has passed the check, return to this step in the available lawful session.
5. Do not use external services or solver programs, token extraction or substitution, fingerprint/User-Agent spoofing, proxy rotation, someone else's session, or rate-limit evasion. One attempt through the normal interface does not authorise circumventing the verification mechanism or any other access restriction.

## 5a. Account login

Use a lawful session that is already available, within the task, without logging in again. If a source (e.g. FamilySearch) genuinely requires login, open or show the user the relevant login page, or the source's tab with its sign-in prompt, in the agent's built-in browser if the environment supports it. For different blocked sources, show the corresponding tabs; reuse a relevant tab that is already open. If there is no browser or no tab the user can reach, give the exact URL and state the limitation, without claiming anything was opened.

Say once where and why a login is needed; **the user logs in themselves.** Do not enter passwords, create accounts or extract tokens for use outside the browser. While there is no reply, mark only this route as blocked on the user in the Search Plan and continue with other sources and with analysing material. After login, return to this step inside the session and within the task.

For an MCP server the user has already connected, the connector itself manages authorisation in the way it supports. That does not entitle the agent to extract, copy or pass on cookies and tokens; never put secrets into queries, vault notes or reports. For the FamilySearch MCP, check the environment and account per `familysearch-mcp.md`.

For FamilySearch, use targeted search through an available supported tool; view documents in a lawful session with access to the specific image. Permitted minimal fragments can be analysed locally with `scripts/familysearch.py browser-import` without handing over the session (`familysearch-indexes.md`). A successful login or an MCP response does not prove access to a specific frame or the absence of its index; record an ambiguous state as unresolved.

## 5b. Technical techniques

Techniques for deep-zoom viewers and transient failures are in `field-lessons.md`, section 7.

Next to buttons that send messages, pay or confirm, select a field by its current element or ref, if the tool supports it. When driving by coordinates after scrolling or lazy loading, refresh the snapshot and check the target and focus before typing: earlier coordinates may have shifted. The author of [#128](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/128) reported on 30.10.2026 that such a click opened a messaging window. If this happens by accident, check the available action history and the window's state, close it and tell the user what actually happened; do not assert that nothing was sent if you could not verify it. The agent never sends correspondence — it only drafts letters in the letters folder (`correspondence.md`).

When clicking, typing or selecting, go by the current page and an available target. If the target is hidden, disabled or covered, stop before acting. Take a hidden ancestor into account too, even if the element itself has a bounding box. If the tool returns `false` without stopping the next command, split the check and the action into separate steps. Continue through a normal available element — for example the visible associated label of a styled checkbox — if the source permits that action.

If you report a verified refusal before acting, state the observed state of the target and what confirms that the click or input did not happen. A missing element, a different page, or a successful click on a visible target leave the check of an unavailable target unconfirmed.

## 5c. Digitised files and viewing conditions

A note saying "digitised" (оцифровано) or ЭФП (электронный фонд пользования, "electronic reading-room fund") proves neither open nor paid remote access. For the specific file, check whether images exist, the viewing regime and the institution's current terms. Until access is obtained, keep the archival reference (шифр) and continue with open catalogues, permitted library copies and other sources.

If viewing requires registration or buying a subscription, prepare the list of files needed and leave the corresponding step to the user per sections 4–5a, as a step in the `Search Plan -` note. Use a lawful session that is already available within the task. For an archive request, check which kinds of service are supported (`source-strategy.md`, section 11); do not turn one archive's restriction into a general rule.

If paid access is time-limited, prepare the files and book sections needed before activation; check how the time is counted and how long the payment takes to be credited. Size the session to the task and to the terms already agreed, without a mandatory separate schedule.

## 6. Geographic restrictions

Do not use a VPN or proxy to circumvent a restriction. Look for:

- an official alternative domain;
- an open catalogue of the same archive;
- a library copy;
- an acceptable web archive;
- the possibility of an official request.

**Web archive.** For a previously published page or file you may look for a public snapshot by its known original address in the [Wayback Machine](https://help.archive.org/help/using-the-wayback-machine/). Check that the copy matches the page or document needed. Save the original URL, the snapshot address and its date (Survey note; on the Source, if one is created). In the conclusion give the date of the available version, and check current terms, coverage and archival references against the custodian's information. The usual access and privacy restrictions apply when choosing and saving a snapshot.

When there are signs of a routing problem, take into account a VPN or tunnel that is already running: the browser and a command-line tool may use different connections. Available local settings help check the route to a specific site; do not change them automatically and do not bring in an external geolocation service without need. An address shown by another site does not establish the route to the archive under split routing. Record the cause of a block as established only once confirmed; otherwise leave it unknown. A failure or timeout by itself does not prove a geographic restriction.

The author of [PR #79](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/79) reported that, for a user located in the country, the portals responded over a direct connection but timed out through the user's VPN; this is an observation, not an established rule about the portals. If access from the user's actual location is permitted, you may suggest how to restore an ordinary direct connection for the relevant site in their existing client. The method depends on the client; the user changes the settings. Such a step does not authorise faking a location or circumventing access terms; if the direct route is unavailable, continue with the alternatives above.

## 7. Rate limit and blocking

In a sequence of name queries to one source, assess the actual content of each response before sending the next. This includes an HTTP 200 carrying a verification or block stub. When you detect a barrier, leave the unsent queries in the Search Plan. If the tool cannot stop the next send inside a batch, send queries one at a time. Record the attempts made and the restrictions per section 8. What to do on a CAPTCHA is in section 5.

On `429`, a temporary block or a repeat CAPTCHA:

1. stop repeated requests;
2. record the failure and the resume point per section 8. Hand a repeat CAPTCHA to the user per section 5, without a new attempt by the agent;
3. once normal access is restored, resume targeted searching at a lower volume;
4. use an alternative official source;
5. do not spread requests across IPs or accounts.

The author of [#247](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/247) reported on 12–13.11.2026 that the ОГАЧО (State Archive of Chelyabinsk Oblast) viewer showed an error instead of the leaf, and on reopening a stub cached by the browser could be displayed. The look of the stub does not establish the current cause of the failure or confirm that access has been restored. Leave the frame unviewed and return to it in the normal way when conditions change, per section 8.

The author of [#160](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/160) reported on 03–04.11.2026 a FamilySearch index refusal with HTTP 403 and `errorCode 15` while the images were available. The author of [#236](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/236) reported on 09.11.2026 a failure loading images while the metadata were available. The causes were not established. Record the affected route per section 8, stop repeat requests to it, and continue with the available checks and with analysing what has already been obtained. Return to it directly once access is restored or conditions otherwise change.

In a user account, a restriction may affect access to the whole account. For DNA services see the terms of access in `evidence-protocol.md`, section "DNA".

A result that looks plausible in form but does not match the query does not by itself establish that a protection mechanism was triggered. The Geneteka/Arolsen observations and how to check such a result are in `search-result-validation.md`, section "What question the sample answers". On a confirmed access restriction follow the order above; do not record an unconfirmed cause as fact.

## 8. Failed access is not a negative result

An unavailable page, a CAPTCHA, a catalogue error or the lack of full-text search does not mean the record does not exist. Record in the `Survey -` note the exact query, time, symptom and actual access result, and in the `Search Plan -` note the address or archival reference, the frame/section needed, the next step and the grounds for a retry, if known. If material that matters can for now be checked only by the user, give them these details and the specific action required. When conditions change, re-check the outstanding item directly, keeping the history of failure and recovery; a single error in a past session does not prove permanent unavailability. No separate register, endless retries or circumvention of restrictions are needed.

The author of [#226](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/226) reported on 10–11.11.2026 that during a long search in a paid session of the ЕАИС (unified archival information system) of Kursk Oblast, other pages of that session also stopped responding. The cause was not established. On such a failure do not add queries of the same kind or test tabs. Save the unfinished query and the return point, and continue with the available checks. After recovery, if the archival reference is known, try a direct move via the card or a targeted search. If necessary, tell the user that access is expiring and what volume is unfinished.

In the Survey note and in the report to the user, distinguish:

- `not found in searched scope`;
- `source unavailable`;
- `search incomplete`;
- `record set not preserved/unknown`.

## 9. Working tabs

Reuse the relevant working tab instead of creating a duplicate. After a finished check or batch, close the tabs the agent created whose state is no longer needed: duplicates, sources already read, and error pages with no useful state. Before closing, save the task-relevant URLs, archival references/IDs, frames, results and resume position in the Survey or Search Plan note; obtaining evidentiary copies — per section 3.

- Keep the user's tabs, unsaved forms and live CAPTCHA/login pages. Do not close other people's or shared working tabs without agreement; if ownership is unknown, leave the tab open. Do not clear cookies/sessions or close the whole browser to free memory.
- Before the final answer, check the remaining tabs of this task against the tabs you know you opened during the work. After saving the needed links and results, close your own unneeded tabs and skip those already closed. On an early stop, do this if control is still available.
- Check the actual result of closing with an available tool. If a tab needing the user's action remains, or closing failed, say so briefly when handing over the result. If control has been lost, note that closing could not be confirmed. Do not repeat the clean-up without new grounds; do not promise reduced RAM use without measuring it.
