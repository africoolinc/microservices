#!/usr/bin/env python3
"""
Notion Integration for Trading Reports
Post trading updates to Notion database
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path

WORKSPACE = "/home/africool/.openclaw/workspace"
NOTION_KEY_PATH = f"{WORKSPACE}/.secrets/notion_api.json"

class NotionReporter:
    def __init__(self):
        self.load_credentials()
        
    def load_credentials(self):
        """Load Notion API credentials"""
        if Path(NOTION_KEY_PATH).exists():
            with open(NOTION_KEY_PATH) as f:
                creds = json.load(f)
                self.api_key = creds.get("api_key")
                self.database_id = creds.get("database_id")
        else:
            self.api_key = None
            self.database_id = None
            
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    def is_configured(self):
        """Check if Notion is configured"""
        return bool(self.api_key and self.database_id)
    
    def create_page(self, title, content, status="Active", tags=None):
        """Create a new page in Notion database"""
        if not self.is_configured():
            return {"error": "Notion not configured"}
        
        # Build properties
        properties = {
            "Title": {"title": [{"text": {"content": title}}]},
            "Status": {"select": {"name": status}},
            "Date": {"date": {"start": datetime.now().isoformat()}}
        }
        
        # Add tags if provided
        if tags:
            properties["Tags"] = {"multi_select": [{"name": t} for t in tags]}
        
        # Build children blocks for content
        children = []
        for line in content.split("\n"):
            if line.strip():
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": line}}]
                    }
                })
        
        data = {
            "parent": {"database_id": self.database_id},
            "properties": properties,
            "children": children
        }
        
        response = requests.post(
            f"{self.base_url}/pages",
            headers=self.headers,
            json=data
        )
        
        return response.json()
    
    def create_trading_report(self, equity, position, pnl, recommendations):
        """Create a trading report page"""
        if not self.is_configured():
            return {"error": "Notion not configured - see .secrets/notion_api.json"}
        
        title = f"📊 Trading Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        content = f"""
Equity: ${equity:.2f}
Position: {position}
PnL: {pnl}
Recommendations: {recommendations}
"""
        return self.create_page(title, content, status="Tracked", tags=["Trading", "Hyperliquid"])
    
    def query_database(self, filter_status=None):
        """Query the Notion database"""
        if not self.is_configured():
            return {"error": "Notion not configured"}
        
        query = {"page_size": 10}
        
        if filter_status:
            query["filter"] = {
                "property": "Status",
                "select": {"equals": filter_status}
            }
        
        response = requests.post(
            f"{self.base_url}/databases/{self.database_id}/query",
            headers=self.headers,
            json=query
        )
        
        return response.json()
    
    def setup_instructions(self):
        """Print setup instructions"""
        print("""
╔════════════════════════════════════════════════════════════════╗
║              NOTION INTEGRATION SETUP                         ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  1. Create Integration:                                       ║
║     - Go to https://www.notion.so/my-integrations             ║
║     - Create new integration "Gibson Trading Desk"            ║
║     - Copy the Internal Integration Token                     ║
║                                                                ║
║  2. Create Database:                                          ║
║     - Create a new database in Notion                        ║
║     - Add columns: Title, Status, Date, Tags                  ║
║     - Share with your integration                             ║
║     - Copy Database ID from URL                               ║
║                                                                ║
║  3. Configure:                                                ║
║     - Create .secrets/notion_api.json:                       ║
║                                                                ║
║     {{                                                        ║
║       "api_key": "secret_...",                               ║
║       "database_id": "..."                                   ║
║     }}                                                        ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
""")

def main():
    reporter = NotionReporter()
    
    if not reporter.is_configured():
        reporter.setup_instructions()
        return
    
    # Test connection
    result = reporter.query_database()
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"✓ Connected to Notion - {len(result.get('results', []))} pages found")

if __name__ == "__main__":
    main()
