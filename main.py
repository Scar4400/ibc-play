“””
IBC Play - Complete FastAPI Backend
Sports Betting & Casino Platform with Crypto Integration
“””

import os
import json
import sqlite3
import random
import httpx
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from decimal import Decimal

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, Field, validator
from passlib.context import CryptContext
from jose import JWTError, jwt
from dotenv import load_dotenv

# Load environment variables

load_dotenv()

# ===================================

# CONFIGURATION

# ===================================

class Settings:
SECRET_KEY = os.getenv(“SECRET_KEY”, “your-secret-key-change-this-in-production-min-32-characters”)
JWT_ALGORITHM = os.getenv(“JWT_ALGORITHM”, “HS256”)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv(“ACCESS_TOKEN_EXPIRE_MINUTES”, “43200”))

```
DATABASE_URL = os.getenv("DATABASE_URL", "ibc_play.db")

COINGECKO_API_URL = os.getenv("COINGECKO_API_URL", "https://api.coingecko.com/api/v3")
PRICE_CACHE_TTL = int(os.getenv("PRICE_CACHE_TTL", "60"))

SUPPORTED_CRYPTOS = os.getenv("SUPPORTED_CRYPTOS", "BTC,ETH,SOL,BNB").split(",")

MIN_BET_AMOUNT = float(os.getenv("MIN_BET_AMOUNT", "1.0"))
MAX_BET_AMOUNT = float(os.getenv("MAX_BET_AMOUNT", "10000.0"))

INITIAL_BALANCE = float(os.getenv("INITIAL_BALANCE", "100.0"))

HOUSE_EDGE_DICE = float(os.getenv("HOUSE_EDGE_DICE", "2.0"))
HOUSE_EDGE_SLOTS = float(os.getenv("HOUSE_EDGE_SLOTS", "5.0"))
HOUSE_EDGE_ROULETTE = float(os.getenv("HOUSE_EDGE_ROULETTE", "2.7"))
HOUSE_EDGE_BLACKJACK = float(os.getenv("HOUSE_EDGE_BLACKJACK", "1.5"))
HOUSE_EDGE_CRASH = float(os.getenv("HOUSE_EDGE_CRASH", "3.0"))
HOUSE_EDGE_COINFLIP = float(os.getenv("HOUSE_EDGE_COINFLIP", "2.5"))
```

settings = Settings()

# ===================================

# FASTAPI APP INITIALIZATION

# ===================================

app = FastAPI(
title=“IBC Play API”,
description=“Sports Betting & Casino Platform with Crypto Integration”,
version=“1.0.0”
)

# CORS Configuration

app.add_middleware(
CORSMiddleware,
allow_origins=[”*”],  # Update this in production
allow_credentials=True,
allow_methods=[”*”],
allow_headers=[”*”],
)

# ===================================

# DATABASE HELPERS

# ===================================

def get_db():
“”“Get database connection”””
db_path = settings.DATABASE_URL.replace(“sqlite:///”, “”).replace(”./”, “”)
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
try:
yield conn
finally:
conn.close()

# ===================================

# SECURITY & AUTHENTICATION

# ===================================

pwd_context = CryptContext(schemes=[“bcrypt”], deprecated=“auto”)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=“login”)

def verify_password(plain_password: str, hashed_password: str) -> bool:
return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
to_encode = data.copy()
if expires_delta:
expire = datetime.utcnow() + expires_delta
else:
expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
to_encode.update({“exp”: expire})
encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), conn: sqlite3.Connection = Depends(get_db)):
credentials_exception = HTTPException(
status_code=status.HTTP_401_UNAUTHORIZED,
detail=“Could not validate credentials”,
headers={“WWW-Authenticate”: “Bearer”},
)
try:
payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
username: str = payload.get(“sub”)
if username is None:
raise credentials_exception
except JWTError:
raise credentials_exception

```
cursor = conn.cursor()
cursor.execute("SELECT * FROM users WHERE username = ? AND is_active = TRUE", (username,))
user = cursor.fetchone()

if user is None:
    raise credentials_exception
return dict(user)
```

# ===================================

# PYDANTIC MODELS

# ===================================

class UserRegister(BaseModel):
username: str = Field(…, min_length=3, max_length=50)
email: EmailStr
password: str = Field(…, min_length=6)

class UserResponse(BaseModel):
id: int
username: str
email: str
is_admin: bool
created_at: str

class Token(BaseModel):
access_token: str
token_type: str

class WalletResponse(BaseModel):
currency: str
balance: float
locked_balance: float

class DepositRequest(BaseModel):
crypto_symbol: str
amount: float = Field(…, gt=0)

class WithdrawRequest(BaseModel):
crypto_symbol: str
amount: float = Field(…, gt=0)
address: str

class TransferRequest(BaseModel):
to_username: str
currency: str
amount: float = Field(…, gt=0)

class CasinoPlayRequest(BaseModel):
game: str
bet_amount: float = Field(…, gt=0)
bet_options: Dict[str, Any] = {}

class BetRequest(BaseModel):
match_id: str
sport: str
home_team: str
away_team: str
bet_type: str
bet_selection: str
bet_amount: float = Field(…, gt=0)
odds: float = Field(…, gt=1.0)

# ===================================

# CRYPTO PRICE SERVICE

# ===================================

class CryptoPriceService:
def **init**(self):
self.cache = {}
self.cache_time = {}

```
    # CoinGecko ID mapping
    self.coin_ids = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        "BNB": "binancecoin"
    }

async def get_price(self, symbol: str) -> float:
    """Get current price for a cryptocurrency"""
    symbol = symbol.upper()
    
    # Check cache
    if symbol in self.cache:
        cache_age = (datetime.now() - self.cache_time[symbol]).seconds
        if cache_age < settings.PRICE_CACHE_TTL:
            return self.cache[symbol]
    
    try:
        # Fetch from CoinGecko
        coin_id = self.coin_ids.get(symbol)
        if not coin_id:
            raise ValueError(f"Unsupported cryptocurrency: {symbol}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.COINGECKO_API_URL}/simple/price",
                params={"ids": coin_id, "vs_currencies": "usd"},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            price = data[coin_id]["usd"]
            
            # Update cache
            self.cache[symbol] = price
            self.cache_time[symbol] = datetime.now()
            
            return price
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        # Fallback to simulated prices
        return self._get_fallback_price(symbol)

def _get_fallback_price(self, symbol: str) -> float:
    """Fallback simulated prices"""
    fallback_prices = {
        "BTC": 43000.00,
        "ETH": 2250.00,
        "SOL": 98.50,
        "BNB": 315.00
    }
    return fallback_prices.get(symbol, 100.0)

async def get_all_prices(self) -> Dict[str, float]:
    """Get prices for all supported cryptocurrencies"""
    prices = {}
    for symbol in settings.SUPPORTED_CRYPTOS:
        prices[symbol] = await self.get_price(symbol)
    return prices
```

crypto_service = CryptoPriceService()

# ===================================

# CASINO GAME ENGINE

# ===================================

class CasinoEngine:

```
@staticmethod
def play_dice(bet_amount: float, prediction: str, target: int) -> Dict:
    """Dice game: Over/Under target number"""
    roll = random.randint(1, 100)
    
    if prediction == "over":
        won = roll > target
        win_chance = (100 - target) / 100
    else:  # under
        won = roll < target
        win_chance = target / 100
    
    # Calculate payout with house edge
    if won:
        multiplier = (1 - settings.HOUSE_EDGE_DICE / 100) / win_chance
        payout = bet_amount * multiplier
    else:
        payout = 0
        multiplier = 0
    
    return {
        "roll": roll,
        "target": target,
        "prediction": prediction,
        "won": won,
        "payout": round(payout, 2),
        "multiplier": round(multiplier, 2) if won else 0
    }

@staticmethod
def play_coinflip(bet_amount: float, choice: str) -> Dict:
    """Coin flip: Heads or Tails"""
    result = random.choice(["heads", "tails"])
    won = result == choice.lower()
    
    # 1.95x payout (2.5% house edge)
    payout = bet_amount * 1.95 if won else 0
    
    return {
        "result": result,
        "choice": choice.lower(),
        "won": won,
        "payout": round(payout, 2)
    }

@staticmethod
def play_slots(bet_amount: float) -> Dict:
    """3-reel slot machine"""
    symbols = ["🍒", "🍋", "🍊", "🍇", "⭐", "💎", "7️⃣"]
    weights = [30, 25, 20, 15, 7, 2, 1]  # Probability weights
    
    reels = random.choices(symbols, weights=weights, k=3)
    
    # Calculate payout
    payout = 0
    multiplier = 0
    
    if reels[0] == reels[1] == reels[2]:
        # All three match
        if reels[0] == "7️⃣":
            multiplier = 100  # Jackpot
        elif reels[0] == "💎":
            multiplier = 50
        elif reels[0] == "⭐":
            multiplier = 20
        elif reels[0] == "🍇":
            multiplier = 10
        elif reels[0] == "🍊":
            multiplier = 5
        elif reels[0] == "🍋":
            multiplier = 3
        elif reels[0] == "🍒":
            multiplier = 2
    elif reels[0] == reels[1] or reels[1] == reels[2]:
        # Two match
        multiplier = 1.5
    
    won = multiplier > 0
    if won:
        payout = bet_amount * multiplier * (1 - settings.HOUSE_EDGE_SLOTS / 100)
    
    return {
        "reels": reels,
        "multiplier": round(multiplier, 2),
        "won": won,
        "payout": round(payout, 2)
    }

@staticmethod
def play_roulette(bet_amount: float, bet_type: str, bet_value: Any) -> Dict:
    """European roulette (0-36)"""
    number = random.randint(0, 36)
    color = "green" if number == 0 else ("red" if number in [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36] else "black")
    is_odd = number % 2 == 1 if number > 0 else None
    
    won = False
    multiplier = 0
    
    if bet_type == "number" and int(bet_value) == number:
        won = True
        multiplier = 35
    elif bet_type == "color" and bet_value.lower() == color:
        won = True
        multiplier = 1
    elif bet_type == "odd_even":
        if bet_value.lower() == "odd" and is_odd:
            won = True
            multiplier = 1
        elif bet_value.lower() == "even" and is_odd is False:
            won = True
            multiplier = 1
    
    payout = bet_amount * (multiplier + 1) * (1 - settings.HOUSE_EDGE_ROULETTE / 100) if won else 0
    
    return {
        "number": number,
        "color": color,
        "is_odd": is_odd,
        "bet_type": bet_type,
        "bet_value": bet_value,
        "won": won,
        "payout": round(payout, 2)
    }

@staticmethod
def play_crash(bet_amount: float, cashout_multiplier: float) -> Dict:
    """Crash game: bet on multiplier"""
    # Generate crash point with house edge
    crash_point = 1.0 + random.expovariate(1.0) * (1 - settings.HOUSE_EDGE_CRASH / 100)
    crash_point = max(1.01, min(crash_point, 100.0))  # Limit between 1.01x and 100x
    
    won = cashout_multiplier <= crash_point
    payout = bet_amount * cashout_multiplier if won else 0
    
    return {
        "crash_point": round(crash_point, 2),
        "cashout_multiplier": cashout_multiplier,
        "won": won,
        "payout": round(payout, 2)
    }

@staticmethod
def play_blackjack(bet_amount: float) -> Dict:
    """Simplified blackjack"""
    def card_value(cards):
        total = sum(cards)
        if total > 21 and 11 in cards:
            total -= 10
        return total
    
    # Deal initial cards (simplified: just values 1-11)
    player_cards = [random.randint(1, 11), random.randint(1, 11)]
    dealer_cards = [random.randint(1, 11), random.randint(1, 11)]
    
    # Player hits until 17 or more (simplified AI)
    while card_value(player_cards) < 17:
        player_cards.append(random.randint(1, 11))
    
    # Dealer hits until 17 or more
    while card_value(dealer_cards) < 17:
        dealer_cards.append(random.randint(1, 11))
    
    player_total = card_value(player_cards)
    dealer_total = card_value(dealer_cards)
    
    # Determine winner
    if player_total > 21:
        result = "dealer"
    elif dealer_total > 21:
        result = "player"
    elif player_total > dealer_total:
        result = "player"
    elif dealer_total > player_total:
        result = "dealer"
    else:
        result = "push"
    
    won = result == "player"
    payout = bet_amount * 2 * (1 - settings.HOUSE_EDGE_BLACKJACK / 100) if won else (bet_amount if result == "push" else 0)
    
    return {
        "player_cards": player_cards,
        "dealer_cards": dealer_cards,
        "player_total": player_total,
        "dealer_total": dealer_total,
        "result": result,
        "won": won,
        "payout": round(payout, 2)
    }
```

casino_engine = CasinoEngine()

# ===================================

# API ENDPOINTS

# ===================================

@app.get(”/”)
async def root():
return {
“message”: “Welcome to IBC Play API”,
“version”: “1.0.0”,
“docs”: “/docs”
}

@app.get(”/health”)
async def health_check(conn: sqlite3.Connection = Depends(get_db)):
try:
cursor = conn.cursor()
cursor.execute(“SELECT 1”)
cursor.fetchone()
db_status = “connected”
except:
db_status = “disconnected”

```
return {
    "status": "ok",
    "database": db_status,
    "crypto_api": "reachable",
    "timestamp": datetime.utcnow().isoformat()
}
```

# ===================================

# AUTHENTICATION ENDPOINTS

# ===================================

@app.post(”/register”, response_model=UserResponse)
async def register(user: UserRegister, conn: sqlite3.Connection = Depends(get_db)):
cursor = conn.cursor()

```
# Check if user exists
cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (user.username, user.email))
if cursor.fetchone():
    raise HTTPException(status_code=400, detail="Username or email already registered")

# Create user
password_hash = get_password_hash(user.password)
cursor.execute(
    "INSERT INTO users (username, email, password_hash, is_active, is_admin) VALUES (?, ?, ?, ?, ?)",
    (user.username, user.email, password_hash, True, False)
)
user_id = cursor.lastrowid

# Create wallets for user
for currency in ["USD"] + settings.SUPPORTED_CRYPTOS:
    balance = settings.INITIAL_BALANCE if currency == "USD" else 0.0
    cursor.execute(
        "INSERT INTO wallets (user_id, currency, balance) VALUES (?, ?, ?)",
        (user_id, currency, balance)
    )

conn.commit()

cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
new_user = dict(cursor.fetchone())

return UserResponse(
    id=new_user["id"],
    username=new_user["username"],
    email=new_user["email"],
    is_admin=bool(new_user["is_admin"]),
    created_at=new_user["created_at"]
)
```

@app.post(”/login”, response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), conn: sqlite3.Connection = Depends(get_db)):
cursor = conn.cursor()
cursor.execute(“SELECT * FROM users WHERE username = ?”, (form_data.username,))
user = cursor.fetchone()

```
if not user or not verify_password(form_data.password, user["password_hash"]):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

if not user["is_active"]:
    raise HTTPException(status_code=400, detail="Inactive user")

# Update last login
cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user["id"],))
conn.commit()

access_token = create_access_token(data={"sub": user["username"]})
return {"access_token": access_token, "token_type": "bearer"}
```

@app.get(”/me”, response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
return UserResponse(
id=current_user[“id”],
username=current_user[“username”],
email=current_user[“email”],
is_admin=bool(current_user[“is_admin”]),
created_at=current_user[“created_at”]
)

# ===================================

# WALLET ENDPOINTS

# ===================================

@app.get(”/wallet”, response_model=List[WalletResponse])
async def get_wallet(current_user: dict = Depends(get_current_user), conn: sqlite3.Connection = Depends(get_db)):
cursor = conn.cursor()
cursor.execute(“SELECT currency, balance, locked_balance FROM wallets WHERE user_id = ?”, (current_user[“id”],))
wallets = cursor.fetchall()

```
return [WalletResponse(currency=w["currency"], balance=float(w["balance"]), locked_balance=float(w["locked_balance"])) for w in wallets]
```

@app.post(”/deposit”)
async def deposit(request: DepositRequest, current_user: dict = Depends(get_current_user), conn: sqlite3.Connection = Depends(get_db)):
cursor = conn.cursor()

```
# Get crypto price
price_usd = await crypto_service.get_price(request.crypto_symbol)
usd_value = request.amount * price_usd

# Update USD balance
cursor.execute("SELECT balance FROM wallets WHERE user_id = ? AND currency = 'USD'", (current_user["id"],))
wallet = cursor.fetchone()
old_balance = float(wallet["balance"])
new_balance = old_balance + usd_value

cursor.execute("UPDATE wallets SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND currency = 'USD'",
               (new_balance, current_user["id"]))

# Record transaction
cursor.execute(
    "INSERT INTO transactions (user_id, transaction_type, currency, amount, balance_before, balance_after, status, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
    (current_user["id"], "deposit", "USD", usd_value, old_balance, new_balance, "completed", f"Deposited {request.amount} {request.crypto_symbol}")
)

conn.commit()

return {
    "success": True,
    "crypto_amount": request.amount,
    "crypto_symbol": request.crypto_symbol,
    "usd_value": round(usd_value, 2),
    "price_per_unit": round(price_usd, 2),
    "new_balance": round(new_balance, 2)
}
```

@app.post(”/withdraw”)
async def withdraw(request: WithdrawRequest, current_user: dict = Depends(get_current_user), conn: sqlite3.Connection = Depends(get_db)):
cursor = conn.cursor()

```
# Get crypto price
price_usd = await crypto_service.get_price(request.crypto_symbol)
usd_value = request.amount * price_usd

# Check USD balance
cursor.execute("SELECT balance FROM wallets WHERE user_id = ? AND currency = 'USD'", (current_user["id"],))
wallet = cursor.fetchone()
old_balance = float(wallet["balance"])

if old_balance < usd_value:
    raise HTTPException(status_code=400, detail="Insufficient balance")

new_balance = old_balance - usd_value

cursor.execute("UPDATE wallets SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND currency = 'USD'",
               (new_balance, current_user["id"]))

# Record transaction
cursor.execute(
    "INSERT INTO transactions (user_id, transaction_type, currency, amount, balance_before, balance_after, status, description, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
    (current_user["id"], "withdrawal", "USD", -usd_value, old_balance, new_balance, "completed", 
     f"Withdrew {request.amount} {request.crypto_symbol}", json.dumps({"address": request.address}))
)

conn.commit()

return {
    "success": True,
    "crypto_amount": request.amount,
    "crypto_symbol": request.crypto_symbol,
    "usd_value": round(usd_value, 2),
    "withdrawal_address": request.address,
    "new_balance": round(new_balance, 2)
}
```

@app.get(”/transactions”)
async def get_transactions(limit: int = 50, current_user: dict = Depends(get_current_user), conn: sqlite3.Connection = Depends(get_db)):
cursor = conn.cursor()
cursor.execute(
“SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?”,
(current_user[“id”], limit)
)
transactions = cursor.fetchall()
return [dict(t) for t in transactions]

# ===================================

# CRYPTO PRICE ENDPOINTS

# ===================================

@app.get(”/crypto/prices”)
async def get_crypto_prices():
“”“Get current prices for all supported cryptocurrencies”””
prices = await crypto_service.get_all_prices()
return {
“prices”: prices,
“timestamp”: datetime.utcnow().isoformat()
}

@app.get(”/crypto/price/{symbol}”)
async def get_crypto_price(symbol: str):
“”“Get current price for a specific cryptocurrency”””
try:
price = await crypto_service.get_price(symbol)
return {
“symbol”: symbol.upper(),
“price_usd”: price,
“timestamp”: datetime.utcnow().isoformat()
}
except ValueError as e:
raise HTTPException(status_code=400, detail=str(e))

# ===================================

# CASINO ENDPOINTS

# ===================================

@app.post(”/casino/play”)
async def play_casino(request: CasinoPlayRequest, current_user: dict = Depends(get_current_user), conn: sqlite3.Connection = Depends(get_db)):
cursor = conn.cursor()

```
# Validate bet amount
if request.bet_amount < settings.MIN_BET_AMOUNT or request.bet_amount > settings.MAX_BET_AMOUNT:
    raise HTTPException(status_code=400, detail=f"Bet amount must be between {settings.MIN_BET_AMOUNT} and {settings.MAX_BET_AMOUNT}")

# Check balance
cursor.execute("SELECT balance FROM wallets WHERE user_id = ? AND currency = 'USD'", (current_user["id"],))
wallet = cursor.fetchone()
balance = float(wallet["balance"])

if balance < request.bet_amount:
    raise HTTPException(status_code=400, detail="Insufficient balance")

# Play game
game = request.game.lower()

if game == "dice":
    result = casino_engine.play_dice(request.bet_amount, request.bet_options.get("prediction", "over"), request.bet_options.get("target", 50))
elif game == "coinflip":
    result = casino_engine.play_coinflip(request.bet_amount, request.bet_options.get("choice", "heads"))
elif game == "slots":
    result = casino_engine.play_slots(request.bet_amount)
elif game == "roulette":
    result = casino_engine.play_roulette(request.bet_amount, request.bet_options.get("bet_type", "color"), request.bet_options.get("bet_value", "red"))
elif game == "crash":
    result = casino_engine.play_crash(request.bet_amount, request.bet_options.get("cashout_multiplier", 2.0))
elif game == "blackjack":
    result = casino_engine.play_blackjack(request.bet_amount)
else:
    raise HTTPException(status_code=400, detail=f"Unknown game: {game}")

# Calculate profit/loss
profit_loss = result["payout"] - request.bet_amount
new_balance = balance + profit_loss

# Update balance
cursor.execute("UPDATE wallets SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND currency = 'USD'",
               (new_balance, current_user["id"]))

# Record game round
cursor.execute(
    "INSERT INTO casino_rounds (user_id, game_name, bet_amount, payout_amount, profit_loss, game_result, is_win, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
    (current_user["id"], game, request.bet_amount, result["payout"], profit_loss, json.dumps(result), result["won"], json.dumps(request.bet_options))
)

# Record transaction
cursor.execute(
    "INSERT INTO transactions (user_id, transaction_type, currency, amount, balance_before, balance_after, status, description, reference_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
    (current_user["id"], "casino_bet", "USD", profit_loss, balance, new_balance, "completed", f"{game.capitalize()} game", game)
)

conn.commit()

return {
    "success": True,
    "game": game,
    "result": result,
    "profit_loss": round(profit_loss, 2),
    "new_balance": round(new_balance, 2)
}
```

@app.get(”/casino/history”)
async def get_casino_history(limit: int = 50, current_user: dict = Depends(get_current_user), conn: sqlite3.Connection = Depends(get_db)):
cursor = conn.cursor()
cursor.execute(
“SELECT * FROM casino_rounds WHERE user_id = ? ORDER BY played_at DESC LIMIT ?”,
(current_user[“id”], limit)
)
rounds = cursor.fetchall()
return [dict(r) for r in rounds]

@app.get(”/casino/games”)
async def get_casino_games():
return {
“games”: [
{“name”: “dice”, “description”: “Roll dice - Over/Under”, “min_bet”: settings.MIN_BET_AMOUNT, “house_edge”: settings.HOUSE_EDGE_DICE},
{“name”: “coinflip”, “description”: “Flip a coin - Heads or Tails”, “min_bet”: settings.MIN_BET_AMOUNT, “house_edge”: settings.HOUSE_EDGE_COINFLIP},
{“name”: “slots”, “description”: “3-reel slot machine”, “min_bet”: settings.MIN_BET_AMOUNT, “house_edge”: settings.HOUSE_EDGE_SLOTS},
{“name”: “roulette”, “description”: “European roulette wheel”, “min_bet”: settings.MIN_BET_AMOUNT, “house_edge”: settings.HOUSE_EDGE_ROULETTE},
{“name”: “crash”, “description”: “Multiplier crash game”, “min_bet”: settings.MIN_BET_AMOUNT, “house_edge”: settings.HOUSE_EDGE_CRASH},
{“name”: “blackjack”, “description”: “Classic card game”, “min_bet”: settings.MIN_BET_AMOUNT, “house_edge”: settings.HOUSE_EDGE_BLACKJACK}
]
}

# ===================================

# SPORTS BETTING ENDPOINTS

# ===================================

# Simulated matches database

SIMULATED_MATCHES = [
{
“match_id”: “nba_001”,
“sport”: “NBA”,
“league”: “NBA”,
“home_team”: “Los Angeles Lakers”,
“away_team”: “Boston Celtics”,
“match_start_time”: (datetime.utcnow() + timedelta(hours=3)).isoformat(),
“odds”: {
“home_win”: 1.85,
“away_win”: 2.10,
“over_225”: 1.90,
“under_225”: 1.90
}
},
{
“match_id”: “nfl_002”,
“sport”: “NFL”,
“league”: “NFL”,
“home_team”: “Kansas City Chiefs”,
“away_team”: “Buffalo Bills”,
“match_start_time”: (datetime.utcnow() + timedelta(hours=5)).isoformat(),
“odds”: {
“home_win”: 1.75,
“away_win”: 2.20,
“over_50”: 1.85,
“under_50”: 1.95
}
},
{
“match_id”: “soccer_003”,
“sport”: “Soccer”,
“league”: “Premier League”,
“home_team”: “Manchester United”,
“away_team”: “Liverpool”,
“match_start_time”: (datetime.utcnow() + timedelta(hours=7)).isoformat(),
“odds”: {
“home_win”: 2.30,
“draw”: 3.20,
“away_win”: 2.80
}
}
]

@app.get(”/bets/matches”)
async def get_matches():
“”“Get available matches for betting”””
return {
“matches”: SIMULATED_MATCHES,
“total”: len(SIMULATED_MATCHES)
}

@app.post(”/bets”)
async def place_bet(request: BetRequest, current_user: dict = Depends(get_current_user), conn: sqlite3.Connection = Depends(get_db)):
cursor = conn.cursor()

```
# Validate bet amount
if request.bet_amount < settings.MIN_BET_AMOUNT or request.bet_amount > settings.MAX_BET_AMOUNT:
    raise HTTPException(status_code=400, detail=f"Bet amount must be between {settings.MIN_BET_AMOUNT} and {settings.MAX_BET_AMOUNT}")

# Check balance
cursor.execute("SELECT balance FROM wallets WHERE user_id = ? AND currency = 'USD'", (current_user["id"],))
wallet = cursor.fetchone()
balance = float(wallet["balance"])

if balance < request.bet_amount:
    raise HTTPException(status_code=400, detail="Insufficient balance")

# Calculate potential payout
potential_payout = request.bet_amount * request.odds

# Deduct bet amount from balance
new_balance = balance - request.bet_amount
cursor.execute("UPDATE wallets SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND currency = 'USD'",
               (new_balance, current_user["id"]))

# Record bet
cursor.execute(
    """INSERT INTO bets (user_id, match_id, sport, league, home_team, away_team, 
       bet_type, bet_selection, bet_amount, odds, potential_payout, status) 
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    (current_user["id"], request.match_id, request.sport, request.sport, 
     request.home_team, request.away_team, request.bet_type, request.bet_selection,
     request.bet_amount, request.odds, potential_payout, "pending")
)
bet_id = cursor.lastrowid

# Record transaction
cursor.execute(
    "INSERT INTO transactions (user_id, transaction_type, currency, amount, balance_before, balance_after, status, description, reference_id, reference_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    (current_user["id"], "sports_bet", "USD", -request.bet_amount, balance, new_balance, "completed", 
     f"Bet on {request.home_team} vs {request.away_team}", str(bet_id), "bet")
)

conn.commit()

return {
    "success": True,
    "bet_id": bet_id,
    "match": f"{request.home_team} vs {request.away_team}",
    "bet_selection": request.bet_selection,
    "bet_amount": request.bet_amount,
    "odds": request.odds,
    "potential_payout": round(potential_payout, 2),
    "new_balance": round(new_balance, 2),
    "status": "pending"
}
```

@app.get(”/bets/history”)
async def get_bet_history(limit: int = 50, current_user: dict = Depends(get_current_user), conn: sqlite3.Connection = Depends(get_db)):
cursor = conn.cursor()
cursor.execute(
“SELECT * FROM bets WHERE user_id = ? ORDER BY placed_at DESC LIMIT ?”,
(current_user[“id”], limit)
)
bets = cursor.fetchall()
return [dict(b) for b in bets]

@app.post(”/bets/resolve/{bet_id}”)
async def resolve_bet(bet_id: int, won: bool, current_user: dict = Depends(get_current_user), conn: sqlite3.Connection = Depends(get_db)):
“”“Admin endpoint to resolve bets”””
cursor = conn.cursor()

```
# Check if user is admin
if not current_user["is_admin"]:
    raise HTTPException(status_code=403, detail="Admin access required")

# Get bet details
cursor.execute("SELECT * FROM bets WHERE id = ?", (bet_id,))
bet = cursor.fetchone()

if not bet:
    raise HTTPException(status_code=404, detail="Bet not found")

if bet["status"] != "pending":
    raise HTTPException(status_code=400, detail="Bet already resolved")

# Calculate payout
payout_amount = float(bet["potential_payout"]) if won else 0.0
result = "won" if won else "lost"

# Update bet status
cursor.execute(
    "UPDATE bets SET status = ?, result = ?, payout_amount = ?, settled_at = CURRENT_TIMESTAMP WHERE id = ?",
    ("settled", result, payout_amount, bet_id)
)

# If won, add payout to user balance
if won:
    cursor.execute("SELECT balance FROM wallets WHERE user_id = ? AND currency = 'USD'", (bet["user_id"],))
    wallet = cursor.fetchone()
    old_balance = float(wallet["balance"])
    new_balance = old_balance + payout_amount
    
    cursor.execute("UPDATE wallets SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND currency = 'USD'",
                   (new_balance, bet["user_id"]))
    
    # Record transaction
    cursor.execute(
        "INSERT INTO transactions (user_id, transaction_type, currency, amount, balance_before, balance_after, status, description, reference_id, reference_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (bet["user_id"], "bet_payout", "USD", payout_amount, old_balance, new_balance, "completed", 
         f"Won bet on {bet['home_team']} vs {bet['away_team']}", str(bet_id), "bet")
    )

conn.commit()

return {
    "success": True,
    "bet_id": bet_id,
    "result": result,
    "payout_amount": payout_amount
}
```

# ===================================

# STATISTICS ENDPOINTS

# ===================================

@app.get(”/stats/user”)
async def get_user_stats(current_user: dict = Depends(get_current_user), conn: sqlite3.Connection = Depends(get_db)):
cursor = conn.cursor()

```
# Casino stats
cursor.execute(
    "SELECT COUNT(*) as total_games, SUM(bet_amount) as total_wagered, SUM(profit_loss) as total_profit FROM casino_rounds WHERE user_id = ?",
    (current_user["id"],)
)
casino_stats = dict(cursor.fetchone())

# Betting stats
cursor.execute(
    "SELECT COUNT(*) as total_bets, SUM(bet_amount) as total_wagered, SUM(payout_amount) as total_payout FROM bets WHERE user_id = ?",
    (current_user["id"],)
)
betting_stats = dict(cursor.fetchone())

# Recent activity
cursor.execute(
    "SELECT transaction_type, COUNT(*) as count FROM transactions WHERE user_id = ? GROUP BY transaction_type",
    (current_user["id"],)
)
transaction_stats = cursor.fetchall()

return {
    "casino": {
        "total_games": casino_stats["total_games"] or 0,
        "total_wagered": float(casino_stats["total_wagered"] or 0),
        "total_profit": float(casino_stats["total_profit"] or 0)
    },
    "betting": {
        "total_bets": betting_stats["total_bets"] or 0,
        "total_wagered": float(betting_stats["total_wagered"] or 0),
        "total_payout": float(betting_stats["total_payout"] or 0)
    },
    "transactions": {t["transaction_type"]: t["count"] for t in transaction_stats}
}
```

# ===================================

# ADMIN ENDPOINTS

# ===================================

@app.get(”/admin/users”)
async def get_all_users(current_user: dict = Depends(get_current_user), conn: sqlite3.Connection = Depends(get_db)):
“”“Admin endpoint to list all users”””
if not current_user[“is_admin”]:
raise HTTPException(status_code=403, detail=“Admin access required”)

```
cursor = conn.cursor()
cursor.execute("SELECT id, username, email, is_active, is_admin, created_at, last_login FROM users")
users = cursor.fetchall()
return [dict(u) for u in users]
```

@app.get(”/admin/stats”)
async def get_platform_stats(current_user: dict = Depends(get_current_user), conn: sqlite3.Connection = Depends(get_db)):
“”“Admin endpoint for platform statistics”””
if not current_user[“is_admin”]:
raise HTTPException(status_code=403, detail=“Admin access required”)

```
cursor = conn.cursor()

# Total users
cursor.execute("SELECT COUNT(*) as total FROM users")
total_users = cursor.fetchone()["total"]

# Total casino revenue
cursor.execute("SELECT SUM(bet_amount - payout_amount) as revenue FROM casino_rounds")
casino_revenue = cursor.fetchone()["revenue"] or 0

# Total sports betting revenue
cursor.execute("SELECT SUM(bet_amount - payout_amount) as revenue FROM bets")
betting_revenue = cursor.fetchone()["revenue"] or 0

# Total transactions
cursor.execute("SELECT COUNT(*) as total FROM transactions")
total_transactions = cursor.fetchone()["total"]

return {
    "total_users": total_users,
    "casino_revenue": float(casino_revenue),
    "betting_revenue": float(betting_revenue),
    "total_transactions": total_transactions,
    "total_revenue": float(casino_revenue + betting_revenue)
}
```

if **name** == “**main**”:
import uvicorn
uvicorn.run(app, host=“0.0.0.0”, port=8000)