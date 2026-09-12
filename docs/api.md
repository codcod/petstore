# Petstore API

Starlette doesn't generate OpenAPI docs for free, so the JSON API is documented here by hand.

## `GET /health`

Liveness check.

```json
{"status": "ok"}
```

## `GET /pets`

Returns all pets, newest last. Accepts `?status=` to filter.

```json
[
  {
    "id": 1,
    "name": "doggie",
    "category": "Dogs",
    "photo_urls": ["https://example.com/doggie.jpg"],
    "tags": ["friendly", "puppy"],
    "status": "available",
    "created_at": "2026-01-01T00:00:00+00:00"
  }
]
```

## `POST /pets`

Body is form-encoded (`application/x-www-form-urlencoded`), not JSON — `photo_urls`/`tags`
are comma-separated strings:

```
name=doggie&category=Dogs&photo_urls=https://example.com/doggie.jpg&tags=friendly,puppy&status=available
```

`name` is required; everything else is optional (`status` defaults to `"available"`).
Returns the created pet (same shape as `GET /pets/{id}`) with `201`, or 400 on a malformed
payload.

## `GET /pets/{id}`

Returns a single pet.

```json
{
  "id": 1,
  "name": "doggie",
  "category": "Dogs",
  "photo_urls": ["https://example.com/doggie.jpg"],
  "tags": ["friendly", "puppy"],
  "status": "available",
  "created_at": "2026-01-01T00:00:00+00:00"
}
```

404 if the id doesn't exist.

## `PUT /pets/{id}`

Body (JSON):

```json
{
  "name": "doggie",
  "category": "Dogs",
  "photo_urls": ["https://example.com/doggie.jpg"],
  "tags": ["friendly"],
  "status": "sold"
}
```

`category` is optional; `photo_urls`/`tags` default to `[]`; `status` defaults to `"available"`.
Returns the updated pet (same shape as `GET`), or 400 on a malformed payload, or 404 if the id
doesn't exist.

## `DELETE /pets/{id}`

Deletes the pet. Returns `204` with no body regardless of whether the id existed.

## HTML/htmx endpoints

Served by `petstore-web` (mounted at `/`, with the JSON API above — served by
`petstore-api` — mounted under it at `/api`), not JSON — see
`packages/petstore-web/src/petstore_web/pets/routes.py` for their form fields:

- `GET /` — the app shell: sidebar nav, pet list, and detail pane. Accepts `?status=` and
  `?selected=` to preselect a status filter / pet on load (e.g. after adding one).
- `GET /pets/new` — full-screen "Add Pet" page.
- `POST /pets/new` — creates a pet, redirects to `/?selected={id}`.
- `GET /pets` — the pet list fragment (`?status=`, `?search=`).
- `GET /pets/{id}/detail` — the detail pane, read view.
- `GET|PUT /pets/{id}/detail/edit` — the detail pane, edit form / save (save also returns
  an out-of-band refresh of the list).
- `DELETE /pets/{id}` — deletes the pet; returns the empty detail state plus an
  out-of-band refresh of the list.
