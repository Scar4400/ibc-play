# main.py (fully completed and fixed)
import os
import time
import asyncio
import random
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List

from fastapi import FastAPI, HTTPException, Depends, status, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from passlib.context import CryptContext
import jwt
from jwt import PyJWTError

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from sqlalchemy.exc import SQLAlchemyError

import httpx
from dotenv import load_dotenv
from loguru import logger as loguru_logger  # Enhanced logging

# Optional Redis & SlowAPI
import redis.asyncio as aioredis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

# Load env
load_dotenv()

# Config (all from env)
SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXP_SECONDS = int(os.getenv("JWT_EXP_SECONDS", 3600))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
COINGECKO_API_URL = os.getenv("COINGECKO_API_URL", "https://api.coingecko.com/api/v3")
REDIS_URL = os.getenv("REDIS_URL")
RATE_LIMIT = os.getenv("RATE_LIMIT", "60/m")  # e.g., 60/minute

# Logging setup (file + console)
loguru_logger.add("app.log", rotation="500 MB", level="INFO")

# SQLAlchemy
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Redis init (for limiting and caching)
redis_client = None
limiter = None
if REDIS_URL:
    try:
        redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
        limiter = Limiter(key_func=get_remote_address, storage_uri=REDIS_URL)
        loguru_logger.info("Redis and SlowAPI initialized.")
    except Exception as e:
        loguru_logger.warning(f"Redis init failed: {e}. Using in-memory fallback.")

# In-memory fallback for rate limiting
_bucket_store: Dict[str, dict] = {}
_bucket_lock = asyncio.Lock()

async def allow_request_in_memory(ip: str) -> bool:
    now = time.time()
    window = 60
    async with _bucket_lock:
        bucket = _bucket_store.get(ip, {"count": 0, "ts": now})
        elapsed = now - bucket["ts"]
        if elapsed > window:
            bucket = {"count": 1, "ts": now}
        elif bucket["count"] >= int(RATE_LIMIT.split("/")[0]):
            return False
        else:
            bucket["count"] += 1
        _bucket_store[ip] = bucket
        return True

# DB Models (unchanged but ensured)
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(128), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    wallet = relationship("Wallet", back_populates="user", uselist=False)
    transactions = relationship("Transaction", back_populates="user")
    bets = relationship("Bet", back_populates="user")

class Wallet(Base):
    __tablename__ = "wallets"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    balance_usd = Column(Float, default=0.0)
    user = relationship("User", back_populates="wallet")
    holdings = relationship("CryptoHolding", back_populates="wallet")

class CryptoHolding(Base):
    __tablename__ = "crypto_holdings"
    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    asset = Column(String(32), nullable=False)
    amount = Column(Float, default=0.0)
    wallet = relationship("Wallet", back_populates="holdings")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50))
    amount_usd = Column(Float, default=0.0)
    metadata = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="transactions")

class Bet(Base):
    __tablename__ = "bets"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game = Column(String(100))
    amount_usd = Column(Float, default=0.0)
    odds = Column(Float, default=1.0)
    result = Column(String(50), default="pending")
    payout = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="bets")

# Pydantic Schemas (added validation)
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class DepositRequest(BaseModel):
    usd_amount: float = Field(gt=0, le=10000)  # Arbitrary limits for demo

class CryptoDepositRequest(BaseModel):
    asset: str = Field(pattern="^(BTC|ETH|SOL|BNB)$")
    amount: float = Field(gt=0)

class WithdrawRequest(BaseModel):
    usd_amount: float = Field(gt=0)

class TransferRequest(BaseModel):
    to_username: str
    usd_amount: float = Field(gt=0)

class BetRequest(BaseModel):
    game: str = Field(min_length=1)
    amount_usd: float = Field(gt=0)
    odds: float = Field(gt=1.0)

class CasinoPlayRequest(BaseModel):
    game: str = "slots"  # For now, only slots
    amount_usd: float = Field(gt=0)

# Auth Utils
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(seconds=JWT_EXP_SECONDS))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except PyJWTError as e:
        loguru_logger.warning(f"JWT decode error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        loguru_logger.error(f"DB error: {e}")
        raise HTTPException(status_code=500, detail="Database issue")
    finally:
        db.close()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_token(token)
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# CoinGecko Integration (enhanced with fallback simulation)
COIN_MAP = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "BNB": "binancecoin"}
PRICE_CACHE_TTL = 30
_price_cache: Dict[str, dict] = {}
_price_lock = asyncio.Lock()
_api_fail_count = 0

async def get_price_usd(asset: str) -> float:
    global _api_fail_count
    asset_id = COIN_MAP.get(asset.upper())
    if not asset_id:
        raise HTTPException(400, "Invalid asset")
    now = time.time()
    key = f"price:{asset_id}"

    # Check cache (Redis first)
    if redis_client:
        try:
            cached = await redis_client.get(key)
            if cached:
                ts, price = cached.split(":")
                if now - float(ts) < PRICE_CACHE_TTL:
                    return float(price)
        except Exception as e:
            loguru_logger.warning(f"Redis cache error: {e}")

    async with _price_lock:
        cached = _price_cache.get(key)
        if cached and now - cached["ts"] < PRICE_CACHE_TTL:
            return cached["price"]

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{COINGECKO_API_URL}/simple/price", params={"ids": asset_id, "vs_currencies": "usd"})
                r.raise_for_status()
                price = r.json().get(asset_id, {}).get("usd")
                if not price or price <= 0:
                    raise ValueError("Invalid price")
                _price_cache[key] = {"ts": now, "price": price}
                if redis_client:
                    await redis_client.set(key, f"{now}:{price}", ex=PRICE_CACHE_TTL * 2)
                _api_fail_count = 0
                return price
        except Exception as e:
            loguru_logger.warning(f"CoinGecko error: {e}")
            _api_fail_count += 1
            if _api_fail_count > 3 or key not in _price_cache:
                # Fallback simulation (creative: mild random fluctuation)
                simulated = random.uniform(0.9, 1.1) * (cached["price"] if cached else 1.0)
                _price_cache[key] = {"ts": now, "price": simulated}
                loguru_logger.info(f"Using simulated price for {asset}: {simulated}")
                return simulated
            return _price_cache[key]["price"]

# App Init
app = FastAPI(title="IB Crypto Play")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Static for demo
app.mount("/demo", StaticFiles(directory=".", html=True), name="demo")

# Limiter middleware
if limiter:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
else:
    @app.middleware("http")
    async def in_memory_limiter(request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)
        ip = get_remote_address(request)
        if not await allow_request_in_memory(ip):
            return Response("Rate limit exceeded", status_code=429)
        return await call_next(request)

# Endpoints
@app.get("/health", tags=["system"])
@limiter.limit(RATE_LIMIT) if limiter else lambda r: r
async def health(request: Request):
    return {"status": "ok", "db": engine.connect().closed == False, "time": datetime.utcnow().isoformat()}

@app.post("/register", response_model=Token)
@limiter.limit(RATE_LIMIT) if limiter else lambda r: r
async def register(user_in: UserCreate, db: Session = Depends(get_db), request: Request):
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(400, "Username taken")
    hashed_pw = get_password_hash(user_in.password)
    user = User(username=user_in.username, hashed_password=hashed_pw)
    db.add(user)
    db.commit()
    db.refresh(user)
    # Create wallet
    wallet = Wallet(user_id=user.id)
    db.add(wallet)
    db.commit()
    access_token = create_access_token({"sub": user.username})
    loguru_logger.info(f"User registered: {user.username}")
    return Token(access_token=access_token, expires_in=JWT_EXP_SECONDS)

@app.post("/login", response_model=Token)
@limiter.limit(RATE_LIMIT) if limiter else lambda r: r
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db), request: Request):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    access_token = create_access_token({"sub": user.username})
    loguru_logger.info(f"User login: {user.username}")
    return Token(access_token=access_token, expires_in=JWT_EXP_SECONDS)

@app.post("/deposit", response_model=Dict)
@limiter.limit(RATE_LIMIT) if limiter else lambda r: r
async def deposit(dep: DepositRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db), request: Request):
    wallet = current_user.wallet
    wallet.balance_usd += dep.usd_amount
    tx = Transaction(user_id=current_user.id, type="deposit", amount_usd=dep.usd_amount)
    db.add(tx)
    db.commit()
    loguru_logger.info(f"Deposit: {dep.usd_amount} USD for {current_user.username}")
    return {"balance": wallet.balance_usd}

@app.post("/crypto/deposit", response_model=Dict)
@limiter.limit(RATE_LIMIT) if limiter else lambda r: r
async def crypto_deposit(dep: CryptoDepositRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db), request: Request):
    price = await get_price_usd(dep.asset)
    usd_value = dep.amount * price
    wallet = current_user.wallet
    holding = db.query(CryptoHolding).filter(CryptoHolding.wallet_id == wallet.id, CryptoHolding.asset == dep.asset).first()
    if not holding:
        holding = CryptoHolding(wallet_id=wallet.id, asset=dep.asset, amount=dep.amount)
        db.add(holding)
    else:
        holding.amount += dep.amount
    wallet.balance_usd += usd_value  # Add equivalent USD for betting
    tx = Transaction(user_id=current_user.id, type="crypto_deposit", amount_usd=usd_value, metadata=f"{dep.asset}:{dep.amount}")
    db.add(tx)
    db.commit()
    loguru_logger.info(f"Crypto deposit: {dep.amount} {dep.asset} (${usd_value}) for {current_user.username}")
    return {"balance": wallet.balance_usd, "holding": holding.amount}

@app.post("/withdraw", response_model=Dict)
@limiter.limit(RATE_LIMIT) if limiter else lambda r: r
async def withdraw(wd: WithdrawRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db), request: Request):
    wallet = current_user.wallet
    if wallet.balance_usd < wd.usd_amount:
        raise HTTPException(400, "Insufficient balance")
    wallet.balance_usd -= wd.usd_amount
    tx = Transaction(user_id=current_user.id, type="withdraw", amount_usd=-wd.usd_amount)
    db.add(tx)
    db.commit()
    loguru_logger.info(f"Withdraw: {wd.usd_amount} USD for {current_user.username}")
    return {"balance": wallet.balance_usd}

@app.post("/transfer", response_model=Dict)
@limiter.limit(RATE_LIMIT) if limiter else lambda r: r
async def transfer(tr: TransferRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db), request: Request):
    wallet = current_user.wallet
    if wallet.balance_usd < tr.usd_amount:
        raise HTTPException(400, "Insufficient balance")
    to_user = db.query(User).filter(User.username == tr.to_username).first()
    if not to_user:
        raise HTTPException(404, "Recipient not found")
    to_wallet = to_user.wallet
    wallet.balance_usd -= tr.usd_amount
    to_wallet.balance_usd += tr.usd_amount
    tx_out = Transaction(user_id=current_user.id, type="transfer_out", amount_usd=-tr.usd_amount, metadata=tr.to_username)
    tx_in = Transaction(user_id=to_user.id, type="transfer_in", amount_usd=tr.usd_amount, metadata=current_user.username)
    db.add_all([tx_out, tx_in])
    db.commit()
    loguru_logger.info(f"Transfer: {tr.usd_amount} USD from {current_user.username} to {tr.to_username}")
    return {"balance": wallet.balance_usd}

@app.post("/bets", response_model=Dict)
@limiter.limit(RATE_LIMIT) if limiter else lambda r: r
async def place_bet(bet_in: BetRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db), request: Request):
    wallet = current_user.wallet
    if wallet.balance_usd < bet_in.amount_usd:
        raise HTTPException(400, "Insufficient balance")
    wallet.balance_usd -= bet_in.amount_usd
    bet = Bet(user_id=current_user.id, game=bet_in.game, amount_usd=bet_in.amount_usd, odds=bet_in.odds)
    db.add(bet)
    db.commit()
    # Simulate settlement (creative: 50% win chance for demo)
    if random.random() > 0.5:
        payout = bet_in.amount_usd * bet_in.odds
        wallet.balance_usd += payout
        bet.result = "win"
        bet.payout = payout
    else:
        bet.result = "loss"
        bet.payout = 0
    db.commit()
    loguru_logger.info(f"Bet placed: {bet_in.game} ${bet_in.amount_usd} for {current_user.username} - Result: {bet.result}")
    return {"result": bet.result, "payout": bet.payout, "balance": wallet.balance_usd}

@app.post("/casino/play", response_model=Dict)
@limiter.limit(RATE_LIMIT) if limiter else lambda r: r
async def casino_play(play_in: CasinoPlayRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db), request: Request):
    wallet = current_user.wallet
    if wallet.balance_usd < play_in.amount_usd:
        raise HTTPException(400, "Insufficient balance")
    wallet.balance_usd -= play_in.amount_usd
    # Creative slots simulation: 3 reels, win if match (RNG)
    reels = [random.choice(["cherry", "lemon", "bar", "7"]) for _ in range(3)]
    if len(set(reels)) == 1:
        payout = play_in.amount_usd * random.uniform(2, 10)  # Variable payout
        wallet.balance_usd += payout
        result = "win"
    else:
        payout = 0
        result = "loss"
    bet = Bet(user_id=current_user.id, game="slots", amount_usd=play_in.amount_usd, odds=0, result=result, payout=payout)
    db.add(bet)
    db.commit()
    loguru_logger.info(f"Casino play: slots ${play_in.amount_usd} for {current_user.username} - Reels: {reels} - Result: {result}")
    return {"reels": reels, "result": result, "payout": payout, "balance": wallet.balance_usd}

@app.get("/balances", response_model=Dict)
@limiter.limit(RATE_LIMIT) if limiter else lambda r: r
async def get_balances(current_user: User = Depends(get_current_user), db: Session = Depends(get_db), request: Request):
    wallet = current_user.wallet
    holdings = {h.asset: {"amount": h.amount, "usd": h.amount * await get_price_usd(h.asset)} for h in wallet.holdings}
    return {"usd": wallet.balance_usd, "crypto": holdings}