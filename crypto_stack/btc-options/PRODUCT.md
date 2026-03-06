# BTC Options Surge Predictor - Product Blueprint

## Overview
A product under mamaduka.crypto that predicts BTC price surges (>5% in 24-72h) and automates call option purchases for asymmetric upside.

## Core Features

### 1. Surge Prediction Engine
- **ML Models**: CNN-LSTM / GRU hybrid for temporal pattern detection
- **Target**: Predict >5% price movements 24-72h ahead
- **Confidence Threshold**: 70%+ triggers auto-buy
- **Backtest Performance**: 0.98 R² on hourly data, ~$60 MAE

### 2. Feature Set
- **Technical**: OBV, RSI, MACD, ADX, Moving Averages (normalized, 24h rolling)
- **On-Chain**: Whale transactions, funding rates, exchange flows
- **Sentiment**: X/social semantic analysis, VIX, gold/oil, USDX

### 3. Options Execution
- **Platforms**: Deribit (primary), Binance, Aevo (decentralized)
- **Strategy**: Buy OTM calls 5-10% above spot, 1-7 day expiry
- **Risk Management**: 1-5% position size, 50% stop-loss

### 4. Capital Growth & Redistribution
- **Profit Split**: 15% reinvested, 85% redistributed to mamaduka holders
- **Mechanism**: BITS buybacks/burns
- **KPIs**: >70% surge hit rate, >200% ROI per trade

## Architecture

```
┌─────────────────┐
│  mamaduka.crypto│
│  (Frontend)     │
└────────┬────────┘
         │
    ┌────┴────┐
┌───▼────────▼────┐
│ Options API      │
│ (Express/Node)  │
└────┬────────┬────┘
     │        │
┌────▼──┐  ┌──▼────────┐
│ ML    │  │ Exchange  │
│ Engine│  │ Connector │
└────┬──┘  └──┬────────┘
     │        │
     └────┬───┘
          │
   ┌──────▼──────┐
   │ Deribit/   │
   │ Binance    │
   └────────────┘
```

## Product Directory
`projects/members/Gibson/crypto_stack/btc-options/`

## KPIs
- Surge Hit Rate: >70%
- Per Trade ROI: >200%
- Holder APY: >50%
- Backtest Returns: 148-1273% APY (simulations)

## Risk Warning
Options can expire worthless. Mitigate with high-confidence thresholds and diversification.
