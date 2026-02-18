#!/usr/bin/env python3
"""
Gibson Android - Enhanced Device Manager with Family Sharing
==========================================================
Extracts device stats and shares with family via notification system.

Author: Ahie Juma
"""

import subprocess
import json
import os
from datetime import datetime
from pathlib import Path

DEVICE_ID = "192.168.100.224:5555"
OUTPUT_DIR = Path(__file__).parent

class GibsonAndroidManager:
    def __init__(self):
        self.device_id = DEVICE_ID
        self.data = {}
    
    def run_adb(self, cmd):
        result = subprocess.run(
            ["adb", "-s", self.device_id] + cmd,
            capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip()
    
    def get_all_stats(self):
        # Device info
        model = self.run_adb(["shell", "getprop", "ro.product.model"])
        manufacturer = self.run_adb(["shell", "getprop", "ro.product.manufacturer"])
        android = self.run_adb(["shell", "getprop", "ro.build.version.release"])
        
        # Battery
        battery_out = self.run_adb(["shell", "dumpsys", "battery"])
        battery_level = 0
        for line in battery_out.split("\n"):
            if "level:" in line:
                battery_level = int(line.split(":")[1].strip())
                break
        
        # Storage
        storage = self.run_adb(["shell", "df", "/data"])
        storage_used = "N/A"
        try:
            parts = storage.split("\n")[1].split()
            storage_used = parts[4] if len(parts) > 4 else "N/A"
        except:
            pass
        
        # IP
        ip = "N/A"
        try:
            ip_out = self.run_adb(["shell", "ifconfig", "wlan0"])
            ip = ip_out.split("inet addr:")[1].split()[0]
        except:
            pass
        
        self.data = {
            "model": model,
            "manufacturer": manufacturer,
            "android": android,
            "battery": battery_level,
            "storage_used": storage_used,
            "ip": ip,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.data
    
    def generate_family_message(self):
        """Generate shareable family message."""
        
        msg = f"""
📱 **Gibson's Android Status**

🔋 Battery: **{self.data.get('battery', 'N/A')}%**
💾 Storage: **{self.data.get('storage_used', 'N/A')}** used
📶 IP: **{self.data.get('ip', 'N/A')}**
📱 Device: {self.data.get('manufacturer', '')} {self.data.get('model', '')}
🆙 Android: {self.data.get('android', '')}

⏰ Updated: {datetime.now().strftime('%H:%M')}
"""
        return msg.strip()
    
    def save_and_share(self):
        # Save stats
        with open(OUTPUT_DIR / "device_stats.json", "w") as f:
            json.dump(self.data, f, indent=2)
        
        # Save to log
        with open(OUTPUT_DIR / "android_log.jsonl", "a") as f:
            f.write(json.dumps({
                "timestamp": datetime.now().isoformat(),
                "battery": self.data.get("battery"),
                "storage": self.data.get("storage_used")
            }) + "\n")
        
        return self.generate_family_message()

def main():
    manager = GibsonAndroidManager()
    manager.get_all_stats()
    message = manager.save_and_share()
    
    print("✅ Stats updated!")
    print(message)
    
    # Store for family sharing
    with open(OUTPUT_DIR / "family_update.json", "w") as f:
        json.dump({
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "ready": True
        }, f, indent=2)

if __name__ == "__main__":
    main()
