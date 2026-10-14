from pydantic import BaseModel, Field, StrictInt, field_validator


class CreateBillReturnRequest(BaseModel):
    batch_id: str = Field(min_length=24, max_length=24)
    quantity: StrictInt = Field(gt=0)
    reason: str = Field(min_length=3, max_length=250)

    @field_validator("batch_id")
    @classmethod
    def validate_batch_id(cls, value: str) -> str:
        try:
            int(value, 16)
        except ValueError as exc:
            raise ValueError("batch_id must be a valid 24-character ID") from exc

        return value

    @field_validator("reason")
    @classmethod
    def trim_reason(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 3:
            raise ValueError("reason must contain at least 3 characters")

        return value