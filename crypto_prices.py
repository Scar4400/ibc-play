"""
Crypto price fetching module with CoinGecko API integration.
Includes caching, fallback mechanisms, and error handling.
"""

import httpx
import time
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)

# Supported cryptocurrencies mapping to CoinGecko IDs
SUPPORTED_COINS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin"
}

# Fallback simulated prices (used when API fails)
FALLBACK_PRICES = {
    "BTC": 45000.0,
    "ETH": 2500.0,
    "SOL": 100.0,
    "BNB": 350.0
}

# In-memory cache
price_cache: Dict[str, Dict] = {}
CACHE_TTL = 60  # seconds


class CryptoPriceService:
    """Service for fetching and caching cryptocurrency prices."""
    
    def __init__(self):
        self.api_url = os.getenv("COINGECKO_API_URL", "https://api.coingecko.com/api/v3")
        self.api_key = os.getenv("COINGECKO_API_KEY", "")
        self.cache = {}
        self.cache_ttl = CACHE_TTL
        
    def _get_from_cache(self, symbol: str) -> Optional[float]:
        """Get price from cache if not expired."""
        if symbol in self.cache:
            cached_data = self.cache[symbol]
            if time.time() - cached_data["timestamp"] < self.cache_ttl:
                logger.info(f"Cache hit for {symbol}: ${cached_data['price']:.2f}")
                return cached_data["price"]
        return None
    
    def _set_cache(self, symbol: str, price: float):
        """Store price in cache with timestamp."""
        self.cache[symbol] = {
            "price": price,
            "timestamp": time.time()
        }
    
    async def get_price(self, symbol: str) -> float:
        """
        Get current USD price for a cryptocurrency.
        
        Args:
            symbol: Crypto symbol (BTC, ETH, SOL, BNB)
            
        Returns:
            Current price in USD
            
        Raises:
            ValueError: If symbol is not supported
        """
        symbol = symbol.upper()
        
        if symbol not in SUPPORTED_COINS:
            raise ValueError(f"Unsupported cryptocurrency: {symbol}")
        
        # Check cache first
        cached_price = self._get_from_cache(symbol)
        if cached_price is not None:
            return cached_price
        
        # Try to fetch from CoinGecko
        try:
            price = await self._fetch_from_coingecko(symbol)
            self._set_cache(symbol, price)
            logger.info(f"Fetched {symbol} price from API: ${price:.2f}")
            return price
            
        except Exception as e:
            logger.warning(f"Failed to fetch {symbol} from API: {str(e)}. Using fallback price.")
            fallback_price = FALLBACK_PRICES[symbol]
            self._set_cache(symbol, fallback_price)
            return fallback_price
    
    async def _fetch_from_coingecko(self, symbol: str) -> float:
        """Fetch price from CoinGecko API."""
        coin_id = SUPPORTED_COINS[symbol]
        url = f"{self.api_url}/simple/price"
        
        params = {
            "ids": coin_id,
            "vs_currencies": "usd"
        }
        
        headers = {}
        if self.api_key:
            headers["x-cg-pro-api-key"] = self.api_key
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if coin_id not in data or "usd" not in data[coin_id]:
                raise ValueError(f"Invalid response from CoinGecko for {symbol}")
            
            return float(data[coin_id]["usd"])
    
    async def get_multiple_prices(self, symbols: list[str]) -> Dict[str, float]:
        """
        Get prices for multiple cryptocurrencies at once.
        
        Args:
            symbols: List of crypto symbols
            
        Returns:
            Dictionary mapping symbols to USD prices
        """
        prices = {}
        for symbol in symbols:
            try:
                prices[symbol] = await self.get_price(symbol)
            except Exception as e:
                logger.error(f"Failed to get price for {symbol}: {str(e)}")
                prices[symbol] = FALLBACK_PRICES.get(symbol, 0.0)
        
        return prices
    
    def convert_to_usd(self, amount: float, symbol: str, price: Optional[float] = None) -> float:
        """
        Convert crypto amount to USD value.
        
        Args:
            amount: Amount of cryptocurrency
            symbol: Crypto symbol
            price: Optional pre-fetched price
            
        Returns:
            USD value
        """
        if symbol == "USD":
            return amount
        
        if price is None:
            # Use cached price or fallback if not provided
            cached = self._get_from_cache(symbol)
            price = cached if cached else FALLBACK_PRICES.get(symbol, 0.0)
        
        return amount * price
    
    def convert_from_usd(self, usd_amount: float, symbol: str, price: Optional[float] = None) -> float:
        """
        Convert USD to crypto amount.
        
        Args:
            usd_amount: USD amount
            symbol: Crypto symbol
            price: Optional pre-fetched price
            
        Returns:
            Crypto amount
        """
        if symbol == "USD":
            return usd_amount
        
        if price is None:
            cached = self._get_from_cache(symbol)
            price = cached if cached else FALLBACK_PRICES.get(symbol, 1.0)
        
        if price == 0:
            price = FALLBACK_PRICES.get(symbol, 1.0)
        
        return usd_amount / price
    
    def is_supported(self, symbol: str) -> bool:
        """Check if cryptocurrency is supported."""
        return symbol.upper() in SUPPORTED_COINS or symbol.upper() == "USD"
    
    def get_supported_currencies(self) -> list[str]:
        """Get list of all supported currencies."""
        return ["USD"] + list(SUPPORTED_COINS.keys())


# Global singleton instance
crypto_service = CryptoPriceService()


# Convenience functions
async def get_crypto_price(symbol: str) -> float:
    """Get current crypto price in USD."""
    return await crypto_service.get_price(symbol)


async def get_all_prices() -> Dict[str, float]:
    """Get all supported crypto prices."""
    symbols = list(SUPPORTED_COINS.keys())
    return await crypto_service.get_multiple_prices(symbols)


def convert_to_usd(amount: float, currency: str) -> float:
    """Convert amount to USD (synchronous)."""
    return crypto_service.convert_to_usd(amount, currency)


def is_currency_supported(currency: str) -> bool:
    """Check if currency is supported."""
    return crypto_service.is_supported(currency)