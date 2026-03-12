#!/usr/bin/env python3
"""
Environment Scanner for Android Device
======================================
Autonomously scans and monitors:
- WiFi signals
- Noise levels
- GPS coordinates
- Movement detection (accelerometer)

Syncs data with mothership (Linux) via HTTP API.

Author: Ahie Juma (Terminator Mobile Agent)
"""

import subprocess
import json
import os
import logging
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import requests
import math

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EnvScanner")

# Configuration
DEVICE_ID = "192.168.100.224:5555"  # Wireless ADB
OUTPUT_DIR = Path(__file__).parent
ENV_DATA_FILE = OUTPUT_DIR / "environment_data.json"
MOVEMENT_LOG = OUTPUT_DIR / "movement_log.jsonl"

# Mothership sync config
# Note: For mobile (V20), 192.168.100.182 is the mothership (this machine) via local network
MOTHERSHIP_URL = "http://192.168.100.182:10555/api/envsync"  # Crypto portal on mothership
SYNC_ENABLED = True
SYNC_INTERVAL = 300  # 5 minutes

# Movement detection thresholds
MOVEMENT_THRESHOLD = 0.5  # m/s² deviation from baseline
BASELINE_SAMPLES = 10


class EnvironmentScanner:
    """Autonomous environment scanning for Android device."""
    
    def __init__(self, device_id: str = None):
        self.device_id = device_id or DEVICE_ID
        self.data = {
            "wifi": {},
            "gps": {},
            "noise": {"level": "N/A", "status": "unavailable"},
            "movement": {"status": "idle", "acceleration": {}},
            "timestamp": datetime.now().isoformat()
        }
        self.baseline = {"x": 0, "y": 0, "z": 9.8}
        self.baseline_samples = []
        self.movement_detected = False
        self.last_movement_time = None
        self.is_scanning = False
        
    def run_adb(self, command: List[str], timeout: int = 30) -> str:
        """Run ADB command on device."""
        cmd = ["adb", "-s", self.device_id] + command
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return result.stdout
        except Exception as e:
            logger.error(f"ADB command failed: {e}")
            return ""
    
    # ========== WiFi Scanning ==========
    def scan_wifi_networks(self) -> Dict:
        """Scan for available WiFi networks."""
        logger.info("📡 Scanning WiFi networks...")
        
        wifi_data = {
            "current_network": "N/A",
            "signal_strength": 0,
            "frequency": 0,
            "networks": []
        }
        
        # Get current connection info
        result = self.run_adb(["shell", "dumpsys", "wifi"])
        
        # Parse WiFi config for current network
        config_result = self.run_adb(["shell", "dumpsys", "wifi", "wifi"])
        
        # Parse main wifi dump
        for line in result.split("\n"):
            # Current SSID (try multiple patterns)
            if '"Juma"' in line:  # Known network name
                wifi_data["current_network"] = "Juma"
            elif "SSID=" in line:
                try:
                    ssid = line.split("SSID=")[1].split(",")[0].strip().strip('"')
                    if ssid and ssid != "<unknown ssid>" and len(ssid) > 1:
                        wifi_data["current_network"] = ssid
                except:
                    pass
            
            # RSSI (signal strength) - look for actual signal values
            if "rssi=" in line.lower():
                try:
                    rssi = int(line.split("rssi=")[1].split()[0])
                    if rssi != 0:  # Ignore 0 values
                        wifi_data["signal_strength"] = rssi
                except:
                    pass
            
            # Frequency
            if "frequency=" in line.lower():
                try:
                    freq = int(line.split("frequency=")[1].split()[0])
                    if freq > 0:
                        wifi_data["frequency"] = freq
                except:
                    pass
        
        # Get current IP
        try:
            ip_result = self.run_adb(["shell", "ifconfig", "wlan0"])
            if "inet addr:" in ip_result:
                wifi_data["ip_address"] = ip_result.split("inet addr:")[1].split()[0]
        except:
            pass
        
        self.data["wifi"] = wifi_data
        logger.info(f"   Found: {wifi_data['current_network']} (RSSI: {wifi_data['signal_strength']})")
        
        return wifi_data
    
    # ========== GPS Scanning ==========
    def get_gps_location(self) -> Dict:
        """Get current GPS coordinates."""
        logger.info("🛰️ Reading GPS location...")
        
        gps_data = {
            "latitude": 0,
            "longitude": 0,
            "altitude": 0,
            "accuracy": 0,
            "provider": "unknown"
        }
        
        # Get last known location from location service
        result = self.run_adb(["shell", "dumpsys", "location"])
        
        for line in result.split("\n"):
            if "last location=" in line:
                # Parse location string: Location[gps -1.217755,36.939079 hAcc=28.782...]
                try:
                    loc_str = line.split("last location=")[1].strip()
                    
                    # Extract coordinates
                    if "gps" in loc_str or "network" in loc_str:
                        if "gps" in loc_str:
                            gps_data["provider"] = "gps"
                        elif "network" in loc_str:
                            gps_data["provider"] = "network"
                    
                    # Extract lat/lng - format: lat,lng or lat,lng hAcc=...
                    if "," in loc_str:
                        coords_part = loc_str.split()[1] if " " in loc_str else loc_str
                        coords = coords_part.replace("hAcc", "").strip().split(",")
                        if len(coords) >= 2:
                            gps_data["latitude"] = float(coords[0])
                            gps_data["longitude"] = float(coords[1])
                    
                    # Extract accuracy
                    if "hAcc=" in loc_str:
                        acc_str = loc_str.split("hAcc=")[1].split()[0]
                        gps_data["accuracy"] = float(acc_str)
                    
                    # Extract altitude
                    if "alt=" in loc_str:
                        alt_str = loc_str.split("alt=")[1].split()[0]
                        gps_data["altitude"] = float(alt_str)
                        
                except Exception as e:
                    logger.warning(f"   GPS parse error: {e}")
        
        self.data["gps"] = gps_data
        logger.info(f"   Location: {gps_data['latitude']},{gps_data['longitude']} ({gps_data['provider']})")
        
        return gps_data
    
    # ========== Noise Level Detection ==========
    def measure_noise_level(self) -> Dict:
        """Measure ambient noise level."""
        logger.info("🔊 Measuring noise level...")
        
        noise_data = {
            "level": "N/A",
            "status": "unavailable",
            "db_estimate": 0
        }
        
        # Try to get audio context / media volume as proxy
        result = self.run_adb(["shell", "dumpsys", "audio"])
        
        # Look for media/alarm/ring volumes
        for line in result.split("\n"):
            if ".Media volume:" in line or "media:" in line.lower():
                try:
                    vol = int(line.split(":")[-1].strip())
                    # Estimate dB (0-15 scale to ~30-90 dB)
                    db_estimate = 30 + (vol / 15) * 60
                    noise_data["db_estimate"] = db_estimate
                    noise_data["level"] = self._classify_noise(db_estimate)
                    noise_data["status"] = "measured"
                except:
                    pass
        
        # Alternative: Try to get proximity sensor as activity indicator
        if noise_data["status"] == "unavailable":
            prox_result = self.run_adb(["shell", "dumpsys", "sensorservice"])
            for line in prox_result.split("\n"):
                if "PROXIMITY" in line and "last" in line.lower():
                    noise_data["status"] = "sensor_active"
        
        self.data["noise"] = noise_data
        logger.info(f"   Noise: {noise_data['level']} (~{noise_data['db_estimate']} dB)")
        
        return noise_data
    
    def _classify_noise(self, db: float) -> str:
        """Classify noise level."""
        if db < 40:
            return "quiet"
        elif db < 60:
            return "moderate"
        elif db < 80:
            return "loud"
        else:
            return "very_loud"
    
    # ========== Movement Detection ==========
    def detect_movement(self) -> Dict:
        """Detect movement using accelerometer."""
        logger.info("🏃 Checking movement...")
        
        movement_data = {
            "status": "idle",
            "acceleration": {"x": 0, "y": 0, "z": 0},
            "magnitude": 0,
            "is_moving": False
        }
        
        # Get accelerometer data
        result = self.run_adb(["shell", "dumpsys", "sensorservice"])
        
        accel_data = []
        in_accel_section = False
        
        for line in result.split("\n"):
            if "ACCELEROMETER" in line:
                in_accel_section = True
            elif in_accel_section and "last" in line.lower():
                # Parse: ts=xxx wall=xxx x, y, z,
                try:
                    if "," in line:
                        parts = line.split(",")
                        for part in parts:
                            if "x=" in part:
                                movement_data["acceleration"]["x"] = float(part.split("=")[1])
                            elif "y=" in part:
                                movement_data["acceleration"]["y"] = float(part.split("=")[1])
                            elif "z=" in part:
                                movement_data["acceleration"]["z"] = float(part.split("=")[1])
                except Exception as e:
                    logger.warning(f"   Accel parse error: {e}")
                in_accel_section = False
        
        # Calculate magnitude
        ax = movement_data["acceleration"]["x"]
        ay = movement_data["acceleration"]["y"]
        az = movement_data["acceleration"]["z"]
        magnitude = math.sqrt(ax**2 + ay**2 + az**2)
        movement_data["magnitude"] = magnitude
        
        # Establish baseline if needed
        if len(self.baseline_samples) < BASELINE_SAMPLES:
            self.baseline_samples.append({"x": ax, "y": ay, "z": az})
            if len(self.baseline_samples) == BASELINE_SAMPLES:
                self.baseline = {
                    "x": sum(s["x"] for s in self.baseline_samples) / BASELINE_SAMPLES,
                    "y": sum(s["y"] for s in self.baseline_samples) / BASELINE_SAMPLES,
                    "z": sum(s["z"] for s in self.baseline_samples) / BASELINE_SAMPLES
                }
                logger.info(f"   📏 Baseline established: {self.baseline}")
        
        # Detect movement
        if self.baseline:
            deviation = math.sqrt(
                (ax - self.baseline["x"])**2 + 
                (ay - self.baseline["y"])**2 + 
                (az - self.baseline["z"])**2
            )
            movement_data["deviation"] = deviation
            
            if deviation > MOVEMENT_THRESHOLD:
                movement_data["status"] = "moving"
                movement_data["is_moving"] = True
                self.last_movement_time = datetime.now()
                self.movement_detected = True
                logger.warning(f"   ⚠️ MOVEMENT DETECTED! Deviation: {deviation:.2f} m/s²")
            else:
                movement_data["status"] = "idle"
        
        self.data["movement"] = movement_data
        
        return movement_data
    
    def log_movement_event(self):
        """Log movement event to file."""
        if self.movement_detected:
            event = {
                "timestamp": datetime.now().isoformat(),
                "gps": self.data.get("gps", {}),
                "wifi": self.data.get("wifi", {}).get("current_network", "unknown"),
                "acceleration": self.data["movement"]["acceleration"]
            }
            with open(MOVEMENT_LOG, 'a') as f:
                f.write(json.dumps(event) + "\n")
            self.movement_detected = False
    
    # ========== Sync with Mothership ==========
    def sync_to_mothership(self) -> bool:
        """Sync environment data to mothership."""
        if not SYNC_ENABLED:
            return False
            
        try:
            response = requests.post(
                MOTHERSHIP_URL,
                json=self.data,
                timeout=10
            )
            if response.status_code == 200:
                logger.info(f"✅ Synced to mothership: {response.json()}")
                return True
            else:
                logger.warning(f"⚠️ Sync failed: {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Sync error: {e}")
        
        return False
    
    # ========== Full Scan ==========
    def run_full_scan(self) -> Dict:
        """Run complete environment scan."""
        logger.info("🔍 Starting environment scan...")
        
        self.data = {
            "wifi": self.scan_wifi_networks(),
            "gps": self.get_gps_location(),
            "noise": self.measure_noise_level(),
            "movement": self.detect_movement(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Log movement if detected
        if self.data["movement"]["is_moving"]:
            self.log_movement_event()
        
        # Save data
        with open(ENV_DATA_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
        
        # Try sync
        self.sync_to_mothership()
        
        logger.info("✅ Environment scan complete")
        return self.data
    
    def format_summary(self) -> str:
        """Format scan summary."""
        wifi = self.data.get("wifi", {})
        gps = self.data.get("gps", {})
        noise = self.data.get("noise", {})
        movement = self.data.get("movement", {})
        
        return f"""
🌍 **Terminator Environment Scan**
{self.data.get('timestamp', '')}

📡 **WiFi**
- Network: {wifi.get('current_network', 'N/A')}
- Signal: {wifi.get('signal_strength', 'N/A')} dBm
- Freq: {wifi.get('frequency', 'N/A')} MHz
- IP: {wifi.get('ip_address', 'N/A')}

🛰️ **GPS**
- Location: {gps.get('latitude', 0):.6f}, {gps.get('longitude', 0):.6f}
- Altitude: {gps.get('altitude', 'N/A')}m
- Accuracy: {gps.get('accuracy', 'N/A')}m
- Provider: {gps.get('provider', 'N/A')}

🔊 **Noise**
- Level: {noise.get('level', 'N/A')}
- Estimated: {noise.get('db_estimate', 'N/A')} dB

🏃 **Movement**
- Status: {movement.get('status', 'N/A')}
- Magnitude: {movement.get('magnitude', 0):.2f} m/s²
- Moving: {'YES ⚠️' if movement.get('is_moving') else 'No'}
"""


def continuous_scan(interval: int = 60):
    """Run continuous scanning."""
    scanner = EnvironmentScanner()
    logger.info(f"🔄 Starting continuous scan (interval: {interval}s)")
    
    while True:
        try:
            scanner.run_full_scan()
            print(scanner.format_summary())
            time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("⏹️ Scan stopped")
            break
        except Exception as e:
            logger.error(f"Scan error: {e}")
            time.sleep(interval)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Environment Scanner for Android")
    parser.add_argument("--scan", action="store_true", help="Run full scan")
    parser.add_argument("--continuous", action="store_true", help="Run continuous scan")
    parser.add_argument("--interval", type=int, default=60, help="Scan interval in seconds")
    parser.add_argument("--sync", action="store_true", help="Sync to mothership")
    
    args = parser.parse_args()
    
    scanner = EnvironmentScanner()
    
    if args.continuous:
        continuous_scan(args.interval)
    elif args.scan or args.sync:
        scanner.run_full_scan()
        print(scanner.format_summary())
        if args.sync:
            scanner.sync_to_mothership()
    else:
        # Default: single scan
        scanner.run_full_scan()
        print(scanner.format_summary())


if __name__ == "__main__":
    main()