#!/usr/bin/env python3
"""
Gibson Android - Enhanced Stats with All Features
==============================================
- Device stats
- Location (GPS)
- Notifications
- Apps
- Network details
- System info

Author: Ahie Juma
"""

import subprocess
import json
from datetime import datetime
from pathlib import Path

DEVICE_ID = "192.168.100.224:5555"
OUTPUT_DIR = Path(__file__).parent

def run_adb(cmd):
    result = subprocess.run(
        ["adb", "-s", DEVICE_ID] + cmd,
        capture_output=True, text=True, timeout=30
    )
    return result.stdout.strip()

def get_device_info():
    return {
        "model": run_adb(["shell", "getprop", "ro.product.model"]),
        "manufacturer": run_adb(["shell", "getprop", "ro.product.manufacturer"]),
        "brand": run_adb(["shell", "getprop", "ro.product.brand"]),
        "android_version": run_adb(["shell", "getprop", "ro.build.version.release"]),
        "security_patch": run_adb(["shell", "getprop", "ro.build.version.security_patch"]),
        "serial": run_adb(["shell", "getprop", "ro.serialno"]),
        "android_id": run_adb(["shell", "settings", "get", "secure", "android_id"]),
    }

def get_battery():
    out = run_adb(["shell", "dumpsys", "battery"])
    data = {}
    for line in out.split("\n"):
        if "level:" in line: data["level"] = int(line.split(":")[1].strip())
        if "status:" in line: data["status"] = line.split(":")[1].strip()
        if "health:" in line: data["health"] = line.split(":")[1].strip()
        if "temperature:" in line: data["temperature"] = float(line.split(":")[1].strip()) / 10
        if "voltage:" in line: data["voltage"] = int(line.split(":")[1].strip())
        if "technology:" in line: data["technology"] = line.split(":")[1].strip()
    return data

def get_storage():
    out = run_adb(["shell", "df"])
    storage = {}
    for line in out.split("\n"):
        if "/data" in line:
            parts = line.split()
            storage["total"] = parts[1]
            storage["used"] = parts[2]
            storage["available"] = parts[3]
            storage["percent"] = parts[4]
    return storage

def get_network():
    # WiFi IP
    ip = "N/A"
    try:
        out = run_adb(["shell", "ifconfig", "wlan0"])
        ip = out.split("inet addr:")[1].split()[0]
    except: pass
    
    # WiFi name
    ssid = "N/A"
    try:
        out = run_adb(["shell", "dumpsys", "wifi", "|", "grep", "SSID"])
        ssid = out.split("SSID:")[1].split("\n")[0].strip()
    except: pass
    
    # Mobile data
    mobile_ip = "N/A"
    try:
        out = run_adb(["shell", "ifconfig", "rmnet0"])
        mobile_ip = out.split("inet addr:")[1].split()[0]
    except: pass
    
    return {"wifi_ip": ip, "wifi_ssid": ssid, "mobile_ip": mobile_ip}

def get_location():
    # Check if location is enabled
    location_enabled = run_adb(["shell", "settings", "get", "secure", "location_providers_allowed"])
    gps_enabled = "gps" in location_enabled.lower() if location_enabled else False
    
    return {
        "providers_allowed": location_enabled,
        "gps_enabled": gps_enabled,
        "note": "Exact coordinates require location permission"
    }

def get_memory():
    out = run_adb(["shell", "dumpsys", "meminfo"])
    data = {}
    for line in out.split("\n"):
        if "Total RAM:" in line:
            data["total_ram"] = line.split(":")[1].strip()
        if "Free RAM:" in line:
            data["free_ram"] = line.split(":")[1].strip()
        if "Used RAM:" in line:
            data["used_ram"] = line.split(":")[1].strip()
    return data

def get_cpu():
    out = run_adb(["shell", "cat", "/proc/cpuinfo"])
    cpu = {}
    for line in out.split("\n")[:10]:
        if "model name" in line: cpu["model"] = line.split(":")[1].strip()
        if "Hardware" in line: cpu["hardware"] = line.split(":")[1].strip()
        if "BogoMIPS" in line: cpu["bogomips"] = line.split(":")[1].strip()
    return cpu

def get_apps():
    # Get user apps
    out = run_adb(["shell", "pm", "list", "packages", "-3"])
    apps = [line.replace("package:", "").strip() for line in out.strip().split("\n") if "package:" in line]
    return {"user_apps_count": len(apps), "apps": apps[:20]}

def get_screen():
    out = run_adb(["shell", "dumpsys", "window", "displays"])
    data = {}
    for line in out.split("\n"):
        if "mDisplayId=" in line:
            data["display_id"] = line.split("=")[1].split()[0]
        if "mScreenWidth" in line:
            data["width"] = line.split("=")[1].split()[0]
        if "mScreenHeight" in line:
            data["height"] = line.split("=")[1].split(",")[0]
    return data

def get_uptime():
    out = run_adb(["shell", "cat", "/proc/uptime"])
    try:
        seconds = float(out.split()[0])
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return {"uptime_hours": hours, "uptime_minutes": minutes}
    except:
        return {}

def get_notifications_count():
    # Get notification summary
    out = run_adb(["shell", "dumpsys", "notification", "|", "grep", "Bundle"])
    try:
        # Count notifications
        count = len([l for l in out.split("\n") if "Bundle" in l])
        return {"notification_count": count}
    except:
        return {"notification_count": 0}

def get_bluetooth():
    out = run_adb(["shell", "dumpsys", "bluetooth_manager"])
    connected = []
    try:
        for line in out.split("\n"):
            if "Device" in line and "Connected" in line:
                connected.append(line.strip())
    except: pass
    return {"connected_devices": connected}

def get_all_stats():
    print("📱 Gathering all device stats...")
    
    stats = {
        "timestamp": datetime.now().isoformat(),
        "device_info": get_device_info(),
        "battery": get_battery(),
        "storage": get_storage(),
        "network": get_network(),
        "location": get_location(),
        "memory": get_memory(),
        "cpu": get_cpu(),
        "apps": get_apps(),
        "screen": get_screen(),
        "uptime": get_uptime(),
        "bluetooth": get_bluetooth()
    }
    
    return stats

def format_family_summary(stats):
    """Format for family sharing."""
    battery = stats.get("battery", {})
    network = stats.get("network", {})
    device = stats.get("device_info", {})
    
    emoji = "🔋"
    if battery.get("level", 0) < 20: emoji = "🪫"
    elif battery.get("level", 0) < 50: emoji = "🔌"
    
    return f"""
╔══════════════════════════════════════╗
║   📱 GIBSON'S ANDROID STATUS       ║
╚══════════════════════════════════════╝

{emoji} Battery: {battery.get('level', 'N/A')}% ({battery.get('status', 'N/A')})
💾 Storage: {stats.get('storage', {}).get('percent', 'N/A')} used
📶 WiFi: {network.get('wifi_ssid', 'N/A')}
🌐 IP: {network.get('wifi_ip', 'N/A')}
📱 {device.get('manufacturer', '')} {device.get('model', '')}
🆙 Android: {device.get('android_version', '')}
⏱️ Uptime: {stats.get('uptime', {}).get('uptime_hours', 'N/A')}h

📦 Apps: {stats.get('apps', {}).get('user_apps_count', 'N/A')}
💾 RAM: {stats.get('memory', {}).get('used_ram', 'N/A')}

🕐 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

def main():
    stats = get_all_stats()
    
    # Save full stats
    with open(OUTPUT_DIR / "device_stats_full.json", "w") as f:
        json.dump(stats, f, indent=2)
    
    # Save simplified for family
    with open(OUTPUT_DIR / "device_stats.json", "w") as f:
        simple = {
            "battery": stats.get("battery", {}).get("level", 0),
            "storage_used": stats.get("storage", {}).get("percent", "N/A"),
            "ip": stats.get("network", {}).get("wifi_ip", "N/A"),
            "model": f"{stats.get('device_info', {}).get('manufacturer', '')} {stats.get('device_info', {}).get('model', '')}",
            "android": stats.get("device_info", {}).get("android_version", ""),
            "timestamp": stats.get("timestamp")
        }
        json.dump(simple, f, indent=2)
    
    # Print family summary
    print(format_family_summary(stats))
    print("✅ Stats saved!")

if __name__ == "__main__":
    main()
