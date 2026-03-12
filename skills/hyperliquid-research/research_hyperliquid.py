#!/usr/bin/env python3
"""
Hyperliquid Market Research Tool
Research BTC futures markets and optimize trade placement
Uses official hyperliquid-python-sdk
"""

import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Add SDK to path
WORKSPACE = "/home/africool/.openclaw/workspace"
sys.path.append(f"{WORKSPACE}/hyperliquid-python-sdk")

from hyperliquid.info import Info
from hyperliquid.utils import constants

# Master account
MASTER_ADDRESS = "0xc87c0284dd20bbf1285fca722cbae68e379cc291"

BASE_URL = constants.MAINNET_API_URL

def get_analysis():
    """Get comprehensive BTC analysis"""
    info = Info(BASE_URL, skip_ws=True)
    
    print("=" * 60)
    print("HYPERLIQUID BTC FUTURES RESEARCH")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. Get mid price
    mids = info.all_mids()
    btc_mid = float(mids.get("BTC", 0))
    print(f"\n📊 MARKET DATA")
    print(f"  Mid Price:    ${btc_mid:,.2f}")
    
    # 2. Order Book
    try:
        l2 = info.l2_snapshot("BTC")
        bids = l2.get("bids", [])[:5]
        asks = l2.get("asks", [])[:5]
        
        if bids and asks:
            best_bid = float(bids[0]["px"])
            best_ask = float(asks[0]["px"])
            spread = (best_ask - best_bid) / best_ask * 100
            
            bid_depth = sum(float(b["sz"]) * float(b["px"]) for b in bids)
            ask_depth = sum(float(a["sz"]) * float(a["px"]) for a in asks)
            
            print(f"\n📚 ORDER BOOK")
            print(f"  Best Bid:    ${best_bid:,.0f}")
            print(f"  Best Ask:    ${best_ask:,.0f}")
            print(f"  Spread:      {spread:.4f}%")
            print(f"  Bid Depth:   ${bid_depth:,.0f} (5 levels)")
            print(f"  Ask Depth:   ${ask_depth:,.0f} (5 levels)")
            print(f"  Imbalance:   {((bid_depth - ask_depth)/(bid_depth + ask_depth))*100:+.1f}%")
    except Exception as e:
        print(f"  Order book error: {e}")
    
    # 3. Account state
    try:
        state = info.user_state(MASTER_ADDRESS)
        equity = float(state.get("marginSummary", {}).get("accountValue", 0))
        print(f"\n💰 ACCOUNT")
        print(f"  Equity:      ${equity:,.2f}")
        
        # Positions
        positions = state.get("assetPositions", [])
        if positions:
            for p in positions:
                pos = p.get("position", {})
                if pos:
                    size = float(pos.get("szi", 0))
                    if size != 0:
                        entry = float(pos.get("entryPx", 0))
                        print(f"  Position:    {size:.5f} BTC @ ${entry:,.0f}")
    except Exception as e:
        print(f"  Account error: {e}")
    
    # 4. Suggested Entry/Exit
    print(f"\n🎯 OPTIMAL TRADE SETUP (Swing V2 Strategy)")
    
    # Entry: Buy on dips
    entry = btc_mid * 0.985  # 1.5% below
    print(f"  Limit Entry:  ${entry:,.0f} (-1.5%)")
    
    # Stop: Based on liquidation below $40k
    stop = 40000
    print(f"  Stop Loss:    ${stop:,.0f} (liquidation)")
    
    # Take profits (Swing V2)
    tp1 = btc_mid * 1.40
    tp2 = btc_mid * 1.70
    tp3 = btc_mid * 2.00
    print(f"  TP1 (40%):   ${tp1:,.0f}")
    print(f"  TP2 (70%):   ${tp2:,.0f}")
    print(f"  TP3 (100%):  ${tp3:,.0f}")
    
    # Risk
    print(f"\n⚠️ RISK ASSESSMENT")
    print(f"  Leverage:    10x max (Swing V2)")
    print(f"  Liquidation: Below $40k")
    
    print("=" * 60)

if __name__ == "__main__":
    get_analysis()
