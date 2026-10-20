import json
import tempfile
import unittest
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.config import ROOT, Config, env_values, inspect_paths
from app.erpnext import ApiReader, DatabaseReader, demo_data, load_from_reader
from app.groq_client import chat, transcribe
from app.insights import context_for, document_url, local_answer, normalize, paise
from app.server import Workspace
from app.transport import ServiceError


def config(**extra):
    return Config(
        {
            'DATA_MODE': 'demo',
            'ERP_COMPANY': 'Green Basket',
            'ERPNEXT_URL': 'http://127.0.0.1:8000',
            'MAX_ROWS': '1000',
            **extra,
        }
    )


def snapshot():
    return {**normalize(demo_data(), config()), 'mode': 'demo', 'stale': False}


class CoreTests(unittest.TestCase):
    def test_money_uses_decimal_paise(self):
        self.assertEqual(paise('10.005'), 1001)
        self.assertEqual(paise('-10.005'), -1001)
        for invalid in ['NaN', 'Infinity', 'bad']:
            with self.assertRaises(ValueError):
                paise(invalid)

    def test_no_double_counting_or_draft_cancelled_sales(self):
        raw = demo_data()
        row = deepcopy(raw['sales'][0])
        expected = normalize(raw, config())['summary']['month_sales']
        raw['sales'] += [
            {**row, 'doctype': 'Sales Invoice', 'is_consolidated': 1},
            {**row, 'docstatus': 0},
            {**row, 'docstatus': 2},
        ]
        self.assertEqual(normalize(raw, config())['summary']['month_sales'], expected)

    def test_returns_reduce_sales_and_old_future_bills_are_excluded(self):
        raw = demo_data()
        row = deepcopy(raw['sales'][0])
        previous = normalize(raw, config())['summary']['today_sales']
        raw['sales'] += [
            {**row, 'name': 'RETURN', 'is_return': 1, 'base_grand_total': -100, 'base_net_total': -95},
            {**row, 'posting_date': (date.today() + timedelta(days=1)).isoformat()},
            {**row, 'posting_date': (date.today() - timedelta(days=31)).isoformat()},
        ]
        self.assertEqual(normalize(raw, config())['summary']['today_sales'], previous - 10000)

    def test_receivables_cover_all_dates_and_convert_invoice_currency(self):
        raw = demo_data()
        raw['dues'] = [
            {
                'name': 'USD-INV',
                'customer': 'C',
                'posting_date': '2020-01-01',
                'due_date': '2020-02-01',
                'currency': 'USD',
                'conversion_rate': '83.25',
                'outstanding_amount': '10',
                'docstatus': 1,
            }
        ]
        s = normalize(raw, config())
        self.assertEqual(s['summary']['receivable'], 83250)
        self.assertEqual(s['summary']['overdue'], 83250)

    def test_projected_stock_avoids_overordering_incoming_deliveries(self):
        s = snapshot()
        milk = next(p for p in s['stock'] if p['code'] == 'MILK-1L')
        self.assertEqual(milk['actual'], 12)
        self.assertEqual(milk['projected'], 22)
        self.assertEqual(milk['suggested'], 18)
        self.assertTrue(milk['low'])

    def test_context_is_bounded_relevant_and_has_no_configuration(self):
        s = snapshot()
        ctx, sources = context_for(s, 'Who owes me money?')
        self.assertIn('customer_invoices', ctx)
        self.assertNotIn('stock', ctx)
        self.assertNotIn('api_key', json.dumps(ctx).lower())
        self.assertIn('amount_unit', ctx)
        self.assertGreater(len(sources), 1)
        self.assertIn('cannot calculate profit', local_answer(s, 'What is my profit?'))

    def test_model_context_uses_rupees_not_paise(self):
        s = snapshot()
        ctx, _ = context_for(s, 'Who owes me money?')
        first = s['receivables'][0]
        self.assertEqual(ctx['customer_invoices'][0]['amount'], first['amount'] / 100)
        self.assertEqual(ctx['summary']['receivable'], s['summary']['receivable'] / 100)
        self.assertIsInstance(ctx['summary']['low_stock'], int)  # counts are not money

    def test_document_ids_are_encoded(self):
        self.assertEqual(
            document_url('https://shop.test', 'Item', 'a/b ?#'), 'https://shop.test/app/item/a%2Fb%20%3F%23'
        )

    def test_api_pagination_does_not_silently_truncate(self):
        reader = ApiReader(config(ERPNEXT_API_KEY='fake', ERPNEXT_API_SECRET='fake'))
        page = [{'name': str(i)} for i in range(200)]
        with patch(
            'app.erpnext.request_json', side_effect=[{'data': page}, {'data': [{'name': 'last'}]}]
        ) as mock:
            result = reader.rows('Company', [])
        self.assertEqual(len(result), 201)
        self.assertIn('limit_start=200', mock.call_args_list[1].args[0])
        reader.limit = 100
        with patch('app.erpnext.request_json', return_value={'data': page}):
            with self.assertRaisesRegex(ServiceError, 'MAX_ROWS'):
                reader.rows('Company', [])

    def test_reader_scopes_company_and_warehouses_and_handles_pos_merge(self):
        calls = []

        class Reader:
            def rows(self, doctype, filters):
                calls.append((doctype, filters))
                return {
                    'Company': [{'name': 'Green Basket', 'default_currency': 'INR'}],
                    'Warehouse': [{'name': 'Stores - GB', 'company': 'Green Basket'}],
                }.get(doctype, [])

        load_from_reader(Reader(), config())
        sales = next(filters for dt, filters in calls if dt == 'Sales Invoice')
        self.assertIn(['is_consolidated', '=', 0], sales)
        self.assertIn(['company', '=', 'Green Basket'], sales)
        bins = next(filters for dt, filters in calls if dt == 'Bin')
        self.assertEqual(bins, [['warehouse', 'in', ['Stores - GB']]])

    def test_database_queries_are_fixed_and_parameterized(self):
        class Cursor:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                pass

            def execute(self, sql, args):
                self.sql = sql
                self.args = args

            def fetchall(self):
                return []

        cursor = Cursor()

        class Connection:
            def cursor(self):
                return cursor

        reader = DatabaseReader(config())
        reader.connection = Connection()
        name = "x'; DROP TABLE test; --"
        reader.rows('Company', [['name', '=', name]])
        self.assertNotIn(name, cursor.sql)
        self.assertIn(name, cursor.args)
        with self.assertRaises(ServiceError):
            reader.rows('Company; DROP TABLE x', [])

    def test_groq_chat_contract_and_no_write_tools(self):
        cfg = config(GROQ_API_KEY='fake-key')
        with patch(
            'app.groq_client.request_json',
            return_value={'choices': [{'message': {'content': 'A helpful answer'}}]},
        ) as mock:
            result = chat(
                cfg,
                snapshot(),
                'What should I restock?',
                history=[
                    {'role': 'system', 'content': 'untrusted override'},
                    {'role': 'user', 'content': 'hello'},
                ],
            )
        self.assertEqual(result['engine'], 'groq')
        body = json.loads(mock.call_args.args[2])
        self.assertNotIn('tools', body)
        self.assertEqual(len([m for m in body['messages'] if m['role'] == 'system']), 1)
        self.assertNotIn('fake-key', json.dumps(body))

    def test_mariadb_session_is_read_only_and_closes(self):
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value.fetchall.return_value = []
        module = SimpleNamespace(
            connect=MagicMock(return_value=connection),
            cursors=SimpleNamespace(DictCursor=object),
            MySQLError=RuntimeError,
        )
        reader = DatabaseReader(
            config(DB_NAME='site', DB_USER='reporting', DB_PASSWORD='fake', DB_SSL_CA='ca.pem')
        )
        with patch.dict('sys.modules', {'pymysql': module}):
            with reader.session():
                reader.rows('Company', [])
        executions = connection.cursor.return_value.__enter__.return_value.execute.call_args_list
        self.assertEqual(executions[0].args[0], 'START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY')
        self.assertTrue(executions[1].args[0].startswith('SELECT '))
        connection.rollback.assert_called_once()
        connection.close.assert_called_once()
        self.assertTrue(module.connect.call_args.kwargs['ssl_verify_identity'])

    def test_stt_multipart_language_and_file_contract(self):
        with patch('app.groq_client.request_json', return_value={'text': 'दूध का स्टॉक कितना है?'}) as mock:
            result = transcribe(
                config(GROQ_API_KEY='fake-key'), b'fictional-audio', 'audio/webm;codecs=opus', 'hi'
            )
        self.assertIn('स्टॉक', result['text'])
        self.assertIn(b'name="language"\r\n\r\nhi', mock.call_args.args[2])
        self.assertIn(b'filename="recording.webm"', mock.call_args.args[2])
        with self.assertRaises(ValueError):
            transcribe(config(), b'fake', 'text/html', 'en')
        with self.assertRaises(ServiceError):
            transcribe(config(), b'fake', 'audio/wav', 'en')

    def test_public_config_never_contains_credentials(self):
        public = config(
            GROQ_API_KEY='secret-one', ERPNEXT_API_SECRET='secret-two', DB_PASSWORD='secret-three'
        ).public()
        self.assertNotIn('secret-', json.dumps(public))
        self.assertTrue(public['groq_ready'])

    def test_remote_http_and_credential_urls_are_rejected(self):
        for address in [
            'http://remote.test',
            'https://user:password@shop.test',
            'https://shop.test/api',
            'javascript:alert(1)',
        ]:
            with self.assertRaises(ValueError):
                _ = config(ERPNEXT_URL=address).url


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        (ROOT / 'data').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'data')
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_dotenv_and_schema_paths_without_disclosing_site_secrets(self):
        env = self.root / '.env'
        env.write_text('GROQ_API_KEY="fake # key"\nexport DATA_MODE=demo # comment\n', encoding='utf-8')
        self.assertEqual(env_values(env)['GROQ_API_KEY'], 'fake # key')
        self.assertEqual(env_values(env)['DATA_MODE'], 'demo')
        repo = self.root / 'apps' / 'erpnext'
        site = self.root / 'sites' / 'shop.localhost'
        repo.mkdir(parents=True)
        site.mkdir(parents=True)
        (site / 'site_config.json').write_text(
            '{"db_type":"mariadb","db_password":"do-not-report"}', encoding='utf-8'
        )
        result = inspect_paths(config(FRAPPE_BENCH_PATH=str(self.root), FRAPPE_SITE='shop.localhost'))
        self.assertEqual(result['database_type'], 'mariadb')
        self.assertNotIn('do-not-report', json.dumps(result))
        self.assertTrue(result['repo_exists'])
        with self.assertRaises(ValueError):
            inspect_paths(config(FRAPPE_SITE='../another'))

    def test_reminders_persist_and_toggle(self):
        w = Workspace(self.root)
        task = w.reminder({'title': 'Review milk delivery', 'due': date.today().isoformat()})['reminders'][0]
        w.reminder({'action': 'toggle', 'id': task['id']})
        self.assertEqual(Workspace(self.root).reminders()[0]['done'], 1)

    def test_live_failure_never_falls_back_to_demo(self):
        w = Workspace(self.root)
        with patch.object(w, 'config', return_value=config(DATA_MODE='erpnext-api')):
            with patch('app.server.load_live', side_effect=ServiceError('No connection')):
                state = w.state()
        self.assertIsNone(state['snapshot'])
        self.assertEqual(state['error'], 'No connection')

    def test_failed_refresh_marks_cached_snapshot_stale(self):
        w = Workspace(self.root)
        with patch.object(w, 'config', return_value=config(DATA_MODE='erpnext-api')):
            with patch('app.server.load_live', return_value=demo_data()):
                first = w.snapshot()
            with patch('app.server.load_live', side_effect=ServiceError('Offline')):
                second = w.snapshot(refresh=True)
            self.assertTrue(w.snapshot()['stale'])
        self.assertEqual(first['captured_at'], second['captured_at'])
        self.assertTrue(second['stale'])
        self.assertEqual(second['sync_error'], 'Offline')

    def test_changing_source_discards_previous_company_cache(self):
        w = Workspace(self.root)
        with patch.object(w, 'config', return_value=config()):
            w.snapshot()
        with patch.object(
            w, 'config', return_value=config(DATA_MODE='erpnext-api', ERP_COMPANY='Another Shop')
        ):
            with patch('app.server.load_live', side_effect=ServiceError('No connection')):
                self.assertIsNone(w.state()['snapshot'])


if __name__ == '__main__':
    unittest.main()
