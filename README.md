# IB Crypto Play — Enhanced (FastAPI demo)

A demo sports-betting & casino prototype with cryptocurrency integration. This repo provides:

- FastAPI backend (JWT auth, SQLite/Postgres via SQLAlchemy)
- CoinGecko integration for real crypto prices
- SQLite or Postgres persistence
- Optional Redis for caching and rate limiting
- Docker + docker-compose for local dev (Postgres + Redis)
- Alembic migrations bootstrap
- Demo UI: `ib-crypto-play-demo.html` (single-file React demo)
- GitHub Actions CI workflow and Render deployment config (Docker)

> This is a **demo prototype**. Do not use for real-money gambling without legal/regulatory, security, and financial audits.

---

## Quick feature summary
- Users, wallets, bets, transactions, crypto holdings stored in DB
- Real-time price lookup (CoinGecko) with caching
- Basic casino slots endpoint and bet placement/settlement endpoints
- Rate limiting fallback and recommended Redis-based limiter
- Docker Compose for local environment (Postgres + Redis)
- Improvements: logging, input validation, error handling, static demo

---

## Local dev — recommended (Docker)

**Prereqs**
- Docker & Docker Compose installed.

**Run**
1. Copy `.env.example` to `.env` and edit values (especially `SECRET_KEY`).
2. Start containers:
   ```bash
   docker compose up --build
