# Choosing the billing-system integration

Research checked on **20 October 2026** using upstream product documentation and repositories.

## Conclusion

**ERPNext is the selected open-source integration target.** No reliable, independent India-only usage ranking was established. Claims of worldwide customers, GitHub stars, or vendor-reported ecosystem size cannot establish which open-source billing product is most used by Indian shops.

| Candidate | Evidence relevant to this project | Decision |
| --- | --- | --- |
| ERPNext | Open-source source code, retail/POS, inventory and billing records, documented Frappe REST API, MariaDB deployment model, and an India Compliance ecosystem. | Selected: a practical foundation for a separate assistant with native stock/invoice adapters. |
| Odoo Community | Open-source business application suite with POS and invoicing; Odoo documents Indian localization modules. Feature availability must be checked by edition/module rather than assuming everything on the commercial product page is Community functionality. | Credible alternative, but an Odoo-specific adapter is not implemented here. |

ERPNext is a larger ERP, so adopting it is not equivalent to installing a small Windows invoice tool. ShopSage connects to an existing setup; it does not install ERPNext. Its purpose is to make daily interpretation and follow-up easier without rebuilding the accounting engine.

## Primary sources

- [ERPNext for India](https://frappe.io/erpnext/india): India positioning and compliance ecosystem.
- [ERPNext upstream repository](https://github.com/frappe/erpnext): open-source ERP and source structure.
- [ERPNext POS](https://docs.frappe.io/erpnext/point-of-sale): retail workflow.
- [India Compliance upstream](https://github.com/resilient-tech/india-compliance): separate integration/app ecosystem.
- [Frappe REST API](https://docs.frappe.io/framework/user/en/api/rest): token authentication, resource queries, filtering and pagination.
- [Frappe database administration](https://docs.frappe.io/framework-git/administration/database-administration): MariaDB is the default and most-tested deployment choice; other engines must not be assumed interchangeable.
- [Frappe directory structure](https://docs.frappe.io/framework/user/en/basics/directory-structure): bench/app/site layout.
- [Odoo Community](https://www.odoo.com/page/community) and [Indian localization](https://www.odoo.com/documentation/18.0/applications/finance/fiscal_localizations/india.html): alternative platform and localization scope.

## AI and voice choices

The owner explicitly selected **Groq**, the provider used by the original Sage project. The default chat model is configurable; the implementation uses `llama-3.3-70b-versatile`. Groq Whisper `whisper-large-v3-turbo` provides multilingual transcription. Playback uses the browser's device speech voices to avoid adding another required provider/key; installed Hindi voice availability varies.

- [Groq supported models](https://console.groq.com/docs/models)
- [Groq text generation](https://console.groq.com/docs/text-chat)
- [Groq speech-to-text](https://console.groq.com/docs/speech-to-text)
- [PyMySQL connection parameters](https://pymysql.readthedocs.io/en/latest/modules/connections.html)
- [MariaDB read-only transactions](https://mariadb.com/docs/server/reference/sql-statements/transactions/start-transaction)

Provider model availability and quotas can change; edit the configured model if necessary. The assistant never invents prices, regulations, internet research or supplier actions on behalf of the model.
