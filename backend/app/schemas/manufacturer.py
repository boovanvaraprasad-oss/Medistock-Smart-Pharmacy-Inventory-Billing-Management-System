from pydantic import BaseModel, Field

class CreateManufacturerRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class ManufacturerResponse(BaseModel):
    id: str
    name: str
    is_active: bool

class UpdateManufacturerRequest(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    is_active: bool |None = None