# Poly.Fun
**Degenerate sniping with probabilistic edge.**

![Python](https://img.shields.io/badge/Python-3.9%2B-blue) ![Solana](https://img.shields.io/badge/Solana-Mainnet-green) ![License](https://img.shields.io/badge/License-MIT-lightgrey)

## Table of Contents

* [Important Disclaimer](#important-disclaimer)
* [Technical Summary](#technical-summary)
* [Features](#features)
* [Architecture](#architecture)
* [Installation](#installation)
    * [Prerequisites](#prerequisites)
    * [Setup](#setup)
* [Usage](#usage)
    * [Configuration Variables](#configuration-variables)
* [Requirements](#requirements)
* [Roadmap](#roadmap)

---

## Important Disclaimer

**EDUCATIONAL PURPOSES ONLY.**
This software handles real cryptocurrency private keys and executes financial transactions.

* **High Risk:** Memecoins are volatile assets. Slippage can be high, and rug pulls are common.
* **Security:** Never commit your `.env` file or private keys to GitHub.
* **Liability:** The authors are not responsible for any financial losses incurred while using this bot. **Use a burner wallet with small amounts of funds.**

---

## Technical Summary

Poly.Fun is built on Python’s asyncio framework for non-blocking concurrency, this system ingests millisecond-latency price ticks from Polymarket’s CLOB via WebSockets. An in-memory state machine processes data streams to identify volatility anomalies against a configurable threshold. The asset discovery engine employs lightweight NLP for keyword extraction and validates liquidity via the DexScreener API. Trade execution is handled by the Solana Python SDK (solders and solana-py) interacting with the Jupiter Aggregator v6 API, enabling secure, local transaction signing and asynchronous RPC broadcasting.

---

## Features

* **Async WebSocket Core:** Connects directly to Polymarket's CLOB (Central Limit Order Book) for millisecond-latency price updates, avoiding slow REST polling.
* **Custom "Big Move" Logic:** Tracks market state in memory and only triggers alerts on price swings exceeding a defined threshold (e.g., > 3 cents within a 60s window).
* **NLP Keyword Extraction:** Uses smart filtering to remove stop-words and identify tradable tickers based on prediction market questions.
* **Liquidity Filtering:** Automatically filters DexScreener results to avoid "dead" or illiquid scam tokens.
* **Jupiter v6 Integration:** Uses the Jupiter Aggregator API for the most efficient swap routes on Solana.
* **Safety Confirmations:** Includes an interactive "Press Y to Confirm" step to prevent accidental buys on false positives.

---

## Architecture

1.  **Monitor:** The bot subscribes to the top 50 active Polymarket events via WebSocket (`wss://ws-clob.polymarket.com/ws`).
2.  **Analyze:** It compares incoming ticks against a local state cache. If `abs(NewPrice - OldPrice) > THRESHOLD`, an alert is triggered.
3.  **Search:** The bot parses the market question (e.g., *"Will Trump win...?"*) into keywords and queries the DexScreener API for Solana pairs.
4.  **Route:** It queries Jupiter for a swap quote (SOL -> Token).
5.  **Execute:** It constructs a signed transaction using `solders` and broadcasts it via `solana-py`.

---

## Installation

### Prerequisites
* Python 3.9+
* A Solana Wallet (Phantom, Solflare, etc.) exported as a Base58 Private Key.
* (Optional) A custom RPC URL (Helius, QuickNode, Alchemy) for faster execution.

### Setup

1.  **Clone the Repository**
    ```bash
    gh repo clone nijirom/Poly.Fun
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Configuration**
   Create a `.env` file in the root directory. Run the command matching your OS:
    
    **Windows (Command Prompt):**
    ```cmd
    type nul > .env
    ```
    
    **Windows (PowerShell):**
    ```powershell
    ni .env
    ```
    
    **Mac / Linux:**
    ```bash
    touch .env
    ```

    Open the file and add your secrets (do not share this file!):
    ```env
    # Your Wallet Private Key (Base58 string)
    SOLANA_PRIVATE_KEY=your_private_key_here
    
    # Optional: Custom RPC (defaults to public mainnet)
    RPC_URL=[https://api.mainnet-beta.solana.com](https://api.mainnet-beta.solana.com)
    ```

---

## Usage

Run the sniper:

```bash
python async_sniper.py
```

### Configuration Variables
You can tweak the logic at the top of async_sniper.py:

    MOVE_THRESHOLD = 0.03: The price change (in cents) required to trigger a search.

    SLIPPAGE_BPS = 50: The slippage tolerance (50 = 0.5%).

    USDC_MINT / SOL_MINT: The input token for your swaps (default is SOL).

---


## Requirements
``` plaintext
aiohttp
websockets
solders
solana
colorama
python-dotenv
requests
```
---

## Roadmap
[ ] Short Selling: Integrate with perpetual protocols to short tokens on bad news.

[ ] Telegram Integration: Send alerts to a Telegram channel instead of just the CLI.

[ ] MEV Protection: Integrate Jito bundles to avoid being sandwiched on buys.

[ ] AI Analysis: Use a lightweight LLM to better determine sentiment (Bullish/Bearish) before buying.
