from pathlib import Path

from petstore_api.logging import RequestLoggingMiddleware
from petstore_api.main import app as api_app
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from petstore_web.pets.routes import nav_html, pet_detail_html, pet_list_html
from petstore_web.pets.routes import routes as pet_web_routes
from petstore_web.templating import load_template

STATIC_DIR = Path(__file__).resolve().parent / 'static'

BASE_TEMPLATE = load_template('base.html')
INDEX_TEMPLATE = load_template('index.html')
PET_FORM_PAGE_TEMPLATE = load_template('pets/pet_form_page.html')


async def index(request: Request) -> HTMLResponse:
    status = request.query_params.get('status')
    selected = request.query_params.get('selected')
    selected_id = int(selected) if selected else None

    content = INDEX_TEMPLATE.substitute(
        nav=nav_html(status),
        pet_list=await pet_list_html(status=status, selected_id=selected_id),
        pet_detail=await pet_detail_html(selected_id),
    )
    return HTMLResponse(BASE_TEMPLATE.substitute(title='Petstore', content=content))


async def add_pet_page(request: Request) -> HTMLResponse:
    content = PET_FORM_PAGE_TEMPLATE.substitute()
    return HTMLResponse(BASE_TEMPLATE.substitute(title='Add Pet', content=content))


app = Starlette(
    routes=[
        Route('/', index, methods=['GET']),
        Route('/pets/new', add_pet_page, methods=['GET']),
        *pet_web_routes,
        Mount('/static', app=StaticFiles(directory=STATIC_DIR)),
        # ponytail: api_app carries its own RequestLoggingMiddleware (needed when it
        # runs standalone), so requests through this mount get logged/x-request-id'd
        # twice. Fix by splitting api_app into an unwrapped router + a separately
        # middleware-wrapped app if that double log line ever becomes a problem.
        Mount('/api', app=api_app),
    ],
    middleware=[Middleware(RequestLoggingMiddleware)],
)
