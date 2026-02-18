#!/usr/bin/env python3
"""
Android Device Manager for Gibson
==============================
Extracts calls, messages, and stats from connected Android device.
Shares with family via notification system.

Author: Ahie Juma (Lyrikali Economic Agent)
"""

import subprocess
import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AndroidManager")

# Configuration
DEVICE_ID = "192.168.100.224:5555"  # Wireless ADB
OUTPUT_DIR = Path(__file__).parent
CALLS_FILE = OUTPUT_DIR / "calls.json"
MESSAGES_FILE = OUTPUT_DIR / "messages.json"
STATS_FILE = OUTPUT_DIR / "device_stats.json"
LOG_FILE = OUTPUT_DIR / "android_log.jsonl"

# Family notification config
FAMILY_NOTIFY = True


class AndroidDeviceManager:
    """Manage Android device data extraction and sharing."""
    
    def __init__(self, device_id: str = None):
        self.device_id = device_id or DEVICE_ID
        self.data = {
            "calls": [],
            "messages": [],
            "stats": {},
            "timestamp": datetime.now().isoformat()
        }
    
    def run_adb(self, command: List[str]) -> str:
        """Run ADB command on device."""
        cmd = ["adb", "-s", self.device_id] + command
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.stdout
        except Exception as e:
            logger.error(f"ADB command failed: {e}")
            return ""
    
    def get_device_info(self) -> Dict:
        """Get basic device information."""
        logger.info("📱 Gathering device info...")
        
        info = {
            "model": self.run_adb(["shell", "getprop", "ro.product.model"]).strip(),
            "manufacturer": self.run_adb(["shell", "getprop", "ro.product.manufacturer"]).strip(),
            "android_version": self.run_adb(["shell", "getprop", "ro.build.version.release"]).strip(),
            "serial": self.run_adb(["shell", "getprop", "ro.serialno"]).strip(),
            "android_id": self.run_adb(["shell", "settings", "get", "secure", "android_id"]).strip(),
        }
        
        # Network info
        try:
            ip = self.run_adb(["shell", "ifconfig", "wlan0"]).split("inet addr:")[1].split()[0]
            info["ip_address"] = ip
        except:
            info["ip_address"] = "N/A"
        
        return info
    
    def get_battery_status(self) -> Dict:
        """Get battery information."""
        logger.info("🔋 Checking battery status...")
        
        battery = self.run_adb(["shell", "dumpsys", "battery"])
        
        status = {}
        for line in battery.split("\n"):
            if "level:" in line:
                status["level"] = int(line.split(":")[1].strip())
            if "status:" in line:
                status["charge_status"] = line.split(":")[1].strip()
            if "health:" in line:
                status["health"] = line.split(":")[1].strip()
            if "temperature:" in line:
                status["temperature"] = float(line.split(":")[1].strip()) / 10
        
        return status
    
    def get_storage_info(self) -> Dict:
        """Get storage information."""
        logger.info("💾 Checking storage...")
        
        storage = self.run_adb(["shell", "df", "/data"])
        
        try:
            lines = storage.split("\n")
            if len(lines) > 1:
                parts = lines[1].split()
                return {
                    "total": parts[1],
                    "used": parts[2],
                    "available": parts[3],
                    "percent_used": parts[4]
                }
        except:
            pass
        
        return {}
    
    def get_call_logs(self, limit: int = 50) -> List[Dict]:
        """Extract call logs."""
        logger.info("📞 Extracting call logs...")
        
        # Use content provider to get call logs
        calls = []
        
        # Get calls via adb
        result = self.run_adb([
            "shell", "content", "query",
            "--uri", "content://calls",
            "--projection", "number,date,duration,type",
            "--sort", "date DESC",
            "--limit", str(limit)
        ])
        
        for line in result.strip().split("\n"):
            if "number=" in line:
                call = {}
                for field in ["number=", "date=", "duration=", "type="]:
                    if field in line:
                        start = line.index(field) + len(field)
                        end = line.find(",", start) if "," in line[start:] else len(line)
                        call[field.replace("=", "")] = line[start:end].strip()
                
                if call.get("number"):
                    # Convert type: 1=incoming, 2=outgoing, 3=missed
                    call_type = {1: "incoming", 2: "outgoing", 3: "missed"}.get(
                        int(call.get("type", 0)), "unknown")
                    call["call_type"] = call_type
                    
                    # Format date
                    try:
                        timestamp = int(call.get("date", 0)) // 1000
                        call["datetime"] = datetime.fromtimestamp(timestamp).isoformat()
                    except:
                        call["datetime"] = "unknown"
                    
                    calls.append(call)
        
        self.data["calls"] = calls
        return calls
    
    def get_sms_logs(self, limit: int = 50) -> List[Dict]:
        """Extract SMS messages."""
        logger.info("💬 Extracting SMS messages...")
        
        messages = []
        
        # Get SMS via adb
        result = self.run_adb([
            "shell", "content", "query",
            "--uri", "content://sms",
            "--projection", "address,body,date,type",
            "--sort", "date DESC",
            "--limit", str(limit)
        ])
        
        for line in result.strip().split("\n"):
            if "address=" in line:
                msg = {}
                for field in ["address=", "body=", "date=", "type="]:
                    if field in line:
                        start = line.index(field) + len(field)
                        end = line.find(",", start) if "," in line[start:] else len(line)
                        msg[field.replace("=", "")] = line[start:end].strip()
                
                if msg.get("address"):
                    # Type: 1=inbox, 2=sent
                    msg["direction"] = "received" if msg.get("type") == "1" else "sent"
                    
                    try:
                        timestamp = int(msg.get("date", 0)) // 1000
                        msg["datetime"] = datetime.fromtimestamp(timestamp).isoformat()
                    except:
                        msg["datetime"] = "unknown"
                    
                    messages.append(msg)
        
        self.data["messages"] = messages
        return messages
    
    def get_contacts_count(self) -> int:
        """Get contacts count."""
        result = self.run_adb([
            "shell", "content", "query",
            "--uri", "content://contacts",
            "--projection", "count(*)"
        ])
        
        try:
            return int(result.strip())
        except:
            return 0
    
    def get_app_list(self) -> List[Dict]:
        """Get installed apps."""
        logger.info("📦 Getting app list...")
        
        result = self.run_adb(["shell", "pm", "list", "packages", "-3"])  # Third-party apps only
        
        apps = []
        for line in result.strip().split("\n"):
            if "package:" in line:
                apps.append(line.replace("package:", "").strip())
        
        return apps[:50]  # Limit to 50
    
    def get_all_stats(self) -> Dict:
        """Get all device statistics."""
        logger.info("📊 Gathering all stats...")
        
        stats = {
            "device_info": self.get_device_info(),
            "battery": self.get_battery_status(),
            "storage": self.get_storage_info(),
            "contacts_count": self.get_contacts_count(),
            "apps_count": len(self.get_app_list()),
            "last_updated": datetime.now().isoformat()
        }
        
        self.data["stats"] = stats
        return stats
    
    def save_data(self):
        """Save all data to files."""
        logger.info("💾 Saving data...")
        
        # Save calls
        with open(CALLS_FILE, 'w') as f:
            json.dump(self.data["calls"], f, indent=2, default=str)
        
        # Save messages  
        with open(MESSAGES_FILE, 'w') as f:
            json.dump(self.data["messages"], f, indent=2, default=str)
        
        # Save stats
        with open(STATS_FILE, 'w') as f:
            json.dump(self.data["stats"], f, indent=2, default=str)
        
        # Append to log
        with open(LOG_FILE, 'a') as f:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "calls_count": len(self.data["calls"]),
                "messages_count": len(self.data["messages"]),
                "battery_level": self.data["stats"].get("battery", {}).get("level", 0)
            }
            f.write(json.dumps(log_entry) + "\n")
        
        logger.info(f"✅ Data saved to {OUTPUT_DIR}")
        
        return {
            "calls": str(CALLS_FILE),
            "messages": str(MESSAGES_FILE),
            "stats": str(STATS_FILE)
        }
    
    def generate_family_summary(self) -> str:
        """Generate summary for family sharing."""
        
        stats = self.data.get("stats", {})
        device = stats.get("device_info", {})
        battery = stats.get("battery", {})
        
        summary = f"""
📱 **Gibson's Android Device Report**
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

📊 **Device Status**
- **Model**: {device.get('model', 'N/A')}
- **Battery**: {battery.get('level', 'N/A')}% ({battery.get('charge_status', 'N/A')})
- **Storage**: {stats.get('storage', {}).get('percent_used', 'N/A')} used
- **IP**: {device.get('ip_address', 'N/A')}

📞 **Communication**
- **Calls Today**: {len([c for c in self.data['calls'] if 'today' in c.get('datetime', '')])} (recent: {len(self.data['calls'])})
- **Messages Today**: {len([m for m in self.data['messages'] if 'today' in m.get('datetime', '')])} (recent: {len(self.data['messages'])})

📦 **Apps**: {stats.get('apps_count', 'N/A')} installed
👥 **Contacts**: {stats.get('contacts_count', 'N/A')}
"""
        
        return summary
    
    def run_full_sync(self):
        """Run complete sync."""
        logger.info("🔄 Starting full Android sync...")
        
        # Get all data
        self.get_all_stats()
        self.get_call_logs()
        self.get_sms_logs()
        
        # Save
        files = self.save_data()
        
        # Generate summary
        summary = self.generate_family_summary()
        
        print(summary)
        
        return files


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Android Device Manager for Gibson")
    parser.add_argument("--sync", action="store_true", help="Run full sync")
    parser.add_argument("--stats", action="store_true", help="Get device stats only")
    parser.add_argument("--calls", action="store_true", help="Get call logs only")
    parser.add_argument("--messages", action="store_true", help="Get messages only")
    parser.add_argument("--family", action="store_true", help="Generate family summary")
    
    args = parser.parse_args()
    
    manager = AndroidDeviceManager()
    
    if args.sync or not any([args.stats, args.calls, args.messages, args.family]):
        manager.run_full_sync()
    elif args.stats:
        stats = manager.get_all_stats()
        print(json.dumps(stats, indent=2))
    elif args.calls:
        calls = manager.get_call_logs()
        print(json.dumps(calls, indent=2, default=str))
    elif args.messages:
        messages = manager.get_sms_logs()
        print(json.dumps(messages, indent=2, default=str))
    elif args.family:
        manager.get_all_stats()
        manager.get_call_logs()
        manager.get_sms_logs()
        print(manager.generate_family_summary())


if __name__ == "__main__":
    main()
