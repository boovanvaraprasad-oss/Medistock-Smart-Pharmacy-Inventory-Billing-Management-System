from pydantic import (
    BaseModel,
    Field,
    StrictInt,
    field_validator,
)


class StockAdjustmentRequest(BaseModel):
    medicine_id: str
    quantity: int = Field(gt=0)


class AdjustBatchStockRequest(BaseModel):
    medicine_id: str
    batch_id: str

    # Positive adds stock; negative removes stock.
    # Zero is rejected because it would not change inventory.
    quantity_change: StrictInt

    reason: str = Field(
        min_length=1,
        max_length=250,
    )

    @field_validator("quantity_change")
    @classmethod
    def quantity_change_must_not_be_zero(
        cls,
        value: int,
    ) -> int:
        if value == 0:
            raise ValueError(
                "quantity_change cannot be zero"
            )

        return value

    @field_validator("reason")
    @classmethod
    def reason_must_not_be_blank(
        cls,
        value: str,
    ) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "A reason is required"
            )

        return cleaned_value