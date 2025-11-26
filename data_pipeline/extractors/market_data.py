"""
Financial Market Data Extractor
Fetches stock prices, market data, and financial metrics
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
import json
from decimal import Decimal

logger = logging.getLogger(__name__)

class MarketDataExtractor:
    """Extract financial market data for analysis"""
    
    # Free tier APIs for market data
    YAHOO_FINANCE_API = "https://query1.finance.yahoo.com/v8/finance"
    ALPHA_VANTAGE_API = "https://www.alphavantage.co/query"
    FINNHUB_API = "https://finnhub.io/api/v1"
    
    def __init__(self, api_keys: Dict[str, str] = None):
        """
        Initialize market data extractor
        
        Args:
            api_keys: Dictionary of API keys for various services
        """
        self.session = None
        self.api_keys = api_keys or {}
        self.cache = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    async def get_stock_price(self, ticker: str, date: Optional[str] = None) -> Optional[Dict]:
        """
        Get stock price for a specific ticker
        
        Args:
            ticker: Stock ticker symbol
            date: Optional date (YYYY-MM-DD format)
            
        Returns:
            Price data dictionary
        """
        try:
            if date:
                # Get historical price
                return await self._get_historical_price(ticker, date)
            else:
                # Get current price
                return await self._get_current_price(ticker)
                
        except Exception as e:
            logger.error(f"Error fetching price for {ticker}: {e}")
            return None
            
    async def _get_current_price(self, ticker: str) -> Dict:
        """Get current stock price from Yahoo Finance"""
        
        url = f"{self.YAHOO_FINANCE_API}/chart/{ticker}"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                
                if 'chart' in data and 'result' in data['chart']:
                    result = data['chart']['result'][0]
                    meta = result.get('meta', {})
                    
                    return {
                        'ticker': ticker,
                        'price': meta.get('regularMarketPrice'),
                        'previous_close': meta.get('previousClose'),
                        'volume': meta.get('regularMarketVolume'),
                        'market_cap': meta.get('marketCap'),
                        'change': meta.get('regularMarketPrice', 0) - meta.get('previousClose', 0),
                        'change_percent': self._calculate_change_percent(
                            meta.get('regularMarketPrice'),
                            meta.get('previousClose')
                        ),
                        'timestamp': datetime.now().isoformat()
                    }
                    
        return {}
        
    async def _get_historical_price(self, ticker: str, date: str) -> Dict:
        """Get historical stock price"""
        
        # Convert date to timestamp
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        timestamp = int(date_obj.timestamp())
        
        # Get data for date range
        url = f"{self.YAHOO_FINANCE_API}/chart/{ticker}"
        params = {
            'period1': timestamp - 86400,  # Day before
            'period2': timestamp + 86400,  # Day after
            'interval': '1d'
        }
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                
                if 'chart' in data and 'result' in data['chart']:
                    result = data['chart']['result'][0]
                    quotes = result.get('indicators', {}).get('quote', [{}])[0]
                    
                    if quotes:
                        return {
                            'ticker': ticker,
                            'date': date,
                            'open': quotes.get('open', [None])[0],
                            'high': quotes.get('high', [None])[0],
                            'low': quotes.get('low', [None])[0],
                            'close': quotes.get('close', [None])[0],
                            'volume': quotes.get('volume', [None])[0]
                        }
                        
        return {}
        
    def _calculate_change_percent(self, current: float, previous: float) -> float:
        """Calculate percentage change"""
        if previous and previous != 0:
            return ((current - previous) / previous) * 100
        return 0.0
        
    async def get_stock_performance(self, ticker: str, start_date: str, end_date: str) -> Dict:
        """
        Calculate stock performance metrics over a period
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Performance metrics
        """
        try:
            # Get price at start and end
            start_price = await self._get_historical_price(ticker, start_date)
            end_price = await self._get_historical_price(ticker, end_date)
            
            if start_price and end_price:
                start_close = start_price.get('close', 0)
                end_close = end_price.get('close', 0)
                
                if start_close and end_close:
                    return {
                        'ticker': ticker,
                        'period': f"{start_date} to {end_date}",
                        'start_price': start_close,
                        'end_price': end_close,
                        'absolute_change': end_close - start_close,
                        'percent_change': self._calculate_change_percent(end_close, start_close),
                        'performance_rating': self._rate_performance(
                            self._calculate_change_percent(end_close, start_close)
                        )
                    }
                    
        except Exception as e:
            logger.error(f"Error calculating performance for {ticker}: {e}")
            
        return {}
        
    def _rate_performance(self, percent_change: float) -> str:
        """Rate stock performance based on percentage change"""
        if percent_change > 20:
            return 'Excellent'
        elif percent_change > 10:
            return 'Good'
        elif percent_change > 0:
            return 'Positive'
        elif percent_change > -10:
            return 'Negative'
        else:
            return 'Poor'
            
    async def get_company_info(self, ticker: str) -> Dict:
        """
        Get company information and fundamentals
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Company information
        """
        try:
            if self.api_keys.get('finnhub'):
                # Use Finnhub for company profile
                url = f"{self.FINNHUB_API}/stock/profile2"
                params = {
                    'symbol': ticker,
                    'token': self.api_keys['finnhub']
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'ticker': ticker,
                            'name': data.get('name'),
                            'industry': data.get('finnhubIndustry'),
                            'sector': data.get('gics'),
                            'market_cap': data.get('marketCapitalization'),
                            'country': data.get('country'),
                            'exchange': data.get('exchange'),
                            'ipo_date': data.get('ipo'),
                            'website': data.get('weburl'),
                            'logo': data.get('logo')
                        }
            else:
                # Fallback to Yahoo Finance
                return await self._get_yahoo_company_info(ticker)
                
        except Exception as e:
            logger.error(f"Error fetching company info for {ticker}: {e}")
            
        return {}
        
    async def _get_yahoo_company_info(self, ticker: str) -> Dict:
        """Get company info from Yahoo Finance"""
        # Simplified - would implement Yahoo Finance scraping
        return {
            'ticker': ticker,
            'name': ticker,  # Would fetch actual name
            'sector': 'Unknown',
            'industry': 'Unknown'
        }
        
    async def get_market_sentiment(self, ticker: str) -> Dict:
        """
        Get market sentiment and news for a stock
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Sentiment analysis
        """
        sentiment = {
            'ticker': ticker,
            'overall_sentiment': 'Neutral',
            'sentiment_score': 0.0,
            'news_count': 0,
            'positive_news': 0,
            'negative_news': 0,
            'neutral_news': 0,
            'analyst_rating': 'Hold',
            'price_target': 0.0
        }
        
        try:
            if self.api_keys.get('finnhub'):
                # Get news sentiment from Finnhub
                url = f"{self.FINNHUB_API}/news"
                params = {
                    'category': 'company',
                    'symbol': ticker,
                    'token': self.api_keys['finnhub']
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        news = await response.json()
                        
                        # Analyze news sentiment (simplified)
                        for article in news:
                            sentiment['news_count'] += 1
                            # Would use actual NLP for sentiment analysis
                            # For now, use random assignment
                            import random
                            article_sentiment = random.choice(['positive', 'negative', 'neutral'])
                            
                            if article_sentiment == 'positive':
                                sentiment['positive_news'] += 1
                            elif article_sentiment == 'negative':
                                sentiment['negative_news'] += 1
                            else:
                                sentiment['neutral_news'] += 1
                                
                        # Calculate overall sentiment
                        if sentiment['news_count'] > 0:
                            positive_ratio = sentiment['positive_news'] / sentiment['news_count']
                            negative_ratio = sentiment['negative_news'] / sentiment['news_count']
                            
                            if positive_ratio > 0.6:
                                sentiment['overall_sentiment'] = 'Positive'
                                sentiment['sentiment_score'] = positive_ratio
                            elif negative_ratio > 0.6:
                                sentiment['overall_sentiment'] = 'Negative'
                                sentiment['sentiment_score'] = -negative_ratio
                            else:
                                sentiment['overall_sentiment'] = 'Neutral'
                                sentiment['sentiment_score'] = positive_ratio - negative_ratio
                                
        except Exception as e:
            logger.error(f"Error fetching sentiment for {ticker}: {e}")
            
        return sentiment
        
    async def get_insider_trading(self, ticker: str) -> List[Dict]:
        """
        Get insider trading data for a stock
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            List of insider trades
        """
        insider_trades = []
        
        try:
            # Would fetch from SEC EDGAR or financial data provider
            # For now, return example data
            
            example_trades = [
                {
                    'ticker': ticker,
                    'insider_name': 'John Smith',
                    'position': 'CEO',
                    'transaction_date': '2025-01-15',
                    'transaction_type': 'Buy',
                    'shares': 10000,
                    'price': 150.25,
                    'value': 1502500
                },
                {
                    'ticker': ticker,
                    'insider_name': 'Jane Doe',
                    'position': 'CFO',
                    'transaction_date': '2025-01-10',
                    'transaction_type': 'Sell',
                    'shares': 5000,
                    'price': 148.50,
                    'value': 742500
                }
            ]
            
            return example_trades
            
        except Exception as e:
            logger.error(f"Error fetching insider trading for {ticker}: {e}")
            
        return insider_trades
        
    async def compare_to_market(self, ticker: str, benchmark: str = 'SPY') -> Dict:
        """
        Compare stock performance to market benchmark
        
        Args:
            ticker: Stock ticker symbol
            benchmark: Benchmark ticker (default: SPY for S&P 500)
            
        Returns:
            Comparison metrics
        """
        try:
            # Get 30-day performance for both
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            stock_perf = await self.get_stock_performance(
                ticker,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            market_perf = await self.get_stock_performance(
                benchmark,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            if stock_perf and market_perf:
                return {
                    'ticker': ticker,
                    'benchmark': benchmark,
                    'period': '30 days',
                    'stock_return': stock_perf.get('percent_change', 0),
                    'market_return': market_perf.get('percent_change', 0),
                    'alpha': stock_perf.get('percent_change', 0) - market_perf.get('percent_change', 0),
                    'outperformed': stock_perf.get('percent_change', 0) > market_perf.get('percent_change', 0)
                }
                
        except Exception as e:
            logger.error(f"Error comparing {ticker} to market: {e}")
            
        return {}


async def main():
    """Example usage"""
    
    # Example API keys (would load from environment)
    api_keys = {
        'finnhub': 'your_finnhub_api_key',
        'alphavantage': 'your_alphavantage_key'
    }
    
    async with MarketDataExtractor(api_keys) as extractor:
        # Get current price
        price = await extractor.get_stock_price('AAPL')
        print(f"Apple current price: ${price.get('price', 'N/A')}")
        
        # Get performance
        perf = await extractor.get_stock_performance(
            'AAPL',
            '2025-01-01',
            '2025-01-20'
        )
        print(f"Apple performance: {perf.get('percent_change', 0):.2f}%")
        
        # Get sentiment
        sentiment = await extractor.get_market_sentiment('AAPL')
        print(f"Apple sentiment: {sentiment.get('overall_sentiment')}")
        
        # Compare to market
        comparison = await extractor.compare_to_market('AAPL', 'SPY')
        print(f"Apple vs S&P 500: Alpha = {comparison.get('alpha', 0):.2f}%")


if __name__ == "__main__":
    asyncio.run(main())