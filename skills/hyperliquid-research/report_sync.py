#!/usr/bin/env python3
"""
Trading Report Sync - Gmail Calendar + Notion
Generate and sync trading reports to multiple platforms
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = "/home/africool/.openclaw/workspace"
sys.path.append(f"{WORKSPACE}/projects/members/Gibson/skills/hyperliquid-research")

from position_manager import PositionManager
from notion_reporter import NotionReporter

class TradingReportSync:
    def __init__(self):
        self.pos_manager = PositionManager()
        self.notion = NotionReporter()
        
    def generate_summary(self):
        """Generate trading summary from position manager"""
        # Run position manager
        report = self.pos_manager.run()
        
        # Format for display
        btc_price = report["market"]["btc_price"]
        equity = report["account"]["equity"]
        positions = report["account"]["positions_count"]
        
        # Get position details
        pos_details = ""
        for pos in report["account"]["positions"]:
            size = pos["size"]
            entry = pos["entry_price"]
            pnl_pct = ((btc_price - entry) / entry) * 100
            pos_details += f"• {size} BTC @ ${entry:,.0f} ({pnl_pct:+.1f}%)\n"
        
        recommendations = ", ".join(report["recommendations"]) if report["recommendations"] else "HOLD"
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "btc_price": btc_price,
            "equity": equity,
            "positions": positions,
            "position_details": pos_details,
            "recommendations": recommendations
        }
        
        return summary
    
    def sync_notion(self, summary):
        """Sync to Notion"""
        if not self.notion.is_configured():
            print("[Sync] Notion not configured - skipping")
            return {"status": "skipped", "reason": "Not configured"}
        
        position_text = summary["position_details"].replace("\n", " | ")
        
        result = self.notion.create_trading_report(
            equity=summary["equity"],
            position=position_text,
            pnl=summary["recommendations"],
            recommendations=summary["recommendations"]
        )
        
        if "error" in result:
            return {"status": "error", "detail": result["error"]}
        
        return {"status": "success", "notion": result}
    
    def sync_gmail_calendar(self, summary):
        """Generate iCal file for Gmail Calendar import"""
        # Create ICS file
        start = datetime.now()
        end = start + timedelta(minutes=30)
        
        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Gibson Trading Desk//EN
BEGIN:VEVENT
UID:trading-report-{start.strftime('%Y%m%d%H%M')}
DTSTAMP:{start.strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{start.strftime('%Y%m%dT%H%M%S')}
DTEND:{end.strftime('%Y%m%dT%H%M%S')}
SUMMARY:📊 Trading Report - {start.strftime('%H:%M')}
DESCRIPTION:Equity: ${summary['equity']:.2f}\\nBTC: ${summary['btc_price']:,.0f}\\nPositions: {summary['positions']}\\nAction: {summary['recommendations']}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""
        
        # Save ICS file
        ics_path = Path(WORKSPACE) / "memory" / "calendar" / f"trading_report_{start.strftime('%Y%m%d_%H%M')}.ics"
        ics_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(ics_path, 'w') as f:
            f.write(ics_content)
        
        # Also save latest
        latest_path = Path(WORKSPACE) / "memory" / "calendar" / "latest_trading_report.ics"
        with open(latest_path, 'w') as f:
            f.write(ics_content)
        
        return {"status": "success", "file": str(ics_path)}
    
    def run(self):
        """Run full sync"""
        print("=" * 60)
        print("TRADING REPORT SYNC")
        print("=" * 60)
        
        # Generate summary
        summary = self.generate_summary()
        
        print(f"\n📊 Summary:")
        print(f"  BTC: ${summary['btc_price']:,.0f}")
        print(f"  Equity: ${summary['equity']:.2f}")
        print(f"  Positions: {summary['positions']}")
        print(f"  Action: {summary['recommendations']}")
        
        # Sync to Notion
        print(f"\n📓 Syncing to Notion...")
        notion_result = self.sync_notion(summary)
        print(f"  Result: {notion_result['status']}")
        
        # Sync to Gmail Calendar
        print(f"\n📅 Syncing to Gmail Calendar...")
        gmail_result = self.sync_gmail_calendar(summary)
        print(f"  Result: {gmail_result['status']}")
        print(f"  File: {gmail_result.get('file', 'N/A')}")
        
        print("\n" + "=" * 60)
        print("SYNC COMPLETE")
        print("=" * 60)
        
        return {
            "summary": summary,
            "notion": notion_result,
            "gmail": gmail_result
        }

if __name__ == "__main__":
    sync = TradingReportSync()
    sync.run()
