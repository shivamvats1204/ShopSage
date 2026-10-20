import csv
import io
import json
import sqlite3
import threading
import time
import uuid
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .config import ROOT, Config, inspect_paths
from .erpnext import demo_data, load_live
from .groq_client import chat, transcribe
from .insights import context_for, local_answer, normalize
from .transport import ServiceError


class Workspace:
    def __init__(self, root=ROOT):
        self.root = root
        self.lock = threading.Lock()
        self.cached = None
        self.cache_key = None
        self.cached_time = 0
        self.last_error = None
        self.db_path = root / 'data' / 'assistant.db'
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.db_path)
        try:
            with db:
                db.execute(
                    'CREATE TABLE IF NOT EXISTS reminders(id TEXT PRIMARY KEY,title TEXT NOT NULL,due TEXT NOT NULL,done INTEGER DEFAULT 0)'
                )
        finally:
            db.close()

    def config(self):
        return Config.load(self.root / '.env')

    def snapshot(self, refresh=False):
        config = self.config()
        fingerprint = tuple(
            config.get(k)
            for k in [
                'DATA_MODE',
                'ERP_COMPANY',
                'ERP_WAREHOUSE',
                'ERPNEXT_URL',
                'ERPNEXT_API_KEY',
                'ERPNEXT_API_SECRET',
                'DB_HOST',
                'DB_PORT',
                'DB_NAME',
                'DB_USER',
                'DB_PASSWORD',
                'DB_SSL_CA',
                'MAX_ROWS',
            ]
        )
        with self.lock:
            if fingerprint != self.cache_key:
                self.cached = None
                self.last_error = None
                self.cache_key = fingerprint
            ttl = config.number('CACHE_SECONDS', 60, 5, 3600)
            if self.cached is not None and not refresh and time.monotonic() - self.cached_time < ttl:
                return {
                    **self.cached,
                    'stale': bool(self.last_error),
                    **({'sync_error': self.last_error} if self.last_error else {}),
                }
            try:
                raw = demo_data() if config.mode == 'demo' else load_live(config)
                try:
                    snapshot = normalize(raw, config)
                except (KeyError, TypeError, AttributeError):
                    raise ServiceError(
                        'ERPNext returned records in an unexpected shape. Check that the ERPNext version and custom fields match the integration guide.'
                    ) from None
                snapshot.update(mode=config.mode, stale=False)
                self.cached = snapshot
                self.last_error = None
                self.cached_time = time.monotonic()
                return snapshot
            except (ServiceError, ValueError) as error:
                self.last_error = str(error)
                if self.cached:
                    return {**self.cached, 'stale': True, 'sync_error': str(error)}
                raise

    def reminders(self):
        db = sqlite3.connect(self.db_path)
        db.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in db.execute('SELECT * FROM reminders ORDER BY done,due,title')]
        finally:
            db.close()

    def reminder(self, data):
        db = sqlite3.connect(self.db_path)
        try:
            with db:
                if data.get('action') == 'toggle':
                    if not db.execute(
                        'UPDATE reminders SET done=1-done WHERE id=?', (data.get('id'),)
                    ).rowcount:
                        raise ValueError('Reminder not found.')
                else:
                    title = str(data.get('title', '')).strip()
                    if not 1 <= len(title) <= 200:
                        raise ValueError('Give your reminder a short title (up to 200 characters).')
                    due = date.fromisoformat(str(data.get('due', '')))
                    db.execute(
                        'INSERT INTO reminders VALUES(?,?,?,0)', (uuid.uuid4().hex, title, due.isoformat())
                    )
        finally:
            db.close()
        return {'reminders': self.reminders()}

    def state(self, refresh=False):
        config = self.config()
        try:
            snapshot = self.snapshot(refresh)
            error = None
        except (ServiceError, ValueError) as e:
            snapshot = None
            error = str(e)
        return {
            'config': config.public(),
            'snapshot': snapshot,
            'error': error,
            'reminders': self.reminders(),
        }


class Handler(BaseHTTPRequestHandler):
    def response(self, status, value, mime='application/json; charset=utf-8', filename=None):
        body = (
            json.dumps(value, ensure_ascii=False, default=str).encode()
            if mime.startswith('application/json')
            else value
        )
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Permissions-Policy', 'microphone=(self), camera=()')
        self.send_header(
            'Content-Security-Policy',
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; media-src 'self' blob:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
        )
        if filename:
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(body)

    def check_host(self):
        if self.headers.get('Host') not in [
            f'127.0.0.1:{self.server.server_port}',
            f'localhost:{self.server.server_port}',
        ]:
            self.response(403, {'error': 'Open ShopSage using its local address.'})
            return False
        return True

    def do_GET(self):
        if not self.check_host():
            return
        path = self.path.split('?')[0]
        try:
            if path == '/api/state':
                return self.response(200, self.server.workspace.state())
            if path == '/api/connection':
                config = self.server.workspace.config()
                return self.response(200, {'config': config.public(), 'paths': inspect_paths(config)})
            if path == '/api/export/stock':
                snapshot = self.server.workspace.snapshot()
                stream = io.StringIO(newline='')
                writer = csv.writer(stream)
                writer.writerow(
                    [
                        'Item code',
                        'Item',
                        'Unit',
                        'Actual quantity',
                        'Projected quantity',
                        'Safety stock',
                        'Suggested top-up',
                        'Source captured at',
                        'Stale',
                    ]
                )

                def safe(v):
                    return "'" + v if isinstance(v, str) and v[:1] in ['=', '+', '-', '@', '\t', '\r'] else v

                for p in snapshot['stock']:
                    writer.writerow(
                        [
                            safe(p[k])
                            for k in ['code', 'name', 'unit', 'actual', 'projected', 'safety', 'suggested']
                        ]
                        + [snapshot['captured_at'], snapshot.get('stale', False)]
                    )
                return self.response(
                    200,
                    stream.getvalue().encode('utf-8-sig'),
                    'text/csv; charset=utf-8',
                    'shopsage-stock.csv',
                )
            files = {
                '/': ('index.html', 'text/html; charset=utf-8'),
                '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                '/base.css': ('base.css', 'text/css; charset=utf-8'),
                '/style.css': ('style.css', 'text/css; charset=utf-8'),
                '/favicon.svg': ('favicon.svg', 'image/svg+xml'),
            }
            if path not in files:
                return self.response(404, {'error': 'Not found.'})
            filename, mime = files[path]
            return self.response(200, (ROOT / 'web' / filename).read_bytes(), mime)
        except (ServiceError, ValueError) as e:
            self.response(400, {'error': str(e)})
        except Exception:
            self.response(
                500,
                {'error': 'ShopSage could not load this resource. Check your configuration and try again.'},
            )

    def do_POST(self):
        if not self.check_host():
            return
        if self.headers.get('Origin') and self.headers['Origin'] != 'http://' + self.headers.get('Host', ''):
            return self.response(403, {'error': 'Use the ShopSage workspace for this request.'})
        path = self.path.split('?')[0]
        try:
            length = int(self.headers.get('Content-Length', '0'))
            limit = 12_000_000 if path == '/api/transcribe' else 65_536
            if not 0 < length <= limit:
                raise ValueError('Request is empty or too large.')
            raw = self.rfile.read(length)
            config = self.server.workspace.config()
            if path == '/api/transcribe':
                return self.response(
                    200,
                    transcribe(
                        config,
                        raw,
                        self.headers.get('Content-Type', ''),
                        self.headers.get('X-Language', 'auto'),
                    ),
                )
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                return self.response(415, {'error': 'Expected a JSON request.'})
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError('Expected a JSON object.')
            if path == '/api/refresh':
                return self.response(200, self.server.workspace.state(refresh=True))
            if path == '/api/reminder':
                return self.response(200, self.server.workspace.reminder(data))
            if path == '/api/chat':
                question = data.get('question')
                if not isinstance(question, str) or not 1 <= len(question.strip()) <= 2000:
                    raise ValueError('Enter a question of up to 2,000 characters.')
                history = data.get('history', [])
                if not isinstance(history, list):
                    raise ValueError('Conversation history must be a list.')
                snapshot = self.server.workspace.snapshot()
                if config.get('GROQ_API_KEY'):
                    answer = chat(config, snapshot, question, history, data.get('language', 'en-IN'))
                else:
                    _, sources = context_for(snapshot, question)
                    answer = {
                        'text': local_answer(snapshot, question),
                        'engine': 'local',
                        'sources': sources,
                        'model': None,
                    }
                answer.update(
                    captured_at=snapshot['captured_at'],
                    stale=snapshot.get('stale', False),
                    mode=snapshot['mode'],
                )
                return self.response(200, answer)
            self.response(404, {'error': 'Unknown action.'})
        except (ValueError, TypeError) as e:
            self.response(400, {'error': str(e) or 'Check the entered values.'})
        except ServiceError as e:
            self.response(503, {'error': str(e)})
        except Exception:
            self.response(
                500,
                {'error': 'This request could not finish. Try again. Your ERPNext records were not changed.'},
            )

    def log_message(self, fmt, *args):
        # No query strings, request bodies, conversation text or credentials in logs.
        pass


def run(port=8890):
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.workspace = Workspace()
    print(f'ShopSage is ready: http://127.0.0.1:{port}', flush=True)
    print('Independent ERPNext enhancer. Keep this terminal open. Ctrl+C stops the app.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
