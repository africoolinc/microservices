#!/usr/bin/env python3
"""
Family Notification Sender for Gibson's Android
===========================================
Sends device status updates to family members.

Note: Requires service worker to be set up on family devices.
Each family member needs to enable push notifications first.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

# Config
FAMILY_MEMBERS_DIR = Path("/home/africool/.openclaw/workspace/.secrets/family_members")
DEVICE_STATS_FILE = Path(__file__).parent / "family_update.json"


def get_device_stats():
    """Get current device stats."""
    stats_file = Path(__file__).parent / "device_stats.json"
    if stats_file.exists():
        with open(stats_file) as f:
            return json.load(f)
    return {}


def format_status_message(stats):
    """Format status for family sharing."""
    
    battery = stats.get("battery", 0)
    battery_emoji = "🔋" if battery > 50 else "🪫"
    
    msg = f"""
╔══════════════════════════════════╗
║   📱 GIBSON'S DEVICE UPDATE     ║
╚══════════════════════════════════╝

{battery_emoji} Battery: {battery}%
💾 Storage: {stats.get('storage_used', 'N/A')}
📶 IP: {stats.get('ip', 'N/A')}
📱 {stats.get('manufacturer', '')} {stats.get('model', '')}
🆙 Android: {stats.get('android', '')}

⏰ Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    return msg.strip()


def get_active_family_members():
    """Get family members with push enabled."""
    members = []
    for file in FAMILY_MEMBERS_DIR.glob("*.json"):
        with open(file) as f:
            data = json.load(f)
            if data.get("member_info", {}).get("notification_preferences", {}).get("push_enabled"):
                members.append({
                    "name": data.get("member_info", {}).get("name"),
                    "token": data.get("member_info", {}).get("notification_preferences", {}).get("device_token")
                })
    return members


def send_notification(title, message, member_name=None):
    """Send notification via family system."""
    # This would integrate with the notification system
    # For now, just print what would be sent
    
    print(f"📨 Notification ready to send:")
    print(f"   Title: {title}")
    print(f"   Message: {message}")
    
    if member_name:
        print(f"   To: {member_name}")
    
    # Save pending notification
    pending = {
        "title": title,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "sent": False
    }
    
    with open(Path(__file__).parent / "pending_notifications.json", "w") as f:
        json.dump(pending, f, indent=2)
    
    return pending


def main():
    print("📱 Gibson Android - Family Notification Sender")
    print("=" * 50)
    
    # Get stats
    stats = get_device_stats()
    
    if not stats:
        print("❌ No stats found. Run family_sync.py first.")
        return
    
    # Format message
    message = format_status_message(stats)
    print(message)
    
    # Check active family members
    members = get_active_family_members()
    
    print(f"\n👨‍👩‍👧‍👦 Family Members with Push Enabled: {len(members)}")
    
    if members:
        for member in members:
            print(f"   - {member['name']}")
        
        # Send to all
        send_notification("Gibson's Device Update", message)
    else:
        print("\n⚠️ No family members have push notifications enabled.")
        print("   Family members need to enable service worker first.")
    
    print("\n✅ Notification prepared!")
    print("\nTo enable family notifications, each member needs to:")
    print("1. Visit the family notification setup page")
    print("2. Enable push notifications")
    print("3. Save their device token")


if __name__ == "__main__":
    main()
