# src/main.py
from typing import List, Optional, Literal
from bson import ObjectId
from fastapi import FastAPI, HTTPException, Request, Query, Depends, Security
from pydantic import BaseModel, Field
import motor.motor_asyncio
import strawberry
from strawberry.fastapi import GraphQLRouter
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

SECRET_KEY = "super-secret-key"  # demo only; load from env in real apps
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Simple in-memory user for training
fake_users_db = {
    "alice": {"username": "alice", "hashed_password": pwd_context.hash("wonderland")}
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str) -> dict | None:
    user = fake_users_db.get(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return {"username": user["username"]}

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = fake_users_db.get(username)
    if user is None:
        raise credentials_exception
    return {"username": user["username"]}




@strawberry.type
class MutationResult:
    success: bool
    message: str

# ------------------------------------------------------------------------------
# App metadata
# ------------------------------------------------------------------------------
app = FastAPI(title="Testing Bootcamp API", version="14.0.0")

# ------------------------------------------------------------------------------
# Lazy Mongo initialization (kept from Day 11+)
# ------------------------------------------------------------------------------
def ensure_mongo(request: Request):
    state = request.app.state
    if not hasattr(state, "client"):
        state.client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    if not hasattr(state, "db"):
        state.db = state.client.testing_db
    if not hasattr(state, "products"):
        state.products = state.db.products
    return state.products

# ------------------------------------------------------------------------------
# Models & constants
# ------------------------------------------------------------------------------
class Product(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    price: float = Field(..., ge=0.0)

SORTABLE_FIELDS = {"name", "price"}

# Simple demo auth (in real life, use env vars / a DB / JWT etc.)
VALID_API_KEYS = {"secret123", "topkey456"}
VALID_BEARER_TOKENS = {"bearer-abc-123"}

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)):
    """
    REST auth helper via X-API-Key.
    Raises 403 if missing/invalid.
    """
    if api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid or missing API Key")
    return api_key

def extract_valid_bearer_or_raise(request: Request) -> str:
    """
    GraphQL auth helper via Authorization: Bearer <token>.
    Raises Exception (GraphQL error) if missing/invalid.
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise Exception("Unauthorized: Bearer token required")
    token = auth.split(" ", 1)[1].strip()
    if token not in VALID_BEARER_TOKENS:
        raise Exception("Forbidden: Invalid Bearer token")
    return token

# ------------------------------------------------------------------------------
# Basic health
# ------------------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "API is running", "version": app.version}

# ------------------------------------------------------------------------------
# REST Endpoints (public)
# ------------------------------------------------------------------------------
@app.post("/products")
async def create_product(product: Product, request: Request):
    col = ensure_mongo(request)
    result = await col.insert_one(product.model_dump())
    return {"message": "Product added", "id": str(result.inserted_id)}

@app.get("/products")
async def list_products(
    request: Request,
    limit: int = Query(100, ge=1, le=200),
    skip: int = Query(0, ge=0, le=10_000),
    sort_by: str = Query("name"),
    order: Literal["asc", "desc"] = Query("asc"),
    name_contains: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0.0),
    max_price: Optional[float] = Query(None, ge=0.0),
):
    col = ensure_mongo(request)

    if sort_by not in SORTABLE_FIELDS:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by. Allowed: {sorted(SORTABLE_FIELDS)}")

    if (min_price is not None and max_price is not None) and (min_price > max_price):
        raise HTTPException(status_code=400, detail="min_price cannot be greater than max_price.")

    query: dict = {}
    if name_contains:
        query["name"] = {"$regex": name_contains, "$options": "i"}
    if min_price is not None or max_price is not None:
        price = {}
        if min_price is not None:
            price["$gte"] = float(min_price)
        if max_price is not None:
            price["$lte"] = float(max_price)
        query["price"] = price

    sort_dir = 1 if order == "asc" else -1

    items = []
    cursor = col.find(query).skip(skip).limit(limit).sort(sort_by, sort_dir)
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        items.append(doc)
    return items

@app.get("/products/first-id")
async def first_product_id(request: Request):
    col = ensure_mongo(request)
    doc = await col.find_one({})
    if not doc:
        raise HTTPException(status_code=404, detail="No products")
    return {"id": str(doc["_id"]), "name": doc["name"], "price": doc["price"]}

# ------------------------------------------------------------------------------
# REST Endpoint (secured via API Key)
# ------------------------------------------------------------------------------
@app.post("/secure/products")
async def secure_create_product(
    product: Product,
    request: Request,
    api_key: str = Depends(verify_api_key),
):
    col = ensure_mongo(request)
    result = await col.insert_one(product.model_dump())
    return {"message": "Secure product added", "id": str(result.inserted_id)}


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token(data={"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return {"username": current_user["username"]}


def _require_bearer_username_from_request(request: Request) -> str:
    """
    Extracts and validates a JWT Bearer token from the request's Authorization header.

    Args:
        request (Request): The incoming FastAPI request object.

    Returns:
        str: The username (subject) extracted from the token payload.

    Raises:
        HTTPException: If the Authorization header is missing, invalid, the token is invalid,
                       or the payload does not contain a username.
    """
    auth = request.headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ------------------------------------------------------------------------------
# GraphQL Types & Schema
# ------------------------------------------------------------------------------
@strawberry.type
class ProductType:
    name: str
    price: float

@strawberry.input
class ProductInput:
    name: str
    price: float

@strawberry.type
class MutationResult:
    success: bool
    message: str

async def get_context(request: Request):
    # strawberry will pass this to resolvers as info.context["request"]
    return {"request": request}

@strawberry.type
class Query:
    @strawberry.field
    async def all_products(
        self,
        info,
        name_contains: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: Optional[int] = 100,
        skip: Optional[int] = 0,
        sort_by: Optional[str] = "name",
        order: Optional[str] = "asc",
    ) -> List[ProductType]:
        request: Request = info.context["request"]
        col = ensure_mongo(request)

        # Basic validation mirroring REST
        if limit < 1 or limit > 200:
            raise ValueError("limit must be between 1 and 200.")
        if skip < 0 or skip > 10_000:
            raise ValueError("skip must be between 0 and 10000.")
        if sort_by not in SORTABLE_FIELDS:
            raise ValueError(f"Invalid sort_by. Allowed: {sorted(SORTABLE_FIELDS)}")
        if order.lower() not in ("asc", "desc"):
            raise ValueError("order must be 'asc' or 'desc'")
        if (min_price is not None and max_price is not None) and (min_price > max_price):
            raise ValueError("min_price cannot be greater than max_price.")

        query: dict = {}
        if name_contains:
            query["name"] = {"$regex": name_contains, "$options": "i"}
        if (min_price is not None) or (max_price is not None):
            price = {}
            if min_price is not None:
                price["$gte"] = float(min_price)
            if max_price is not None:
                price["$lte"] = float(max_price)
            query["price"] = price

        sort_dir = 1 if order.lower() == "asc" else -1

        out: list[ProductType] = []
        cursor = col.find(query).skip(skip).limit(limit).sort(sort_by, sort_dir)
        async for doc in cursor:
            out.append(ProductType(name=doc["name"], price=float(doc["price"])))
        return out

    # NEW: secured GraphQL field requiring Bearer token
    @strawberry.field
    async def secret_products(self, info) -> List[ProductType]:
        request: Request = info.context["request"]
        # Will raise if invalid/missing
        extract_valid_bearer_or_raise(request)

        col = ensure_mongo(request)
        results: list[ProductType] = []
        cursor = col.find().limit(3)
        async for doc in cursor:
            results.append(ProductType(name=doc["name"], price=float(doc["price"])))
        return results

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def add_product(self, info, product: ProductInput) -> MutationResult:
        request = info.context["request"]
        user = _require_bearer_username_from_request(request)
        col = ensure_mongo(request)
        await col.insert_one({"name": product.name, "price": float(product.price)})
        return MutationResult(success=True, message=f"Product '{product.name}' added by {user}.")

    @strawberry.mutation
    async def update_product(self, info, id: str, product: ProductInput) -> MutationResult:
        request = info.context["request"]
        _ = _require_bearer_username_from_request(request)
        col = ensure_mongo(request)
        try:
            oid = ObjectId(id)
        except Exception:
            return MutationResult(success=False, message="Invalid product ID.")
        result = await col.update_one({"_id": oid}, {"$set": {"name": product.name, "price": float(product.price)}})
        if result.matched_count == 0:
            return MutationResult(success=False, message="Product not found.")
        return MutationResult(success=True, message="Product updated.")

    @strawberry.mutation
    async def delete_product(self, info, id: str) -> MutationResult:
        request = info.context["request"]
        _ = _require_bearer_username_from_request(request)
        col = ensure_mongo(request)
        try:
            oid = ObjectId(id)
        except Exception:
            return MutationResult(success=False, message="Invalid product ID.")
        result = await col.delete_one({"_id": oid})
        if result.deleted_count == 0:
            return MutationResult(success=False, message="Product not found.")
        return MutationResult(success=True, message="Product deleted.")


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")
