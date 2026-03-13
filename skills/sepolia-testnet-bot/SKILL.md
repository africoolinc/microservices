# Skill: Sepolia Testnet Bot

## Description
Tests the crypto-register deployment using Sepolia testnet ETH. Monitors test addresses, validates smart contract interactions, and rates the service deployment.

## Configuration
- **Test Address:** `0xcA2a481E128d8A1FCE636E0D4fe10fF5987f028F`
- **Etherscan:** https://sepolia.etherscan.io/address/0xcA2a481E128d8A1FCE636E0D4fe10fF5987f028F
- **Network:** Sepolia (Chain ID: 11155111)

## Usage

```bash
# Full test
python3 skills/sepolia-testnet-bot/testnet_bot.py

# Quick balance check
python3 skills/sepolia-testnet-bot/testnet_bot.py --balance

# Test deployment
python3 skills/sepolia-testnet-bot/testnet_bot.py --test-deployment

# Rate service
python3 skills/sepolia-testnet-bot/testnet_bot.py --rate
```

## Features
- ETH balance check on Sepolia
- Transaction monitoring
- Deployment testing
- Service rating (1-10)

## Requirements
- `web3` library
- `requests` library
- Etherscan API key (optional, for detailed tx data)