import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from test_core import config

from app.config import ROOT
from app.server import Handler, Workspace


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / 'data').mkdir(exist_ok=True)
        cls.temp = tempfile.TemporaryDirectory(dir=ROOT / 'data')
        cls.workspace = Workspace(Path(cls.temp.name))
        cls.config_patch = patch.object(
            cls.workspace, 'config', return_value=config(GROQ_API_KEY='fake-test-key')
        )
        cls.config_patch.start()
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.server.workspace = cls.workspace
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.config_patch.stop()
        cls.temp.cleanup()

    def get(self, path):
        with urlopen(self.base + path, timeout=5) as response:
            return response.read(), response.headers

    def post(self, path, data, headers=None):
        req = Request(
            self.base + path,
            data=json.dumps(data).encode(),
            headers={'Content-Type': 'application/json', **(headers or {})},
        )
        with urlopen(req, timeout=5) as response:
            return json.load(response)

    def test_state_and_connection_redact_credentials(self):
        for path in ['/api/state', '/api/connection']:
            body, _ = self.get(path)
            self.assertNotIn(b'fake-test-key', body)
            self.assertIsInstance(json.loads(body), dict)

    def test_static_files_and_stock_export(self):
        for path in ['/', '/app.js', '/base.css', '/style.css', '/favicon.svg', '/api/export/stock']:
            body, headers = self.get(path)
            self.assertGreater(len(body), 0)
            self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        with self.assertRaises(HTTPError) as error:
            self.get('/.env')
        self.assertEqual(error.exception.code, 404)
        error.exception.close()

    def test_groq_chat_route_with_mock_provider(self):
        with patch(
            'app.groq_client.request_json',
            return_value={'choices': [{'message': {'content': 'Mock answer — no live model was called.'}}]},
        ):
            response = self.post('/api/chat', {'question': 'What should I restock?', 'history': []})
        self.assertEqual(response['engine'], 'groq')
        self.assertEqual(response['mode'], 'demo')
        self.assertIn('Mock answer', response['text'])

    def test_transcription_route_with_mock_provider(self):
        req = Request(
            self.base + '/api/transcribe',
            data=b'fictional-webm-bytes',
            headers={'Content-Type': 'audio/webm', 'X-Language': 'hi'},
        )
        with patch('app.groq_client.request_json', return_value={'text': 'दूध का स्टॉक कितना है?'}):
            with urlopen(req, timeout=5) as response:
                result = json.load(response)
        self.assertIn('स्टॉक', result['text'])

    def test_foreign_origin_and_host_rejected(self):
        for headers in [{'Origin': 'https://foreign.invalid'}, {'Host': 'foreign.invalid'}]:
            with self.assertRaises(HTTPError) as error:
                self.post('/api/refresh', {}, headers)
            self.assertEqual(error.exception.code, 403)
            error.exception.close()

    def test_reminder_round_trip(self):
        response = self.post('/api/reminder', {'title': 'HTTP test reminder', 'due': '2026-10-20'})
        task = response['reminders'][0]
        updated = self.post('/api/reminder', {'action': 'toggle', 'id': task['id']})
        self.assertEqual(updated['reminders'][0]['done'], 1)


if __name__ == '__main__':
    unittest.main()
