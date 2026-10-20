"""Exercise the REST adapter over real HTTP against a fake Frappe server (no ERPNext needed)."""

import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from test_core import config

from app.config import ROOT
from app.erpnext import demo_data, load_live
from app.insights import normalize
from app.server import Workspace
from app.transport import ServiceError

AUTH = 'token key123:secret456'


def make_handler(data, seen):
    class Fake(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urlparse(self.path)
            seen.append(self.headers.get('Authorization'))
            if self.headers.get('Authorization') != AUTH:
                return self.send(401, {})
            doctype = unquote(url.path.rsplit('/', 1)[1])
            q = parse_qs(url.query)
            rows = data.get(doctype, [])
            if doctype == 'Sales Invoice':
                # honour the consolidated filter and the outstanding filter like Frappe would
                filters = json.loads(q['filters'][0])
                if ['outstanding_amount', '>', 0] in filters:
                    rows = data['dues']
                else:
                    rows = [r for r in rows if r.get('doctype') == 'Sales Invoice']
            start, size = int(q['limit_start'][0]), int(q['limit_page_length'][0])
            self.send(200, {'data': rows[start : start + size]})

        def send(self, status, value):
            body = json.dumps(value).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    return Fake


class FrappeHttpTests(unittest.TestCase):
    def setUp(self):
        demo = demo_data()
        self.data = {
            'Company': [{'name': 'Green Basket', 'default_currency': 'INR'}],
            'Warehouse': demo['warehouses'],
            'Item': demo['items'],
            'Bin': demo['bins'],
            'POS Invoice': [r for r in demo['sales']],
            'Sales Invoice': [],
            'dues': demo['dues'],
            'Purchase Invoice': demo['supplier_dues'],
        }
        self.seen = []
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(self.data, self.seen))
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def cfg(self, **extra):
        return config(
            DATA_MODE='erpnext-api',
            ERPNEXT_URL=self.url,
            ERPNEXT_API_KEY='key123',
            ERPNEXT_API_SECRET='secret456',
            **extra,
        )

    def test_full_load_over_http_matches_demo_totals(self):
        raw = load_live(self.cfg())
        live = normalize(raw, self.cfg())['summary']
        expected = normalize(demo_data(), config())['summary']
        self.assertEqual(live['today_sales'], expected['today_sales'])
        self.assertEqual(live['receivable'], expected['receivable'])
        self.assertTrue(all(h == AUTH for h in self.seen))
        self.assertGreater(len(self.seen), 6)  # paginated: >200 POS rows needs several calls

    def test_bad_credentials_give_actionable_error_without_secrets(self):
        with self.assertRaises(ServiceError) as ctx:
            load_live(
                config(
                    DATA_MODE='erpnext-api',
                    ERPNEXT_URL=self.url,
                    ERPNEXT_API_KEY='bad',
                    ERPNEXT_API_SECRET='bad',
                )
            )
        self.assertIn('401', str(ctx.exception))
        self.assertNotIn('bad:bad', str(ctx.exception))

    def test_malformed_rows_become_service_error_not_crash(self):
        self.data['Item'] = [{'item_code': 'X', 'is_stock_item': 1, 'disabled': 0}]  # missing item_name etc.
        self.data['Bin'] = [
            {
                'item_code': 'X',
                'warehouse': 'Stores - GB',
                'actual_qty': 1,
                'projected_qty': 1,
                'stock_value': 1,
            }
        ]
        tmp = tempfile.TemporaryDirectory(dir=ROOT / 'data')
        self.addCleanup(tmp.cleanup)
        w = Workspace(Path(tmp.name))
        from unittest.mock import patch

        with patch.object(w, 'config', return_value=self.cfg()):
            state = w.state()
        self.assertIsNone(state['snapshot'])
        self.assertIn('unexpected shape', state['error'])


if __name__ == '__main__':
    unittest.main()
