# GitHub Repository for Gibson's Microservices Stack

## Repository Information
**Repository URL**: https://github.com/africoolinc/microservices-stack  
**Username**: africoolinc@gmail.com  

## Authentication
This repository uses HTTPS authentication. The credentials are stored securely in `.secrets/git_credentials_africoolinc.json`.

---

## Repository Setup Commands

On the remote machine:

```bash
# On remote machine (10.144.118.159)
cd /opt/microservices-stack

# Initialize git if not already done
git init
git branch -M main

# Configure identity
git config --global user.email "africoolinc@gmail.com"
git config --global user.name "africoolinc"

# Add remote
git remote add origin https://github.com/africoolinc/microservices-stack.git

# Store credentials (optional, but convenient)
git config --global credential.helper store

# Add all files
git add -A
git commit -m "Initial commit: Production microservices stack"

# Push to GitHub (it will ask for username and password)
git push -u origin main
```

---
Generated: 2026-02-17 (Updated)
