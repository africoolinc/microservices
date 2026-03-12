#!/usr/bin/env python3
"""
Hyperliquid Position Manager & Research Tool
Active position monitoring, management, and intelligent logging
"""

import sys
import json
import time
from datetime import datetime
from pathlib import Path

WORKSPACE = "/home/africool/.openclaw/workspace"
sys.path.append(f"{WORKSPACE}/hyperliquid-python-sdk")

from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
import eth_account

# Configuration
MASTER_ADDRESS = "0xc87c0284dd20bbf1285fca722cbae68e379cc291"
AGENT_ADDRESS = "0x970d1e1756804cc1420e1202cd3833d83f2b93d5"
SECRETS_PATH = f"{WORKSPACE}/.secrets/hyperliquid.json"

# Strategy Parameters
MAX_LEVERAGE = 10
TAKE_PROFIT_1 = 0.40
TAKE_PROFIT_2 = 0.70
TAKE_PROFIT_3 = 1.00
LIQUIDATION_PROTECTION = 40000

# Files
LOG_FILE = Path(WORKSPACE) / "projects/trading/position_manager_log.jsonl"
STATE_FILE = Path(WORKSPACE) / "projects/trading/position_state.json"
ANALYSIS_FILE = Path(WORKSPACE) / "projects/trading/market_analysis.json"

class PositionManager:
    def __init__(self):
        # Load credentials
        with open(SECRETS_PATH) as f:
            creds = json.load(f)
        
        self.secret_key = creds['secret_key']
        self.account = eth_account.Account.from_key(self.secret_key)
        self.base_url = constants.MAINNET_API_URL
        
        self.info = Info(self.base_url, skip_ws=True)
        self.exchange = Exchange(self.account, self.base_url, account_address=MASTER_ADDRESS)
        
        self.load_state()
        
    def log(self, msg, level="INFO"):
        entry = {"time": datetime.now().isoformat(), "msg": msg, "level": level}
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"[PosMgr] {msg}")
    
    def load_state(self):
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                self.state = json.load(f)
        else:
            self.state = {
                "positions": [],
                "last_update": None,
                "alerts": [],
                "total_pnl": 0,
                "trades_count": 0
            }
    
    def save_state(self):
        self.state["last_update"] = datetime.now().isoformat()
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def get_market_data(self):
        """Get comprehensive market data"""
        mids = self.info.all_mids()
        btc_mid = float(mids.get("BTC", 0))
        
        # Get order book
        try:
            l2 = self.info.l2_snapshot("BTC")
            bids = l2.get("bids", [])[:5]
            asks = l2.get("asks", [])[:5]
            
            if bids and asks:
                best_bid = float(bids[0]["px"])
                best_ask = float(asks[0]["px"])
                spread = (best_ask - best_bid) / best_ask * 100
                
                bid_depth = sum(float(b["sz"]) * float(b["px"]) for b in bids)
                ask_depth = sum(float(a["sz"]) * float(a["px"]) for a in asks)
                
                book = {
                    "best_bid": best_bid,
                    "best_ask": best_ask,
                    "spread": spread,
                    "bid_depth": bid_depth,
                    "ask_depth": ask_depth,
                    "imbalance": (bid_depth - ask_depth) / (bid_depth + ask_depth) if (bid_depth + ask_depth) > 0 else 0
                }
            else:
                book = None
        except:
            book = None
        
        return {
            "btc_price": btc_mid,
            "order_book": book,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_account_data(self):
        """Get account positions and equity"""
        state = self.info.user_state(MASTER_ADDRESS)
        equity = float(state.get("marginSummary", {}).get("accountValue", 0))
        
        positions = []
        for p in state.get("assetPositions", []):
            pos = p.get("position", {})
            if pos and float(pos.get("szi", 0)) != 0:
                positions.append({
                    "coin": pos.get("coin"),
                    "size": float(pos.get("szi", 0)),
                    "entry_price": float(pos.get("entryPx", 0)),
                    "liq_price": float(pos.get("liquidationPx", 0)),
                    "margin_used": float(pos.get("marginUsed", 0))
                })
        
        return {
            "equity": equity,
            "positions": positions,
            "timestamp": datetime.now().isoformat()
        }
    
    def calculate_pnl(self, entry, current, size, side="Long"):
        """Calculate PnL"""
        if side == "Long":
            pnl_pct = (current - entry) / entry
        else:
            pnl_pct = (entry - current) / entry
        
        pnl_usd = size * current * pnl_pct
        return pnl_pct, pnl_usd
    
    def analyze_opportunities(self, market, account):
        """Analyze market for trading opportunities"""
        opportunities = []
        btc_price = market["btc_price"]
        
        # Opportunity 1: Buy on dip
        if account["positions"]:
            for pos in account["positions"]:
                entry = pos["entry_price"]
                size = pos["size"]
                current = btc_price
                
                pnl_pct, pnl_usd = self.calculate_pnl(entry, current, size)
                
                # Check take profit triggers
                if pnl_pct >= TAKE_PROFIT_3:
                    opportunities.append({
                        "type": "TAKE_PROFIT_100",
                        "action": "Sell 80%",
                        "pnl_pct": pnl_pct * 100,
                        "pnl_usd": pnl_usd
                    })
                elif pnl_pct >= TAKE_PROFIT_2:
                    opportunities.append({
                        "type": "TAKE_PROFIT_70",
                        "action": "Sell 50%",
                        "pnl_pct": pnl_pct * 100,
                        "pnl_usd": pnl_usd
                    })
                elif pnl_pct >= TAKE_PROFIT_1:
                    opportunities.append({
                        "type": "TAKE_PROFIT_40",
                        "action": "Sell 30%",
                        "pnl_pct": pnl_pct * 100,
                        "pnl_usd": pnl_usd
                    })
                
                # Check re-entry (dip)
                if pnl_pct < 0:
                    dip = abs(pnl_pct)
                    if dip >= 0.08:
                        opportunities.append({
                            "type": "REENTRY_FULL",
                            "action": "Buy 100% on dip",
                            "dip_pct": dip * 100
                        })
                    elif dip >= 0.05:
                        opportunities.append({
                            "type": "REENTRY_HALF",
                            "action": "Buy 50% on dip",
                            "dip_pct": dip * 100
                        })
        
        # Opportunity 2: New position (if no position)
        if not account["positions"]:
            entry = btc_price * 0.985  # 1.5% below
            opportunities.append({
                "type": "NEW_POSITION",
                "action": f"Buy at ${entry:,.0f}",
                "entry_price": entry
            })
        
        # Opportunity 3: Order book imbalance
        if market["order_book"]:
            imb = market["order_book"]["imbalance"]
            if imb > 0.3:
                opportunities.append({
                    "type": "BUY_SIGNAL",
                    "action": "Strong bid pressure",
                    "imbalance": imb
                })
            elif imb < -0.3:
                opportunities.append({
                    "type": "SELL_SIGNAL",
                    "action": "Strong ask pressure",
                    "imbalance": imb
                })
        
        return opportunities
    
    def generate_report(self, market, account, opportunities):
        """Generate intelligent status report"""
        btc_price = market["btc_price"]
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "market": {
                "btc_price": btc_price,
                "spread": market["order_book"]["spread"] if market["order_book"] else None,
                "imbalance": market["order_book"]["imbalance"] if market["order_book"] else None
            },
            "account": {
                "equity": account["equity"],
                "positions_count": len(account["positions"]),
                "positions": account["positions"]
            },
            "opportunities": opportunities,
            "recommendations": []
        }
        
        # Generate recommendations
        if opportunities:
            for opp in opportunities:
                if "TAKE_PROFIT" in opp["type"]:
                    report["recommendations"].append(f"🎯 {opp['type']}: {opp['action']} (${opp['pnl_usd']:+.2f})")
                elif "REENTRY" in opp["type"]:
                    report["recommendations"].append(f"📥 {opp['type']}: {opp['action']}")
                elif opp["type"] == "NEW_POSITION":
                    report["recommendations"].append(f"🆕 {opp['type']}: {opp['action']}")
        
        # Check liquidation risk
        for pos in account["positions"]:
            if pos["liq_price"] > 0 and pos["liq_price"] < LIQUIDATION_PROTECTION:
                report["recommendations"].append(f"⚠️ LIQUIDATION RISK: ${pos['liq_price']:,.0f}")
        
        # Save analysis
        with open(ANALYSIS_FILE, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def run(self):
        """Main execution"""
        self.log("=" * 50)
        self.log("POSITION MANAGER CYCLE")
        self.log("=" * 50)
        
        # Get data
        market = self.get_market_data()
        account = self.get_account_data()
        
        self.log(f"BTC: ${market['btc_price']:,.0f}")
        self.log(f"Equity: ${account['equity']:,.2f}")
        self.log(f"Positions: {len(account['positions'])}")
        
        # Analyze opportunities
        opportunities = self.analyze_opportunities(market, account)
        
        # Generate report
        report = self.generate_report(market, account, opportunities)
        
        self.log(f"\n📊 ANALYSIS:")
        for rec in report["recommendations"]:
            self.log(f"  {rec}")
        
        if not report["recommendations"]:
            self.log("  ✅ No action required - HOLD")
        
        self.log("=" * 50)
        
        # Save state
        self.state["positions"] = account["positions"]
        self.save_state()
        
        return report

if __name__ == "__main__":
    manager = PositionManager()
    report = manager.run()
    
    # Print summary
    print("\n" + "=" * 50)
    print("STATUS REPORT")
    print("=" * 50)
    print(f"BTC Price: ${report['market']['btc_price']:,.2f}")
    print(f"Equity: ${report['account']['equity']:,.2f}")
    print(f"Open Positions: {report['account']['positions_count']}")
    print("\nRecommendations:")
    for rec in report["recommendations"]:
        print(f"  • {rec}")
    print("=" * 50)
