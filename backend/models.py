from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


# User Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    username: str
    email: str
    full_name: str
    created_at: datetime


# Zakat Entry Models
class ZakatEntry(BaseModel):
    amount: float
    category: str  # e.g., "Gold", "Silver", "Cash", "Business", "Agriculture"
    description: Optional[str] = None
    date: datetime = Field(default_factory=datetime.now)
    zakat_amount: float  # Calculated zakat (usually 2.5% of amount)
    user_id: str


class ZakatCreate(BaseModel):
    amount: float
    category: str
    description: Optional[str] = None
    date: Optional[datetime] = None


class ZakatUpdate(BaseModel):
    amount: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None


class ZakatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    amount: float
    category: str
    description: Optional[str]
    date: datetime
    zakat_amount: float
    user_id: str


# Token Models
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None