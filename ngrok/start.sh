#!/bin/bash
cd "$(dirname "$0")"

# Activate venv
source venv/bin/activate

# Check ngrok
if ! curl -s localhost:4040/api/tunnels >/dev/null 2>&1; then
    echo "Starting ngrok..."
    ngrok http 5050 &
    sleep 3
fi

# Get ngrok URL
URL=$(curl -s localhost:4040/api/tunnels | grep -o 'https://[^"]*' | head -1)
echo "🌐 Service URL: $URL"
echo "📱 Twilio SMS endpoint: $URL/incoming-sms"
echo "📞 Twilio Voice endpoint: $URL/incoming-call"

# Start server
python3 main.py
