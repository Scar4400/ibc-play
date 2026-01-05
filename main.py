"""
IBC Play - Crypto Sports Betting & Casino Platform
Complete FastAPI backend with authentication, wallet management, betting, and casino games.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import random

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
from jose import JWTError, jwt
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from db_init import get_connection, init_database
from crypto_prices import crypto_service, get_crypto_price, is_currency_supported

# Load environment variables
load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-minimum-32-characters-long")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database on startup
init_database()

# FastAPI app
app = FastAPI(
    title="IBC Play API",
    description="Crypto Sports Betting & Casino Platform",
    version="1.0.0"
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ===========================
# PYDANTIC MODELS
# ===========================

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: str

class WalletBalance(BaseModel):
    currency: str
    balance: float
    locked_balance: float
    usd_value: Optional[float] = None

class DepositRequest(BaseModel):
    currency: str
    amount: float = Field(..., gt=0)

class WithdrawRequest(BaseModel):
    currency: str
    amount: float = Field(..., gt=0)

class TransferRequest(BaseModel):
    from_currency: str
    to_currency: str
    amount: float = Field(..., gt=0)

class BetCreate(BaseModel):
    bet_type: str
    sport: Optional[str] = None
    event_name: str
    selection: str
    odds: float = Field(..., gt=1.0)
    stake_amount: float = Field(..., gt=0)
    stake_currency: str = "USD"

class CasinoPlayRequest(BaseModel):
    game: str
    bet_amount: float = Field(..., gt=0)
    bet_currency: str = "USD"
    bet_options: Optional[Dict[str, Any]] = None

# ===========================
# AUTHENTICATION FUNCTIONS
# ===========================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user is None:
        raise credentials_exception
    
    return dict(user)

# ===========================
# DATABASE HELPER FUNCTIONS
# ===========================

def get_user_by_username(username: str) -> Optional[dict]:
    """Get user by username."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_wallet(user_id: int, currency: str) -> Optional[dict]:
    """Get user's wallet for specific currency."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM wallets WHERE user_id = ? AND currency = ?",
        (user_id, currency)
    )
    wallet = cursor.fetchone()
    conn.close()
    return dict(wallet) if wallet else None

def update_wallet_balance(user_id: int, currency: str, amount_change: float) -> bool:
    """Update wallet balance atomically."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get current balance
        cursor.execute(
            "SELECT balance FROM wallets WHERE user_id = ? AND currency = ?",
            (user_id, currency)
        )
        result = cursor.fetchone()
        
        if not result:
            # Create wallet if doesn't exist
            cursor.execute(
                "INSERT INTO wallets (user_id, currency, balance) VALUES (?, ?, ?)",
                (user_id, currency, max(0, amount_change))
            )
        else:
            new_balance = result["balance"] + amount_change
            if new_balance < 0:
                raise ValueError("Insufficient balance")
            
            cursor.execute(
                "UPDATE wallets SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND currency = ?",
                (new_balance, user_id, currency)
            )
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to update wallet balance: {str(e)}")
        raise
    finally:
        conn.close()

def record_transaction(user_id: int, tx_type: str, currency: str, amount: float, 
                      status: str = "completed", description: str = "", 
                      reference_id: str = None, metadata: dict = None) -> int:
    """Record a financial transaction."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Calculate USD value
        if currency == "USD":
            usd_value = amount
        else:
            price = crypto_service._get_from_cache(currency)
            usd_value = amount * price if price else None
        
        cursor.execute('''
        INSERT INTO transactions (user_id, transaction_type, currency, amount, usd_value, 
                                 status, description, reference_id, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, tx_type, currency, amount, usd_value, status, description,
              reference_id, json.dumps(metadata) if metadata else None))
        
        tx_id = cursor.lastrowid
        conn.commit()
        return tx_id
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to record transaction: {str(e)}")
        raise
    finally:
        conn.close()

# ===========================
# HEALTH & INFO ENDPOINTS
# ===========================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "IBC Play API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for deployment platforms."""
    try:
        # Test database connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    try:
        # Test crypto API
        price = await crypto_service.get_price("BTC")
        crypto_api_status = "reachable"
    except Exception as e:
        crypto_api_status = f"degraded: {str(e)}"
    
    return {
        "status": "ok",
        "db": db_status,
        "crypto_api": crypto_api_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/prices")
@limiter.limit("30/minute")
async def get_crypto_prices(request: Request):
    """Get current cryptocurrency prices."""
    try:
        prices = await crypto_service.get_multiple_prices(["BTC", "ETH", "SOL", "BNB"])
        return {
            "prices": prices,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to fetch prices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch prices")

# ===========================
# AUTHENTICATION ENDPOINTS
# ===========================

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(user: UserCreate, request: Request):
    """Register a new user."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", 
                      (user.username, user.email))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username or email already registered")
        
        # Create user
        hashed_password = get_password_hash(user.password)
        cursor.execute('''
        INSERT INTO users (username, email, hashed_password, full_name, is_active, is_verified)
        VALUES (?, ?, ?, ?, 1, 0)
        ''', (user.username, user.email, hashed_password, user.full_name))
        
        user_id = cursor.lastrowid
        
        # Create default wallets
        for currency in ["USD", "BTC", "ETH", "SOL", "BNB"]:
            initial_balance = 10000.0 if currency == "USD" else 0.0
            cursor.execute('''
            INSERT INTO wallets (user_id, currency, balance)
            VALUES (?, ?, ?)
            ''', (user_id, currency, initial_balance))
        
        conn.commit()
        
        # Return user data
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        new_user = dict(cursor.fetchone())
        
        return UserResponse(
            id=new_user["id"],
            username=new_user["username"],
            email=new_user["email"],
            full_name=new_user["full_name"],
            is_active=bool(new_user["is_active"]),
            created_at=new_user["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")
    finally:
        conn.close()

@app.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None):
    """Login and get JWT token."""
    user = get_user_by_username(form_data.username)
    
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user["is_active"]:
        raise HTTPException(status_code=400, detail="User account is inactive")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        is_active=bool(current_user["is_active"]),
        created_at=current_user["created_at"]
    )

# ===========================
# WALLET ENDPOINTS
# ===========================

@app.get("/wallet")
async def get_wallet(current_user: dict = Depends(get_current_user)):
    """Get all user wallet balances with USD values."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM wallets WHERE user_id = ?", (current_user["id"],))
        wallets = [dict(row) for row in cursor.fetchall()]
        
        # Get current prices
        prices = await crypto_service.get_multiple_prices(["BTC", "ETH", "SOL", "BNB"])
        
        # Calculate USD values
        wallet_data = []
        total_usd = 0.0
        
        for wallet in wallets:
            currency = wallet["currency"]
            balance = wallet["balance"]
            
            if currency == "USD":
                usd_value = balance
            else:
                usd_value = balance * prices.get(currency, 0.0)
            
            total_usd += usd_value
            
            wallet_data.append({
                "currency": currency,
                "balance": balance,
                "locked_balance": wallet["locked_balance"],
                "usd_value": round(usd_value, 2)
            })
        
        return {
            "wallets": wallet_data,
            "total_usd_value": round(total_usd, 2),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    finally:
        conn.close()

@app.post("/deposit")
@limiter.limit("20/minute")
async def deposit(
    request: Request,
    deposit_req: DepositRequest,
    current_user: dict = Depends(get_current_user)
):
    """Deposit funds to wallet."""
    if not is_currency_supported(deposit_req.currency):
        raise HTTPException(status_code=400, detail="Unsupported currency")
    
    try:
        # Get current price if crypto
        if deposit_req.currency != "USD":
            price = await get_crypto_price(deposit_req.currency)
        else:
            price = 1.0
        
        # Update wallet
        update_wallet_balance(current_user["id"], deposit_req.currency, deposit_req.amount)
        
        # Record transaction
        tx_id = record_transaction(
            user_id=current_user["id"],
            tx_type="deposit",
            currency=deposit_req.currency,
            amount=deposit_req.amount,
            status="completed",
            description=f"Deposit {deposit_req.amount} {deposit_req.currency}",
            metadata={"price_usd": price}
        )
        
        return {
            "success": True,
            "transaction_id": tx_id,
            "currency": deposit_req.currency,
            "amount": deposit_req.amount,
            "message": f"Successfully deposited {deposit_req.amount} {deposit_req.currency}"
        }
        
    except Exception as e:
        logger.error(f"Deposit failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Deposit failed")

@app.post("/withdraw")
@limiter.limit("10/minute")
async def withdraw(
    request: Request,
    withdraw_req: WithdrawRequest,
    current_user: dict = Depends(get_current_user)
):
    """Withdraw funds from wallet."""
    if not is_currency_supported(withdraw_req.currency):
        raise HTTPException(status_code=400, detail="Unsupported currency")
    
    try:
        # Check balance
        wallet = get_user_wallet(current_user["id"], withdraw_req.currency)
        if not wallet or wallet["balance"] < withdraw_req.amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        # Get current price
        if withdraw_req.currency != "USD":
            price = await get_crypto_price(withdraw_req.currency)
        else:
            price = 1.0
        
        # Update wallet
        update_wallet_balance(current_user["id"], withdraw_req.currency, -withdraw_req.amount)
        
        # Record transaction
        tx_id = record_transaction(
            user_id=current_user["id"],
            tx_type="withdrawal",
            currency=withdraw_req.currency,
            amount=withdraw_req.amount,
            status="completed",
            description=f"Withdraw {withdraw_req.amount} {withdraw_req.currency}",
            metadata={"price_usd": price}
        )
        
        return {
            "success": True,
            "transaction_id": tx_id,
            "currency": withdraw_req.currency,
            "amount": withdraw_req.amount,
            "message": f"Successfully withdrew {withdraw_req.amount} {withdraw_req.currency}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Withdrawal failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Withdrawal failed")

@app.post("/transfer")
@limiter.limit("15/minute")
async def transfer(
    request: Request,
    transfer_req: TransferRequest,
    current_user: dict = Depends(get_current_user)
):
    """Transfer/convert between currencies."""
    if not is_currency_supported(transfer_req.from_currency) or not is_currency_supported(transfer_req.to_currency):
        raise HTTPException(status_code=400, detail="Unsupported currency")
    
    if transfer_req.from_currency == transfer_req.to_currency:
        raise HTTPException(status_code=400, detail="Cannot transfer to same currency")
    
    try:
        # Check balance
        wallet = get_user_wallet(current_user["id"], transfer_req.from_currency)
        if not wallet or wallet["balance"] < transfer_req.amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        # Get prices
        from_price = 1.0 if transfer_req.from_currency == "USD" else await get_crypto_price(transfer_req.from_currency)
        to_price = 1.0 if transfer_req.to_currency == "USD" else await get_crypto_price(transfer_req.to_currency)
        
        # Calculate conversion
        usd_value = transfer_req.amount * from_price
        to_amount = usd_value / to_price
        
        # Execute transfer
        update_wallet_balance(current_user["id"], transfer_req.from_currency, -transfer_req.amount)
        update_wallet_balance(current_user["id"], transfer_req.to_currency, to_amount)
        
        # Record transactions
        record_transaction(
            user_id=current_user["id"],
            tx_type="transfer_out",
            currency=transfer_req.from_currency,
            amount=transfer_req.amount,
            description=f"Transfer to {transfer_req.to_currency}",
            metadata={"to_currency": transfer_req.to_currency, "to_amount": to_amount}
        )
        
        record_transaction(
            user_id=current_user["id"],
            tx_type="transfer_in",
            currency=transfer_req.to_currency,
            amount=to_amount,
            description=f"Transfer from {transfer_req.from_currency}",
            metadata={"from_currency": transfer_req.from_currency, "from_amount": transfer_req.amount}
        )
        
        return {
            "success": True,
            "from_currency": transfer_req.from_currency,
            "from_amount": transfer_req.amount,
            "to_currency": transfer_req.to_currency,
            "to_amount": round(to_amount, 8),
            "exchange_rate": round(to_amount / transfer_req.amount, 8)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transfer failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Transfer failed")

@app.get("/transactions")
async def get_transactions(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get user transaction history."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        SELECT * FROM transactions 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
        ''', (current_user["id"], limit))
        
        transactions = [dict(row) for row in cursor.fetchall()]
        
        return {
            "transactions": transactions,
            "count": len(transactions)
        }
        
    finally:
        conn.close()

# ===========================
# SPORTS BETTING ENDPOINTS
# ===========================

@app.post("/bets")
@limiter.limit("30/minute")
async def place_bet(
    request: Request,
    bet: BetCreate,
    current_user: dict = Depends(get_current_user)
):
    """Place a sports bet."""
    try:
        # Validate currency and balance
        if not is_currency_supported(bet.stake_currency):
            raise HTTPException(status_code=400, detail="Unsupported currency")
        
        wallet = get_user_wallet(current_user["id"], bet.stake_currency)
        if not wallet or wallet["balance"] < bet.stake_amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        # Calculate potential payout
        potential_payout = bet.stake_amount * bet.odds
        
        # Deduct stake from wallet
        update_wallet_balance(current_user["id"], bet.stake_currency, -bet.stake_amount)
        
        # Create bet record
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO bets (user_id, bet_type, sport, event_name, selection, odds, 
                         stake_amount, stake_currency, potential_payout, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (current_user["id"], bet.bet_type, bet.sport, bet.event_name, 
              bet.selection, bet.odds, bet.stake_amount, bet.stake_currency, potential_payout))
        
        bet_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Record transaction
        record_transaction(
            user_id=current_user["id"],
            tx_type="bet_placed",
            currency=bet.stake_currency,
            amount=bet.stake_amount,
            reference_id=str(bet_id),
            description=f"Bet on {bet.event_name}"
        )
        
        return {
            "success": True,
            "bet_id": bet_id,
            "stake_amount": bet.stake_amount,
            "potential_payout": round(potential_payout, 2),
            "status": "pending"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bet placement failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to place bet")

@app.get("/bets/history")
async def get_bet_history(
    limit: int = 50,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get user bet history."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if status:
            cursor.execute('''
            SELECT * FROM bets 
            WHERE user_id = ? AND status = ?
            ORDER BY placed_at DESC 
            LIMIT ?
            ''', (current_user["id"], status, limit))
        else:
            cursor.execute('''
            SELECT * FROM bets 
            WHERE user_id = ? 
            ORDER BY placed_at DESC 
            LIMIT ?
            ''', (current_user["id"], limit))
        
        bets = [dict(row) for row in cursor.fetchall()]
        
        return {
            "bets": bets,
            "count": len(bets)
        }
        
    finally:
        conn.close()

@app.post("/bets/{bet_id}/resolve")
async def resolve_bet(
    bet_id: int,
    result: str,
    current_user: dict = Depends(get_current_user)
):
    """Resolve a bet (admin/simulation endpoint)."""
    if result not in ["won", "lost", "void"]:
        raise HTTPException(status_code=400, detail="Invalid result")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get bet
        cursor.execute("SELECT * FROM bets WHERE id = ? AND user_id = ?", (bet_id, current_user["id"]))
        bet = cursor.fetchone()
        
        if not bet:
            raise HTTPException(status_code=404, detail="Bet not found")
        
        if bet["status"] != "pending":
            raise HTTPException(status_code=400, detail="Bet already settled")
        
        bet = dict(bet)
        settled_amount = 0.0
        
        if result == "won":
            settled_amount = bet["potential_payout"]
            update_wallet_balance(current_user["id"], bet["stake_currency"], settled_amount)
        elif result == "void":
            settled_amount = bet["stake_amount"]
            update_wallet_balance(current_user["id"], bet["stake_currency"], settled_amount)
        
        # Update bet
        cursor.execute('''
        UPDATE bets 
        SET status = 'settled', result = ?, settled_amount = ?, settled_at = CURRENT_TIMESTAMP
        WHERE id = ?
        ''', (result, settled_amount, bet_id))
        
        conn.commit()
        
        # Record transaction if won or void
        if result in ["won", "void"]:
            record_transaction(
                user_id=current_user["id"],
                tx_type="bet_won" if result == "won" else "bet_void",
                currency=bet["stake_currency"],
                amount=settled_amount,
                reference_id=str(bet_id),
                description=f"Bet settled: {result}"
            )
        
        return {
            "success": True,
            "bet_id": bet_id,
            "result": result,
            "settled_amount": settled_amount
        }
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Bet resolution failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to resolve bet")
    finally:
        conn.close()

# ===========================
# CASINO ENDPOINTS
# ===========================

@app.post("/casino/play")
@limiter.limit("30/minute")
async def casino_play(
    request: Request,
    play_req: CasinoPlayRequest,
    current_user: dict = Depends(get_current_user)
):
    """Play casino games."""
    try:
        # Validate currency and balance
        if not is_currency_supported(play_req.bet_currency):
            raise HTTPException(status_code=400, detail="Unsupported currency")
        
        wallet = get_user_wallet(current_user["id"], play_req.bet_currency)
        if not wallet or wallet["balance"] < play_req.bet_amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        # Deduct bet from wallet
        update_wallet_balance(current_user["id"], play_req.bet_currency, -play_req.bet_amount)
        
        # Simulate casino game (slots example)
        game_result = {}
        payout = 0.0
        result_status = "loss"
        
        if play_req.game.lower() == "slots":
            # Simple slots simulation: 3 reels
            reels = [random.choice(["🍒", "🍋", "💎", "7️⃣"]) for _ in range(3)]
            game_result["reels"] = reels
            
            if len(set(reels)) == 1:  # All match
                multiplier = random.uniform(5, 20)
                payout = play_req.bet_amount * multiplier
                result_status = "win"
            elif len(set(reels)) == 2:  # Two match
                multiplier = random.uniform(1.5, 3)
                payout = play_req.bet_amount * multiplier
                result_status = "win"
            
            game_result["multiplier"] = multiplier if result_status == "win" else 0
        
        # Credit winnings if any
        if payout > 0:
            update_wallet_balance(current_user["id"], play_req.bet_currency, payout)
        
        # Record bet
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO bets (user_id, bet_type, sport, event_name, selection, odds, 
                         stake_amount, stake_currency, potential_payout, status, result, settled_amount)
        VALUES (?, 'casino', ?, ?, ?, 0, ?, ?, ?, 'settled', ?, ?)
        ''', (current_user["id"], play_req.game, play_req.game, "casino_play", 
              play_req.bet_amount, play_req.bet_currency, payout, result_status, payout))
        
        bet_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Record transaction
        record_transaction(
            user_id=current_user["id"],
            tx_type="casino_play",
            currency=play_req.bet_currency,
            amount=play_req.bet_amount,
            reference_id=str(bet_id),
            description=f"Casino play: {play_req.game}",
            metadata={"game": play_req.game, "result": result_status, "payout": payout}
        )
        
        return {
            "success": True,
            "bet_id": bet_id,
            "game": play_req.game,
            "result": result_status,
            "game_result": game_result,
            "bet_amount": play_req.bet_amount,
            "payout": round(payout, 2),
            "net_profit": round(payout - play_req.bet_amount, 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Casino play failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Casino play failed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)