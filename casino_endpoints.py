"""
Casino API endpoints to be integrated into main FastAPI application.
Add these routes to your main.py file.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import json
import logging

from casino_games import play_casino_game, GAMES
from db_init import get_connection

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

# Create router
casino_router = APIRouter(prefix="/casino", tags=["casino"])

# ===========================
# CASINO ENDPOINTS
# ===========================

@casino_router.get("/games")
async def list_casino_games():
    """List all available casino games."""
    games_info = {
        "dice": {
            "name": "Dice",
            "description": "Predict if roll (0-100) will be over or under target",
            "options": ["prediction (over/under)", "target (0-100)"],
            "min_bet": 1.0,
            "max_multiplier": 99.0
        },
        "coinflip": {
            "name": "Coin Flip",
            "description": "Simple heads or tails",
            "options": ["choice (heads/tails)"],
            "min_bet": 1.0,
            "max_multiplier": 1.95
        },
        "slots": {
            "name": "Slots",
            "description": "3-reel slot machine",
            "options": [],
            "min_bet": 1.0,
            "max_multiplier": 100.0
        },
        "roulette": {
            "name": "Roulette",
            "description": "European roulette (0-36)",
            "options": ["bet_type (red/black/odd/even/number)", "value (for number bets)"],
            "min_bet": 1.0,
            "max_multiplier": 35.0
        },
        "crash": {
            "name": "Crash",
            "description": "Cash out before the crash",
            "options": ["cashout_at (multiplier)"],
            "min_bet": 1.0,
            "max_multiplier": 100.0
        },
        "blackjack": {
            "name": "Blackjack",
            "description": "Beat the dealer (simplified)",
            "options": [],
            "min_bet": 1.0,
            "max_multiplier": 2.0
        }
    }
    
    return {
        "games": games_info,
        "total": len(games_info)
    }

@casino_router.post("/play")
@limiter.limit("60/minute")
async def play_game(
    request: Request,
    play_request: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Play a casino game.
    
    Request body:
    {
        "game": "dice",
        "bet_amount": 10.0,
        "bet_currency": "USD",
        "bet_options": {"prediction": "over", "target": 50}
    }
    """
    try:
        game_name = play_request.get("game")
        bet_amount = play_request.get("bet_amount")
        bet_currency = play_request.get("bet_currency", "USD")
        bet_options = play_request.get("bet_options", {})
        
        # Validation
        if not game_name or game_name not in GAMES:
            raise HTTPException(status_code=400, detail=f"Invalid game. Available: {list(GAMES.keys())}")
        
        if not bet_amount or bet_amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid bet amount")
        
        if bet_amount < 1.0:
            raise HTTPException(status_code=400, detail="Minimum bet is 1.0")
        
        if bet_amount > 10000.0:
            raise HTTPException(status_code=400, detail="Maximum bet is 10,000")
        
        # Check if currency is supported
        from crypto_prices import is_currency_supported
        if not is_currency_supported(bet_currency):
            raise HTTPException(status_code=400, detail="Unsupported currency")
        
        # Check balance
        from main import get_user_wallet, update_wallet_balance, record_transaction
        wallet = get_user_wallet(current_user["id"], bet_currency)
        if not wallet or wallet["balance"] < bet_amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        # Deduct bet from wallet
        update_wallet_balance(current_user["id"], bet_currency, -bet_amount)
        
        # Play game
        game_result = play_casino_game(game_name, bet_amount, bet_options)
        
        # Add payout to wallet if won
        payout_amount = game_result.get("payout", 0.0)
        if payout_amount > 0:
            update_wallet_balance(current_user["id"], bet_currency, payout_amount)
        
        # Record casino round in database
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO casino_rounds (user_id, game_name, bet_amount, bet_currency, 
                                   result, payout_amount, multiplier, game_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            current_user["id"],
            game_name,
            bet_amount,
            bet_currency,
            game_result.get("result"),
            payout_amount,
            game_result.get("multiplier"),
            json.dumps(game_result)
        ))
        
        round_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Record transaction
        record_transaction(
            user_id=current_user["id"],
            tx_type="casino_play",
            currency=bet_currency,
            amount=bet_amount,
            reference_id=str(round_id),
            description=f"Casino game: {game_name}",
            metadata={"payout": payout_amount, "result": game_result.get("result")}
        )
        
        # Return result
        return {
            "success": True,
            "round_id": round_id,
            "game": game_name,
            "bet_amount": bet_amount,
            "bet_currency": bet_currency,
            "result": game_result.get("result"),
            "payout": payout_amount,
            "multiplier": game_result.get("multiplier"),
            "game_data": game_result,
            "new_balance": wallet["balance"] - bet_amount + payout_amount
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Casino game error: {str(e)}")
        # Refund bet on error
        try:
            update_wallet_balance(current_user["id"], bet_currency, bet_amount)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Game error: {str(e)}")

@casino_router.get("/history")
async def get_casino_history(
    limit: int = 50,
    game: str = None,
    current_user: dict = Depends(get_current_user)
):
    """Get user's casino game history."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if game:
            cursor.execute('''
            SELECT * FROM casino_rounds 
            WHERE user_id = ? AND game_name = ?
            ORDER BY created_at DESC 
            LIMIT ?
            ''', (current_user["id"], game, limit))
        else:
            cursor.execute('''
            SELECT * FROM casino_rounds 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
            ''', (current_user["id"], limit))
        
        rounds = []
        for row in cursor.fetchall():
            round_data = dict(row)
            # Parse game_data JSON
            if round_data.get("game_data"):
                try:
                    round_data["game_data"] = json.loads(round_data["game_data"])
                except:
                    pass
            rounds.append(round_data)
        
        return {
            "rounds": rounds,
            "count": len(rounds)
        }
        
    finally:
        conn.close()

@casino_router.get("/stats")
async def get_casino_stats(current_user: dict = Depends(get_current_user)):
    """Get user's casino statistics."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Total rounds
        cursor.execute(
            "SELECT COUNT(*) as total FROM casino_rounds WHERE user_id = ?",
            (current_user["id"],)
        )
        total_rounds = cursor.fetchone()["total"]
        
        # Total wagered
        cursor.execute(
            "SELECT SUM(bet_amount) as total FROM casino_rounds WHERE user_id = ?",
            (current_user["id"],)
        )
        total_wagered = cursor.fetchone()["total"] or 0.0
        
        # Total won
        cursor.execute(
            "SELECT SUM(payout_amount) as total FROM casino_rounds WHERE user_id = ?",
            (current_user["id"],)
        )
        total_won = cursor.fetchone()["total"] or 0.0
        
        # Win rate
        cursor.execute(
            "SELECT COUNT(*) as wins FROM casino_rounds WHERE user_id = ? AND result = 'win'",
            (current_user["id"],)
        )
        wins = cursor.fetchone()["wins"]
        win_rate = (wins / total_rounds * 100) if total_rounds > 0 else 0.0
        
        # Biggest win
        cursor.execute(
            "SELECT MAX(payout_amount) as max_win FROM casino_rounds WHERE user_id = ?",
            (current_user["id"],)
        )
        biggest_win = cursor.fetchone()["max_win"] or 0.0
        
        # Favorite game
        cursor.execute('''
        SELECT game_name, COUNT(*) as plays 
        FROM casino_rounds 
        WHERE user_id = ? 
        GROUP BY game_name 
        ORDER BY plays DESC 
        LIMIT 1
        ''', (current_user["id"],))
        fav = cursor.fetchone()
        favorite_game = fav["game_name"] if fav else None
        
        return {
            "total_rounds": total_rounds,
            "total_wagered": round(total_wagered, 2),
            "total_won": round(total_won, 2),
            "net_profit": round(total_won - total_wagered, 2),
            "win_rate": round(win_rate, 2),
            "biggest_win": round(biggest_win, 2),
            "favorite_game": favorite_game
        }
        
    finally:
        conn.close()

# To integrate into main.py, add:
# from casino_endpoints import casino_router
# app.include_router(casino_router)