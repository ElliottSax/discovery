"""
ETL Pipeline Orchestrator
Coordinates data extraction, transformation, and loading
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
import json
from pathlib import Path

from data_pipeline.extractors.senate_trades import SenateTradingExtractor
from data_pipeline.extractors.house_trades import HouseTradingExtractor
from data_pipeline.extractors.market_data import MarketDataExtractor

logger = logging.getLogger(__name__)

class ETLOrchestrator:
    """Main orchestrator for the ETL pipeline"""
    
    def __init__(self, config: Dict = None):
        """
        Initialize ETL orchestrator
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.senate_extractor = SenateTradingExtractor()
        self.house_extractor = HouseTradingExtractor()
        self.market_extractor = MarketDataExtractor(self.config.get('api_keys', {}))
        
        # Data storage paths
        self.data_dir = Path(self.config.get('data_dir', './data'))
        self.data_dir.mkdir(exist_ok=True)
        
        # Pipeline state
        self.last_run = None
        self.stats = {
            'trades_processed': 0,
            'politicians_tracked': 0,
            'stocks_analyzed': 0,
            'errors': 0
        }
        
    async def run_full_pipeline(self) -> Dict:
        """
        Run the complete ETL pipeline
        
        Returns:
            Pipeline execution summary
        """
        logger.info("Starting full ETL pipeline run")
        start_time = datetime.now()
        
        results = {
            'start_time': start_time.isoformat(),
            'status': 'running',
            'stages': {}
        }
        
        try:
            # Stage 1: Extract politician trades
            logger.info("Stage 1: Extracting politician trades")
            trades = await self._extract_trades()
            results['stages']['extraction'] = {
                'status': 'completed',
                'senate_trades': len(trades.get('senate', [])),
                'house_trades': len(trades.get('house', []))
            }
            
            # Stage 2: Transform and enrich data
            logger.info("Stage 2: Transforming and enriching data")
            enriched_data = await self._transform_and_enrich(trades)
            results['stages']['transformation'] = {
                'status': 'completed',
                'records_transformed': len(enriched_data)
            }
            
            # Stage 3: Load to database
            logger.info("Stage 3: Loading to database")
            load_results = await self._load_to_database(enriched_data)
            results['stages']['loading'] = {
                'status': 'completed',
                'records_loaded': load_results['records_loaded']
            }
            
            # Stage 4: Generate analytics
            logger.info("Stage 4: Generating analytics")
            analytics = await self._generate_analytics(enriched_data)
            results['stages']['analytics'] = {
                'status': 'completed',
                'reports_generated': len(analytics)
            }
            
            # Update stats
            self.last_run = datetime.now()
            results['end_time'] = self.last_run.isoformat()
            results['duration'] = (self.last_run - start_time).total_seconds()
            results['status'] = 'completed'
            
            logger.info(f"ETL pipeline completed in {results['duration']:.2f} seconds")
            
        except Exception as e:
            logger.error(f"ETL pipeline failed: {e}")
            results['status'] = 'failed'
            results['error'] = str(e)
            self.stats['errors'] += 1
            
        return results
        
    async def _extract_trades(self) -> Dict:
        """
        Extract trades from all sources
        
        Returns:
            Dictionary of trades by source
        """
        trades = {'senate': [], 'house': []}
        
        # Extract Senate trades
        async with self.senate_extractor as extractor:
            senate_trades = await extractor.fetch_recent_disclosures(days_back=30)
            trades['senate'] = senate_trades
            logger.info(f"Extracted {len(senate_trades)} Senate trades")
            
        # Extract House trades
        async with self.house_extractor as extractor:
            house_trades = await extractor.fetch_recent_disclosures(days_back=30)
            trades['house'] = house_trades
            logger.info(f"Extracted {len(house_trades)} House trades")
            
        return trades
        
    async def _transform_and_enrich(self, trades: Dict) -> List[Dict]:
        """
        Transform and enrich trade data with market information
        
        Args:
            trades: Raw trade data
            
        Returns:
            List of enriched trade records
        """
        enriched_records = []
        
        async with self.market_extractor as market:
            # Process all trades
            all_trades = trades.get('senate', []) + trades.get('house', [])
            
            for disclosure in all_trades:
                politician_name = disclosure.get('politician_name')
                
                for transaction in disclosure.get('transactions', []):
                    # Create enriched record
                    record = {
                        'politician_name': politician_name,
                        'chamber': disclosure.get('source'),
                        'state': disclosure.get('state'),
                        'party': disclosure.get('party'),
                        'disclosure_date': disclosure.get('disclosure_date'),
                        'transaction_date': transaction.get('date'),
                        'ticker': transaction.get('ticker'),
                        'asset_name': transaction.get('asset_name'),
                        'transaction_type': transaction.get('transaction_type'),
                        'amount_range': transaction.get('amount_range'),
                        'amount_min': self._parse_amount_range(transaction.get('amount_range'))[0],
                        'amount_max': self._parse_amount_range(transaction.get('amount_range'))[1]
                    }
                    
                    # Enrich with market data
                    if record['ticker']:
                        # Get price at transaction
                        price_data = await market.get_stock_price(
                            record['ticker'],
                            record['transaction_date']
                        )
                        if price_data:
                            record['price_at_transaction'] = price_data.get('close')
                            
                        # Get current price
                        current_price = await market.get_stock_price(record['ticker'])
                        if current_price:
                            record['current_price'] = current_price.get('price')
                            
                        # Calculate performance
                        if record.get('price_at_transaction') and record.get('current_price'):
                            record['return_pct'] = (
                                (record['current_price'] - record['price_at_transaction']) /
                                record['price_at_transaction'] * 100
                            )
                            
                        # Get company info
                        company_info = await market.get_company_info(record['ticker'])
                        if company_info:
                            record['sector'] = company_info.get('sector')
                            record['industry'] = company_info.get('industry')
                            
                    enriched_records.append(record)
                    
        logger.info(f"Enriched {len(enriched_records)} trade records")
        return enriched_records
        
    def _parse_amount_range(self, amount_range: str) -> tuple:
        """
        Parse amount range string to min/max values
        
        Args:
            amount_range: Amount range string (e.g., "$1,001 - $15,000")
            
        Returns:
            Tuple of (min, max) values
        """
        if not amount_range:
            return (0, 0)
            
        # Remove $ and commas
        clean_range = amount_range.replace('$', '').replace(',', '')
        
        # Split by dash
        parts = clean_range.split('-')
        
        if len(parts) == 2:
            try:
                min_val = float(parts[0].strip())
                max_val = float(parts[1].strip())
                return (min_val, max_val)
            except:
                pass
                
        return (0, 0)
        
    async def _load_to_database(self, data: List[Dict]) -> Dict:
        """
        Load enriched data to database
        
        Args:
            data: Enriched trade records
            
        Returns:
            Load results
        """
        # For now, save to JSON files
        # In production, would load to PostgreSQL
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save trades
        trades_file = self.data_dir / f'trades_{timestamp}.json'
        with open(trades_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
            
        # Create DataFrame for analysis
        df = pd.DataFrame(data)
        
        # Save as CSV for easy analysis
        csv_file = self.data_dir / f'trades_{timestamp}.csv'
        df.to_csv(csv_file, index=False)
        
        # Update stats
        self.stats['trades_processed'] += len(data)
        self.stats['politicians_tracked'] = df['politician_name'].nunique()
        self.stats['stocks_analyzed'] = df['ticker'].nunique()
        
        logger.info(f"Loaded {len(data)} records to {trades_file}")
        
        return {
            'records_loaded': len(data),
            'files_created': [str(trades_file), str(csv_file)]
        }
        
    async def _generate_analytics(self, data: List[Dict]) -> List[Dict]:
        """
        Generate analytics and reports
        
        Args:
            data: Enriched trade records
            
        Returns:
            List of generated analytics
        """
        analytics = []
        
        if not data:
            return analytics
            
        df = pd.DataFrame(data)
        
        # 1. Top traded stocks
        top_stocks = df['ticker'].value_counts().head(10).to_dict()
        analytics.append({
            'type': 'top_traded_stocks',
            'data': top_stocks,
            'generated_at': datetime.now().isoformat()
        })
        
        # 2. Most active traders
        trader_activity = df.groupby('politician_name').size().sort_values(ascending=False).head(10).to_dict()
        analytics.append({
            'type': 'most_active_traders',
            'data': trader_activity,
            'generated_at': datetime.now().isoformat()
        })
        
        # 3. Sector distribution
        if 'sector' in df.columns:
            sector_dist = df['sector'].value_counts().to_dict()
            analytics.append({
                'type': 'sector_distribution',
                'data': sector_dist,
                'generated_at': datetime.now().isoformat()
            })
            
        # 4. Buy vs Sell ratio
        if 'transaction_type' in df.columns:
            transaction_types = df['transaction_type'].value_counts().to_dict()
            analytics.append({
                'type': 'transaction_types',
                'data': transaction_types,
                'generated_at': datetime.now().isoformat()
            })
            
        # 5. Performance analysis
        if 'return_pct' in df.columns:
            performance_stats = {
                'average_return': df['return_pct'].mean(),
                'median_return': df['return_pct'].median(),
                'best_performer': df.nlargest(1, 'return_pct')[['politician_name', 'ticker', 'return_pct']].to_dict('records')[0] if len(df) > 0 else None,
                'worst_performer': df.nsmallest(1, 'return_pct')[['politician_name', 'ticker', 'return_pct']].to_dict('records')[0] if len(df) > 0 else None
            }
            analytics.append({
                'type': 'performance_analysis',
                'data': performance_stats,
                'generated_at': datetime.now().isoformat()
            })
            
        # Save analytics
        analytics_file = self.data_dir / f'analytics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(analytics_file, 'w') as f:
            json.dump(analytics, f, indent=2, default=str)
            
        logger.info(f"Generated {len(analytics)} analytics reports")
        
        return analytics
        
    def get_pipeline_status(self) -> Dict:
        """
        Get current pipeline status and statistics
        
        Returns:
            Status dictionary
        """
        return {
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': (self.last_run + timedelta(hours=6)).isoformat() if self.last_run else None,
            'stats': self.stats,
            'data_directory': str(self.data_dir),
            'files': [str(f) for f in self.data_dir.glob('*.json')][:10]  # Last 10 files
        }


async def main():
    """Example usage"""
    
    # Configuration
    config = {
        'data_dir': './data/pipeline',
        'api_keys': {
            'finnhub': 'your_finnhub_key',
            'alphavantage': 'your_alphavantage_key'
        }
    }
    
    # Create orchestrator
    orchestrator = ETLOrchestrator(config)
    
    # Run pipeline
    results = await orchestrator.run_full_pipeline()
    
    print("Pipeline Results:")
    print(json.dumps(results, indent=2, default=str))
    
    # Get status
    status = orchestrator.get_pipeline_status()
    print("\nPipeline Status:")
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    asyncio.run(main())