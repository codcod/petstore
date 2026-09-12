import logging
import time
import uuid
from collections.abc import MutableMapping
from contextvars import ContextVar
from typing import Any

from starlette.types import ASGIApp, Receive, Scope, Send

request_id_var: ContextVar[str] = ContextVar('request_id', default='-')

logger = logging.getLogger('petstore')


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler()
    # On the handler, so every logger's records (ours and third-party, e.g.
    # httpx2's) get a request_id before hitting the shared formatter below.
    handler.addFilter(_RequestIdFilter())
    handler.setFormatter(
        logging.Formatter(
            '%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s'
        )
    )
    logging.basicConfig(level=level, handlers=[handler])
    # Also on our own logger, so it still runs when something (like
    # unittest's assertLogs) swaps in its own handler for a test.
    logger.addFilter(_RequestIdFilter())


class RequestLoggingMiddleware:
    """Tags every request with an id (reused from an incoming X-Request-ID header, or
    generated) so its log lines can be correlated, and logs method/path/status/duration."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get('headers') or [])
        request_id = headers.get(b'x-request-id', b'').decode() or uuid.uuid4().hex
        token = request_id_var.set(request_id)
        start = time.perf_counter()
        status_code = 500

        async def send_wrapper(message: MutableMapping[str, Any]) -> None:
            nonlocal status_code
            if message['type'] == 'http.response.start':
                status_code = message['status']
                message['headers'].append((b'x-request-id', request_id.encode()))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            logger.exception('%s %s failed', scope['method'], scope['path'])
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                '%s %s %d %.1fms',
                scope['method'],
                scope['path'],
                status_code,
                duration_ms,
            )
            request_id_var.reset(token)
