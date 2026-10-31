"""Frozen Pydantic v2 domain records for the illustrative order-fulfillment matrix."""
from __future__ import annotations
from datetime import datetime
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Literal, Annotated, Union, Self, Mapping, Any
from pydantic import BaseModel, ConfigDict, Field, SerializeAsAny, field_validator, model_validator


@dataclass(frozen=True)
class ConfigSnapshot:
    version:str
    fingerprint:str
    specs:tuple[Mapping[str,Any],...]
    max_event_bytes:int
    max_tokens:int
    max_batch:int
    aliases:Mapping[str,str]


Id = Annotated[str, Field(min_length=1,max_length=64, pattern=r'^[A-Za-z0-9][A-Za-z0-9_-]*$')]
Amount = Annotated[Decimal, Field(gt=Decimal('0'), decimal_places=2, max_digits=15)]
Quantity = Annotated[int, Field(gt=0, le=1000000)]

class FrozenRecord(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid', frozen=True)

class LineItem(FrozenRecord):
    sku_code: Id
    quantity: Quantity
    unit_price: Amount

class Common(FrozenRecord):
    event_type: Literal['ORDER_CREATED','PAYMENT_AUTHORIZED','INVENTORY_RESERVED','SHIPMENT_DISPATCHED','ORDER_CANCELLED']
    event_id: Id
    tenant_id: Id
    order_id: Id
    source: Literal['ERP','PAYMENT','WMS','CARRIER']
    occurred_at: datetime

    @field_validator('occurred_at')
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('timezone_required')
        return value

class OrderCreated(Common):
    event_type: Literal['ORDER_CREATED']
    customer_ref: Id
    gross_amount: Amount
    currency: Literal['USD']
    lines_json: tuple[LineItem,...] | None = None

    @model_validator(mode='after')
    def total_matches(self) -> Self:
        if self.lines_json is not None:
            # Price validation guarantees exact cent values. Integer arithmetic
            # avoids rounding/traps inherited from a caller's Decimal context.
            total_cents = 0
            for line in self.lines_json:
                numerator, denominator = line.unit_price.as_integer_ratio()
                cents = numerator * 100 // denominator
                total_cents += line.quantity * cents
            gross_numerator, gross_denominator = self.gross_amount.as_integer_ratio()
            if total_cents * gross_denominator != gross_numerator * 100:
                raise ValueError('line_total_mismatch')
        return self

class PaymentAuthorized(Common):
    event_type: Literal['PAYMENT_AUTHORIZED']
    payment_ref: Id
    authorized_amount: Amount
    currency: Literal['USD']

class InventoryReserved(Common):
    event_type: Literal['INVENTORY_RESERVED']
    warehouse_ref: Id
    sku_code: Id
    quantity: Quantity

class ShipmentDispatched(Common):
    event_type: Literal['SHIPMENT_DISPATCHED']
    shipment_ref: Id
    carrier_code: Id
    tracking_ref: Id
    quantity: Quantity

class OrderCancelled(Common):
    event_type: Literal['ORDER_CANCELLED']
    reason: Literal['CUSTOMER_REQUEST','FULFILLMENT_FAILURE']

MODEL_REGISTRY: dict[str,type[Common]] = {
 'order_created.v1':OrderCreated,
 'payment_authorized.v1':PaymentAuthorized,
 'inventory_reserved.v1':InventoryReserved,
 'shipment_dispatched.v1':ShipmentDispatched,
 'order_cancelled.v1':OrderCancelled,
}

class Failure(str, Enum):
    PARSE_ERROR='PARSE_ERROR'
    SCHEMA_VIOLATION='SCHEMA_VIOLATION'
    UNSUPPORTED_EVENT='UNSUPPORTED_EVENT'
    AMBIGUOUS_EVENT='AMBIGUOUS_EVENT'
    INPUT_LIMIT='INPUT_LIMIT'
    CONFIG_ERROR='CONFIG_ERROR'

class ErrorItem(FrozenRecord):
    path: str
    rule_id: str
    code: str
    message: str

class Transform(FrozenRecord):
    path: str
    rule_id: str
    before_digest: str
    after_digest: str

class ValidationResult(FrozenRecord):
    input_ref: str
    index: int
    config_fingerprint: str
    event_type: str | None
    schema_id: str | None
    schema_version: str | None
    status: Literal['ACCEPTED','REJECTED']
    failure_category: Failure | None
    record: SerializeAsAny[Common] | None = None
    errors: tuple[ErrorItem,...] = ()
    transforms: tuple[Transform,...] = ()
    trace: tuple[str,...] = ()
    input_sha256: str

    def canonical(self)->str:
        return self.model_dump_json(exclude_none=True)
