from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Register(Input):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    email: EmailStr
    name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        if not value.strip():
            raise ValueError("Name cannot be blank")
        return value.strip()


class Login(Input):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class Token(Input):
    token: str = Field(min_length=20, max_length=200)


class OrganisationInput(Input):
    name: str = Field(min_length=1, max_length=100)


class InviteInput(Input):
    email: EmailStr
    role: Literal["creator", "reviewer"]


class MemberInput(Input):
    role: Literal["creator", "reviewer"]
    status: Literal["active", "disabled"] = "active"


class PriceFact(Input):
    kind: Literal["price"] = "price"
    entity: str = Field(min_length=1, max_length=150)
    amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: Literal["INR", "USD", "EUR", "GBP"]
    unit: str = Field(min_length=1, max_length=80)
    effective_from: date
    effective_to: date | None = None


class RuleInput(Input):
    type: Literal[
        "approved_fact",
        "product_name",
        "prohibited_term",
        "required_disclaimer",
        "tone",
        "channel_instruction",
    ]
    rule_key: str = Field(min_length=1, max_length=100)
    value: str = Field(min_length=1, max_length=2000)
    scope_channel: Literal[
        "global",
        "general",
        "linkedin",
        "instagram",
        "website",
        "email",
        "advertisement",
    ] = "global"
    source_document_id: UUID | None = None
    source_excerpt: str | None = Field(default=None, max_length=2000)
    source_location: str | None = Field(default=None, max_length=100)
    approved: bool = False
    fact: PriceFact | None = None
    revision: int = Field(default=1, ge=1)

    @field_validator("rule_key")
    @classmethod
    def normalise_key(cls, value):
        return value.casefold().replace(" ", "_")
