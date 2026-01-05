"""
Database initialization and schema definition for IBC Play platform.
Includes all tables for users, wallets, transactions, bets, and casino operations.
"""

import sqlite3
from datetime import datetime
from typing import Optional
import os

DATABASE_PATH = os.getenv("DATABASE_URL", "sqlite:///./ibc_play.db").replace("sqlite:///", "")


def get_connection():
    """Get database connection with row factory for dict-like access."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize all database tables with proper schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            full_name TEXT,
            is_active BOOLEAN DEFAULT 1,
            is_verified BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Wallets table - stores crypto and fiat balances
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            currency TEXT NOT NULL,
            balance REAL DEFAULT 0.0,
            locked_balance REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, currency)
        )
        ''')
        
        # Transactions table - all financial movements
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            currency TEXT NOT NULL,
            amount REAL NOT NULL,
            usd_value REAL,
            status TEXT DEFAULT 'pending',
            description TEXT,
            reference_id TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        ''')
        
        # Bets table - sports betting records
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            bet_type TEXT NOT NULL,
            sport TEXT,
            event_name TEXT NOT NULL,
            selection TEXT NOT NULL,
            odds REAL NOT NULL,
            stake_amount REAL NOT NULL,
            stake_currency TEXT NOT NULL,
            potential_payout REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            result TEXT,
            settled_amount REAL,
            event_start_time TIMESTAMP,
            placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            settled_at TIMESTAMP,
            metadata TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        ''')
        
        # Casino rounds table - all casino game outcomes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS casino_rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game_name TEXT NOT NULL,
            bet_amount REAL NOT NULL,
            bet_currency TEXT NOT NULL,
            result TEXT NOT NULL,
            payout_amount REAL DEFAULT 0.0,
            multiplier REAL,
            house_edge REAL,
            game_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        ''')
        
        # Crypto holdings table - tracks crypto portfolio
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS crypto_holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            amount REAL NOT NULL,
            average_buy_price REAL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, symbol)
        )
        ''')
        
        # Price cache table - cache external API prices
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            price_usd REAL NOT NULL,
            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_wallets_user_id ON wallets(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bets_user_id ON bets(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bets_status ON bets(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_casino_rounds_user_id ON casino_rounds(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_casino_rounds_game ON casino_rounds(game_name)')
        
        conn.commit()
        print("✅ Database initialized successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Database initialization failed: {str(e)}")
        raise
    finally:
        conn.close()


def create_demo_user():
    """Create a demo user for testing purposes."""
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if demo user exists
        cursor.execute("SELECT id FROM users WHERE username = ?", ("demo",))
        if cursor.fetchone():
            print("Demo user already exists")
            return
        
        # Create demo user
        hashed_password = pwd_context.hash("demo123")
        cursor.execute('''
        INSERT INTO users (username, email, hashed_password, full_name, is_active, is_verified)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', ("demo", "demo@ibcplay.com", hashed_password, "Demo User", 1, 1))
        
        user_id = cursor.lastrowid
        
        # Create default wallets
        currencies = ["USD", "BTC", "ETH", "SOL", "BNB"]
        for currency in currencies:
            initial_balance = 10000.0 if currency == "USD" else 0.0
            cursor.execute('''
            INSERT INTO wallets (user_id, currency, balance)
            VALUES (?, ?, ?)
            ''', (user_id, currency, initial_balance))
        
        conn.commit()
        print(f"✅ Demo user created (username: demo, password: demo123)")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to create demo user: {str(e)}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("Initializing IBC Play database...")
    init_database()
    create_demo_user()
    print("Database setup complete!")