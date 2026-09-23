from pydantic import BaseModel, Field


class CreateUnitRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=50,
    )


class UnitResponse(BaseModel):
    id: str
    name: str
    is_active: bool


class UpdateUnitRequest(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    is_active: bool | None = None