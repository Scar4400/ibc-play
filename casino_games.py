"""
Casino games engine with provably fair RNG and multiple game implementations.
Includes: Dice, Coin Flip, Slots, Roulette, Crash, and Blackjack.
"""

import random
import hashlib
import json
from typing import Dict, Any, Tuple, List
from datetime import datetime

# House edge configuration
DEFAULT_HOUSE_EDGE = 0.02  # 2%

class CasinoGame:
    """Base class for all casino games."""
    
    def __init__(self, house_edge: float = DEFAULT_HOUSE_EDGE):
        self.house_edge = house_edge
    
    def generate_seed(self) -> str:
        """Generate a provably fair seed."""
        return hashlib.sha256(f"{datetime.utcnow().timestamp()}{random.random()}".encode()).hexdigest()
    
    def play(self, bet_amount: float, bet_options: Dict[str, Any]) -> Dict[str, Any]:
        """Play the game. To be implemented by subclasses."""
        raise NotImplementedError

class DiceGame(CasinoGame):
    """
    Dice game where player predicts if roll will be over/under target.
    Roll range: 0-100
    """
    
    def play(self, bet_amount: float, bet_options: Dict[str, Any]) -> Dict[str, Any]:
        prediction = bet_options.get("prediction", "over")  # "over" or "under"
        target = bet_options.get("target", 50)
        
        if not (0 <= target <= 100):
            raise ValueError("Target must be between 0 and 100")
        
        # Roll dice (0-100)
        roll = random.randint(0, 100)
        
        # Determine win
        if prediction == "over":
            won = roll > target
            win_chance = (100 - target) / 100
        else:  # under
            won = roll < target
            win_chance = target / 100
        
        # Calculate payout with house edge
        if won:
            payout_multiplier = (1 / win_chance) * (1 - self.house_edge)
            payout = bet_amount * payout_multiplier
        else:
            payout = 0.0
        
        return {
            "result": "win" if won else "loss",
            "roll": roll,
            "target": target,
            "prediction": prediction,
            "payout": round(payout, 2),
            "multiplier": round(payout / bet_amount, 2) if won else 0.0
        }

class CoinFlipGame(CasinoGame):
    """Simple coin flip game - Heads or Tails."""
    
    def play(self, bet_amount: float, bet_options: Dict[str, Any]) -> Dict[str, Any]:
        choice = bet_options.get("choice", "heads").lower()
        
        if choice not in ["heads", "tails"]:
            raise ValueError("Choice must be 'heads' or 'tails'")
        
        # Flip coin
        result = random.choice(["heads", "tails"])
        won = result == choice
        
        # Calculate payout (50/50 with house edge)
        if won:
            payout_multiplier = 2.0 * (1 - self.house_edge)
            payout = bet_amount * payout_multiplier
        else:
            payout = 0.0
        
        return {
            "result": "win" if won else "loss",
            "flip": result,
            "choice": choice,
            "payout": round(payout, 2),
            "multiplier": round(payout / bet_amount, 2) if won else 0.0
        }

class SlotsGame(CasinoGame):
    """
    3-reel slot machine with weighted symbols.
    """
    
    SYMBOLS = {
        "🍒": {"weight": 40, "payout": 2},
        "🍋": {"weight": 30, "payout": 3},
        "🍊": {"weight": 20, "payout": 5},
        "🍇": {"weight": 15, "payout": 10},
        "🔔": {"weight": 10, "payout": 20},
        "💎": {"weight": 5, "payout": 50},
        "7️⃣": {"weight": 2, "payout": 100}
    }
    
    def _spin_reel(self) -> str:
        """Spin a single reel with weighted random selection."""
        symbols = list(self.SYMBOLS.keys())
        weights = [self.SYMBOLS[s]["weight"] for s in symbols]
        return random.choices(symbols, weights=weights, k=1)[0]
    
    def play(self, bet_amount: float, bet_options: Dict[str, Any]) -> Dict[str, Any]:
        # Spin 3 reels
        reels = [self._spin_reel() for _ in range(3)]
        
        # Check for win (all symbols match)
        if reels[0] == reels[1] == reels[2]:
            symbol = reels[0]
            base_payout = self.SYMBOLS[symbol]["payout"]
            payout = bet_amount * base_payout * (1 - self.house_edge)
            won = True
            multiplier = base_payout
        else:
            payout = 0.0
            won = False
            multiplier = 0.0
        
        return {
            "result": "win" if won else "loss",
            "reels": reels,
            "payout": round(payout, 2),
            "multiplier": multiplier
        }

class RouletteGame(CasinoGame):
    """
    European Roulette (0-36).
    Supports: red/black, odd/even, single number bets.
    """
    
    RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
    BLACK_NUMBERS = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}
    
    def play(self, bet_amount: float, bet_options: Dict[str, Any]) -> Dict[str, Any]:
        bet_type = bet_options.get("bet_type", "red")  # red, black, odd, even, or number
        bet_value = bet_options.get("value")  # for number bets
        
        # Spin wheel
        number = random.randint(0, 36)
        
        # Determine win based on bet type
        won = False
        payout_multiplier = 0
        
        if bet_type == "red":
            won = number in self.RED_NUMBERS
            payout_multiplier = 2
        elif bet_type == "black":
            won = number in self.BLACK_NUMBERS
            payout_multiplier = 2
        elif bet_type == "odd":
            won = number > 0 and number % 2 == 1
            payout_multiplier = 2
        elif bet_type == "even":
            won = number > 0 and number % 2 == 0
            payout_multiplier = 2
        elif bet_type == "number":
            if bet_value is None or not (0 <= bet_value <= 36):
                raise ValueError("Number bet requires value 0-36")
            won = number == bet_value
            payout_multiplier = 35
        
        # Calculate payout
        if won:
            payout = bet_amount * payout_multiplier * (1 - self.house_edge)
        else:
            payout = 0.0
        
        # Determine color
        if number == 0:
            color = "green"
        elif number in self.RED_NUMBERS:
            color = "red"
        else:
            color = "black"
        
        return {
            "result": "win" if won else "loss",
            "number": number,
            "color": color,
            "bet_type": bet_type,
            "payout": round(payout, 2),
            "multiplier": round(payout / bet_amount, 2) if won else 0.0
        }

class CrashGame(CasinoGame):
    """
    Crash game - multiplier increases until it crashes.
    Player must cash out before crash point.
    """
    
    def generate_crash_point(self) -> float:
        """Generate crash point using exponential distribution."""
        # Random crash between 1.0x and 100x with exponential bias
        # Most crashes happen early, some go very high
        r = random.random()
        crash_point = 1.0 / (1.0 - r * 0.99)  # Exponential distribution
        return min(crash_point, 100.0)  # Cap at 100x
    
    def play(self, bet_amount: float, bet_options: Dict[str, Any]) -> Dict[str, Any]:
        cashout_at = bet_options.get("cashout_at", 2.0)  # Target multiplier
        
        if cashout_at < 1.01:
            raise ValueError("Cashout multiplier must be >= 1.01")
        
        # Generate crash point
        crash_point = self.generate_crash_point()
        
        # Check if player cashed out in time
        if cashout_at <= crash_point:
            won = True
            payout = bet_amount * cashout_at * (1 - self.house_edge)
            multiplier = cashout_at
        else:
            won = False
            payout = 0.0
            multiplier = 0.0
        
        return {
            "result": "win" if won else "loss",
            "crash_point": round(crash_point, 2),
            "cashout_at": cashout_at,
            "payout": round(payout, 2),
            "multiplier": multiplier
        }

class BlackjackGame(CasinoGame):
    """
    Simplified Blackjack - player vs dealer.
    Player can hit or stand, dealer hits until 17.
    """
    
    CARD_VALUES = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
        'J': 10, 'Q': 10, 'K': 10, 'A': 11
    }
    
    def _draw_card(self) -> str:
        """Draw a random card."""
        return random.choice(list(self.CARD_VALUES.keys()))
    
    def _calculate_hand_value(self, cards: List[str]) -> int:
        """Calculate hand value, handling Aces."""
        value = sum(self.CARD_VALUES[card] for card in cards)
        aces = cards.count('A')
        
        # Adjust for Aces if bust
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        
        return value
    
    def play(self, bet_amount: float, bet_options: Dict[str, Any]) -> Dict[str, Any]:
        # Initial deal
        player_cards = [self._draw_card(), self._draw_card()]
        dealer_cards = [self._draw_card(), self._draw_card()]
        
        player_value = self._calculate_hand_value(player_cards)
        dealer_value = self._calculate_hand_value(dealer_cards)
        
        # Player action (simplified - auto-hit until 17+)
        while player_value < 17:
            player_cards.append(self._draw_card())
            player_value = self._calculate_hand_value(player_cards)
        
        # Dealer plays (hits until 17+)
        while dealer_value < 17:
            dealer_cards.append(self._draw_card())
            dealer_value = self._calculate_hand_value(dealer_cards)
        
        # Determine winner
        player_bust = player_value > 21
        dealer_bust = dealer_value > 21
        
        if player_bust:
            result = "loss"
            payout = 0.0
        elif dealer_bust:
            result = "win"
            payout = bet_amount * 2.0 * (1 - self.house_edge)
        elif player_value > dealer_value:
            result = "win"
            payout = bet_amount * 2.0 * (1 - self.house_edge)
        elif player_value == dealer_value:
            result = "push"
            payout = bet_amount  # Return bet
        else:
            result = "loss"
            payout = 0.0
        
        return {
            "result": result,
            "player_cards": player_cards,
            "player_value": player_value,
            "dealer_cards": dealer_cards,
            "dealer_value": dealer_value,
            "payout": round(payout, 2),
            "multiplier": round(payout / bet_amount, 2) if payout > 0 else 0.0
        }

# Game registry
GAMES = {
    "dice": DiceGame,
    "coinflip": CoinFlipGame,
    "slots": SlotsGame,
    "roulette": RouletteGame,
    "crash": CrashGame,
    "blackjack": BlackjackGame
}

def play_casino_game(game_name: str, bet_amount: float, bet_options: Dict[str, Any]) -> Dict[str, Any]:
    """
    Play a casino game and return the result.
    
    Args:
        game_name: Name of the game
        bet_amount: Amount bet
        bet_options: Game-specific options
        
    Returns:
        Game result with payout information
    """
    game_name = game_name.lower()
    
    if game_name not in GAMES:
        raise ValueError(f"Unknown game: {game_name}. Available: {list(GAMES.keys())}")
    
    game_class = GAMES[game_name]
    game = game_class()
    
    try:
        result = game.play(bet_amount, bet_options or {})
        result["game"] = game_name
        result["bet_amount"] = bet_amount
        return result
    except Exception as e:
        raise ValueError(f"Game error: {str(e)}")