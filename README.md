# 🎰 IBC Play - Crypto Sports Betting & Casino Platform

> A full-stack sports betting and casino platform with cryptocurrency integration, built with FastAPI, React, and real-time crypto pricing.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

![IBC Play Banner](https://via.placeholder.com/1200x300/667eea/ffffff?text=IBC+Play+-+Crypto+Betting+%26+Casino)

-----

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [API Documentation](#-api-documentation)
- [Casino Games](#-casino-games)
- [Deployment](#-deployment)
- [Screenshots](#-screenshots)
- [Contributing](#-contributing)
- [License](#-license)

-----

## ✨ Features

### 🎲 Casino Games

- **6 Fully Functional Games**
  - 🎰 Slots (3-reel with jackpots)
  - 🎲 Dice (Over/Under)
  - 🪙 Coin Flip
  - 🎡 Roulette (European wheel)
  - 🚀 Crash Game
  - 🃏 Blackjack

### ⚽ Sports Betting

- Live match odds
- Multiple bet types
- Real-time bet placement
- Comprehensive betting history

### 💰 Wallet Management

- Multi-currency support (USD, BTC, ETH, SOL, BNB)
- Real-time crypto prices via CoinGecko API
- Instant deposits & withdrawals
- Complete transaction history

### 🔐 Security

- JWT-based authentication
- Password hashing with bcrypt
- Secure session management
- Input validation & sanitization

### 📊 Analytics

- User statistics dashboard
- Win/loss tracking
- Profit/loss calculations
- Game history analytics

-----

## 🛠️ Tech Stack

### Backend

|Technology           |Purpose                               |
|---------------------|--------------------------------------|
|**FastAPI**          |Modern Python web framework           |
|**SQLite/PostgreSQL**|Database (SQLite dev, PostgreSQL prod)|
|**SQLAlchemy**       |ORM and database toolkit              |
|**Pydantic**         |Data validation                       |
|**python-jose**      |JWT token handling                    |
|**passlib**          |Password hashing                      |
|**httpx**            |Async HTTP client                     |

### Frontend

|Technology      |Purpose              |
|----------------|---------------------|
|**React 18**    |UI framework         |
|**Tailwind CSS**|Utility-first styling|
|**Fetch API**   |HTTP requests        |

### External Services

|Service          |Purpose                |
|-----------------|-----------------------|
|**CoinGecko API**|Real-time crypto prices|
|**Render.com**   |Hosting & deployment   |

-----

## 🚀 Quick Start

### Prerequisites

```bash
# Required
- Python 3.9+
- pip
- Git

# Optional
- PostgreSQL (for production)
- Redis (for caching)
```

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Scar4400/ibc-play.git
cd ibc-play

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment
cp .env.example .env
# Edit .env with your configuration

# 5. Initialize database
python db_init.py

# 6. Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Access the Application

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: Open `index.html` in browser or use http server

**Default Admin Login:**

- Username: `admin`
- Password: `admin123` (⚠️ Change immediately!)

-----

## 📁 Project Structure

```
ibc-play/
├── main.py                    # FastAPI application
├── db_init.py                 # Database initialization
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
├── render.yaml               # Render deployment config
├── index.html                # React frontend demo
├── alembic/                  # Database migrations
│   └── versions/
├── frontend/                 # Frontend assets (if separated)
│   └── index.html
├── logs/                     # Application logs
└── docs/                     # Documentation
    ├── SETUP_GUIDE.md
    └── API.md
```

-----

## 📚 API Documentation

### Base URL

```
Development: http://localhost:8000
Production: https://your-app.onrender.com
```

### Authentication

All protected endpoints require a JWT token in the `Authorization` header:

```bash
Authorization: Bearer <your_jwt_token>
```

### Key Endpoints

#### Authentication

```bash
POST /register          # Register new user
POST /login             # Login and get JWT
GET  /me                # Get current user info
```

#### Wallet

```bash
GET  /wallet            # Get all wallets
POST /deposit           # Deposit crypto
POST /withdraw          # Withdraw crypto
GET  /transactions      # Transaction history
```

#### Casino

```bash
GET  /casino/games      # List available games
POST /casino/play       # Play a game
GET  /casino/history    # Game history
```

#### Sports Betting

```bash
GET  /bets/matches      # Available matches
POST /bets              # Place a bet
GET  /bets/history      # Betting history
```

#### Crypto Prices

```bash
GET  /crypto/prices     # All crypto prices
GET  /crypto/price/{symbol}  # Specific crypto price
```

### Example Requests

**Register User:**

```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "player1",
    "email": "player1@example.com",
    "password": "securepass123"
  }'
```

**Login:**

```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=player1&password=securepass123"
```

**Play Slots:**

```bash
curl -X POST http://localhost:8000/casino/play \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "game": "slots",
    "bet_amount": 10.0,
    "bet_options": {}
  }'
```

For complete API documentation, visit `/docs` when the server is running.

-----

## 🎮 Casino Games

### Game Details

|Game         |Min Bet|House Edge|Description             |
|-------------|-------|----------|------------------------|
|**Slots**    |$1     |5%        |3-reel slot with jackpot|
|**Dice**     |$1     |2%        |Roll over/under target  |
|**Coin Flip**|$1     |2.5%      |50/50 heads or tails    |
|**Roulette** |$1     |2.7%      |European wheel (0-36)   |
|**Crash**    |$1     |3%        |Cash out before crash   |
|**Blackjack**|$1     |1.5%      |Beat the dealer         |

### Game Mechanics

#### Slots

```
Symbols: 🍒 🍋 🍊 🍇 ⭐ 💎 7️⃣
Three 7️⃣: 100x (Jackpot!)
Three 💎: 50x
Three ⭐: 20x
Three matching: 2-10x
Two matching: 1.5x
```

#### Dice

```
Roll: 1-100
Bet Types:
  - Over <target>
  - Under <target>
Win Chance: Calculated based on target
Payout: Dynamic based on probability
```

#### Roulette

```
Numbers: 0-36
Bet Types:
  - Number (35:1)
  - Color (1:1)
  - Odd/Even (1:1)
```

-----

## 🌐 Deployment

### Deploy to Render.com

**Step 1:** Push code to GitHub

```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

**Step 2:** Create Render Web Service

1. Connect GitHub repository
1. Use `render.yaml` configuration
1. Set environment variables
1. Deploy!

**Step 3:** Access Your App

```
Backend: https://ibc-play-api.onrender.com
Frontend: https://ibc-play-frontend.onrender.com
```

### Environment Variables (Production)

```env
SECRET_KEY=<generate-secure-32-char-key>
DATABASE_URL=postgresql://user:pass@host:5432/db
COINGECKO_API_URL=https://api.coingecko.com/api/v3
CORS_ORIGINS=https://your-frontend.com
```

For detailed deployment instructions, see <SETUP_GUIDE.md>.

-----

## 📸 Screenshots

### Casino Dashboard

![Casino](https://via.placeholder.com/800x500/667eea/ffffff?text=Casino+Dashboard)

### Sports Betting

![Sports](https://via.placeholder.com/800x500/764ba2/ffffff?text=Sports+Betting)

### Wallet Management

![Wallet](https://via.placeholder.com/800x500/f093fb/ffffff?text=Wallet+Management)

-----

## 🏗️ Architecture

```mermaid
graph TB
    A[User Browser] -->|HTTPS| B[React Frontend]
    B -->|REST API| C[FastAPI Backend]
    C -->|JWT Auth| D[Auth Middleware]
    C -->|ORM| E[SQLite/PostgreSQL]
    C -->|HTTP| F[CoinGecko API]
    C -->|Cache| G[Redis Optional]
    
    subgraph Backend Services
        C
        D
        E
    end
    
    subgraph External Services
        F
        G
    end
```

-----

## 🧪 Testing

### Manual Testing

```bash
# Run backend tests
pytest tests/

# Test specific endpoint
curl http://localhost:8000/health
```

### Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8000/crypto/prices
```

-----

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
1. Create a feature branch (`git checkout -b feature/AmazingFeature`)
1. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
1. Push to the branch (`git push origin feature/AmazingFeature`)
1. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Add docstrings to functions
- Write tests for new features
- Update documentation

-----

## 📝 Roadmap

- [ ] Add more casino games (Baccarat, Poker)
- [ ] Implement live sports betting odds
- [ ] Add chat system
- [ ] Mobile app (React Native)
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Social features (leaderboards, achievements)
- [ ] Payment gateway integration

-----

## ⚠️ Disclaimer

**This is a demonstration project for educational purposes only.**

- Not licensed for real-money gambling
- Requires proper licensing and compliance for commercial use
- No real cryptocurrency transactions
- Users must comply with local gambling laws

-----

## 📄 License

This project is licensed under the MIT License - see the <LICENSE> file for details.

-----

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [CoinGecko](https://www.coingecko.com/) - Crypto price API
- [React](https://reactjs.org/) - UI library
- [Tailwind CSS](https://tailwindcss.com/) - CSS framework
- [Render](https://render.com/) - Hosting platform

-----

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Scar4400/ibc-play/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Scar4400/ibc-play/discussions)
- **Email**: support@ibcplay.com

-----

## 🌟 Star History

If you find this project helpful, please consider giving it a ⭐!

[![Star History Chart](https://api.star-history.com/svg?repos=Scar4400/ibc-play&type=Date)](https://star-history.com/#Scar4400/ibc-play&Date)

-----

<div align="center">

**Made with ❤️ by the IBC Play Team**

[Website](https://ibcplay.com) · [Documentation](https://docs.ibcplay.com) · [Demo](https://demo.ibcplay.com)

</div>