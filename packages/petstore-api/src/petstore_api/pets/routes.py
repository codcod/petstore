from collections.abc import Sequence

import msgspec
from sqlalchemy import RowMapping, insert, select, update
from sqlalchemy import delete as sa_delete
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from petstore_api.db import engine
from petstore_api.pets.models import pets
from petstore_api.pets.schemas import PetCreate, PetOut, PetUpdate


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


async def _fetch_pet(pet_id: int) -> RowMapping:
    async with engine.connect() as conn:
        result = await conn.execute(select(pets).where(pets.c.id == pet_id))
        row = result.mappings().first()
    if row is None:
        raise HTTPException(404, f'pet {pet_id} not found')
    return row


async def _fetch_pets(status: str | None = None) -> Sequence[RowMapping]:
    query = select(pets).order_by(pets.c.id)
    if status:
        query = query.where(pets.c.status == status)

    async with engine.connect() as conn:
        result = await conn.execute(query)
        return result.mappings().all()


async def _form_data(request: Request) -> PetCreate:
    form = await request.form()
    try:
        return msgspec.convert(dict(form), type=PetCreate)
    except msgspec.ValidationError as exc:
        raise HTTPException(400, str(exc)) from exc


def _pet_values(data: PetCreate) -> dict:
    return {
        'name': data.name,
        'category': data.category,
        'photo_urls': _split_csv(data.photo_urls),
        'tags': _split_csv(data.tags),
        'status': data.status,
    }


async def _update_pet(pet_id: int, values: dict) -> RowMapping:
    async with engine.begin() as conn:
        result = await conn.execute(
            update(pets).where(pets.c.id == pet_id).values(**values).returning(pets)
        )
        row = result.mappings().first()
    if row is None:
        raise HTTPException(404, f'pet {pet_id} not found')
    return row


def _row_to_out(row: RowMapping) -> PetOut:
    return PetOut(
        id=row['id'],
        name=row['name'],
        category=row['category'],
        photo_urls=list(row['photo_urls'] or []),
        tags=list(row['tags'] or []),
        status=row['status'],
        created_at=row['created_at'].isoformat(),
    )


async def list_pets(request: Request) -> JSONResponse:
    status = request.query_params.get('status')
    rows = await _fetch_pets(status)
    return JSONResponse([msgspec.to_builtins(_row_to_out(r)) for r in rows])


async def create_pet(request: Request) -> JSONResponse:
    data = await _form_data(request)
    async with engine.begin() as conn:
        result = await conn.execute(
            insert(pets).values(**_pet_values(data)).returning(pets)
        )
        row = result.mappings().one()
    return JSONResponse(msgspec.to_builtins(_row_to_out(row)), status_code=201)


async def get_pet(request: Request) -> JSONResponse:
    row = await _fetch_pet(int(request.path_params['pet_id']))
    return JSONResponse(msgspec.to_builtins(_row_to_out(row)))


async def update_pet(request: Request) -> JSONResponse:
    pet_id = int(request.path_params['pet_id'])
    try:
        data = msgspec.json.decode(await request.body(), type=PetUpdate)
    except msgspec.ValidationError as exc:
        raise HTTPException(400, str(exc)) from exc
    row = await _update_pet(
        pet_id,
        {
            'name': data.name,
            'category': data.category,
            'photo_urls': data.photo_urls,
            'tags': data.tags,
            'status': data.status,
        },
    )
    return JSONResponse(msgspec.to_builtins(_row_to_out(row)))


async def delete_pet(request: Request) -> JSONResponse:
    pet_id = int(request.path_params['pet_id'])
    async with engine.begin() as conn:
        await conn.execute(sa_delete(pets).where(pets.c.id == pet_id))
    return JSONResponse(None, status_code=204)


routes = [
    Route('/pets', list_pets, methods=['GET']),
    Route('/pets', create_pet, methods=['POST']),
    Route('/pets/{pet_id:int}', delete_pet, methods=['DELETE']),
    Route('/pets/{pet_id:int}', get_pet, methods=['GET']),
    Route('/pets/{pet_id:int}', update_pet, methods=['PUT']),
]
