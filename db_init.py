"""
IBC Play - Database Initialization and Schema
SQLite/PostgreSQL compatible schema with complete persistence layer
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path

# Database file path
DB_PATH = "ibc_play.db"


def get_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def init_database():
    """Initialize the complete database schema"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # ===================================
        # USERS TABLE
        # ===================================
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
        ''')
        
        # ===================================
        # WALLETS TABLE
        # ===================================
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            currency VARCHAR(10) NOT NULL,
            balance DECIMAL(20, 8) DEFAULT 0.0,
            locked_balance DECIMAL(20, 8) DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, currency)
        )
        ''')
        
        # ===================================
        # TRANSACTIONS TABLE
        # ===================================
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            transaction_type VARCHAR(20) NOT NULL,
            currency VARCHAR(10) NOT NULL,
            amount DECIMAL(20, 8) NOT NULL,
            balance_before DECIMAL(20, 8),
            balance_after DECIMAL(20, 8),
            reference_id VARCHAR(100),
            reference_type VARCHAR(50),
            status VARCHAR(20) DEFAULT 'pending',
            description TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        ''')
        
        # ===================================
        # CRYPTO HOLDINGS TABLE
        # ===================================
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS crypto_holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            crypto_symbol VARCHAR(10) NOT NULL,
            amount DECIMAL(20, 8) DEFAULT 0.0,
            avg_purchase_price DECIMAL(20, 8),
            total_invested DECIMAL(20, 8) DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, crypto_symbol)
        )
        ''')
        
        # ===================================
        # SPORTS BETS TABLE
        # ===================================
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            match_id VARCHAR(100) NOT NULL,
            sport VARCHAR(50),
            league VARCHAR(100),
            home_team VARCHAR(100),
            away_team VARCHAR(100),
            bet_type VARCHAR(50) NOT NULL,
            bet_selection VARCHAR(100) NOT NULL,
            bet_amount DECIMAL(20, 8) NOT NULL,
            odds DECIMAL(10, 4) NOT NULL,
            potential_payout DECIMAL(20, 8),
            status VARCHAR(20) DEFAULT 'pending',
            result VARCHAR(20),
            payout_amount DECIMAL(20, 8) DEFAULT 0.0,
            match_start_time TIMESTAMP,
            placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            settled_at TIMESTAMP,
            metadata TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        ''')
        
        # ===================================
        # CASINO ROUNDS TABLE
        # ===================================
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS casino_rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game_name VARCHAR(50) NOT NULL,
            bet_amount DECIMAL(20, 8) NOT NULL,
            payout_amount DECIMAL(20, 8) DEFAULT 0.0,
            profit_loss DECIMAL(20, 8),
            game_result TEXT,
            game_state TEXT,
            house_edge DECIMAL(5, 2),
            is_win BOOLEAN DEFAULT FALSE,
            played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        ''')
        
        # ===================================
        # CRYPTO PRICES CACHE TABLE
        # ===================================
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS crypto_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol VARCHAR(10) NOT NULL UNIQUE,
            price_usd DECIMAL(20, 8) NOT NULL,
            price_change_24h DECIMAL(10, 4),
            market_cap DECIMAL(30, 2),
            volume_24h DECIMAL(30, 2),
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # ===================================
        # SESSIONS TABLE (Optional - for tracking)
        # ===================================
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token VARCHAR(255) NOT NULL UNIQUE,
            ip_address VARCHAR(45),
            user_agent TEXT,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        ''')
        
        # ===================================
        # SYSTEM LOGS TABLE
        # ===================================
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_level VARCHAR(20) NOT NULL,
            user_id INTEGER,
            action VARCHAR(100),
            message TEXT,
            stack_trace TEXT,
            ip_address VARCHAR(45),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
        ''')
        
        # ===================================
        # CREATE INDEXES FOR PERFORMANCE
        # ===================================
        
        # User indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        
        # Wallet indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_wallets_user_id ON wallets(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_wallets_currency ON wallets(currency)')
        
        # Transaction indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_created ON transactions(created_at)')
        
        # Bet indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bets_user_id ON bets(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bets_status ON bets(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bets_match_id ON bets(match_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bets_placed_at ON bets(placed_at)')
        
        # Casino indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_casino_user_id ON casino_rounds(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_casino_game ON casino_rounds(game_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_casino_played_at ON casino_rounds(played_at)')
        
        # Session indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at)')
        
        conn.commit()
        print("✅ Database schema initialized successfully!")
        print(f"📁 Database location: {os.path.abspath(DB_PATH)}")
        
        # Print table summary
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\n📊 Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
    except sqlite3.Error as e:
        print(f"❌ Database initialization error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def seed_initial_data():
    """Seed the database with initial data for testing"""
    from passlib.context import CryptContext
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if admin user exists
        cursor.execute("SELECT id FROM users WHERE username = ?", ("admin",))
        if cursor.fetchone() is None:
            # Create password context
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            # Create admin user
            admin_password = pwd_context.hash("admin123")  # Change this!
            cursor.execute('''
            INSERT INTO users (username, email, password_hash, is_admin, is_active)
            VALUES (?, ?, ?, ?, ?)
            ''', ("admin", "admin@ibcplay.com", admin_password, True, True))
            
            admin_id = cursor.lastrowid
            
            # Create wallet for admin with initial balance
            for currency in ["USD", "BTC", "ETH", "SOL", "BNB"]:
                balance = 1000.0 if currency == "USD" else 0.0
                cursor.execute('''
                INSERT INTO wallets (user_id, currency, balance)
                VALUES (?, ?, ?)
                ''', (admin_id, currency, balance))
            
            print("✅ Admin user created: admin / admin123")
            print("⚠️  Please change the admin password immediately!")
        
        # Seed initial crypto prices
        initial_prices = [
            ("BTC", 43000.00, 2.5),
            ("ETH", 2250.00, 3.2),
            ("SOL", 98.50, -1.5),
            ("BNB", 315.00, 1.8)
        ]
        
        for symbol, price, change in initial_prices:
            cursor.execute('''
            INSERT OR REPLACE INTO crypto_prices (symbol, price_usd, price_change_24h, last_updated)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (symbol, price, change))
        
        print("✅ Initial crypto prices seeded")
        
        conn.commit()
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        conn.rollback()
    finally:
        conn.close()


def drop_all_tables():
    """Drop all tables - USE WITH CAUTION!"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        tables = [
            'system_logs', 'user_sessions', 'crypto_prices',
            'casino_rounds', 'bets', 'crypto_holdings',
            'transactions', 'wallets', 'users'
        ]
        
        for table in tables:
            cursor.execute(f'DROP TABLE IF EXISTS {table}')
        
        conn.commit()
        print("✅ All tables dropped successfully")
    except sqlite3.Error as e:
        print(f"❌ Error dropping tables: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    print("🚀 Initializing IBC Play Database...")
    print("=" * 50)
    
    # Initialize database
    init_database()
    
    # Seed initial data
    print("\n🌱 Seeding initial data...")
    seed_initial_data()
    
    print("\n" + "=" * 50)
    print("✨ Database setup complete!")
    print("\nNext steps:")
    print("1. Review the .env file and set your SECRET_KEY")
    print("2. Change the admin password")
    print("3. Start the FastAPI server: uvicorn main:app --reload")