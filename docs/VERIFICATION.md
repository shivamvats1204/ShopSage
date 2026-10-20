# Verification — 20 October 2026

## Automated result

**30 tests passed** with `python -m unittest discover -s tests -v`.

Coverage includes:

- Decimal-to-paise conversion, negative returns and date filtering.
- Exclusion of draft/cancelled invoices and consolidated POS duplicate summaries.
- Company/warehouse scoping and fractional/projected stock calculations.
- All-date unpaid invoice selection and invoice-currency conversion to INR.
- Frappe API pagination and explicit row-limit failure instead of silent truncation.
- Fixed parameterized database queries and rejection of unsupported DocTypes.
- MariaDB read-only consistent-snapshot setup, TLS verification options, rollback and connection close using a mocked driver.
- Bounded, relevant Groq context without configuration or keys; no model write tools.
- Groq chat payload and multipart English/Hindi transcription contracts using mocked provider responses.
- Redacted public configuration and local bench/site inspection without exposing site passwords.
- Personal reminder persistence and completion.
- Live-source failure never reverting to demo; failed refresh marking cached records stale; company/source changes clearing the old cache.
- Local HTTP routes for state/config, static files, stock CSV, chat, transcription and reminders.
- REST adapter over real HTTP against a fake Frappe server (token auth header, pagination across many pages, HTTP 401 handling without leaking secrets, malformed rows reported as a clear error instead of a crash). This is a protocol-level check, not a real ERPNext.
- Rejection of foreign Host/Origin headers; `.env` returning HTTP 404.

`node --check web/app.js` and `python -m compileall -q app run.py doctor.py` passed. `python doctor.py` confirmed the delivered configuration is demo mode with no Groq/ERPNext/database credentials configured; it printed readiness metadata only.

## Browser checks

The standalone app was run at `http://127.0.0.1:8890` in the in-app browser.

- Daily view showed ₹2,790 invoiced today, ₹2,400 overdue, four low-stock items and ₹10,090 in unpaid supplier invoices from the fictional fixture.
- A stock question produced a clearly labelled **local summary** with record source details while no Groq key was configured.
- Searching “milk” showed 12 packs on hand, 22 projected, safety stock 20, and suggested top-up 18; warehouse detail matched.
- Restock planning produced a reviewable draft explicitly labelled as fictional and not a purchase order.
- Overdue invoice filter showed Priya Sharma ₹1,540 and Rajesh Kumar ₹860.
- Today’s bills filter showed six original POS documents totalling ₹2,790.
- A local sample reminder was created and marked complete; it persisted when revisiting the page.
- Read-aloud controls entered the speaking state and could be stopped. Device voice selection listed available Windows English voices. Stop/cancel handling suppresses expected cancellation errors.
- Microphone entry without a key showed the correct setup explanation rather than attempting transcription.
- Connection & voice displayed redacted configuration status, model names, language/voice controls and data-handling information.
- A 390 × 844 phone viewport showed stacked content, readable primary actions and a functioning navigation drawer that closed without changing the selected page.
- No JavaScript console errors were observed in the checked flows.

Screenshots: [desktop](desktop.jpg), [phone](mobile.jpg).

## Dependency and model checks

`PyMySQL==1.2.3` exists on PyPI. Groq lists `llama-3.3-70b-versatile` and `whisper-large-v3-turbo` as production models with no deprecation notice (checked 20 October 2026).

## Live ERPNext check (20 October 2026)

A real ERPNext v15 (Frappe `version-15`, MariaDB 10.11, WSL Ubuntu) was installed with a fictional INR company, 8 stock items, 9 submitted Sales Invoices (including a return and a paid invoice) and 2 Purchase Invoices. ShopSage connected through the REST adapter with a dedicated API user. Receivable, overdue, payable, today and 30-day sales totals matched direct SQL on the ERPNext database exactly. A real Groq chat completion answered from this data. This exposed a unit bug (the model misreading integer paise), fixed by sending rupee amounts in the model context, with a regression test.

Not covered by that check: POS Invoices (no POS profile was configured), the MariaDB direct adapter, India Compliance/GST customizations and large datasets.

## What is not verified live

**Whisper transcription, microphone recording upload and the MariaDB direct connection have not been exercised live.** The live ERPNext REST read and a live Groq chat completion are covered above. Provider/driver behavior was checked through contracts and mocks, while UI/domain flows used fictional sample data. Audible output quality and Hindi voice playback were not assessed; no Hindi voice was installed on the tested device.

An actual shop connection needs the owner's ERPNext endpoint/company and a reporting user/token or SELECT-only SQL account. Create `.env` from `.env.example` and add the owner's Groq key. Reconcile sample real records in ERPNext after connecting. The integration contract targets upstream version-15 fields, not a certification of every ERPNext version or customization.

The test server is stopped after verification. Start the application using `Start-ShopSage.cmd` or `python run.py` to use it. Browser test reminders remain only in the ignored local assistant database; automated tests use isolated disposable databases.
