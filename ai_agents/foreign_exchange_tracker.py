"""
Foreign Exchange Tracker for ULTRATHINK
Tracks political trading on global stock exchanges
Detects cross-border coordination and regulatory arbitrage
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import pytz

logger = logging.getLogger(__name__)


class ForeignExchangeTracker:
    """Track political trading across global exchanges"""

    EXCHANGES = {
        'US': {
            'name': 'US Stock Exchanges',
            'suffix': '',
            'currency': 'USD',
            'timezone': 'America/New_York',
            'disclosure_days': 45,  # US STOCK Act
            'major_indices': ['SPY', 'QQQ', 'DIA']
        },
        'LSE': {
            'name': 'London Stock Exchange',
            'suffix': '.L',
            'currency': 'GBP',
            'timezone': 'Europe/London',
            'disclosure_days': 14,  # UK Parliament rules
            'major_indices': ['FTSE', 'ISF.L']
        },
        'TSX': {
            'name': 'Toronto Stock Exchange',
            'suffix': '.TO',
            'currency': 'CAD',
            'timezone': 'America/Toronto',
            'disclosure_days': 30,  # Canadian disclosure
            'major_indices': ['XIU.TO']  # TSX 60
        },
        'HKEX': {
            'name': 'Hong Kong Exchange',
            'suffix': '.HK',
            'currency': 'HKD',
            'timezone': 'Asia/Hong_Kong',
            'disclosure_days': 7,  # Stricter rules
            'major_indices': ['2800.HK']  # Hang Seng
        },
        'TSE': {
            'name': 'Tokyo Stock Exchange',
            'suffix': '.T',
            'currency': 'JPY',
            'timezone': 'Asia/Tokyo',
            'disclosure_days': 30,
            'major_indices': ['1329.T']  # Nikkei 225
        },
        'XETRA': {
            'name': 'Deutsche Börse (XETRA)',
            'suffix': '.DE',
            'currency': 'EUR',
            'timezone': 'Europe/Berlin',
            'disclosure_days': 30,  # EU MAR rules
            'major_indices': ['EXS1.DE']  # DAX
        },
        'EURONEXT': {
            'name': 'Euronext Paris',
            'suffix': '.PA',
            'currency': 'EUR',
            'timezone': 'Europe/Paris',
            'disclosure_days': 30,
            'major_indices': ['CW8.PA']  # CAC 40
        }
    }

    def __init__(self):
        self.patterns = []

    def detect_cross_border_patterns(self, trades_by_exchange: Dict[str, List[Dict]]) -> List[Dict]:
        """Detect coordinated trading across countries"""

        patterns = []

        # Group trades by politician
        politician_trades = defaultdict(lambda: defaultdict(list))
        for exchange, trades in trades_by_exchange.items():
            for trade in trades:
                politician = trade.get('politician_name')
                politician_trades[politician][exchange].append(trade)

        # Find politicians trading on multiple exchanges
        for politician, exchanges in politician_trades.items():
            if len(exchanges) > 1:
                pattern = self._analyze_cross_border_politician(politician, exchanges)
                if pattern:
                    patterns.append(pattern)

        # Find synchronized timing across countries
        timing_patterns = self._detect_synchronized_timing(trades_by_exchange)
        patterns.extend(timing_patterns)

        # Find sector coordination (same sector, different countries)
        sector_patterns = self._detect_sector_coordination(trades_by_exchange)
        patterns.extend(sector_patterns)

        return patterns

    def _analyze_cross_border_politician(self, politician: str, exchanges: Dict) -> Optional[Dict]:
        """Analyze a politician trading on multiple exchanges"""

        exchange_list = list(exchanges.keys())
        total_trades = sum(len(trades) for trades in exchanges.values())

        # Calculate diversification across countries
        country_diversity = len(exchange_list)

        # Check timing correlation
        all_dates = []
        for exchange, trades in exchanges.items():
            for trade in trades:
                date = trade.get('transaction_date')
                if date:
                    all_dates.append((date, exchange))

        all_dates.sort()

        # Find clusters (trades within 7 days across different countries)
        clusters = []
        for i, (date1, ex1) in enumerate(all_dates):
            cluster = [(date1, ex1)]
            for date2, ex2 in all_dates[i+1:]:
                if ex1 != ex2:  # Different exchange
                    date1_obj = datetime.fromisoformat(date1)
                    date2_obj = datetime.fromisoformat(date2)
                    if abs((date2_obj - date1_obj).days) <= 7:
                        cluster.append((date2, ex2))

            if len(cluster) > 1:
                clusters.append(cluster)

        if country_diversity >= 2 and clusters:
            return {
                'type': 'cross_border_trading',
                'politician': politician,
                'exchanges': exchange_list,
                'country_diversity': country_diversity,
                'total_trades': total_trades,
                'timing_clusters': len(clusters),
                'significance': 'high' if country_diversity >= 3 else 'medium',
                'explanation': f"{politician} trades on {country_diversity} exchanges with {len(clusters)} timing clusters",
                'regulatory_concern': 'Possible arbitrage using different disclosure rules'
            }

        return None

    def _detect_synchronized_timing(self, trades_by_exchange: Dict) -> List[Dict]:
        """Find trades at similar times across exchanges (adjusted for time zones)"""

        patterns = []

        # Convert all trades to UTC
        utc_trades = []
        for exchange, trades in trades_by_exchange.items():
            tz = pytz.timezone(self.EXCHANGES[exchange]['timezone'])
            for trade in trades:
                date_str = trade.get('transaction_date')
                if date_str:
                    try:
                        # Assume market close time for each exchange
                        local_time = tz.localize(datetime.fromisoformat(date_str).replace(hour=16, minute=0))
                        utc_time = local_time.astimezone(pytz.UTC)
                        utc_trades.append({
                            'utc_time': utc_time,
                            'exchange': exchange,
                            'trade': trade
                        })
                    except:
                        pass

        # Find trades within 24 hours across different exchanges
        utc_trades.sort(key=lambda x: x['utc_time'])

        for i, trade1 in enumerate(utc_trades):
            synchronized_group = [trade1]
            for trade2 in utc_trades[i+1:]:
                if trade2['exchange'] != trade1['exchange']:
                    time_diff = abs((trade2['utc_time'] - trade1['utc_time']).total_seconds())
                    if time_diff <= 24 * 3600:  # Within 24 hours
                        synchronized_group.append(trade2)

            if len(synchronized_group) >= 3:  # At least 3 trades
                patterns.append({
                    'type': 'synchronized_global_timing',
                    'num_trades': len(synchronized_group),
                    'exchanges': list(set(t['exchange'] for t in synchronized_group)),
                    'time_window': '24_hours',
                    'significance': 'very_high',
                    'explanation': f"{len(synchronized_group)} trades across {len(set(t['exchange'] for t in synchronized_group))} countries within 24 hours"
                })

        return patterns

    def _detect_sector_coordination(self, trades_by_exchange: Dict) -> List[Dict]:
        """Find same sector traded across countries (e.g., tech stocks in US + UK + Japan)"""

        patterns = []

        # Sector keywords
        SECTORS = {
            'tech': ['NVDA', 'MSFT', 'AAPL', 'GOOGL', 'ARM.L', '6758.T', 'SAP.DE'],
            'finance': ['JPM', 'BAC', 'GS', 'BARC.L', '8306.T', 'DBK.DE'],
            'pharma': ['JNJ', 'PFE', 'AZN.L', '4502.T', 'BAYRY.DE'],
            'energy': ['XOM', 'CVX', 'BP.L', 'SHEL.L', '5020.T']
        }

        # Group trades by sector
        sector_trades = defaultdict(lambda: defaultdict(list))
        for exchange, trades in trades_by_exchange.items():
            for trade in trades:
                ticker = trade.get('ticker', '')
                for sector, tickers in SECTORS.items():
                    if any(t in ticker for t in tickers):
                        sector_trades[sector][exchange].append(trade)

        # Find sectors traded across multiple exchanges
        for sector, exchanges in sector_trades.items():
            if len(exchanges) >= 2:
                total_trades = sum(len(trades) for trades in exchanges.values())
                patterns.append({
                    'type': 'sector_coordination',
                    'sector': sector,
                    'exchanges': list(exchanges.keys()),
                    'total_trades': total_trades,
                    'significance': 'high' if len(exchanges) >= 3 else 'medium',
                    'explanation': f"{sector} sector traded across {len(exchanges)} countries"
                })

        return patterns

    def detect_regulatory_arbitrage(self, trades_by_exchange: Dict) -> List[Dict]:
        """Find trades exploiting different disclosure rules"""

        patterns = []

        # Group by politician
        politician_trades = defaultdict(lambda: defaultdict(list))
        for exchange, trades in trades_by_exchange.items():
            for trade in trades:
                politician = trade.get('politician_name')
                politician_trades[politician][exchange].append(trade)

        for politician, exchanges in politician_trades.items():
            # Check if trading in country with shorter disclosure window before US
            for exchange in exchanges:
                if exchange == 'US':
                    continue

                disclosure_days = self.EXCHANGES[exchange]['disclosure_days']
                us_disclosure_days = self.EXCHANGES['US']['disclosure_days']

                if disclosure_days < us_disclosure_days:
                    # This exchange has faster disclosure requirements
                    # Check if politician traded here before US trades

                    foreign_trades = exchanges.get(exchange, [])
                    us_trades = exchanges.get('US', [])

                    if foreign_trades and us_trades:
                        # Find foreign trades before US trades
                        arbitrage_instances = []
                        for f_trade in foreign_trades:
                            f_date = datetime.fromisoformat(f_trade.get('transaction_date', ''))
                            for us_trade in us_trades:
                                us_date = datetime.fromisoformat(us_trade.get('transaction_date', ''))
                                if f_date < us_date:
                                    days_diff = (us_date - f_date).days
                                    if disclosure_days < days_diff < us_disclosure_days:
                                        arbitrage_instances.append({
                                            'foreign_trade': f_trade,
                                            'us_trade': us_trade,
                                            'days_between': days_diff
                                        })

                        if arbitrage_instances:
                            patterns.append({
                                'type': 'regulatory_arbitrage',
                                'politician': politician,
                                'fast_disclosure_exchange': exchange,
                                'fast_disclosure_days': disclosure_days,
                                'slow_disclosure_exchange': 'US',
                                'slow_disclosure_days': us_disclosure_days,
                                'instances': len(arbitrage_instances),
                                'significance': 'very_high',
                                'explanation': f"{politician} traded on {exchange} ({disclosure_days} day disclosure) before US trades (45 day disclosure)",
                                'regulatory_concern': 'HIGH - Exploiting disclosure timing differences'
                            })

        return patterns

    def get_exchange_info(self, ticker: str) -> Optional[str]:
        """Determine which exchange a ticker belongs to"""
        for exchange, info in self.EXCHANGES.items():
            suffix = info['suffix']
            if suffix and ticker.endswith(suffix):
                return exchange
            elif not suffix and '.' not in ticker:
                return 'US'
        return None

    def convert_currency(self, amount: float, from_currency: str, to_currency: str = 'USD') -> float:
        """Convert currency (simplified - use real API in production)"""

        # Approximate exchange rates (use real-time API in production)
        RATES = {
            'USD': 1.0,
            'GBP': 1.27,
            'CAD': 0.74,
            'EUR': 1.09,
            'JPY': 0.0067,
            'HKD': 0.13
        }

        if from_currency == to_currency:
            return amount

        usd_amount = amount * RATES.get(from_currency, 1.0)
        return usd_amount / RATES.get(to_currency, 1.0)

    def analyze_all_exchanges(self, all_trades: List[Dict]) -> Dict[str, Any]:
        """Comprehensive multi-exchange analysis"""

        # Separate trades by exchange
        trades_by_exchange = defaultdict(list)
        for trade in all_trades:
            ticker = trade.get('ticker', '')
            exchange = self.get_exchange_info(ticker)
            if exchange:
                trades_by_exchange[exchange].append(trade)

        # Run all detection methods
        results = {
            'timestamp': datetime.now().isoformat(),
            'exchanges_analyzed': list(trades_by_exchange.keys()),
            'total_trades': len(all_trades),
            'trades_by_exchange': {ex: len(trades) for ex, trades in trades_by_exchange.items()},
            'patterns': {
                'cross_border': self.detect_cross_border_patterns(trades_by_exchange),
                'regulatory_arbitrage': self.detect_regulatory_arbitrage(trades_by_exchange)
            },
            'statistics': self._calculate_statistics(trades_by_exchange)
        }

        return results

    def _calculate_statistics(self, trades_by_exchange: Dict) -> Dict:
        """Calculate multi-exchange statistics"""

        stats = {}

        for exchange, trades in trades_by_exchange.items():
            currency = self.EXCHANGES[exchange]['currency']

            total_value_local = sum(
                trade.get('amount_min', 0) or trade.get('amount_max', 0) or 0
                for trade in trades
            )

            total_value_usd = self.convert_currency(total_value_local, currency, 'USD')

            stats[exchange] = {
                'total_trades': len(trades),
                'total_value_local': total_value_local,
                'total_value_usd': total_value_usd,
                'currency': currency,
                'unique_tickers': len(set(t.get('ticker') for t in trades)),
                'unique_politicians': len(set(t.get('politician_name') for t in trades))
            }

        return stats


__all__ = ['ForeignExchangeTracker']


if __name__ == "__main__":
    # Example usage
    tracker = ForeignExchangeTracker()

    print("=== Foreign Exchange Tracker ===")
    print(f"\nSupported Exchanges: {len(tracker.EXCHANGES)}")
    for code, info in tracker.EXCHANGES.items():
        print(f"  {code}: {info['name']} ({info['currency']}) - {info['disclosure_days']} day disclosure")

    print("\n=== Setup Instructions ===")
    print("""
To add foreign exchange support:

1. Update database to accept foreign tickers
2. Add data ingestion for foreign exchanges
3. Configure exchange-specific scraping
4. Enable currency conversion API

Data Sources (FREE/CHEAP):
- Yahoo Finance: Free API for all exchanges
- Alpha Vantage: Free tier, 500 calls/day
- Financial Modeling Prep: $19.99/month for global data
    """)
