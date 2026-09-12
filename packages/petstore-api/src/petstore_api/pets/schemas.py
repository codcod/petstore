import msgspec


class PetCreate(msgspec.Struct):
    """Payload from the HTML add-pet form — tags/photo_urls arrive as comma-separated text."""

    name: str
    category: str | None = None
    photo_urls: str | None = None
    tags: str | None = None
    status: str = 'available'


class PetUpdate(msgspec.Struct):
    name: str
    category: str | None = None
    photo_urls: list[str] = msgspec.field(default_factory=list)
    tags: list[str] = msgspec.field(default_factory=list)
    status: str = 'available'


class PetOut(msgspec.Struct):
    id: int
    name: str
    category: str | None
    photo_urls: list[str]
    tags: list[str]
    status: str
    created_at: str
