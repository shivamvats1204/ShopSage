import json
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener


class ServiceError(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_json(url, headers=None, body=None, method=None, timeout=35):
    request = Request(
        url,
        data=body,
        headers={'Accept': 'application/json', 'User-Agent': 'ShopSage/1.0', **(headers or {})},
        method=method,
    )
    try:
        with build_opener(NoRedirect).open(request, timeout=timeout) as response:
            raw = response.read(16_000_001)
            if len(raw) > 16_000_000:
                raise ServiceError('The service response is too large. Narrow the shop or warehouse scope.')
            return json.loads(raw)
    except HTTPError as error:
        # Do not return bodies, headers or URLs: these can contain credentials or ERP internals.
        hints = {
            401: 'Check the API credentials in .env.',
            403: 'Check API permissions and model access.',
            404: 'Check the ERPNext site and schema version.',
            429: 'Rate limit reached. Wait briefly and retry.',
            301: 'Use the final HTTPS site address.',
            302: 'Use the final site address; redirects are not followed.',
        }
        raise ServiceError(
            f'Service returned HTTP {error.code}. {hints.get(error.code, "Try again or check service availability.")}'
        ) from None
    except (URLError, TimeoutError, OSError):
        raise ServiceError(
            'Could not reach the service. Check its address, network and availability.'
        ) from None
    except (ValueError, UnicodeError):
        raise ServiceError('The service returned an unreadable response.') from None
