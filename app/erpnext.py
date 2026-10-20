"""Read-only ERPNext v15 contracts. No generated SQL, mutations or imported Frappe code."""

import json
from contextlib import contextmanager
from datetime import date, timedelta
from urllib.parse import quote, urlencode

from .transport import ServiceError, request_json

FIELDS = {
    'Company': ['name', 'default_currency'],
    'Warehouse': ['name', 'company'],
    'Item': [
        'name',
        'item_code',
        'item_name',
        'item_group',
        'stock_uom',
        'safety_stock',
        'min_order_qty',
        'disabled',
        'is_stock_item',
    ],
    'Bin': ['name', 'item_code', 'warehouse', 'actual_qty', 'projected_qty', 'stock_value', 'stock_uom'],
    'Sales Invoice': [
        'name',
        'posting_date',
        'due_date',
        'customer',
        'customer_name',
        'base_grand_total',
        'base_net_total',
        'outstanding_amount',
        'currency',
        'conversion_rate',
        'docstatus',
        'is_consolidated',
        'is_return',
    ],
    'POS Invoice': [
        'name',
        'posting_date',
        'customer',
        'customer_name',
        'base_grand_total',
        'base_net_total',
        'currency',
        'docstatus',
        'consolidated_invoice',
        'is_return',
    ],
    'Purchase Invoice': [
        'name',
        'posting_date',
        'due_date',
        'supplier',
        'supplier_name',
        'outstanding_amount',
        'currency',
        'conversion_rate',
        'docstatus',
    ],
}


class ApiReader:
    def __init__(self, config):
        self.config = config
        key, secret = config.get('ERPNEXT_API_KEY'), config.get('ERPNEXT_API_SECRET')
        if not key or not secret:
            raise ServiceError('Add ERPNEXT_API_KEY and ERPNEXT_API_SECRET to .env, then reconnect.')
        self.headers = {'Authorization': f'token {key}:{secret}'}
        self.limit = config.number('MAX_ROWS', 10000, 100, 50000)

    def rows(self, doctype, filters):
        output = []
        page_size = 200
        while True:
            params = {
                'fields': json.dumps(FIELDS[doctype]),
                'filters': json.dumps(filters),
                'limit_start': len(output),
                'limit_page_length': page_size,
                'order_by': 'name asc',
            }
            data = request_json(
                self.config.url + '/api/resource/' + quote(doctype, safe='') + '?' + urlencode(params),
                self.headers,
            ).get('data')
            if not isinstance(data, list):
                raise ServiceError('ERPNext returned an unexpected resource response.')
            output.extend(data)
            if len(output) > self.limit:
                raise ServiceError(
                    'ERPNext result exceeds MAX_ROWS. Narrow the warehouse/company or increase MAX_ROWS; no partial totals are shown.'
                )
            if len(data) < page_size:
                return output


class DatabaseReader:
    def __init__(self, config):
        self.config = config
        self.limit = config.number('MAX_ROWS', 10000, 100, 50000)
        self.connection = None

    @contextmanager
    def session(self):
        try:
            import pymysql
        except ImportError:
            raise ServiceError(
                'MariaDB mode needs PyMySQL. Run: pip install -r requirements-db.txt'
            ) from None
        if not all(self.config.get(k) for k in ['DB_NAME', 'DB_USER', 'DB_PASSWORD']):
            raise ServiceError(
                'Set DB_NAME, DB_USER and DB_PASSWORD for a dedicated SELECT-only MariaDB user.'
            )
        kwargs = dict(
            host=self.config.get('DB_HOST', '127.0.0.1'),
            port=self.config.number('DB_PORT', 3306, 1, 65535),
            user=self.config.get('DB_USER'),
            password=self.config.get('DB_PASSWORD'),
            database=self.config.get('DB_NAME'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=8,
            read_timeout=20,
            write_timeout=20,
            autocommit=False,
        )
        if self.config.get('DB_SSL_CA'):
            kwargs.update(ssl_ca=self.config.get('DB_SSL_CA'), ssl_verify_cert=True, ssl_verify_identity=True)
        try:
            self.connection = pymysql.connect(**kwargs)
            with self.connection.cursor() as cursor:
                cursor.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY')
            yield self
        except pymysql.MySQLError:
            raise ServiceError(
                'MariaDB read failed. Check the SELECT-only account, connection, company and ERPNext v15 schema.'
            ) from None
        finally:
            if self.connection:
                self.connection.rollback()
                self.connection.close()
                self.connection = None

    def rows(self, doctype, filters):
        if doctype not in FIELDS or not self.connection:
            raise ServiceError('Unsupported database query.')
        fields = ', '.join(f'`{field}`' for field in FIELDS[doctype])
        clauses, args = [], []
        for field, operator, value in filters:
            if field not in FIELDS[doctype] + ['company'] or operator not in ['=', '>=', '>', 'in']:
                raise ServiceError('Unsupported database filter.')
            if operator == 'in':
                if not value:
                    return []
                clauses.append(f'`{field}` IN ({",".join(["%s"] * len(value))})')
                args.extend(value)
            else:
                clauses.append(f'`{field}` {operator} %s')
                args.append(value)
        sql = (
            f'SELECT {fields} FROM `tab{doctype}`'
            + (' WHERE ' + ' AND '.join(clauses) if clauses else '')
            + ' ORDER BY `name` LIMIT %s'
        )
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (*args, self.limit + 1))
            rows = cursor.fetchall()
        if len(rows) > self.limit:
            raise ServiceError('MariaDB result exceeds MAX_ROWS; no partial totals are shown.')
        return rows


def load_from_reader(reader, config):
    company = reader.rows('Company', [['name', '=', config.company]])
    if len(company) != 1:
        raise ServiceError('Company not found or not readable. Use the exact ERPNext Company name.')
    if company[0]['default_currency'] != 'INR':
        raise ServiceError('This version supports companies with INR as their base currency.')
    warehouses = reader.rows('Warehouse', [['company', '=', config.company]])
    if config.get('ERP_WAREHOUSE'):
        warehouses = [w for w in warehouses if w['name'] == config.get('ERP_WAREHOUSE')]
        if not warehouses:
            raise ServiceError('ERP_WAREHOUSE was not found within the configured company.')
    start = (date.today() - timedelta(days=29)).isoformat()
    common = [['docstatus', '=', 1], ['company', '=', config.company]]
    # Exclude merged Sales Invoices, retain original POS Invoices for correct posting dates.
    sales = reader.rows(
        'Sales Invoice', common + [['posting_date', '>=', start], ['is_consolidated', '=', 0]]
    )
    pos = reader.rows('POS Invoice', common + [['posting_date', '>=', start]])
    dues = reader.rows('Sales Invoice', common + [['outstanding_amount', '>', 0]])
    suppliers = reader.rows('Purchase Invoice', common + [['outstanding_amount', '>', 0]])
    items = reader.rows('Item', [['disabled', '=', 0], ['is_stock_item', '=', 1]])
    bins = reader.rows('Bin', [['warehouse', 'in', [w['name'] for w in warehouses]]]) if warehouses else []
    return {
        'company': config.company,
        'sales': [{**s, 'doctype': 'Sales Invoice'} for s in sales]
        + [{**s, 'doctype': 'POS Invoice'} for s in pos],
        'dues': dues,
        'supplier_dues': suppliers,
        'items': items,
        'bins': bins,
        'warehouses': warehouses,
    }


def load_live(config):
    if config.mode == 'erpnext-api':
        return load_from_reader(ApiReader(config), config)
    reader = DatabaseReader(config)
    with reader.session():
        return load_from_reader(reader, config)


def demo_data():
    today = date.today()
    name = 'Green Basket'
    items, bins, sales = [], [], []
    specs = [
        ('ATTA-5KG', 'Aashirvaad Atta · 5 kg', 'Groceries', 'Bag', 8, 12, 245),
        ('MILK-1L', 'Amul Taaza Milk · 1 L', 'Dairy', 'Pack', 12, 20, 49),
        ('OIL-1L', 'Fortune Sunflower Oil · 1 L', 'Groceries', 'Bottle', 24, 10, 128),
        ('RICE-1KG', 'India Gate Rice · 1 kg', 'Groceries', 'Bag', 42, 15, 102),
        ('SALT-1KG', 'Tata Salt · 1 kg', 'Groceries', 'Pack', 65, 20, 23),
        ('SURF-1KG', 'Surf Excel · 1 kg', 'Household', 'Pack', 6, 10, 115),
        ('BUTTER-100', 'Amul Butter · 100 g', 'Dairy', 'Pack', 0, 8, 52),
        ('TEA-250', 'Tata Tea Gold · 250 g', 'Beverages', 'Pack', 28, 10, 132),
    ]
    for code, title, group, unit, qty, safety, cost in specs:
        items.append(
            dict(
                name=code,
                item_code=code,
                item_name=title,
                item_group=group,
                stock_uom=unit,
                safety_stock=safety,
                min_order_qty=5,
                disabled=0,
                is_stock_item=1,
            )
        )
        bins.append(
            dict(
                name='BIN-' + code,
                item_code=code,
                warehouse='Stores - GB',
                actual_qty=qty,
                projected_qty=qty + (10 if code == 'MILK-1L' else 0),
                stock_value=qty * cost,
                stock_uom=unit,
            )
        )
    for day in range(30):
        for n in range(6 + day % 5):
            total = [342, 560, 845, 128, 275, 640, 98, 160, 425, 280][(n + day) % 10]
            sales.append(
                dict(
                    name=f'ACC-POS-{day:02}-{n:03}',
                    doctype='POS Invoice',
                    posting_date=(today - timedelta(days=day)).isoformat(),
                    customer='CUST-001' if n % 3 == 0 else 'Walk-in',
                    customer_name='Priya Sharma' if n % 3 == 0 else 'Walk-in customer',
                    base_grand_total=total,
                    base_net_total=round(total / 1.05, 2),
                    currency='INR',
                    docstatus=1,
                    consolidated_invoice='ACC-SINV-MERGED' if day else '',
                    is_return=0,
                )
            )

    def due(id, party, amount, days, kind='customer'):
        return dict(
            name=id,
            **{kind: party, kind + '_name': party},
            posting_date=(today - timedelta(days=days + 10)).isoformat(),
            due_date=(today - timedelta(days=days)).isoformat(),
            outstanding_amount=amount,
            currency='INR',
            conversion_rate=1,
            docstatus=1,
        )

    return dict(
        company=name,
        items=items,
        bins=bins,
        sales=sales,
        dues=[
            due('ACC-SINV-0001', 'Priya Sharma', 1540, 3),
            due('ACC-SINV-0002', 'Rajesh Kumar', 860, 1),
            due('ACC-SINV-0003', 'Anita Patel', 420, -4),
        ],
        supplier_dues=[
            due('ACC-PINV-0001', 'Fresh Farm Dairy', 3250, 2, 'supplier'),
            due('ACC-PINV-0002', 'City Wholesale', 6840, -3, 'supplier'),
        ],
        warehouses=[{'name': 'Stores - GB', 'company': name}],
    )
