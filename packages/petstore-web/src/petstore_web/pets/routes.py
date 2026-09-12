from collections.abc import Coroutine
from html import escape
from typing import Any

import httpx2
from petstore_api.main import app as api_app
from petstore_cli.client import AsyncPetstoreClient
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.routing import Route

from petstore_web.templating import load_template

PET_LIST_TEMPLATE = load_template('pets/pet_list.html')
PET_ROW_TEMPLATE = load_template('pets/pet_row.html')
PET_DETAIL_TEMPLATE = load_template('pets/pet_detail.html')
PET_DETAIL_EDIT_TEMPLATE = load_template('pets/pet_detail_edit.html')

STATUSES = ['available', 'pending', 'sold']
NAV_ITEMS = [
    (None, 'All'),
    ('available', 'Available'),
    ('pending', 'Pending'),
    ('sold', 'Sold'),
]

pets_client = AsyncPetstoreClient(
    'http://api', transport=httpx2.ASGITransport(app=api_app)
)


async def _upstream(coro: Coroutine[Any, Any, dict]) -> dict:
    """Await a PetstoreClient call, translating a 404 from the API into one here
    instead of letting httpx2's HTTPStatusError bubble up as an unhandled 500."""
    try:
        return await coro
    except httpx2.HTTPStatusError as exc:
        raise HTTPException(exc.response.status_code, exc.response.text) from exc


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


def _status_options(current: str) -> str:
    return ''.join(
        f'<option value="{status}"{" selected" if status == current else ""}>{status}</option>'
        for status in STATUSES
    )


def _oob(html: str) -> str:
    """Mark a returned #pet-list fragment as an htmx out-of-band swap, so it can
    ride alongside a #pet-detail response instead of being the primary target."""
    return html.replace(
        '<ul id="pet-list">', '<ul id="pet-list" hx-swap-oob="true">', 1
    )


def _empty_detail_html(oob: bool = False) -> str:
    attrs = ' hx-swap-oob="true"' if oob else ''
    return f'<div id="pet-detail" class="detail detail-empty"{attrs}><p>Select a pet to view details.</p></div>'


def nav_html(active_status: str | None) -> str:
    buttons = []
    for status, label in NAV_ITEMS:
        query = f'?status={status}' if status else ''
        active = ' active' if status == active_status else ''
        buttons.append(
            f'<button class="nav-item{active}" hx-get="/pets{query}" '
            f'hx-target="#pet-list" hx-swap="outerHTML">{label}</button>'
        )
    return ''.join(buttons)


def _row_html(pet: dict, selected_id: int | None = None) -> str:
    row_class = (
        'selected' if selected_id is not None and pet['id'] == selected_id else ''
    )
    return PET_ROW_TEMPLATE.substitute(
        id=pet['id'],
        row_class=row_class,
        name=escape(pet['name']),
        category=escape(pet['category']) if pet['category'] else '—',
        tags=escape(', '.join(pet['tags'])) if pet['tags'] else '—',
        status=escape(pet['status']),
    )


def _detail_html(pet: dict) -> str:
    return PET_DETAIL_TEMPLATE.substitute(
        id=pet['id'],
        name=escape(pet['name']),
        category=escape(pet['category']) if pet['category'] else '—',
        tags=escape(', '.join(pet['tags'])) if pet['tags'] else '—',
        status=escape(pet['status']),
        created_at=escape(pet['created_at'][:10]),
    )


def _detail_edit_html(pet: dict) -> str:
    return PET_DETAIL_EDIT_TEMPLATE.substitute(
        id=pet['id'],
        name=escape(pet['name']),
        category=escape(pet['category'] or ''),
        tags=escape(', '.join(pet['tags'])),
        photo_urls=escape(', '.join(pet['photo_urls'])),
        status_options=_status_options(pet['status']),
    )


async def pet_list_html(
    status: str | None = None, search: str | None = None, selected_id: int | None = None
) -> str:
    pets = await pets_client.list_pets(status)
    if search:
        needle = search.strip().lower()
        pets = [pet for pet in pets if needle in pet['name'].lower()]
    items = ''.join(_row_html(pet, selected_id) for pet in pets)
    return PET_LIST_TEMPLATE.substitute(items=items)


async def pet_detail_html(selected_id: int | None) -> str:
    """Render the detail pane for the page's optional ?selected= pet — falls back
    to the empty state rather than 404ing the whole page on a stale/bad id."""
    if selected_id is None:
        return _empty_detail_html()
    try:
        pet = await pets_client.get_pet(selected_id)
    except httpx2.HTTPStatusError:
        return _empty_detail_html()
    return _detail_html(pet)


async def list_pets(request: Request) -> HTMLResponse:
    status = request.query_params.get('status')
    search = request.query_params.get('search')
    return HTMLResponse(await pet_list_html(status=status, search=search))


async def create_pet_page(request: Request) -> RedirectResponse:
    form = await request.form()
    pet = await pets_client.create_pet(
        name=str(form['name']),
        category=str(form.get('category') or '') or None,
        photo_urls=str(form.get('photo_urls') or '') or None,
        tags=str(form.get('tags') or '') or None,
        status=str(form.get('status') or 'available'),
    )
    return RedirectResponse(f'/?selected={pet["id"]}', status_code=303)


async def pet_detail(request: Request) -> HTMLResponse:
    pet = await _upstream(pets_client.get_pet(int(request.path_params['pet_id'])))
    return HTMLResponse(_detail_html(pet))


async def pet_detail_edit_form(request: Request) -> HTMLResponse:
    pet = await _upstream(pets_client.get_pet(int(request.path_params['pet_id'])))
    return HTMLResponse(_detail_edit_html(pet))


async def update_pet_detail(request: Request) -> HTMLResponse:
    pet_id = int(request.path_params['pet_id'])
    form = await request.form()
    pet = await _upstream(
        pets_client.update_pet(
            pet_id,
            name=str(form['name']),
            category=str(form.get('category') or '') or None,
            photo_urls=_split_csv(str(form.get('photo_urls') or '')),
            tags=_split_csv(str(form.get('tags') or '')),
            status=str(form.get('status') or 'available'),
        )
    )
    detail_html = _detail_html(pet)
    list_html = _oob(await pet_list_html(selected_id=pet_id))
    return HTMLResponse(detail_html + list_html)


async def delete_pet(request: Request) -> HTMLResponse:
    pet_id = int(request.path_params['pet_id'])
    await pets_client.delete_pet(pet_id)
    detail_html = _empty_detail_html()
    list_html = _oob(await pet_list_html())
    return HTMLResponse(detail_html + list_html)


routes = [
    Route('/pets', list_pets, methods=['GET']),
    Route('/pets/new', create_pet_page, methods=['POST']),
    Route('/pets/{pet_id:int}/detail', pet_detail, methods=['GET']),
    Route('/pets/{pet_id:int}/detail/edit', pet_detail_edit_form, methods=['GET']),
    Route('/pets/{pet_id:int}/detail/edit', update_pet_detail, methods=['PUT']),
    Route('/pets/{pet_id:int}', delete_pet, methods=['DELETE']),
]
