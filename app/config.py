import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def env_values(path):
    """Small dotenv reader: literal values, optional quotes, no execution/interpolation."""
    values = {}
    if path.exists():
        for raw in path.read_text(encoding='utf-8-sig').splitlines():
            line = raw.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.removeprefix('export ').split('=', 1)
            key, value = key.strip(), value.strip()
            if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', key):
                continue
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            else:
                value = value.split(' #', 1)[0].rstrip()
            values[key] = value
    return values


@dataclass
class Config:
    values: dict = field(repr=False)

    @classmethod
    def load(cls, path=None):
        values = env_values(path or ROOT / '.env')
        values.update(os.environ)
        return cls(values)

    def get(self, key, default=''):
        return self.values.get(key, default).strip()

    def number(self, key, default, lo, hi):
        try:
            value = int(self.get(key, str(default)))
            if not lo <= value <= hi:
                raise ValueError()
            return value
        except ValueError:
            raise ValueError(f'{key} must be between {lo} and {hi}.') from None

    @property
    def mode(self):
        value = self.get('DATA_MODE', 'demo')
        if value not in ['demo', 'erpnext-api', 'erpnext-db']:
            raise ValueError('DATA_MODE must be demo, erpnext-api or erpnext-db.')
        return value

    @property
    def url(self):
        value = self.get('ERPNEXT_URL', 'http://127.0.0.1:8000').rstrip('/')
        p = urlparse(value)
        if not p.hostname or p.username or p.password or p.query or p.fragment or p.path not in ['', '/']:
            raise ValueError(
                'ERPNEXT_URL must be the site origin, without credentials, paths or query parameters.'
            )
        if p.scheme != 'https' and not (
            p.scheme == 'http' and p.hostname in ['localhost', '127.0.0.1', '::1']
        ):
            raise ValueError('Use HTTPS for a remote ERPNext site, or HTTP for localhost development.')
        return value

    @property
    def company(self):
        value = self.get('ERP_COMPANY')
        if not value:
            raise ValueError('Set ERP_COMPANY to the exact ERPNext Company name.')
        return value

    def public(self):
        return {
            'mode': self.mode,
            'shop': self.get('SHOP_NAME', 'Your shop'),
            'owner': self.get('OWNER_NAME', 'Shop owner'),
            'company': self.get('ERP_COMPANY'),
            'warehouse': self.get('ERP_WAREHOUSE'),
            'erp_url': self.url,
            'groq_ready': bool(self.get('GROQ_API_KEY')),
            'groq_model': self.get('GROQ_MODEL', 'llama-3.3-70b-versatile'),
            'stt_model': self.get('GROQ_STT_MODEL', 'whisper-large-v3-turbo'),
            'api_ready': bool(self.get('ERPNEXT_API_KEY') and self.get('ERPNEXT_API_SECRET')),
            'db_ready': bool(self.get('DB_NAME') and self.get('DB_USER') and self.get('DB_PASSWORD')),
        }


SCHEMA_PATHS = {
    'Company': 'erpnext/accounts/doctype/company/company.json',
    'Sales Invoice': 'erpnext/accounts/doctype/sales_invoice/sales_invoice.json',
    'POS Invoice': 'erpnext/accounts/doctype/pos_invoice/pos_invoice.json',
    'Purchase Invoice': 'erpnext/accounts/doctype/purchase_invoice/purchase_invoice.json',
    'Item': 'erpnext/stock/doctype/item/item.json',
    'Bin': 'erpnext/stock/doctype/bin/bin.json',
    'Warehouse': 'erpnext/stock/doctype/warehouse/warehouse.json',
}


def inspect_paths(config):
    bench_text = config.get('FRAPPE_BENCH_PATH')
    repo_text = config.get('ERPNEXT_REPO_PATH')
    bench = Path(bench_text).expanduser().resolve() if bench_text else None
    repo = (
        Path(repo_text).expanduser().resolve() if repo_text else bench / 'apps' / 'erpnext' if bench else None
    )
    site = config.get('FRAPPE_SITE')
    if site and (site in ['.', '..'] or '/' in site or '\\' in site):
        raise ValueError('FRAPPE_SITE must be a site directory name, not a path.')
    import json

    from .erpnext import FIELDS

    rows = []
    for dt, path in SCHEMA_PATHS.items():
        found = (repo / path).is_file() if repo else None
        missing = None
        if found:
            try:
                schema = json.loads((repo / path).read_text(encoding='utf-8'))
                fields = {f['fieldname'] for f in schema['fields']} | {'name', 'docstatus'}
                missing = sorted(set(FIELDS[dt]) - fields)
            except (OSError, ValueError, KeyError, TypeError):
                missing = ['Unreadable DocType definition']
        rows.append(
            {
                'doctype': dt,
                'table': 'tab' + dt,
                'relative_path': path,
                'found': found,
                'missing_fields': missing,
            }
        )
    site_config = bench / 'sites' / site / 'site_config.json' if bench and site else None
    db_type = None
    if site_config and site_config.is_file():
        try:
            # Only report engine metadata. Never expose or reuse the site's credentials.
            value = json.loads(site_config.read_text(encoding='utf-8'))
            db_type = value.get('db_type', 'mariadb')
        except (OSError, ValueError):
            db_type = 'unreadable'
    return {
        'bench_configured': bool(bench),
        'bench_exists': bench.is_dir() if bench else None,
        'repo_configured': bool(repo),
        'repo_exists': repo.is_dir() if repo else None,
        'site_config_exists': site_config.is_file() if site_config else None,
        'database_type': db_type,
        'schema': rows,
    }
