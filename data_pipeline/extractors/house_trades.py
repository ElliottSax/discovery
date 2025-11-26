"""
House of Representatives Stock Trade Data Extractor
Fetches periodic transaction reports from House Financial Disclosures
"""

import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import xml.etree.ElementTree as ET
import json

logger = logging.getLogger(__name__)

class HouseTradingExtractor:
    """Extract House stock trading data from public disclosures"""
    
    # House Financial Disclosure system
    BASE_URL = "https://disclosures-clerk.house.gov"
    
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
        Fetch recent periodic transaction reports from House members
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of disclosure records
        """
        disclosures = []
        
        # Date range for search
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        logger.info(f"Fetching House disclosures from {start_date} to {end_date}")
        
        try:
            # House provides XML feeds for financial disclosures
            # This is a simplified example - actual implementation would parse their specific format
            
            # Fetch Periodic Transaction Reports (PTR)
            ptr_url = f"{self.BASE_URL}/public_disc/ptr-pdfs/{end_date.year}/"
            
            async with self.session.get(ptr_url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Parse the listing page to find PTR files
                    ptr_files = self._extract_ptr_files(content, start_date, end_date)
                    
                    # Process each PTR file
                    for ptr_file in ptr_files:
                        disclosure = await self._process_ptr_file(ptr_file)
                        if disclosure:
                            disclosures.append(disclosure)
                            
        except Exception as e:
            logger.error(f"Error fetching House disclosures: {e}")
            
        logger.info(f"Found {len(disclosures)} House disclosures")
        return disclosures
        
    def _extract_ptr_files(self, content: str, start_date: datetime, end_date: datetime) -> List[str]:
        """
        Extract PTR file links from House disclosure page
        
        Args:
            content: HTML content
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of PTR file URLs
        """
        ptr_files = []
        
        # Parse HTML to find PTR links
        # This is simplified - actual implementation would use BeautifulSoup
        # and handle the House's specific HTML structure
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if 'PTR' in href and href.endswith('.pdf'):
                # Extract date from filename and check range
                # Simplified example - actual implementation would parse date properly
                ptr_files.append(f"{self.BASE_URL}{href}")
                
        return ptr_files
        
    async def _process_ptr_file(self, ptr_url: str) -> Optional[Dict]:
        """
        Process a Periodic Transaction Report file
        
        Args:
            ptr_url: URL to PTR file
            
        Returns:
            Parsed disclosure or None
        """
        try:
            # In production, would use PDF parsing library like PyPDF2 or pdfplumber
            # For now, return example structure
            
            disclosure = {
                'source': 'house',
                'politician_name': self._extract_name_from_url(ptr_url),
                'state': '',  # Would extract from document
                'party': '',  # Would extract from document
                'disclosure_date': datetime.now().isoformat(),
                'document_url': ptr_url,
                'transactions': []
            }
            
            # Extract transactions from PDF
            transactions = await self._extract_transactions_from_pdf(ptr_url)
            disclosure['transactions'] = transactions
            
            return disclosure if disclosure['transactions'] else None
            
        except Exception as e:
            logger.error(f"Error processing PTR file {ptr_url}: {e}")
            return None
            
    def _extract_name_from_url(self, url: str) -> str:
        """Extract representative name from PTR filename"""
        # Simplified - actual implementation would parse filename format
        filename = url.split('/')[-1]
        name_part = filename.replace('PTR_', '').replace('.pdf', '')
        return name_part.replace('_', ' ')
        
    async def _extract_transactions_from_pdf(self, pdf_url: str) -> List[Dict]:
        """
        Extract transaction details from PTR PDF
        
        Args:
            pdf_url: URL to PTR PDF
            
        Returns:
            List of transactions
        """
        transactions = []
        
        try:
            # In production, would download and parse PDF
            # For demonstration, return example transactions
            
            example_transactions = [
                {
                    'date': '2025-01-15',
                    'ticker': 'AAPL',
                    'asset_name': 'Apple Inc.',
                    'transaction_type': 'Purchase',
                    'amount_range': '$1,001 - $15,000',
                    'cap_gains': 'N/A'
                },
                {
                    'date': '2025-01-10',
                    'ticker': 'MSFT',
                    'asset_name': 'Microsoft Corporation',
                    'transaction_type': 'Sale',
                    'amount_range': '$15,001 - $50,000',
                    'cap_gains': '$1,001 - $15,000'
                }
            ]
            
            return example_transactions
            
        except Exception as e:
            logger.error(f"Error extracting transactions from {pdf_url}: {e}")
            
        return transactions
        
    async def fetch_representative_profile(self, rep_name: str) -> Optional[Dict]:
        """
        Fetch detailed profile for a specific representative
        
        Args:
            rep_name: Name of the representative
            
        Returns:
            Representative profile data
        """
        try:
            profile = {
                'name': rep_name,
                'chamber': 'House',
                'state': '',  # Would fetch from official records
                'district': '',  # Would fetch from official records
                'party': '',  # Would fetch from official records
                'committees': [],
                'trading_summary': {
                    'total_trades': 0,
                    'total_value': 0,
                    'most_active_sectors': [],
                    'recent_trades': []
                }
            }
            
            # Fetch trading history
            trades = await self._get_representative_trades(rep_name)
            profile['trading_summary']['recent_trades'] = trades
            profile['trading_summary']['total_trades'] = len(trades)
            
            return profile
            
        except Exception as e:
            logger.error(f"Error fetching representative profile: {e}")
            
        return None
        
    async def _get_representative_trades(self, rep_name: str) -> List[Dict]:
        """
        Get all trades for a specific representative
        
        Args:
            rep_name: Name of the representative
            
        Returns:
            List of trades
        """
        # Would search all PTR filings for this representative
        # and compile comprehensive trade history
        
        return []
        
    async def get_statistics(self) -> Dict:
        """
        Get overall House trading statistics
        
        Returns:
            Statistics dictionary
        """
        stats = {
            'total_members_trading': 0,
            'total_transactions': 0,
            'most_traded_stocks': [],
            'largest_transactions': [],
            'most_active_traders': [],
            'sectors': {
                'technology': 0,
                'healthcare': 0,
                'finance': 0,
                'energy': 0,
                'defense': 0,
                'other': 0
            }
        }
        
        return stats


async def main():
    """Example usage"""
    async with HouseTradingExtractor() as extractor:
        # Fetch recent disclosures
        disclosures = await extractor.fetch_recent_disclosures(days_back=30)
        
        for disclosure in disclosures[:5]:  # Show first 5
            print(f"\n{disclosure['politician_name']}")
            print(f"Filed: {disclosure['disclosure_date']}")
            print(f"Transactions: {len(disclosure['transactions'])}")
            
            for trans in disclosure['transactions'][:3]:  # Show first 3 transactions
                print(f"  - {trans['date']}: {trans['transaction_type']} {trans['ticker']} ({trans['amount_range']})")
                
        # Get statistics
        stats = await extractor.get_statistics()
        print(f"\nHouse Trading Statistics:")
        print(f"Total transactions: {stats['total_transactions']}")
        print(f"Most active sectors: {stats['sectors']}")


if __name__ == "__main__":
    asyncio.run(main())