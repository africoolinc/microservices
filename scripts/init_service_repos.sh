#!/bin/bash
# Gibson's Remote Workspace Git Initializer
# Run this on the remote machine to set up individual repos for services

STACK_DIR="/home/gibz/stackforge"
SERVICES=("ecommerce-platform" "fintech-app" "social-media")

echo "Initializing Git repositories for StackForge services..."

for service in "${SERVICES[@]}"; do
    TARGET_DIR="$STACK_DIR/services/$service"
    if [ -d "$TARGET_DIR" ]; then
        echo "Processing $service..."
        cd "$TARGET_DIR"
        
        if [ ! -d ".git" ]; then
            git init
            git config user.name "Gibson Juma"
            git config user.email "gibson@juma.family"
            git add .
            git commit -m "Initial commit: $service localized source"
            echo "✓ Git repo initialized in $TARGET_DIR"
        else
            echo "⚠ Git repo already exists in $TARGET_DIR"
        fi
    else
        echo "❌ Directory not found: $TARGET_DIR"
    fi
done

echo "Setup complete."
