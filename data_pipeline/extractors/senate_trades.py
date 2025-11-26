"""
Senate Stock Trade Data Extractor
Fetches periodic transaction reports from Senate Financial Disclosures
"""

import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from bs4 import BeautifulSoup
import json

logger = logging.getLogger(__name__)

class SenateTradingExtractor:
    """Extract Senate stock trading data from public disclosures"""
    
    # Senate Electronic Financial Disclosures (EFD) system
    BASE_URL = "https://efdsearch.senate.gov"
    
    def __init__(self):
        self.session = None
        self.data_cache = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    async def fetch_recent_disclosures(self, days_back: int = 30) -> List[Dict]:
        """
        Fetch recent periodic transaction reports
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of disclosure records
        """
        disclosures = []
        
        # Date range for search
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        logger.info(f"Fetching Senate disclosures from {start_date} to {end_date}")
        
        # Search parameters
        params = {
            'start_date': start_date.strftime('%m/%d/%Y'),
            'end_date': end_date.strftime('%m/%d/%Y'),
            'report_type': 'PTR',  # Periodic Transaction Report
        }
        
        try:
            # Note: This is a simplified example - actual implementation would need
            # to handle the Senate's specific API or web scraping requirements
            search_url = f"{self.BASE_URL}/search/report/data/"
            
            async with self.session.post(search_url, data=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for record in data.get('results', []):
                        disclosure = await self._parse_disclosure(record)
                        if disclosure:
                            disclosures.append(disclosure)
                            
        except Exception as e:
            logger.error(f"Error fetching Senate disclosures: {e}")
            
        logger.info(f"Found {len(disclosures)} Senate disclosures")
        return disclosures
        
    async def _parse_disclosure(self, record: Dict) -> Optional[Dict]:
        """
        Parse individual disclosure record
        
        Args:
            record: Raw disclosure data
            
        Returns:
            Parsed disclosure or None if invalid
        """
        try:
            # Extract relevant fields
            disclosure = {
                'source': 'senate',
                'politician_name': record.get('first_name', '') + ' ' + record.get('last_name', ''),
                'state': record.get('state'),
                'party': record.get('party'),
                'disclosure_date': record.get('filed_date'),
                'transactions': []
            }
            
            # Parse PDF or HTML content for transaction details
            if record.get('ptr_link'):
                transactions = await self._extract_transactions(record['ptr_link'])
                disclosure['transactions'] = transactions
                
            return disclosure if disclosure['transactions'] else None
            
        except Exception as e:
            logger.error(f"Error parsing disclosure: {e}")
            return None
            
    async def _extract_transactions(self, document_url: str) -> List[Dict]:
        """
        Extract transaction details from disclosure document
        
        Args:
            document_url: URL to the disclosure document
            
        Returns:
            List of transaction records
        """
        transactions = []
        
        try:
            async with self.session.get(document_url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Parse transaction table (simplified example)
                    # Actual implementation would need specific parsing logic
                    trans_table = soup.find('table', {'class': 'transaction-table'})
                    
                    if trans_table:
                        for row in trans_table.find_all('tr')[1:]:  # Skip header
                            cells = row.find_all('td')
                            if len(cells) >= 6:
                                transaction = {
                                    'date': cells[0].text.strip(),
                                    'ticker': cells[1].text.strip(),
                                    'asset_name': cells[2].text.strip(),
                                    'transaction_type': cells[3].text.strip(),  # Buy/Sell
                                    'amount_range': cells[4].text.strip(),
                                    'comment': cells[5].text.strip() if len(cells) > 5 else ''
                                }
                                transactions.append(transaction)
                                
        except Exception as e:
            logger.error(f"Error extracting transactions from {document_url}: {e}")
            
        return transactions
        
    async def fetch_senator_profile(self, senator_name: str) -> Optional[Dict]:
        """
        Fetch detailed profile for a specific senator
        
        Args:
            senator_name: Name of the senator
            
        Returns:
            Senator profile data
        """
        try:
            # Search for senator
            search_url = f"{self.BASE_URL}/search/member/"
            params = {'search_term': senator_name}
            
            async with self.session.get(search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('results'):
                        member = data['results'][0]
                        
                        profile = {
                            'name': f"{member.get('first_name')} {member.get('last_name')}",
                            'state': member.get('state'),
                            'party': member.get('party'),
                            'office': member.get('office'),
                            'committees': member.get('committees', []),
                            'total_trades': 0,
                            'total_value': 0,
                            'most_traded_stocks': []
                        }
                        
                        # Get trading history
                        history = await self._get_trading_history(senator_name)
                        if history:
                            profile.update(history)
                            
                        return profile
                        
        except Exception as e:
            logger.error(f"Error fetching senator profile: {e}")
            
        return None
        
    async def _get_trading_history(self, senator_name: str) -> Dict:
        """
        Get comprehensive trading history for a senator
        
        Args:
            senator_name: Name of the senator
            
        Returns:
            Trading history statistics
        """
        # Fetch all historical trades
        # Analyze patterns
        # Calculate statistics
        
        return {
            'total_trades': 0,
            'total_value': 0,
            'most_traded_stocks': [],
            'best_performers': [],
            'worst_performers': []
        }


async def main():
    """Example usage"""
    async with SenateTradingExtractor() as extractor:
        # Fetch recent disclosures
        disclosures = await extractor.fetch_recent_disclosures(days_back=30)
        
        for disclosure in disclosures[:5]:  # Show first 5
            print(f"\n{disclosure['politician_name']} ({disclosure['party']}-{disclosure['state']})")
            print(f"Filed: {disclosure['disclosure_date']}")
            print(f"Transactions: {len(disclosure['transactions'])}")
            
            for trans in disclosure['transactions'][:3]:  # Show first 3 transactions
                print(f"  - {trans['date']}: {trans['transaction_type']} {trans['ticker']} ({trans['amount_range']})")


if __name__ == "__main__":
    asyncio.run(main())