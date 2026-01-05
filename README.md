# 🎰 IBC Play - Crypto Sports Betting & Casino Platform

A complete, production-ready sports betting and casino platform with cryptocurrency integration. Built with FastAPI, SQLite/PostgreSQL, and real-time crypto prices from CoinGecko.

**⚠️ Disclaimer**: This is a demonstration platform for educational purposes. Do not use for real money without proper licensing, auditing, and compliance.

---

## 🌟 Features

### 💰 Wallet & Crypto
- **Multi-currency wallets**: USD, BTC, ETH, SOL, BNB
- **Real-time prices**: Live crypto prices via CoinGecko API
- **Deposits & withdrawals**: Instant transactions
- **Currency conversion**: Seamless transfers between currencies
- **Transaction history**: Complete audit trail

### 🎮 Casino Games
- **Dice**: Predict over/under on 0-100 roll
- **Coin Flip**: Classic heads or tails
- **Slots**: 3-reel slot machine with 7 symbols
- **Roulette**: European roulette (0-36)
- **Crash**: Cash out before the multiplier crashes
- **Blackjack**: Beat the dealer (simplified rules)

### ⚽ Sports Betting
- **Multiple bet types**: Single bets, accumulators
- **Live odds**: Dynamic odds calculation
- **Bet history**: Track all your bets
- **Auto-settlement**: Automated bet resolution
- **Multiple sports**: Football, basketball, tennis, etc.

### 🔐 Security & Features
- **JWT Authentication**: Secure token-based auth
- **Password hashing**: Bcrypt encryption
- **Rate limiting**: Protection against abuse
- **Input validation**: Pydantic models
- **Error handling**: Comprehensive logging
- **Database persistence**: SQLite (dev) / PostgreSQL (prod)

---

## 🏗️ Architecture

```mermaid
graph TD
    A[React HTML UI] -->|HTTP/REST| B[FastAPI Backend]
    B -->|JWT Auth| C[Protected Endpoints]
    B -->|SQLAlchemy ORM| D[(SQLite/PostgreSQL)]
    B -->|HTTP Client| E[CoinGecko API]
    B -->|In-Memory| F[Price Cache 60s TTL]
    
    C --> G[/wallet<br>/deposit<br>/withdraw]
    C --> H[/bets<br>/bets/history<br>/bets/resolve]
    C --> I[/casino/play<br>/casino/history<br>/casino/stats]
    
    D --> J[(Users)]
    D --> K[(Wallets)]
    D --> L[(Transactions)]
    D --> M[(Bets)]
    D --> N[(Casino Rounds)]
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/Scar4400/ibc-play.git
cd ibc-play

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your settings (SECRET_KEY is critical!)

# Initialize database
python db_init.py

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Access the Application

- **API Docs**: http://localhost:8000/docs
- **API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Demo Frontend**: Open `ib-crypto-play-demo.html` in your browser

### Demo Account

```
Username: demo
Password: demo123
Initial Balance: $10,000 USD
```

---

## 📚 API Documentation

### Authentication

#### Register
```http
POST /register
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepass123",
  "full_name": "John Doe"
}
```

#### Login
```http
POST /login
Content-Type: application/x-www-form-urlencoded

username=demo&password=demo123
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### Wallet Operations

#### Get Wallet
```http
GET /wallet
Authorization: Bearer <token>
```

**Response:**
```json
{
  "wallets": [
    {
      "currency": "USD",
      "balance": 10000.0,
      "locked_balance": 0.0,
      "usd_value": 10000.0
    },
    {
      "currency": "BTC",
      "balance": 0.5,
      "locked_balance": 0.0,
      "usd_value": 22500.0
    }
  ],
  "total_usd_value": 32500.0
}
```

#### Deposit
```http
POST /deposit
Authorization: Bearer <token>
Content-Type: application/json

{
  "currency": "BTC",
  "amount": 0.1
}
```

#### Withdraw
```http
POST /withdraw
Authorization: Bearer <token>
Content-Type: application/json

{
  "currency": "USD",
  "amount": 100.0
}
```

#### Transfer/Convert
```http
POST /transfer
Authorization: Bearer <token>
Content-Type: application/json

{
  "from_currency": "USD",
  "to_currency": "BTC",
  "amount": 1000.0
}
```

### Sports Betting

#### Place Bet
```http
POST /bets
Authorization: Bearer <token>
Content-Type: application/json

{
  "bet_type": "single",
  "sport": "football",
  "event_name": "Man United vs Liverpool",
  "selection": "Man United to win",
  "odds": 2.5,
  "stake_amount": 100.0,
  "stake_currency": "USD"
}
```

#### Get Bet History
```http
GET /bets/history?limit=20&status=pending
Authorization: Bearer <token>
```

#### Resolve Bet (Admin/Simulation)
```http
POST /bets/{bet_id}/resolve
Authorization: Bearer <token>
Content-Type: application/json

{
  "result": "won"
}
```

### Casino Games

#### List Games
```http
GET /casino/games
```

#### Play Game
```http
POST /casino/play
Authorization: Bearer <token>
Content-Type: application/json

{
  "game": "dice",
  "bet_amount": 10.0,
  "bet_currency": "USD",
  "bet_options": {
    "prediction": "over",
    "target": 50
  }
}
```

**Game Options by Type:**

**Dice:**
```json
{
  "prediction": "over",  // or "under"
  "target": 50          // 0-100
}
```

**Coin Flip:**
```json
{
  "choice": "heads"  // or "tails"
}
```

**Roulette:**
```json
{
  "bet_type": "red",  // "red", "black", "odd", "even", "number"
  "value": 7          // only for "number" bet_type
}
```

**Crash:**
```json
{
  "cashout_at": 2.0  // target multiplier
}
```

**Slots & Blackjack:**
No options required - just play!

#### Get Casino History
```http
GET /casino/history?limit=50&game=dice
Authorization: Bearer <token>
```

#### Get Casino Stats
```http
GET /casino/stats
Authorization: Bearer <token>
```

---

## 🎮 Casino Games Guide

### 🎲 Dice
- **How to play**: Choose "over" or "under" and set a target number (0-100)
- **Winning**: Roll must be above target (over) or below target (under)
- **Payout**: Based on win probability with 2% house edge
- **Example**: Target 70, Over = 30% win chance = 3.27x payout

### 🪙 Coin Flip
- **How to play**: Choose heads or tails
- **Winning**: Coin lands on your choice
- **Payout**: 1.95x (50% win chance, 2% house edge)

### 🎰 Slots
- **How to play**: Spin 3 reels
- **Winning**: All 3 symbols match
- **Payouts**: 
  - 🍒 Cherry: 2x
  - 🍋 Lemon: 3x
  - 🍊 Orange: 5x
  - 🍇 Grape: 10x
  - 🔔 Bell: 20x
  - 💎 Diamond: 50x
  - 7️⃣ Seven: 100x

### 🎡 Roulette
- **How to play**: European wheel (0-36)
- **Bet types**:
  - Red/Black: 2x payout
  - Odd/Even: 2x payout
  - Single number: 35x payout
- **House edge**: 2.7%

### 💥 Crash
- **How to play**: Set cashout multiplier before playing
- **Winning**: Crash point must be higher than cashout target
- **Risk vs Reward**: Higher multipliers = lower probability
- **Max**: 100x multiplier

### 🃏 Blackjack
- **How to play**: Auto-hit until 17+, dealer follows same rules
- **Winning**: Beat dealer without going bust (>21)
- **Payout**: 2x on win, push returns bet
- **Simplified**: No split, double down, or insurance

---

## 🗄️ Database Schema

### Users
```sql
- id: INTEGER PRIMARY KEY
- username: TEXT UNIQUE
- email: TEXT UNIQUE
- hashed_password: TEXT
- full_name: TEXT
- is_active: BOOLEAN
- is_verified: BOOLEAN
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

### Wallets
```sql
- id: INTEGER PRIMARY KEY
- user_id: INTEGER (FK)
- currency: TEXT
- balance: REAL
- locked_balance: REAL
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
- UNIQUE(user_id, currency)
```

### Transactions
```sql
- id: INTEGER PRIMARY KEY
- user_id: INTEGER (FK)
- transaction_type: TEXT
- currency: TEXT
- amount: REAL
- usd_value: REAL
- status: TEXT
- description: TEXT
- reference_id: TEXT
- metadata: TEXT (JSON)
- created_at: TIMESTAMP
- completed_at: TIMESTAMP
```

### Bets
```sql
- id: INTEGER PRIMARY KEY
- user_id: INTEGER (FK)
- bet_type: TEXT
- sport: TEXT
- event_name: TEXT
- selection: TEXT
- odds: REAL
- stake_amount: REAL
- stake_currency: TEXT
- potential_payout: REAL
- status: TEXT
- result: TEXT
- settled_amount: REAL
- placed_at: TIMESTAMP
- settled_at: TIMESTAMP
```

### Casino Rounds
```sql
- id: INTEGER PRIMARY KEY
- user_id: INTEGER (FK)
- game_name: TEXT
- bet_amount: REAL
- bet_currency: TEXT
- result: TEXT
- payout_amount: REAL
- multiplier: REAL
- game_data: TEXT (JSON)
- created_at: TIMESTAMP
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Application
APP_NAME=IBC-Play
ENV=development
DEBUG=True

# Security
SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Database
DATABASE_URL=sqlite:///./ibc_play.db
# For production: postgresql://user:pass@host:5432/dbname

# External APIs
COINGECKO_API_URL=https://api.coingecko.com/api/v3
COINGECKO_API_KEY=

# Casino Settings
HOUSE_EDGE=0.02
MIN_BET_AMOUNT=1.0
MAX_BET_AMOUNT=10000.0

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
```

---

## 🚢 Deployment

### Render.com (Recommended)

1. **Fork/clone the repository**
2. **Connect to Render.com**
3. **Create new Web Service**
4. **Configure**:
   - Build Command: `pip install -r requirements.txt && python db_init.py`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. **Add environment variables**
6. **Deploy!**

The `render.yaml` file is pre-configured for easy deployment.

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python db_init.py

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t ibc-play .
docker run -p 8000:8000 ibc-play
```

---

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

---

## 📈 Future Enhancements

- [ ] Live sports betting with real odds feeds
- [ ] WebSocket support for real-time updates
- [ ] More casino games (Baccarat, Poker, etc.)
- [ ] Leaderboards and achievements
- [ ] Social features (friend bets, chat)
- [ ] Mobile app (React Native)
- [ ] Admin dashboard
- [ ] KYC/AML compliance integration
- [ ] Payment gateway integration
- [ ] Multi-language support

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is for educational purposes. Not licensed for commercial use without proper gambling licenses and compliance.

---

## ⚠️ Important Notes

### Legal Compliance
- **Gambling Regulations**: Ensure compliance with local gambling laws
- **Licensing**: Obtain necessary licenses before real-money operations
- **Age Verification**: Implement age verification (18+/21+)
- **Responsible Gaming**: Add self-exclusion and limit-setting features
- **AML/KYC**: Implement anti-money laundering checks

### Security Considerations
- **Change SECRET_KEY**: Use a strong, random 32+ character key in production
- **HTTPS Only**: Always use HTTPS in production
- **Rate Limiting**: Adjust based on your infrastructure
- **Input Validation**: All inputs are validated, but review for your use case
- **SQL Injection**: Using parameterized queries throughout
- **XSS Protection**: Frontend should sanitize all user inputs

### Performance
- **Database**: Consider PostgreSQL for production (included in render.yaml)
- **Caching**: Redis recommended for production (price cache, sessions)
- **CDN**: Use CDN for static assets
- **Load Balancing**: Scale horizontally with multiple instances

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Scar4400/ibc-play/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Scar4400/ibc-play/discussions)

---

**Built with ❤️ using FastAPI, SQLite, and CoinGecko API**