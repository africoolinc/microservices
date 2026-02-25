# Insilico Terminal Research

**Created:** 2026-02-24  
**Account:** africoolinc@gmail.com  
**Platform:** https://insilicoterminal.com/#/trade

---

## Initial Assessment

**Platform Type:** AI-powered trading terminal for futures/prediction markets  
**Status:** Requires login to access trading interface

### Access Notes
- Website is JavaScript-heavy (React/Vue app)
- Login required: Google OAuth (africoolinc@gmail.com)
- Cannot fetch detailed market data via web_fetch due to client-side rendering

### Next Steps
1. **Login via browser** to explore available markets
2. Identify trading instruments (crypto futures, prediction markets, etc.)
3. Check deposit/withdrawal methods
4. Research platform fees and leverage options

---

## Daily Research Log

### 2026-02-24
- [x] Login to platform (user confirms already signed in)
- [x] Confirm BTC futures market interest
- [x] Obtain API credentials (Blofin via Insilico)
- [ ] Connect to API (IP whitelist blocked)
- [ ] List available markets
- [ ] Understand fee structure

### 2026-02-25
- [ ] Browser automation unavailable (device token mismatch)
- [x] Web fetch shows basic platform info
- [ ] Need manual browser access for detailed exploration

### API Connection Issue
- **Error:** "Your IP is not included in your API key's IP whitelist"
- **Action Required:** Add IP address to Blofin API whitelist

### Current IP
- IPv4: `104.28.211.149` (also seen: `104.28.243.151`)
- IPv6: `2a09:bac5:46e5:145a::207:7`

### Action for User
1. Go to Blofin → API Management
2. Add IP `104.28.211.149` to whitelist
3. Or use `0.0.0.0/0` for all IPs (less secure)

---

## Platform Features (To Research)

### Known Capabilities
- AI-powered trading signals
- Crypto futures trading
- Prediction markets
- Multiple exchange connections (Blofin, other prop firms)

### Markets to Explore
- [ ] BTC/USDT Perpetual
- [ ] ETH/USDT Perpetual  
- [ ] Altcoin futures
- [ ] Prediction market tokens
- [ ] Stock CFDs (if available)

### Trading Desk MVP Features
1. **Market Data Feed** - Real-time prices from Insilico/Blofin
2. **Signal Alerts** - AI-generated trade signals
3. **Portfolio Tracking** - P&L across positions
4. **Auto-Trading** - Execute trades via API (future phase)

---

## Strategy Development
*To be filled as we learn more about the platform*

---

## Questions for Family
- What specific markets are you interested in?
- Do you have any existing knowledge of Insilico's mechanics?
