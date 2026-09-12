from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from petstore_api.logging import RequestLoggingMiddleware, configure_logging
from petstore_api.pets.routes import routes as pet_routes

configure_logging()


async def health(request: Request) -> JSONResponse:
    return JSONResponse({'status': 'ok'})


app = Starlette(
    routes=[
        Route('/health', health, methods=['GET']),
        *pet_routes,
    ],
    middleware=[Middleware(RequestLoggingMiddleware)],
)
