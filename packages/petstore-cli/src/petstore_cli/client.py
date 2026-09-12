from typing import Self

import httpx2

JSON_ACCEPT = {'Accept': 'application/json'}


class PetstoreClient:
    def __init__(
        self, base_url: str, transport: httpx2.BaseTransport | None = None
    ) -> None:
        self._client = httpx2.Client(
            base_url=base_url, headers=JSON_ACCEPT, transport=transport
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        self._client.close()

    def list_pets(self, status: str | None = None) -> list[dict]:
        params = {'status': status} if status else None
        response = self._client.get('/pets', params=params)
        response.raise_for_status()
        return response.json()

    def get_pet(self, pet_id: int) -> dict:
        response = self._client.get(f'/pets/{pet_id}')
        response.raise_for_status()
        return response.json()

    def create_pet(
        self,
        name: str,
        category: str | None = None,
        photo_urls: str | None = None,
        tags: str | None = None,
        status: str = 'available',
    ) -> dict:
        response = self._client.post(
            '/pets',
            data={
                'name': name,
                'category': category,
                'photo_urls': photo_urls,
                'tags': tags,
                'status': status,
            },
        )
        response.raise_for_status()
        return response.json()

    def update_pet(
        self,
        pet_id: int,
        name: str,
        category: str | None = None,
        photo_urls: list[str] | None = None,
        tags: list[str] | None = None,
        status: str = 'available',
    ) -> dict:
        response = self._client.put(
            f'/pets/{pet_id}',
            json={
                'name': name,
                'category': category,
                'photo_urls': photo_urls or [],
                'tags': tags or [],
                'status': status,
            },
        )
        response.raise_for_status()
        return response.json()

    def delete_pet(self, pet_id: int) -> None:
        response = self._client.delete(f'/pets/{pet_id}')
        response.raise_for_status()


class AsyncPetstoreClient:
    """Same API as PetstoreClient, for callers (like petstore_web) already
    running inside an event loop — an ASGITransport requires an async client."""

    def __init__(
        self, base_url: str, transport: httpx2.AsyncBaseTransport | None = None
    ) -> None:
        self._client = httpx2.AsyncClient(
            base_url=base_url, headers=JSON_ACCEPT, transport=transport
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self._client.aclose()

    async def list_pets(self, status: str | None = None) -> list[dict]:
        params = {'status': status} if status else None
        response = await self._client.get('/pets', params=params)
        response.raise_for_status()
        return response.json()

    async def get_pet(self, pet_id: int) -> dict:
        response = await self._client.get(f'/pets/{pet_id}')
        response.raise_for_status()
        return response.json()

    async def create_pet(
        self,
        name: str,
        category: str | None = None,
        photo_urls: str | None = None,
        tags: str | None = None,
        status: str = 'available',
    ) -> dict:
        response = await self._client.post(
            '/pets',
            data={
                'name': name,
                'category': category,
                'photo_urls': photo_urls,
                'tags': tags,
                'status': status,
            },
        )
        response.raise_for_status()
        return response.json()

    async def update_pet(
        self,
        pet_id: int,
        name: str,
        category: str | None = None,
        photo_urls: list[str] | None = None,
        tags: list[str] | None = None,
        status: str = 'available',
    ) -> dict:
        response = await self._client.put(
            f'/pets/{pet_id}',
            json={
                'name': name,
                'category': category,
                'photo_urls': photo_urls or [],
                'tags': tags or [],
                'status': status,
            },
        )
        response.raise_for_status()
        return response.json()

    async def delete_pet(self, pet_id: int) -> None:
        response = await self._client.delete(f'/pets/{pet_id}')
        response.raise_for_status()
