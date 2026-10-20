"""Report readiness without printing credentials or opening external services."""

import json

from app.config import Config, inspect_paths

if __name__ == '__main__':
    try:
        config = Config.load()
        public = config.public()
        checks = {
            'mode': public['mode'],
            'groq_key_configured': public['groq_ready'],
            'frappe_api_credentials_configured': public['api_ready'],
            'mariadb_credentials_configured': public['db_ready'],
            'paths': inspect_paths(config),
            'notes': [
                'No credentials are printed. This checks local configuration only; use Refresh in the app to test data access.',
                'A Groq key enables chat/STT; Frappe credentials or SELECT-only database credentials are separate.',
            ],
        }
        print(json.dumps(checks, indent=2))
    except ValueError as error:
        print(str(error))
        raise SystemExit(1) from None
