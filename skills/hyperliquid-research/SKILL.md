# Hyperliquid Research Skill

Research BTC futures markets on Hyperliquid, analyze optimal trade placement strategies, and generate actionable trading insights.

## Overview

This skill provides tools to:
- Fetch real-time market data from Hyperliquid API
- Analyze order book depth and liquidity
- Calculate optimal entry/exit points
- Research funding rates and market structure
- **Active position management and monitoring**
- **Intelligent logging for informed decision making**

## Prerequisites

```bash
pip install hyperliquid-python-sdk eth-account requests pandas google-api-python-client
```

## Configuration

```json
// .secrets/hyperliquid.json
{
    "secret_key": "0x...",
    "account_address": "0xc87c0284dd20bbf1285fca722cbae68e379cc291"
}
```

## API Base URLs

| Network | URL |
|---------|-----|
| Mainnet | `https://api.hyperliquid.xyz` |
| Testnet | `https://api.hyperliquid-testnet.xyz` |

## Core Functions

### 1. Market Data Fetching

```python
import requests
import json

BASE_URL = "https://api.hyperliquid.xyz"

def info_request(method, params=None):
    """Make info API request"""
    response = requests.post(
        f"{BASE_URL}/info",
        json={"type": method, **(params or {})},
        headers={"Content-Type": "application/json"}
    )
    return response.json()

# Get all mid prices
mids = info_request("allMids")

# Get meta (asset info)
meta = info_request("meta")

# Get user state
user_state = info_request("userState", {"user": "0xc87c..."})
```

### 2. Order Book Analysis

```python
def get_order_book(symbol="BTC"):
    """Get L2 order book with depth"""
    l2_data = info_request("l2Snapshot", {"coin": symbol})
    
    bids = []  # Buy orders
    asks = []  # Sell orders
    
    for level in l2_data.get("bids", [])[:10]:  # Top 10 bids
        bids.append({"px": float(level["px"]), "sz": float(level["sz"])})
    
    for level in l2_data.get("asks", [])[:10]:  # Top 10 asks
        asks.append({"px": float(level["px"]), "sz": float(level["sz"])})
    
    return {"bids": bids, "asks": asks}

def analyze_spread(book):
    """Calculate spread and depth"""
    best_bid = book["bids"][0]["px"] if book["bids"] else 0
    best_ask = book["asks"][0]["px"] if book["asks"] else 0
    
    spread = best_ask - best_bid
    spread_pct = (spread / best_ask) * 100
    
    # Calculate depth
    bid_depth = sum(b["sz"] for b in book["bids"][:5])
    ask_depth = sum(a["sz"] for a in book["asks"][:5])
    
    return {
        "spread": spread,
        "spread_pct": spread_pct,
        "bid_depth_5": bid_depth,
        "ask_depth_5": ask_depth,
        "imbalance": (bid_depth - ask_depth) / (bid_depth + ask_depth)
    }
```

### 3. Funding Rate Analysis

```python
def get_funding_rate(symbol="BTC"):
    """Get current funding rate"""
    ticker = info_request("ticker", {"coin": symbol})
    
    return {
        "funding_rate": float(ticker.get("funding", 0)),
        "open_interest": float(ticker.get("openInterest", 0)),
        "mark_price": float(ticker.get("markPx", 0)),
        "index_price": float(ticker.get("idxPx", 0))
    }

def estimate_funding_cost(funding_rate, position_value, hours=24):
    """Calculate funding cost for position"""
    # Funding is paid every 8 hours
    periods = hours / 8
    cost = position_value * funding_rate * periods
    return cost
```

### 4. Candle Data for Strategy

```python
def get_candles(symbol="BTC", interval="1h", hours=168):
    """Get historical candles (7 days of 1h data = 168 hours)"""
    import time
    end_time = int(time.time())
    start_time = end_time - (hours * 3600)
    
    candles = info_request("candleSnapshot", {
        "coin": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time
    })
    
    return candles

def analyze_volatility(candles):
    """Calculate volatility metrics"""
    closes = [float(c["c"]) for c in candles]
    highs = [float(c["h"]) for c in candles]
    lows = [float(c["l"]) for c in candles]
    
    # Simple volatility (ATR-like)
    ranges = [h - l for h, l in zip(highs, lows)]
    avg_range = sum(ranges) / len(ranges)
    
    # Daily range
    daily_range = sum(ranges[-24:]) / 24  # Last 24 candles
    
    return {
        "avg_hourly_range": avg_range,
        "avg_daily_range": daily_range,
        "current_price": closes[-1],
        "high_24h": max(highs[-24:]),
        "low_24h": min(lows[-24:]),
        "range_24h_pct": (max(highs[-24:]) - min(lows[-24:])) / closes[-1] * 100
    }
```

### 5. Position Sizing Calculator

```python
def calculate_position_size(account_value, risk_pct, entry, stop_loss):
    """Calculate optimal position size based on risk"""
    risk_amount = account_value * risk_pct
    
    # Risk = Position Size * (Entry - Stop Loss)
    # Position Size = Risk / (Entry - Stop Loss)
    position_size = risk_amount / abs(entry - stop_loss)
    
    return position_size

def calculate_leverage(entry, liquidation_target, position_size):
    """Calculate required leverage"""
    position_value = position_size * entry
    margin_required = position_value * (1 - (liquidation_target / entry))
    leverage = position_value / margin_required
    
    return leverage
```

## Optimal Trade Placement Strategy

### Entry Point Selection

| Condition | Entry Strategy |
|-----------|----------------|
| Trend Up + Pullback | Buy at 1-2% below current price (limit) |
| Range Bound | Buy at support, sell at resistance |
| High Funding (negative) | Enter long (receive funding) |
| Low Liquidity | Use smaller position size |

### Order Types

| Order Type | Best For | Example |
|------------|----------|---------|
| **Limit** |.entries | Place 1-2% below market |
| **Market** | Quick entries | Breaking out of range |
| **Post-Only** | Maker fees | Adding liquidity |

### Optimal Order Placement

```python
def suggest_entry(market_price, volatility, funding_rate):
    """Suggest optimal entry parameters"""
    
    # Entry: 1.5% below market for buying
    limit_price = market_price * 0.985
    
    # Stop loss: Based on daily range
    stop_loss = market_price - (volatility["avg_daily_range"] * 2)
    
    # Take profits at 40%, 70%, 100%
    tp1 = market_price * 1.40
    tp2 = market_price * 1.70
    tp3 = market_price * 2.00
    
    return {
        "limit_price": limit_price,
        "stop_loss": stop_loss,
        "take_profits": [tp1, tp2, tp3],
        "position_pct": 0.10 if funding_rate > 0 else 0.15,  # More if receiving funding
        "rationale": "Receiving funding" if funding_rate > 0 else "Standard"
    }
```

## Research Tools

### Run Full Market Analysis

```bash
python3 << 'EOF'
import requests
import json
import time

BASE_URL = "https://api.hyperliquid.xyz/info"

def query(method, params=None):
    r = requests.post(BASE_URL, json={"type": method, **(params or {})})
    return r.json()

# 1. Get BTC ticker
ticker = query("ticker", {"coin": "BTC"})
print(f"Mark: ${ticker.get('markPx')}")
print(f"Index: ${ticker.get('idxPx')}")
print(f"Funding: {float(ticker.get('funding', 0))*100:.4f}%")
print(f"Open Interest: ${float(ticker.get('openInterest', 0)):,.0f}")

# 2. Get order book
l2 = query("l2Snapshot", {"coin": "BTC"})
best_bid = float(l2["bids"][0]["px"])
best_ask = float(l2["asks"][0]["px"])
spread = (best_ask - best_bid) / best_ask * 100
print(f"Spread: {spread:.4f}%")

# 3. Get positions
user = "0xc87c0284dd20bbf1285fca722cbae68e379cc291"
state = query("userState", {"user": user})
print(f"Equity: ${float(state['marginSummary']['accountValue']):.2f}")
EOF
```

## Advanced: Order Book Liquidity Analysis

```python
def find_liquidity_zones(book, depth_pct=0.01):
    """Find significant liquidity zones"""
    zones = []
    
    # Convert to USD value
    for side in ["bids", "asks"]:
        cumulative = 0
        for level in book[side]:
            value = level["px"] * level["sz"]
            cumulative += value
            
            if cumulative > 10000:  # $10k zone
                zones.append({
                    "side": side,
                    "price": level["px"],
                    "cumulative_usd": cumulative
                })
                cumulative = 0
    
    return zones
```

## Best Practices

1. **Always check spread** before market orders (>0.1% = expensive)
2. **Use limit orders** for better fills
3. **Check funding** - can earn or pay significant amounts
4. **Monitor OI** - high OI + low liquidity = volatile
5. **Set stop losses** based on daily volatility (2x ATR)
6. **Start small** - test strategies with <5% of portfolio

## Skill Status

- **Created**: 2026-03-09
- **Location**: `projects/members/Gibson/skills/hyperliquid-research/`
- **Main Script**: `research_hyperliquid.py`

## Position Manager Tool

Active position monitoring, management, and intelligent logging:

```bash
python3 projects/members/Gibson/skills/hyperliquid-research/position_manager.py
```

### Features:
- Real-time position monitoring
- Automatic take profit / re-entry analysis
- Order book imbalance detection
- Liquidation risk alerts
- Recommendations generation

### Output Files:
- `projects/trading/position_manager_log.jsonl` - Activity log
- `projects/trading/position_state.json` - Position state
- `projects/trading/market_analysis.json` - Market analysis

## Gmail Calendar Integration

To sync trading reports to Gmail Calendar:

1. Enable Google Calendar API in Google Cloud Console
2. Download credentials as `credentials.json`
3. Store in `.secrets/gmail/calendar_credentials.json`

```python
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def create_calendar_event(summary, description, start_time, end_time):
    """Create a calendar event for trading report"""
    service = build('calendar', 'v3', credentials=creds)
    
    event = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_time},
        'end': {'dateTime': end_time},
    }
    
    event = service.events().insert(calendarId='primary', body=event).execute()
    return event.get('htmlLink')

# Usage
create_calendar_event(
    "📊 Trading Report - BTC Position",
    "Equity: $22.91 | PnL: +2.3% | Action: HOLD",
    "2026-03-09T20:00:00+03:00",
    "2026-03-09T20:30:00+03:00"
)
```

## Notion Integration

To sync to Notion:

```python
import requests

NOTION_API_KEY = "secret_..."
NOTION_DB_ID = "..."

def create_notion_page(title, content):
    """Create a page in Notion database"""
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    data = {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": {
            "Title": {"title": [{"text": {"content": title}}]},
            "Status": {"select": {"name": "Active"}},
            "Date": {"date": {"start": datetime.now().isoformat()}}
        },
        "children": [
            {"paragraph": {"rich_text": [{"text": {"content": content}}]}}
        ]
    }
    return requests.post(url, json=data, headers=headers).json()
```

## Skill Usage

1. **Run Position Manager** (every 4 hours):
```bash
python3 projects/members/Gibson/skills/hyperliquid-research/position_manager.py
```

2. **Run Market Research**:
```bash
python3 projects/members/Gibson/skills/hyperliquid-research/research_hyperliquid.py
```

3. **View Latest Analysis**:
```bash
cat projects/trading/market_analysis.json
```

## Status

- **Active**: Running on heartbeat cycle
- **Last Run**: Every 4 hours
- **Output**: `projects/trading/market_analysis.json`

## Report Sync Tool

Automatically sync trading reports to Gmail Calendar and Notion:

```bash
python3 projects/members/Gibson/skills/hyperliquid-research/report_sync.py
```

### Features:
- Generates comprehensive trading summary
- Syncs to Notion (if configured)
- Creates iCal files for Gmail Calendar import

### Files Generated:
- `memory/calendar/trading_report_YYYYMMDD_HHMM.ics` - Individual reports
- `memory/calendar/latest_trading_report.ics` - Latest report (importable)

### Notion Setup:
```bash
python3 projects/members/Gibson/skills/hyperliquid-research/notion_reporter.py
```
Will show setup instructions if not configured.

## Skill Components

| Script | Purpose |
|--------|---------|
| `research_hyperliquid.py` | Market research |
| `position_manager.py` | Position monitoring |
| `notion_reporter.py` | Notion integration |
| `report_sync.py` | Full sync (all platforms) |

