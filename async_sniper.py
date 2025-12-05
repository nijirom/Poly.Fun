import asyncio
import aiohttp
import websockets
import json
import os
import base64
import re
from datetime import datetime
from colorama import Fore, Style, init
from dotenv import load_dotenv

# Solana Imports
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts

# Configuration
load_dotenv()
init(autoreset=True)

RPC_URL = os.getenv("RPC_URL", "https://api.mainnet-beta.solana.com")
PRIVATE_KEY_STRING = os.getenv("SOLANA_PRIVATE_KEY")
SLIPPAGE_BPS = 50  # 0.5%
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
SOL_MINT = "So11111111111111111111111111111111111111112"

# --- CUSTOM BIG MOVE CONFIGURATION ---
# A "Big Move" is defined here.
# Polymarket prices range 0.00 to 1.00.
MOVE_THRESHOLD = 0.03  # Trigger if price moves 3 cents (e.g., 0.50 -> 0.53)
TIME_WINDOW_SECONDS = 60  # The move must happen within this window

class PriceTracker:
    """Tracks state of markets to detect big moves."""
    def __init__(self):
        # Format: { token_id: { 'price': float, 'ts': timestamp, 'question': str } }
        self.market_state = {}

    def is_big_move(self, token_id, new_price, question):
        now = datetime.now().timestamp()
        
        if token_id not in self.market_state:
            # Initialize state
            self.market_state[token_id] = {'price': new_price, 'ts': now, 'question': question}
            return False, 0

        old_data = self.market_state[token_id]
        old_price = old_data['price']
        
        # Calculate price delta
        delta = new_price - old_price
        
        # Update state regardless of move (to keep tracking rolling updates)
        self.market_state[token_id] = {'price': new_price, 'ts': now, 'question': question}

        # Check Logic: Absolute move > Threshold
        if abs(delta) >= MOVE_THRESHOLD:
            return True, delta
        
        return False, 0

class SolanaSniper:
    def __init__(self):
        self.tracker = PriceTracker()
        self.wallet = None
        if PRIVATE_KEY_STRING:
            self.wallet = Keypair.from_base58_string(PRIVATE_KEY_STRING)
            print(f"{Fore.GREEN}[+] Wallet loaded: {self.wallet.pubkey()}")
        else:
            print(f"{Fore.YELLOW}[!] Read-Only Mode (No Private Key)")

    async def get_initial_markets(self):
        """Fetch top markets via REST to know what to subscribe to."""
        async with aiohttp.ClientSession() as session:
            url = "https://clob.polymarket.com/markets"
            async with session.get(url) as resp:
                data = await resp.json()
                # Get top 50 active markets
                return data.get('data', [])[:50]

    async def find_tokens(self, keywords):
        """Async DexScreener Search"""
        ignore = {'will', 'the', 'be', 'of', 'in', 'by', 'to', 'a', 'an', 'at', 'on', 'is', 'for', 'price', 'what', 'who'}
        clean_keys = [w for w in keywords if w.lower() not in ignore and len(w) > 3]
        query = " ".join(clean_keys)
        
        if not clean_keys: 
            return []

        print(f"{Fore.CYAN}   [Search] Querying Solana for: {query}")
        async with aiohttp.ClientSession() as session:
            url = f"https://api.dexscreener.com/latest/dex/search?q={query}"
            async with session.get(url) as resp:
                if resp.status != 200: return []
                data = await resp.json()
                
                # Filter for Liquid Solana Pairs
                valid_pairs = []
                for p in data.get('pairs', []):
                    if p['chainId'] == 'solana' and p.get('liquidity', {}).get('usd', 0) > 2000:
                        valid_pairs.append(p)
                return valid_pairs

    async def execute_buy(self, token_address, token_symbol):
        """Async Jupiter Swap"""
        if not self.wallet:
            print(f"{Fore.RED}   [!] No wallet. Cannot Buy.")
            return

        async with AsyncClient(RPC_URL) as rpc:
            async with aiohttp.ClientSession() as session:
                # 1. Get Quote (Buy 0.05 SOL worth)
                amount_lamports = 50000000 # 0.05 SOL
                quote_url = f"https://quote-api.jup.ag/v6/quote?inputMint={SOL_MINT}&outputMint={token_address}&amount={amount_lamports}&slippageBps={SLIPPAGE_BPS}"
                
                async with session.get(quote_url) as q_resp:
                    quote_data = await q_resp.json()
                
                if "error" in quote_data:
                    print(f"{Fore.RED}   [!] Quote Error: {quote_data}")
                    return

                # 2. Get Swap Transaction
                swap_payload = {
                    "quoteResponse": quote_data,
                    "userPublicKey": str(self.wallet.pubkey()),
                    "wrapAndUnwrapSol": True
                }
                
                async with session.post("https://quote-api.jup.ag/v6/swap", json=swap_payload) as s_resp:
                    swap_data = await s_resp.json()
                
                # 3. Sign and Send
                raw_tx_str = swap_data.get("swapTransaction")
                if not raw_tx_str: return

                raw_tx = VersionedTransaction.from_bytes(base64.b64decode(raw_tx_str))
                signature = self.wallet.sign_message(raw_tx.message.to_bytes_versioned(raw_tx.message))
                signed_tx = VersionedTransaction.populate(raw_tx.message, [signature])

                print(f"{Fore.YELLOW}   [Tx] Sending transaction...")
                # Simulate check
                user_confirm = input(f"{Fore.MAGENTA}   >>> CONFIRM BUY {token_symbol}? (y/n): ")
                if user_confirm.lower() == 'y':
                    try:
                        tx_sig = await rpc.send_transaction(signed_tx, opts=TxOpts(skip_preflight=True))
                        print(f"{Fore.GREEN}   [$] SUCCESS! Sig: {tx_sig.value}")
                    except Exception as e:
                        print(f"{Fore.RED}   [!] Tx Failed: {e}")

    async def run(self):
        print(f"{Fore.CYAN}=== Async Poly-Solana Sniper Started ===")
        
        # 1. Get active asset IDs to subscribe to
        initial_markets = await self.get_initial_markets()
        # Map asset_id to question for easy lookup
        asset_map = {}
        for m in initial_markets:
            # Depending on market type, grab the 'Yes' token or the main outcome
            try:
                # Simplified: Grab the first token ID (usually the "Yes" or primary outcome)
                token_id = json.loads(m['clob_token_ids'])[0] 
                asset_map[token_id] = m['question']
            except:
                pass

        token_ids_to_watch = list(asset_map.keys())
        print(f"{Fore.BLUE}[i] Watching {len(token_ids_to_watch)} markets for moves > {MOVE_THRESHOLD}...")

        # 2. Connect to WebSocket
        uri = "wss://ws-clob.polymarket.com/ws"
        async with websockets.connect(uri) as websocket:
            
            # 3. Subscribe
            sub_msg = {
                "type": "market",
                "assets_ids": token_ids_to_watch,
                "channel": "level1" # Provides Best Bid/Ask
            }
            await websocket.send(json.dumps(sub_msg))
            print(f"{Fore.GREEN}[Connected] Listening for ticks...")

            # 4. Event Loop
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)

                    # Iterate through updates
                    for update in data:
                        if 'event_type' in update and update['event_type'] == 'price_change':
                            # Extract Data
                            token_id = update.get('asset_id')
                            price = float(update.get('price', 0))
                            
                            if token_id in asset_map:
                                question = asset_map[token_id]
                                
                                # Check Big Move Logic
                                is_big, delta = self.tracker.is_big_move(token_id, price, question)
                                
                                if is_big:
                                    direction = "UP" if delta > 0 else "DOWN"
                                    color = Fore.GREEN if delta > 0 else Fore.RED
                                    print(f"\n{color}[ALERT] {direction} MOVE ({delta:.3f}) on: {question}")
                                    
                                    # Extract Keywords & Search Solana
                                    # Remove non-alphanumeric
                                    clean_q = re.sub(r'[^\w\s]', '', question) 
                                    keywords = clean_q.split()
                                    
                                    tokens = await self.find_tokens(keywords)
                                    
                                    if tokens:
                                        best = tokens[0]
                                        print(f"{Fore.GREEN}   -> Found: {best['baseToken']['symbol']} (${best['priceUsd']})")
                                        await self.execute_buy(best['baseToken']['address'], best['baseToken']['symbol'])
                                    else:
                                        print(f"{Fore.LIGHTBLACK_EX}   -> No Solana tokens found.")

                except websockets.exceptions.ConnectionClosed:
                    print("Connection lost. Reconnecting...")
                    break
                except Exception as e:
                    pass

if __name__ == "__main__":
    bot = SolanaSniper()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("Exiting...")