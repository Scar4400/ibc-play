# IBC Play — Sports Betting & Casino Demo with Crypto Integration

A fully operational prototype for a sports betting and casino platform using cryptocurrency. Built with FastAPI backend, SQLite/Postgres persistence, CoinGecko for real-time prices, and a React-embedded HTML demo UI.

**Disclaimer**: This is a demo. Not for real-money use without audits/compliance.

## Features
- User registration/login with JWT auth
- Wallet management (USD + crypto: BTC, ETH, SOL, BNB)
- Deposits/withdrawals/transfers with real prices
- Sports bets placement/settlement (simulated outcomes)
- Casino games (e.g., slots with RNG)
- DB persistence for all data
- Rate limiting, logging, error handling
- Deployment-ready for Render.com (with health checks)

## Architecture Diagram
```mermaid
graph TD
    A[User] -->|API Calls| B[FastAPI Backend]
    B -->|JWT Auth| C[Endpoints: /login, /bets, /casino/play, /deposit etc.]
    B -->|SQLAlchemy| D[DB: SQLite/Postgres - Users, Wallets, Bets, Txns]
    B -->|httpx| E[CoinGecko API - Real Prices]
    B -->|Optional Redis| F[Caching & Rate Limiting]
    G[Demo HTML UI - React] -->|Fetch| B