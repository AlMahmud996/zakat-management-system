from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import List
from bson import ObjectId

from models import (
    UserCreate, UserLogin, UserResponse, Token,
    ZakatCreate, ZakatUpdate, ZakatResponse
)
from database import (
    users_collection, zakat_collection,
    connect_to_mongo, close_mongo_connection
)
from auth import (
    get_password_hash, verify_password, create_access_token,
    get_current_user_email, ACCESS_TOKEN_EXPIRE_MINUTES
)

app = FastAPI(title="Zakat Management System API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_db_client():
    """Connect to MongoDB on startup"""
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_db_client():
    """Close MongoDB connection on shutdown"""
    await close_mongo_connection()


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to Zakat Management System API"}


# ==================== AUTH ENDPOINTS ====================

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """Register a new user"""
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username exists
    existing_username = await users_collection.find_one({"username": user.username})
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Hash password
    hashed_password = get_password_hash(user.password)
    
    # Create user document
    user_doc = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "full_name": user.full_name,
        "created_at": datetime.utcnow()
    }
    
    # Insert user
    result = await users_collection.insert_one(user_doc)
    user_doc["id"] = str(result.inserted_id)
    
    return UserResponse(**user_doc)


@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login user and return JWT token"""
    # Find user by email (using username field from form)
    user = await users_collection.find_one({"email": form_data.username})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/me", response_model=UserResponse)
async def get_current_user(email: str = Depends(get_current_user_email)):
    """Get current logged-in user"""
    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user["id"] = str(user["_id"])
    return UserResponse(**user)


# ==================== ZAKAT ENDPOINTS ====================

@app.post("/zakat", response_model=ZakatResponse, status_code=status.HTTP_201_CREATED)
async def create_zakat_entry(
    zakat: ZakatCreate,
    email: str = Depends(get_current_user_email)
):
    """Create a new zakat entry"""
    # Get user
    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Calculate zakat (2.5% of amount)
    zakat_amount = zakat.amount * 0.025
    
    # Create zakat document
    zakat_doc = {
        "amount": zakat.amount,
        "category": zakat.category,
        "description": zakat.description,
        "date": zakat.date if zakat.date else datetime.utcnow(),
        "zakat_amount": zakat_amount,
        "user_id": str(user["_id"]),
        "created_at": datetime.utcnow()
    }
    
    # Insert zakat entry
    result = await zakat_collection.insert_one(zakat_doc)
    zakat_doc["id"] = str(result.inserted_id)
    
    return ZakatResponse(**zakat_doc)


@app.get("/zakat", response_model=List[ZakatResponse])
async def get_zakat_entries(email: str = Depends(get_current_user_email)):
    """Get all zakat entries for current user"""
    # Get user
    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get all zakat entries for user
    cursor = zakat_collection.find({"user_id": str(user["_id"])}).sort("date", -1)
    entries = await cursor.to_list(length=None)
    
    # Format entries
    formatted_entries = []
    for entry in entries:
        entry["id"] = str(entry["_id"])
        formatted_entries.append(ZakatResponse(**entry))
    
    return formatted_entries


@app.get("/zakat/{zakat_id}", response_model=ZakatResponse)
async def get_zakat_entry(
    zakat_id: str,
    email: str = Depends(get_current_user_email)
):
    """Get a specific zakat entry"""
    # Get user
    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get zakat entry
    try:
        entry = await zakat_collection.find_one({
            "_id": ObjectId(zakat_id),
            "user_id": str(user["_id"])
        })
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid zakat ID"
        )
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zakat entry not found"
        )
    
    entry["id"] = str(entry["_id"])
    return ZakatResponse(**entry)


@app.put("/zakat/{zakat_id}", response_model=ZakatResponse)
async def update_zakat_entry(
    zakat_id: str,
    zakat: ZakatUpdate,
    email: str = Depends(get_current_user_email)
):
    """Update a zakat entry"""
    # Get user
    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get existing entry
    try:
        existing_entry = await zakat_collection.find_one({
            "_id": ObjectId(zakat_id),
            "user_id": str(user["_id"])
        })
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid zakat ID"
        )
    
    if not existing_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zakat entry not found"
        )
    
    # Update fields
    update_data = {}
    if zakat.amount is not None:
        update_data["amount"] = zakat.amount
        update_data["zakat_amount"] = zakat.amount * 0.025
    if zakat.category is not None:
        update_data["category"] = zakat.category
    if zakat.description is not None:
        update_data["description"] = zakat.description
    if zakat.date is not None:
        update_data["date"] = zakat.date
    
    # Update entry
    if update_data:
        await zakat_collection.update_one(
            {"_id": ObjectId(zakat_id)},
            {"$set": update_data}
        )
    
    # Get updated entry
    updated_entry = await zakat_collection.find_one({"_id": ObjectId(zakat_id)})
    updated_entry["id"] = str(updated_entry["_id"])
    
    return ZakatResponse(**updated_entry)


@app.delete("/zakat/{zakat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zakat_entry(
    zakat_id: str,
    email: str = Depends(get_current_user_email)
):
    """Delete a zakat entry"""
    # Get user
    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete entry
    try:
        result = await zakat_collection.delete_one({
            "_id": ObjectId(zakat_id),
            "user_id": str(user["_id"])
        })
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid zakat ID"
        )
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zakat entry not found"
        )
    
    return None


@app.get("/zakat/statistics/summary")
async def get_zakat_statistics(email: str = Depends(get_current_user_email)):
    """Get zakat statistics for current user"""
    # Get user
    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get all entries
    cursor = zakat_collection.find({"user_id": str(user["_id"])})
    entries = await cursor.to_list(length=None)
    
    # Calculate statistics
    total_amount = sum(entry["amount"] for entry in entries)
    total_zakat = sum(entry["zakat_amount"] for entry in entries)
    total_entries = len(entries)
    
    # Category breakdown
    category_stats = {}
    for entry in entries:
        category = entry["category"]
        if category not in category_stats:
            category_stats[category] = {
                "count": 0,
                "total_amount": 0,
                "total_zakat": 0
            }
        category_stats[category]["count"] += 1
        category_stats[category]["total_amount"] += entry["amount"]
        category_stats[category]["total_zakat"] += entry["zakat_amount"]
    
    return {
        "total_amount": total_amount,
        "total_zakat": total_zakat,
        "total_entries": total_entries,
        "category_breakdown": category_stats
    }