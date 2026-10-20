# ERPNext integration: data, database and source paths

ShopSage is a **separate companion process**. It neither becomes a Frappe app nor patches ERPNext source files. It uses native ERPNext documents through read-only adapters. The field contract is based on the **version-15** upstream definitions; newer/custom installations need schema validation.

## Recommended route: Frappe REST

Edit ShopSage's `.env`:

```dotenv
DATA_MODE=erpnext-api
ERPNEXT_URL=https://shop.example
ERP_COMPANY=Exact Company Name
ERPNEXT_API_KEY=dedicated_user_key
ERPNEXT_API_SECRET=dedicated_user_secret
ERP_WAREHOUSE=Stores - SHOP
```

Leave `ERP_WAREHOUSE` empty for all company warehouses readable by the reporting user. Use an origin-only site URL, without `/app`, `/api` or a site folder. Local HTTP is accepted only for localhost/loopback; remote endpoints need HTTPS. Redirects are not followed, to avoid forwarding authorization headers to another destination.

Create a dedicated Frappe user and read-only role using the ERPNext/Frappe administration screens. It needs read access to:

- Company and Warehouse
- Item and Bin
- Sales Invoice and POS Invoice
- Purchase Invoice

API responses honor the Frappe user's permissions. Restricted visibility can produce a legitimately partial *company* view; give the reporting user the intended scope, and compare against ERPNext reports before operational use. ShopSage cannot infer the existence of records the user is not allowed to read.

The adapter calls only `GET /api/resource/<DocType>` with explicit fields/filters. It follows `limit_start`/`limit_page_length` until complete. More than `MAX_ROWS` rows for a resource query fails with a clear error rather than producing silently truncated figures. Default cap is 10,000, configurable up to 50,000. Limit company/warehouse scope for large installations.

Reads of separate REST resources are not one atomic ERP transaction. Changes during pagination can affect consistency. Use ERPNext reports for formal reconciliation.

## Optional route: direct MariaDB

Install the optional pinned driver in the Python environment that runs ShopSage:

```powershell
python -m pip install -r requirements-db.txt
```

Configure a **separate SELECT-only database user**, not Administrator/root and not the Frappe application's write account:

```dotenv
DATA_MODE=erpnext-db
ERP_COMPANY=Exact Company Name
ERPNEXT_URL=https://shop.example
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=your_site_database
DB_USER=shopsage_reporting
DB_PASSWORD=your_reporting_account_password
DB_SSL_CA=
```

For a remote connection, configure `DB_SSL_CA` with the database server's trusted CA certificate. The driver then verifies the certificate and server identity. Prefer loopback/SSH tunneling or a secured private deployment; do not expose a database port as a side effect of using this app.

An administrator can grant **SELECT only** on the seven tables listed below. Use the actual database identifier and account host in your deployment. Do not grant write/admin/file privileges. A single site may contain multiple companies: the app's parameterized company filters are not a database access-control boundary. A raw site reporting account can read whatever its SQL grants allow. Prefer a dedicated site/database or an appropriately restricted reporting arrangement when company isolation is required.

Each refresh uses a read-only consistent-snapshot transaction. Queries are built only from hardcoded DocTypes/field/operator allowlists and bound values. No assistant/model text becomes SQL. The transaction rolls back and closes after reading; no ERP table is created or modified.

## Native schema and repository mapping

The table prefix is Frappe's native `tab`, with spaces preserved. Monetary fields in ERPNext are decimal currency amounts; ShopSage converts them to integer paise in memory. It does not migrate them to SQLite or create a replacement billing schema.

Paths below are relative to the ERPNext **repository root**, normally `<bench>/apps/erpnext/`:

| DocType / MariaDB table | Fields used | Source path |
| --- | --- | --- |
| Company / `tabCompany` | `name`, `default_currency` | `erpnext/accounts/doctype/company/company.json` |
| Warehouse / `tabWarehouse` | `name`, `company` | `erpnext/stock/doctype/warehouse/warehouse.json` |
| Item / `tabItem` | `item_code`, `item_name`, `item_group`, `stock_uom`, `safety_stock`, `min_order_qty`, `disabled`, `is_stock_item` | `erpnext/stock/doctype/item/item.json` |
| Bin / `tabBin` | `item_code`, `warehouse`, `actual_qty`, `projected_qty`, `stock_value`, `stock_uom` | `erpnext/stock/doctype/bin/bin.json` |
| Sales Invoice / `tabSales Invoice` | `posting_date`, `due_date`, `customer`, `customer_name`, `base_grand_total`, `base_net_total`, `outstanding_amount`, `currency`, `conversion_rate`, `is_consolidated`, `is_return`, `docstatus` | `erpnext/accounts/doctype/sales_invoice/sales_invoice.json` |
| POS Invoice / `tabPOS Invoice` | `posting_date`, `customer`, `customer_name`, `base_grand_total`, `base_net_total`, `currency`, `consolidated_invoice`, `is_return`, `docstatus` | `erpnext/accounts/doctype/pos_invoice/pos_invoice.json` |
| Purchase Invoice / `tabPurchase Invoice` | `posting_date`, `due_date`, `supplier`, `supplier_name`, `outstanding_amount`, `currency`, `conversion_rate`, `docstatus` | `erpnext/accounts/doctype/purchase_invoice/purchase_invoice.json` |

`name` is the document ID throughout. The adapter also uses `company` as a filter on invoices. `name` and `docstatus` are Frappe standard fields and need not appear inside a DocType's JSON `fields` array.

### POS consolidation

ERPNext can combine POS Invoices into a consolidated Sales Invoice. Reading both without a policy would count the same sale twice. ShopSage uses:

1. Submitted Sales Invoices with `is_consolidated = 0` in the 30-day date window.
2. All submitted original POS Invoices in that window, including those already consolidated.

This preserves the original POS posting dates. Negative return documents reduce turnover. Receivables are a *separate query* on all submitted Sales Invoices with a positive outstanding amount, including consolidated invoices. Outstanding unmerged POS credit is not represented until it becomes a posted invoice receivable.

### Stock and safety thresholds

Bins are restricted to warehouses belonging to `ERP_COMPANY`, optionally narrowed to one `ERP_WAREHOUSE`. Quantities sum per item across those bins. Only enabled stock items with at least one Bin in that scope appear. Stock values come from `Bin.stock_value`.

Item `safety_stock` is a global per-item threshold, not a warehouse reorder rule. The review suggestion is:

```text
suggestion = max(0, 2 × safety_stock − summed_projected_quantity)
if suggestion > 0: suggestion = max(suggestion, item_minimum_order_quantity)
```

Use ERPNext to review actual warehouse reorder levels, purchase UOM conversions, supplier packs, lead times and pending receipts. The assistant does not claim to reproduce ERPNext's automatic material-request logic.

## Bench/site paths

For optional local discovery:

```dotenv
FRAPPE_BENCH_PATH=/home/frappe/frappe-bench
FRAPPE_SITE=shop.localhost
ERPNEXT_REPO_PATH=
```

With no explicit repo path, the inspector checks `<bench>/apps/erpnext`. You may instead configure `ERPNEXT_REPO_PATH` to a separate ERPNext checkout without a bench. It checks the DocType files above, reports missing required fields, and never changes the repository.

A typical existing installation has:

```text
frappe-bench/
  apps/
    frappe/
    erpnext/
      erpnext/accounts/doctype/...
      erpnext/stock/doctype/...
    india_compliance/          # if installed separately
  sites/
    common_site_config.json
    shop.localhost/
      site_config.json
```

The inspector reads only database-engine metadata from the selected `site_config.json` and does not expose or copy its `db_password`. Configure reporting credentials explicitly in ShopSage's `.env`. Site names cannot traverse directories.

Paths must be accessible to the Python process running ShopSage. On Windows, a Linux path inside WSL is not automatically a Windows path. Run ShopSage inside the same WSL distribution, or use an accessible Windows/WSL network path. REST mode needs no local checkout and is the simplest way to connect a hosted/WSL ERPNext site from Windows.

## First connection checklist

1. Check ERPNext's exact Company name and INR base currency.
2. Configure a reporting user/token (recommended) or SELECT-only SQL account.
3. Set the corresponding `DATA_MODE`; keep the Groq key separate.
4. Run `python doctor.py` for redacted readiness and optional schema-path checks.
5. Use **Connection & voice → Reload connection**.
6. Compare a day of invoices, a known customer invoice and a known stock Bin against ERPNext.
7. Check the snapshot timestamp and scope labels before using any suggested action.

ShopSage implements the adapters and configuration, but live acceptance needs your actual ERPNext endpoint/credentials and Groq key. Model/STT responses in automated tests are mocks, not evidence of a live provider connection.

## Upstream references

- [Frappe API](https://docs.frappe.io/framework/user/en/api/rest)
- [Frappe bench structure](https://docs.frappe.io/framework/user/en/basics/directory-structure)
- [Sales Invoice v15 source](https://github.com/frappe/erpnext/blob/version-15/erpnext/accounts/doctype/sales_invoice/sales_invoice.json)
- [POS Invoice v15 source](https://github.com/frappe/erpnext/blob/version-15/erpnext/accounts/doctype/pos_invoice/pos_invoice.json)
- [Item v15 source](https://github.com/frappe/erpnext/blob/version-15/erpnext/stock/doctype/item/item.json)
- [Bin v15 source](https://github.com/frappe/erpnext/blob/version-15/erpnext/stock/doctype/bin/bin.json)
- [POS merge logic](https://github.com/frappe/erpnext/blob/version-15/erpnext/accounts/doctype/pos_invoice_merge_log/pos_invoice_merge_log.py)
