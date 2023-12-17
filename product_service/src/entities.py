from decimal import Decimal

from pydantic import BaseModel, Field


class ProductResponse(BaseModel):
    id: str
    count: int = Field(gt=0)
    price: Decimal
    title: str
    description: str


class ProductRequest(BaseModel):
    count: int = Field(gt=0)
    price: Decimal
    title: str
    description: str


class NewProduct(BaseModel):
    id: str
    price: Decimal
    title: str
    description: str


class NewStock(BaseModel):
    product_id: str
    count: int = Field(gt=0)
