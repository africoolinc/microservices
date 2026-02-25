#!/bin/bash
# Gibson Calendar Alert Service - Twilio + ngrok Setup
# Purpose: Get calls/SMS about calendar events (Gibson's travel events)
# Requirements: Twilio account, ngrok auth token

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/home/africool/.openclaw/workspace/projects/members/Gibson/ngrok"
VENV_DIR="$PROJECT_DIR/venv"

log() { echo -e "${BLUE}[$(date '+%H:%M:%S')] $1${NC}"; }
success() { echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓ $1${NC}"; }
warn() { echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠ $1${NC}"; }
error() { echo -e "${RED}[$(date '+%H:%M:%S')] ✗ $1${NC}" && exit 1; }

cd "$PROJECT_DIR"

# Create venv
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR" || error "Python3 venv failed"
    success "Created venv"
fi

source "$VENV_DIR/bin/activate"

# Install deps
pip install --upgrade pip -q
pip install fastapi uvicorn python-dotenv twilio requests -q
success "Installed dependencies"

# Create .env
if [ ! -f "$PROJECT_DIR/.env" ]; then
    cat > "$PROJECT_DIR/.env" << 'EOF'
# Twilio Config
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
MY_PHONE_NUMBER=+2547xxxxxxx

# Ngrok
NGROK_AUTH_TOKEN=your_ngrok_token

# Alert Settings
CHECK_INTERVAL_MINUTES=60
EOF
    success "Created .env template"
    warn "Edit .env with your Twilio & ngrok credentials!"
fi

# Create main.py - Calendar Alert Service
cat > "$PROJECT_DIR/main.py" << 'EOF'
#!/usr/bin/env python3
"""
Gibson Calendar Alert Service
Monitors calendar events and sends SMS/calls via Twilio when events are near.
"""
import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from twilio.rest import Client
from fastapi import FastAPI, Request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse

load_dotenv()

app = FastAPI(title="Gibson Calendar Alerts")

# Twilio config
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")
MY_PHONE = os.getenv("MY_PHONE_NUMBER")

twilio_client = Client(TWILIO_SID, TWILIO_TOKEN) if TWILIO_SID and TWILIO_TOKEN else None

# Event storage (simple JSON for now)
EVENTS_FILE = "/home/africool/.openclaw/workspace/projects/members/Gibson/travel_itinerary_2026/EVENTS.csv"

def load_events():
    """Load events from EVENTS.csv"""
    events = []
    try:
        with open(EVENTS_FILE, 'r') as f:
            lines = f.readlines()[1:]  # Skip header
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    events.append({
                        'name': parts[0].strip('"'),
                        'month': parts[1].strip('"'),
                        'location': parts[2].strip('"')
                    })
    except Exception as e:
        print(f"Error loading events: {e}")
    return events

def send_sms(message):
    """Send SMS via Twilio"""
    if not twilio_client:
        print("Twilio not configured")
        return False
    try:
        msg = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE,
            to=MY_PHONE
        )
        print(f"SMS sent: {msg.sid}")
        return True
    except Exception as e:
        print(f"SMS failed: {e}")
        return False

def make_call(message):
    """Make Twilio voice call with message"""
    if not twilio_client:
        print("Twilio not configured")
        return False
    try:
        call = twilio_client.calls.create(
            twiml=f"<Response><Say>{message}</Say></Response>",
            from_=TWILIO_PHONE,
            to=MY_PHONE
        )
        print(f"Call initiated: {call.sid}")
        return True
    except Exception as e:
        print(f"Call failed: {e}")
        return False

def check_upcoming_events(days_ahead=3):
    """Check for events in the next N days"""
    events = load_events()
    current_month = datetime.now().strftime("%b")
    current_year = datetime.now().year
    
    alerts = []
    # Simplified: check if any event is this month
    for event in events:
        if event['month'].lower() == current_month.lower():
            alerts.append(f"{event['name']} in {event['location']} this month!")
    
    return alerts

# API Endpoints
@app.get("/")
def root():
    return {"status": "Gibson Calendar Alert Service running", "events": len(load_events())}

@app.post("/check-events")
def check_events():
    """Trigger event check manually or via cron"""
    alerts = check_upcoming_events()
    if alerts:
        for alert in alerts:
            send_sms(f"📅 Gibson Alert: {alert}")
        return {"alerts": alerts, "notified": len(alerts)}
    return {"alerts": [], "notified": 0}

@app.post("/incoming-sms")
async def incoming_sms(request: Request):
    """Handle incoming SMS (for testing/replies)"""
    form = await request.form()
    body = form.get('Body', '')
    from_num = form.get('From')
    
    resp = MessagingResponse()
    
    if 'status' in body.lower():
        events = load_events()
        msg = "Gibson's upcoming events:\n"
        for e in events[:5]:
            msg += f"• {e['name']} ({e['month']}) - {e['location']}\n"
        resp.message(msg)
    else:
        resp.message("Gibson Calendar Bot: Reply 'status' for events list")
    
    return str(resp)

@app.post("/incoming-call")
async def incoming_call(request: Request):
    """Handle incoming voice call"""
    resp = VoiceResponse()
    resp.say("This is Gibson's calendar alert service. Reply with a text message to get event updates.")
    return str(resp)

@app.get("/ngrok-url")
def ngrok_url():
    """Get current ngrok URL"""
    try:
        resp = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        data = resp.json()
        tunnels = data.get('tunnels', [])
        for t in tunnels:
            if t.get('proto') == 'https':
                return {"url": t.get('public_url'), "expires": "ngrok free: 2 hours"}
    except:
        pass
    return {"error": "ngrok not running or not accessible"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5050)
EOF

# Create setup script for easy running
cat > "$PROJECT_DIR/start.sh" << 'EOF'
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
EOF

chmod +x "$PROJECT_DIR/start.sh"

# Create cron job template
cat > "$PROJECT_DIR/crontab.txt" << 'EOF'
# Gibson Calendar Alerts - Add to crontab
# Check events every hour and send SMS if needed
0 * * * * cd /home/africool/.openclaw/workspace/projects/members/Gibson/ngrok && source venv/bin/activate && python3 -c "
import requests
try:
    r = requests.post('http://localhost:5050/check-events', timeout=10)
    print('Checked:', r.json())
except:
    pass
"
EOF

success "Setup complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Edit $PROJECT_DIR/.env with your Twilio credentials"
echo "2. Get ngrok token: https://dashboard.ngrok.com/get-started/your-authtoken"
echo "3. Run: cd $PROJECT_DIR && ./start.sh"
echo "4. Configure Twilio webhooks to your ngrok URL"
echo ""
echo "📅 Calendar check endpoint: http://localhost:5050/check-events"
