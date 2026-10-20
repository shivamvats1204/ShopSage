from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from urllib.parse import quote


def number(value):
    try:
        result = Decimal(str(value or 0))
        if not result.is_finite():
            raise ValueError()
        return result
    except (InvalidOperation, ValueError):
        raise ValueError('ERPNext contains an invalid numeric value.') from None


def paise(value):
    return int((number(value) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def invoice_due(row):
    rate = number(row.get('conversion_rate', 1))
    if rate <= 0:
        raise ValueError(
            'An invoice has no usable conversion rate. Check ERPNext before using INR dues totals.'
        )
    return paise(number(row.get('outstanding_amount')) * rate)


def document_url(base, doctype, name):
    routes = {
        'Sales Invoice': 'sales-invoice',
        'POS Invoice': 'pos-invoice',
        'Purchase Invoice': 'purchase-invoice',
        'Item': 'item',
        'Customer': 'customer',
        'Supplier': 'supplier',
    }
    return base + '/app/' + routes[doctype] + '/' + quote(str(name), safe='')


def normalize(raw, config, today=None):
    today = today or date.today()
    since = today - timedelta(days=29)
    base = config.url
    sales = []
    for row in raw['sales']:
        stamp = str(row['posting_date'])[:10]
        if row.get('docstatus') != 1 or not since.isoformat() <= stamp <= today.isoformat():
            continue
        if row['doctype'] == 'Sales Invoice' and row.get('is_consolidated'):
            continue
        sales.append(
            {
                'name': row['name'],
                'date': stamp,
                'customer': row.get('customer_name') or row.get('customer'),
                'total': paise(row['base_grand_total']),
                'net': paise(row['base_net_total']),
                'doctype': row['doctype'],
                'is_return': bool(row.get('is_return')),
                'url': document_url(base, row['doctype'], row['name']),
            }
        )
    sales.sort(key=lambda s: (s['date'], s['name']), reverse=True)

    def dues(rows, party, doctype):
        output = []
        for row in rows:
            if row.get('docstatus') != 1 or number(row.get('outstanding_amount')) <= 0:
                continue
            due_date = str(row.get('due_date') or row['posting_date'])[:10]
            output.append(
                {
                    'name': row['name'],
                    'party': row.get(party + '_name') or row.get(party),
                    'party_id': row.get(party),
                    'date': str(row['posting_date'])[:10],
                    'due_date': due_date,
                    'amount': invoice_due(row),
                    'overdue': due_date < today.isoformat(),
                    'days_overdue': max(0, (today - date.fromisoformat(due_date)).days),
                    'url': document_url(base, doctype, row['name']),
                    'doctype': doctype,
                }
            )
        return sorted(output, key=lambda x: (not x['overdue'], x['due_date']))

    receivables = dues(raw['dues'], 'customer', 'Sales Invoice')
    payables = dues(raw['supplier_dues'], 'supplier', 'Purchase Invoice')
    bins = {}
    for row in raw['bins']:
        bins.setdefault(row['item_code'], []).append(row)
    stock = []
    for item in raw['items']:
        code = item['item_code']
        if code not in bins or item.get('disabled') or not item.get('is_stock_item'):
            continue
        locations = bins[code]
        actual = sum((number(b['actual_qty']) for b in locations), Decimal(0))
        projected = sum((number(b['projected_qty']) for b in locations), Decimal(0))
        safety = number(item['safety_stock'])
        suggestion = max(Decimal(0), safety * 2 - projected)
        if suggestion > 0:
            suggestion = max(suggestion, number(item.get('min_order_qty')))
        stock.append(
            {
                'code': code,
                'name': item['item_name'],
                'category': item['item_group'],
                'unit': item['stock_uom'],
                'actual': float(actual),
                'projected': float(projected),
                'safety': float(safety),
                'low': actual <= safety,
                'suggested': float(suggestion),
                'value': sum(paise(b['stock_value']) for b in locations),
                'warehouses': [
                    {
                        'name': b['warehouse'],
                        'actual': float(number(b['actual_qty'])),
                        'projected': float(number(b['projected_qty'])),
                    }
                    for b in locations
                ],
                'url': document_url(base, 'Item', code),
            }
        )
    stock.sort(key=lambda p: (not p['low'], p['actual'], p['name']))
    daily = []
    for i in range(29, -1, -1):
        stamp = (today - timedelta(days=i)).isoformat()
        daily.append({'date': stamp, 'total': sum(s['total'] for s in sales if s['date'] == stamp)})
    current = [s for s in sales if s['date'] == today.isoformat()]
    return {
        'company': raw['company'],
        'currency': 'INR',
        'today': today.isoformat(),
        'captured_at': datetime.now().astimezone().isoformat(timespec='seconds'),
        'sales': sales,
        'receivables': receivables,
        'payables': payables,
        'stock': stock,
        'daily': daily,
        'warehouses': [w['name'] for w in raw['warehouses']],
        'summary': {
            'today_sales': sum(s['total'] for s in current),
            'today_net': sum(s['net'] for s in current),
            'today_documents': len(current),
            'month_sales': sum(s['total'] for s in sales),
            'receivable': sum(r['amount'] for r in receivables),
            'overdue': sum(r['amount'] for r in receivables if r['overdue']),
            'payable': sum(r['amount'] for r in payables),
            'low_stock': sum(p['low'] for p in stock),
            'stock_value': sum(p['value'] for p in stock),
        },
    }


MONEY_KEYS = {
    'today_sales',
    'today_net',
    'month_sales',
    'receivable',
    'overdue',
    'payable',
    'stock_value',
    'amount',
    'total',
    'net',
}


def to_rupees(value):
    """Models misread integer paise, so the prompt carries rupee amounts (2 dp) instead."""
    if isinstance(value, dict):
        return {
            k: (
                round(v / 100, 2)
                if k in MONEY_KEYS and isinstance(v, int) and not isinstance(v, bool)
                else to_rupees(v)
            )
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [to_rupees(v) for v in value]
    return value


def context_for(snapshot, question):
    """Only send a bounded selection to Groq; never config, credentials or filesystem paths."""
    q = question.lower()
    result = {
        'date': snapshot['today'],
        'currency': 'INR',
        'amount_unit': 'all money values are in Indian rupees (INR), already converted; do not divide or multiply them',
        'summary': snapshot['summary'],
        'source_mode': snapshot['mode'],
        'captured_at': snapshot['captured_at'],
        'stale': snapshot.get('stale', False),
        'daily_sales': snapshot['daily'][-7:],
    }
    sources = ['Sales Invoice + POS Invoice (30-day window, consolidated Sales Invoices excluded)']
    if any(
        w in q
        for w in ['stock', 'item', 'product', 'reorder', 'restock', 'milk', 'shelf', 'maal', 'स्टॉक', 'सामान']
    ):
        result['stock'] = [
            {k: p[k] for k in ['code', 'name', 'unit', 'actual', 'projected', 'safety', 'suggested']}
            for p in snapshot['stock']
            if p['low']
        ][:40]
        sources += ['Item.safety_stock + Bin.actual_qty / projected_qty (selected warehouses)']
    if any(
        w in q for w in ['customer', 'owe', 'credit', 'collect', 'receivable', 'reminder', 'उधार', 'पैसे']
    ) or ('due' in q and not any(w in q for w in ['supplier', 'vendor', 'purchase', 'payable'])):
        result['customer_invoices'] = [
            {k: r[k] for k in ['name', 'party', 'amount', 'due_date', 'overdue']}
            for r in snapshot['receivables'][:40]
        ]
        sources += ['Sales Invoice.outstanding_amount × conversion_rate (all dates, submitted documents)']
    if any(w in q for w in ['supplier', 'purchase', 'payable', 'vendor', 'सप्लायर']):
        result['supplier_invoices'] = [
            {k: r[k] for k in ['name', 'party', 'amount', 'due_date', 'overdue']}
            for r in snapshot['payables'][:40]
        ]
        sources += ['Purchase Invoice.outstanding_amount × conversion_rate (all dates, submitted documents)']
    if any(w in q for w in ['bill', 'invoice', 'sale', 'बिल', 'बिक्री']):
        result['recent_invoices'] = [
            {k: r[k] for k in ['name', 'date', 'total', 'net', 'doctype', 'is_return']}
            for r in snapshot['sales'][:20]
        ]
    result['selection_notice'] = (
        'Lists are bounded selections; summary totals include all fetched rows. Stock scope is selected warehouses; sales and invoice dues are company-wide. Outstanding invoices are not a full accounts-receivable ledger. Stock suggestions use projected quantity and item safety stock, not ERPNext warehouse reorder rules.'
    )
    return to_rupees(result), sources


def local_answer(snapshot, question):
    def fmt(x):
        return f'₹{x/100:,.2f}'

    q = question.lower()
    s = snapshot['summary']
    if 'reminder' in q or 'draft' in q:
        return 'Draft for your review:\nHello [customer name], this is a friendly reminder about invoice [invoice number], with ₹[outstanding amount] still open. When convenient, please let us know when you expect to settle it. If you have already paid, please share the payment details so we can check our records. Thank you!\n\nReplace the placeholders with verified invoice details. This message has not been sent.'
    if any(w in q for w in ['stock', 'restock', 'reorder', 'स्टॉक']):
        low = [p for p in snapshot['stock'] if p['low']]
        return (
            f"{len(low)} items are at or below safety stock.\n"
            + '\n'.join(
                f"• {p['name']}: {p['actual']:g} {p['unit']} on hand; {p['projected']:g} projected. Suggested top-up: {p['suggested']:g}."
                for p in low[:10]
            )
            + '\nSuggestions account for projected quantity. Check deliveries and supplier pack sizes in ERPNext.'
        )
    if any(w in q for w in ['customer', 'owe', 'credit', 'collect', 'उधार']):
        return (
            f"Unpaid submitted sales invoices total {fmt(s['receivable'])}; {fmt(s['overdue'])} is overdue.\n"
            + '\n'.join(
                f"• {r['party']}: {fmt(r['amount'])} on {r['name']}; due {r['due_date']}."
                for r in snapshot['receivables'][:10]
            )
            + '\nCheck and record receipts in ERPNext. Unconsolidated POS credit and unallocated advances are not represented by this invoice list.'
        )
    if any(w in q for w in ['supplier', 'payable', 'purchase']):
        return f"Unpaid submitted purchase invoices total {fmt(s['payable'])}.\n" + '\n'.join(
            f"• {r['party']}: {fmt(r['amount'])}; due {r['due_date']}." for r in snapshot['payables'][:10]
        )
    if any(w in q for w in ['profit', 'margin']):
        return 'I cannot calculate profit from this snapshot: cost-of-goods and expense ledgers are not loaded. Net sales exclude invoice taxes; they are not profit. Open ERPNext’s accounting reports for the full picture.'
    return f"Today’s invoiced sales are {fmt(s['today_sales'])} across {s['today_documents']} submitted documents, including returns. Net sales before invoice taxes: {fmt(s['today_net'])}.\n{s['low_stock']} items need a stock check, and {fmt(s['overdue'])} of posted sales-invoice dues is overdue.\nThese are invoice figures, not cash collected."
