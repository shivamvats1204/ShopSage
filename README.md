# ShopSage

**An independent, voice-enabled enhancer assistant for ERPNext shop owners.**

ShopSage makes bills, stock and unpaid invoices easier to understand. ERPNext keeps doing the billing and accounting; ShopSage adds a calm daily workspace, natural-language help, spoken questions, read-aloud replies, follow-up drafts and personal reminders.

It is a standalone project, with its own Git repository, `.env`, code and launcher. It does not import or depend on the earlier `Sage` project.

## Why ERPNext?

ERPNext is an open-source retail/accounting integration target with POS, inventory and an India Compliance ecosystem. Its upstream source and document model are available for integration. A reliable, independently verified ranking of open-source billing software usage specifically in India was not found, so this project does **not** claim ERPNext is India's most-used billing software.

The choice is based on suitability: open source, India support, native stock and invoice records, documented REST access and a MariaDB deployment model. [ERPNext for India](https://frappe.io/erpnext/india), [ERPNext repository](https://github.com/frappe/erpnext), [Frappe API](https://docs.frappe.io/framework/user/en/api/rest).

## Start in a minute

Requires **Python 3.10 or newer**. Default/demo, REST integration, Groq chat and Groq transcription use Python's standard library; no packages or Node installation are required to run.

1. Open this folder in a terminal, or double-click **Start-ShopSage.cmd** on Windows.
2. Run `python run.py` if using a terminal.
3. Open **http://127.0.0.1:8890**. Keep the terminal open; Ctrl+C stops the server.

Copy `.env.example` to `.env` (`copy .env.example .env` on Windows, `cp .env.example .env` elsewhere). The template starts with a clearly labelled **fictional sample shop** and contains no real key. Edit `.env` locally; it is ignored by Git. Never paste secrets into chat or commit them.

Add your Groq key:

```dotenv
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_STT_MODEL=whisper-large-v3-turbo
```

Environment variables override `.env`. The file is re-read on requests: after editing it, use **Connection & voice → Reload connection**. A key enables conversational AI and transcription; without it, the app explicitly offers local rule-based summaries instead. It does not pretend those summaries came from a model.

## Connect your billing software

Recommended: connect an existing ERPNext instance through its REST API:

```dotenv
DATA_MODE=erpnext-api
ERPNEXT_URL=https://your-erpnext-site.example
ERP_COMPANY=Exact Company Name
ERPNEXT_API_KEY=your_dedicated_users_api_key
ERPNEXT_API_SECRET=your_dedicated_users_api_secret
ERP_WAREHOUSE=
SHOP_NAME=Your shop
OWNER_NAME=Your name
```

The **Groq key and ERPNext credentials are separate**. Use a dedicated ERPNext reporting user, with only the necessary read permissions. A Groq key alone cannot connect to a shop's billing records. An empty `ERP_WAREHOUSE` reads all warehouses belonging to the configured company that the user can access; sales and dues always remain company-wide.

Use `http://127.0.0.1:8000` for a local Frappe development instance. Remote sites require HTTPS. The REST adapter follows Frappe's token authentication and pagination. It never calls write endpoints, arbitrary RPC methods or generated SQL. It fails on permissions/schema/row-limit problems instead of showing incomplete totals as complete or substituting demo data.

An optional **direct MariaDB reader** is included for operators who need database integration. It uses ERPNext's `tabSales Invoice`, `tabPOS Invoice`, `tabItem`, `tabBin`, `tabWarehouse`, `tabCompany` and `tabPurchase Invoice` tables, fixed queries, bound parameters and a read-only transaction. See the [integration guide](docs/ERPNEXT_INTEGRATION.md) for configuration, source paths and permission boundaries.

No ERPNext instance is bundled or installed by this project. Its source contracts were checked against the upstream **version-15** DocTypes; validate your installed schema before adopting another release. The REST adapter was verified against a real ERPNext v15 instance (see [verification notes](docs/VERIFICATION.md)); the direct MariaDB reader has only been tested with a mocked driver.

## A simpler shop routine

| Screen | What you can do |
| --- | --- |
| My shop today | See invoiced sales, overdue amounts, stock alerts, supplier dues and reminders. |
| Talk to Sage | Ask about shop records, plan a restock, understand invoices, or draft a friendly reminder. |
| Stock check | Search products, compare actual/projected/safety stock, inspect warehouses and export a review list. |
| Customer dues | Find unpaid submitted sales invoices and open the original document in ERPNext. |
| My bills | View 30 days of submitted Sales/POS Invoices, filter today/returns, and open ERPNext billing. |
| Supplier dues | Review open purchase invoices and their due dates. |
| My reminders | Keep personal dated to-dos, without changing ERPNext tasks. |
| Connection & voice | Check integration readiness, optional source paths, language and read-aloud preferences. |

Billing links open ERPNext in a separate tab. In demo mode, sample document links explain that you must connect your actual shop first. ShopSage does not issue invoices, receive payments, amend stock, place orders or send reminders to other people. Drafts can be copied or downloaded for your review.

## Talk and listen

- **Speech to text:** press the microphone, choose **Record my question**, stop the recording, and choose **Transcribe**. Groq Whisper converts English/Hindi audio to editable text. Review the transcript, then press Send. You can also choose an audio file if recording is unavailable.
- **Text to speech:** use **Read aloud** under an answer or enable automatic reading in Connection & voice. Uses the browser's speech-synthesis API and your device's available voices. Reading voice and conversation language are separately selectable.
- English (India) and Hindi are available as conversation/transcription language preferences. The main interface is currently English.
- Microphone recording needs a browser that supports `getUserMedia` and `MediaRecorder`, such as a current Chrome/Edge browser, on localhost or HTTPS. This local app serves loopback HTTP.
- Hindi read-aloud requires a Hindi voice installed on the device. ShopSage reports a missing Hindi voice rather than silently claiming support. The tested Windows device exposed English voices only.
- Recordings are limited to 60 seconds/12 MB and held in memory. File uploads are limited to 12 MB. Audio is sent to Groq only when Transcribe is pressed. The server does not save audio files.

## Data you can trust—and its limits

- **Invoiced sales:** submitted Sales Invoices **excluding consolidated POS summary invoices**, plus original submitted POS Invoices. Keeps the POS posting dates and avoids double counting merged sales. Negative returns reduce totals. Drafts/cancellations and dates outside the 30-day window are excluded.
- **Today before invoice taxes:** ERPNext `base_net_total`; this is **not profit**. Cost-of-goods and expense ledgers are not loaded.
- **Open invoice amounts:** positive `outstanding_amount` on submitted Sales/Purchase Invoices, across all dates, converted to INR with that invoice's conversion rate. They are an invoice follow-up view, **not a full receivables/payables ledger**. Unallocated advances, net credit positions and unconsolidated POS credit are not incorporated.
- **Stock:** enabled stock items with a `Bin` in the selected company warehouses. Items without a Bin in that scope are not listed. Quantities support fractional stock units.
- **Restock suggestion:** top up to twice `Item.safety_stock`, using summed `Bin.projected_qty` and the item's minimum order quantity. These are review suggestions, **not ERPNext warehouse reorder rules**, forecasts or automatically submitted orders.
- **Money:** normalized as integer paise using decimal half-up rounding. Company base currency must be INR; invoice outstanding amounts may be in other currencies and are converted using stored rates.
- **Refresh:** snapshots cache for 60 seconds by default. A failed refresh labels the last successful snapshot stale. Changing company/source discards the previous cache. API reads are not a transactionally consistent ERP snapshot; use ERPNext's reports for reconciliation.
- **Dates:** follow the computer running Python. Set its clock/timezone correctly; overdue means due date is earlier than today.

## Privacy and storage

The API key is read server-side; the UI sees readiness booleans, not the key. `.env` is ignored by Git, cannot be served by the static-file route, and is never embedded in the Groq prompt. Errors do not echo provider response bodies, credentials or SQL parameters.

When AI is enabled, your question, limited recent chat and selected shop context are sent to Groq. The assistant has no action tools or database access of its own; it receives a bounded snapshot prepared by the server. Names in relevant customer/supplier invoice selections can be included. Review [Groq's data documentation](https://console.groq.com/docs/your-data) for provider handling. Some installed TTS voices may use the voice provider's online service.

ShopSage keeps only personal reminders in `data/assistant.db`. ERP data stays in ERPNext; the snapshot cache stays in process memory. Chat is browser memory only and clears on refresh. Voice preferences use local browser storage. To back up reminders, stop ShopSage and copy the assistant database. No import UI is provided.

The server binds to `127.0.0.1` and has no multi-user login or internet deployment configuration. It rejects foreign Origin/Host requests. Use it as a single-computer companion, not as a public web server. Direct database mode bypasses Frappe row permissions; prefer the REST adapter unless you have a properly scoped reporting account.

## Project layout

```text
ShopSage/
  .env.example              Shareable configuration template
  .env                      Your ignored local settings and key (create from .env.example)
  run.py / Start-ShopSage.cmd
  doctor.py                 Safe local readiness report
  requirements-db.txt       Optional MariaDB driver only
  requirements-dev.txt      Formatter and linter (development only)
  pyproject.toml            black / ruff settings
  .github/workflows/ci.yml  Lint, format check and tests on every push
  app/
    config.py               Environment loader and bench/site path inspection
    erpnext.py              Read-only REST and MariaDB adapters, demo fixture
    insights.py             Native-record normalization and grounded context
    groq_client.py          Groq chat + multipart Whisper transcription
    transport.py            Bounded outbound JSON requests; no redirects
    server.py               Local HTTP API, snapshot cache and reminders
  web/                      Self-contained responsive UI, recording and TTS
  tests/                    Domain, adapter and local HTTP contract tests
  docs/                     Integration notes, research and verification
  data/                     Ignored assistant reminders database
```

## Check it

```powershell
python doctor.py
python -m unittest discover -s tests -v
python -m compileall -q app run.py doctor.py
node --check web/app.js
```

Optional, for contributors: `pip install -r requirements-dev.txt`, then `ruff check .` and `black --check .`. Frontend files are formatted with Prettier (`.prettierrc.json`).

Node is optional and used only for the syntax check. HTTP tests start a temporary loopback server; Groq responses are mocked and no real key or external billing system is used. Test data is isolated under the ignored data directory. See [verification notes](docs/VERIFICATION.md) for what was tested and what still needs live credentials.

Read the [research decision](docs/RESEARCH.md) and [ERPNext integration guide](docs/ERPNEXT_INTEGRATION.md) before connecting a production shop.

## License

[MIT](LICENSE). ERPNext and Frappe are trademarks of their respective owners; ShopSage is an independent project and is not affiliated with or endorsed by them.
