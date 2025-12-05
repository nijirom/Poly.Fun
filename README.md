# Poly.Fun
Degenerate sniping with probabilistic edge.
## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Disclaimer](#disclaimer)

# Overview
Poly.Fun bridges the gap between off-chain information markets and on-chain decentralized exchanges. By monitoring the Polymarket CLOB (Central Limit Order Book) for significant price deviations, the system allows traders to capture volatility on Solana-based assets that are correlated to specific real-world outcomes


# Features
- Real-time Volatility Scanning: Python-based scanner monitors specific Polymarket Token IDs for custom price deltas.

- Instant Swap Routes: Integrated with Jupiter Aggregator to find the best liquidity paths.

- Non-Custodial Execution: All transactions are signed via the user's browser wallet (Phantom/Solflare); private keys are never exposed to the server.

- Custom Asset Mapping: JSON-based configuration to link specific prediction events to specific Solana SPL tokens.


# Architecture
- Backend: Python 3.10+, py-clob-client

- Frontend: Next.js 14, TypeScript, Tailwind CSS

- Blockchain Integration: @solana/web3.js, Jupiter v6 API


# Prerequisites
- Node.js (v18 or higher)

- Python (v3.9 or higher)

- Solana Wallet (Phantom or Solflare browser extension)

- RPC Node (Optional but recommended for production: Helius or QuickNode)


## Installation
### Backend Setup
Handles the data polling and signal generation.
```bash
cd backend
pip install -r requirements.txt
```
### Frontend Setup
Handles wallet connections and transaction executions
```bash
cd frontend
npm install
#or
yarn install
```
# Configuration
Navigate to config/market_map.json. This file maps the prediction market to the tradable asset.
-polymarket_token_id: The specific outcome ID from Polymarket (e.g., "Trump Wins 2024").
-targets: The Solana Mint Addresses (CA) for the tokens you wish to buy based on the signal direction
```json
{
    "polymarket_token_id": "YOUR_POLYMARKET_ID_HERE",
    "targets": {
        "UP": "SOLANA_MINT_ADDRESS_FOR_BULLISH_NEWS",
        "DOWN": "SOLANA_MINT_ADDRESS_FOR_BEARISH_NEWS"
    }
}
```

# Usage
1. Start the Scanner Open a terminal in the backend directory:
```bash
python scanner.py
```
2. Start the Terminal Open a separate terminal in the frontend directory:
```bash
npm run dev
```
3. Execute Trades
- Navigate to http://localhost:3000.

- Connect your Solana Wallet.

- Watch the terminal for signals.

- Click "Execute" when a volatility target is identified.

# Disclaimer
This software is for educational purposes only. Trading cryptocurrencies and prediction markets involves significant risk. This software does not constitute financial advice. The developers are not responsible for financial losses, slippage, or failed transactions due to network congestion.
