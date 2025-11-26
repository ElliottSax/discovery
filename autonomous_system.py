#!/usr/bin/env python3
"""
Autonomous Trading Analysis System
Fetches data, analyzes patterns, and generates insights automatically
No database required - works standalone
"""

import json
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import time
import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🤖 AUTONOMOUS TRADING ANALYSIS SYSTEM")
print("=" * 80)

class DataFetcher:
    """Fetches politician trading data from various sources"""
    
    def __init__(self):
        self.data_sources = {
            'senate': 'https://efdsearch.senate.gov/search/home',
            'house': 'https://disclosures-clerk.house.gov/PublicDisclosure/FinancialDisclosure',
            'quiver': 'https://www.quiverquant.com/sources/senatetrading'
        }
        
    def fetch_live_data(self):
        """
        Fetch real politician trading data
        Note: In production, this would connect to real APIs
        """
        print("\n📡 Attempting to fetch live data...")
        
        # For demonstration, we'll simulate API calls
        # In production, this would use requests/selenium to get real data
        
        try:
            # Simulate API call
            time.sleep(1)
            print("   ⚠️  Live API not configured - using generated sample data")
            return None
        except Exception as e:
            print(f"   ❌ Error fetching live data: {e}")
            return None
            
    def generate_sample_data(self, num_politicians=10, days=365):
        """Generate realistic sample trading data for testing"""
        print("\n📊 Generating sample trading data...")
        
        # Popular stocks politicians trade
        tickers = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 
                  'JPM', 'BAC', 'JNJ', 'PFE', 'XOM', 'CVX', 'BA', 'LMT']
        
        # Generate politician profiles
        politicians = []
        first_names = ['Nancy', 'Mitch', 'Chuck', 'Kevin', 'Elizabeth', 
                      'Ron', 'Ted', 'Josh', 'Susan', 'John']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones',
                     'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        parties = ['Democrat', 'Republican']
        
        for i in range(num_politicians):
            politicians.append({
                'id': i + 1,
                'name': f"{first_names[i]} {last_names[i]}",
                'party': random.choice(parties),
                'state': random.choice(['CA', 'TX', 'NY', 'FL', 'PA', 'OH']),
                'trading_frequency': random.choice(['high', 'medium', 'low'])
            })
            
        # Generate trades
        trades = []
        start_date = datetime.now() - timedelta(days=days)
        
        for politician in politicians:
            # Number of trades based on frequency
            if politician['trading_frequency'] == 'high':
                num_trades = random.randint(50, 150)
            elif politician['trading_frequency'] == 'medium':
                num_trades = random.randint(20, 50)
            else:
                num_trades = random.randint(5, 20)
                
            for _ in range(num_trades):
                # Generate trade date
                trade_date = start_date + timedelta(
                    days=random.randint(0, days)
                )
                
                # Create trade
                trades.append({
                    'politician_id': politician['id'],
                    'politician_name': politician['name'],
                    'party': politician['party'],
                    'transaction_date': trade_date.strftime('%Y-%m-%d'),
                    'ticker': random.choice(tickers),
                    'transaction_type': random.choice(['buy', 'sell']),
                    'amount_min': random.choice([1000, 5000, 15000, 50000]),
                    'amount_max': random.choice([15000, 50000, 100000, 250000]),
                })
                
        print(f"   ✅ Generated {len(trades)} trades for {num_politicians} politicians")
        
        return {
            'politicians': politicians,
            'trades': trades
        }

class PatternAnalyzer:
    """Analyzes trading patterns without external dependencies"""
    
    def __init__(self, data):
        self.politicians = pd.DataFrame(data['politicians'])
        self.trades = pd.DataFrame(data['trades'])
        self.trades['transaction_date'] = pd.to_datetime(self.trades['transaction_date'])
        
    def analyze_cycles(self):
        """Detect cyclical trading patterns"""
        print("\n🔄 Analyzing Trading Cycles...")
        
        results = {}
        
        for politician_name in self.trades['politician_name'].unique():
            politician_trades = self.trades[
                self.trades['politician_name'] == politician_name
            ]
            
            # Calculate trading frequency by month
            monthly_trades = politician_trades.groupby(
                politician_trades['transaction_date'].dt.to_period('M')
            ).size()
            
            if len(monthly_trades) > 3:
                # Simple cycle detection - find average period between trades
                trade_dates = politician_trades['transaction_date'].sort_values()
                intervals = trade_dates.diff().dt.days.dropna()
                
                if len(intervals) > 0:
                    avg_interval = intervals.mean()
                    
                    # Classify cycle
                    if avg_interval < 7:
                        cycle_type = "Weekly"
                    elif avg_interval < 30:
                        cycle_type = "Monthly"  
                    elif avg_interval < 90:
                        cycle_type = "Quarterly"
                    else:
                        cycle_type = "Irregular"
                        
                    results[politician_name] = {
                        'avg_days_between_trades': round(avg_interval, 1),
                        'cycle_type': cycle_type,
                        'total_trades': len(politician_trades),
                        'most_traded_stock': politician_trades['ticker'].mode()[0] if len(politician_trades['ticker'].mode()) > 0 else 'N/A'
                    }
                    
        return results
        
    def detect_patterns(self):
        """Detect interesting trading patterns"""
        print("\n🔍 Detecting Trading Patterns...")
        
        patterns = {
            'surge_traders': [],
            'consistent_traders': [],
            'sector_specialists': [],
            'contrarian_traders': []
        }
        
        for politician_name in self.trades['politician_name'].unique():
            politician_trades = self.trades[
                self.trades['politician_name'] == politician_name
            ]
            
            # Surge trading - multiple trades in short period
            politician_trades = politician_trades.sort_values('transaction_date')
            for i in range(len(politician_trades) - 2):
                window = politician_trades.iloc[i:i+3]
                date_range = (window['transaction_date'].max() - window['transaction_date'].min()).days
                
                if date_range <= 7 and date_range > 0:  # 3 trades in 7 days
                    patterns['surge_traders'].append({
                        'politician': politician_name,
                        'period': window['transaction_date'].min().strftime('%Y-%m-%d'),
                        'trades': len(window)
                    })
                    break
                    
            # Sector specialist - focuses on specific sectors
            ticker_counts = politician_trades['ticker'].value_counts()
            if len(ticker_counts) > 0:
                concentration = ticker_counts.iloc[0] / len(politician_trades)
                if concentration > 0.3:  # 30%+ trades in one stock
                    patterns['sector_specialists'].append({
                        'politician': politician_name,
                        'focused_stock': ticker_counts.index[0],
                        'concentration': f"{concentration*100:.1f}%"
                    })
                    
            # Consistent trader - regular intervals
            if len(politician_trades) > 10:
                trade_dates = politician_trades['transaction_date'].sort_values()
                intervals = trade_dates.diff().dt.days.dropna()
                if len(intervals) > 0:
                    cv = intervals.std() / intervals.mean() if intervals.mean() > 0 else 1
                    if cv < 0.5:  # Low coefficient of variation
                        patterns['consistent_traders'].append({
                            'politician': politician_name,
                            'avg_interval_days': round(intervals.mean(), 1)
                        })
                        
        return patterns
        
    def correlation_analysis(self):
        """Analyze correlations between politicians"""
        print("\n🔗 Analyzing Cross-Politician Correlations...")
        
        correlations = []
        politicians = self.trades['politician_name'].unique()
        
        for i in range(len(politicians)):
            for j in range(i+1, len(politicians)):
                pol1_trades = set(
                    self.trades[self.trades['politician_name'] == politicians[i]]['ticker']
                )
                pol2_trades = set(
                    self.trades[self.trades['politician_name'] == politicians[j]]['ticker']
                )
                
                if pol1_trades and pol2_trades:
                    overlap = len(pol1_trades & pol2_trades)
                    total = len(pol1_trades | pol2_trades)
                    
                    if total > 0:
                        similarity = overlap / total
                        
                        if similarity > 0.3:  # 30%+ overlap
                            correlations.append({
                                'politician1': politicians[i],
                                'politician2': politicians[j],
                                'similarity': f"{similarity*100:.1f}%",
                                'shared_stocks': list(pol1_trades & pol2_trades)[:3]
                            })
                            
        return correlations
        
    def generate_insights(self):
        """Generate actionable insights from analysis"""
        print("\n💡 Generating Insights...")
        
        insights = []
        
        # Most active traders
        trade_counts = self.trades.groupby('politician_name').size().sort_values(ascending=False)
        most_active = trade_counts.head(3)
        
        insights.append({
            'type': 'Most Active Traders',
            'description': 'Politicians with highest trading frequency',
            'data': most_active.to_dict()
        })
        
        # Popular stocks
        stock_counts = self.trades['ticker'].value_counts().head(5)
        insights.append({
            'type': 'Most Traded Stocks',
            'description': 'Stocks most frequently traded by politicians',
            'data': stock_counts.to_dict()
        })
        
        # Party analysis
        party_trades = self.trades.groupby('party').agg({
            'transaction_type': 'count',
            'ticker': lambda x: x.nunique()
        }).rename(columns={'transaction_type': 'total_trades', 'ticker': 'unique_stocks'})
        
        insights.append({
            'type': 'Party Trading Analysis',
            'description': 'Trading patterns by political party',
            'data': party_trades.to_dict()
        })
        
        # Buy vs Sell ratio
        transaction_types = self.trades['transaction_type'].value_counts()
        buy_sell_ratio = transaction_types.get('buy', 0) / transaction_types.get('sell', 1)
        
        insights.append({
            'type': 'Market Sentiment',
            'description': 'Overall buy/sell ratio indicates market sentiment',
            'data': {
                'buy_sell_ratio': round(buy_sell_ratio, 2),
                'interpretation': 'Bullish' if buy_sell_ratio > 1.2 else 'Bearish' if buy_sell_ratio < 0.8 else 'Neutral'
            }
        })
        
        return insights

class AutonomousRunner:
    """Runs the complete analysis pipeline automatically"""
    
    def __init__(self):
        self.fetcher = DataFetcher()
        self.analyzer = None
        self.results = {}
        
    def run(self):
        """Execute full autonomous analysis"""
        print("\n🚀 Starting Autonomous Analysis Pipeline")
        print("-" * 80)
        
        # Step 1: Get data
        print("\nStep 1: Data Acquisition")
        data = self.fetcher.fetch_live_data()
        
        if not data:
            # Use sample data if live data not available
            data = self.fetcher.generate_sample_data(
                num_politicians=15,
                days=180
            )
            
        # Step 2: Initialize analyzer
        print("\nStep 2: Initializing Pattern Analyzer")
        self.analyzer = PatternAnalyzer(data)
        print("   ✅ Analyzer ready")
        
        # Step 3: Run analyses
        print("\nStep 3: Running Analyses")
        
        # Cycle analysis
        cycles = self.analyzer.analyze_cycles()
        self.results['cycles'] = cycles
        
        # Pattern detection
        patterns = self.analyzer.detect_patterns()
        self.results['patterns'] = patterns
        
        # Correlation analysis
        correlations = self.analyzer.correlation_analysis()
        self.results['correlations'] = correlations
        
        # Generate insights
        insights = self.analyzer.generate_insights()
        self.results['insights'] = insights
        
        # Step 4: Display results
        self.display_results()
        
        # Step 5: Save report
        self.save_report()
        
        return self.results
        
    def display_results(self):
        """Display analysis results in readable format"""
        print("\n" + "=" * 80)
        print("📈 ANALYSIS RESULTS")
        print("=" * 80)
        
        # Trading Cycles
        print("\n🔄 TRADING CYCLES")
        print("-" * 40)
        
        if self.results['cycles']:
            for politician, cycle_data in list(self.results['cycles'].items())[:5]:
                print(f"\n{politician}:")
                print(f"  • Cycle Type: {cycle_data['cycle_type']}")
                print(f"  • Avg Days Between Trades: {cycle_data['avg_days_between_trades']}")
                print(f"  • Total Trades: {cycle_data['total_trades']}")
                print(f"  • Most Traded Stock: {cycle_data['most_traded_stock']}")
        else:
            print("No significant cycles detected")
            
        # Trading Patterns
        print("\n\n🔍 TRADING PATTERNS")
        print("-" * 40)
        
        if self.results['patterns']['surge_traders']:
            print("\n📈 Surge Traders (Multiple trades in short period):")
            for trader in self.results['patterns']['surge_traders'][:3]:
                print(f"  • {trader['politician']}: {trader['trades']} trades around {trader['period']}")
                
        if self.results['patterns']['sector_specialists']:
            print("\n🎯 Sector Specialists (Focused on specific stocks):")
            for specialist in self.results['patterns']['sector_specialists'][:3]:
                print(f"  • {specialist['politician']}: {specialist['concentration']} in {specialist['focused_stock']}")
                
        if self.results['patterns']['consistent_traders']:
            print("\n⏰ Consistent Traders (Regular intervals):")
            for trader in self.results['patterns']['consistent_traders'][:3]:
                print(f"  • {trader['politician']}: Trades every {trader['avg_interval_days']} days on average")
                
        # Correlations
        print("\n\n🔗 POLITICIAN CORRELATIONS")
        print("-" * 40)
        
        if self.results['correlations']:
            print("\nPoliticians with similar trading patterns:")
            for corr in self.results['correlations'][:5]:
                print(f"  • {corr['politician1']} ↔ {corr['politician2']}: {corr['similarity']} similarity")
                print(f"    Shared stocks: {', '.join(corr['shared_stocks'])}")
        else:
            print("No significant correlations found")
            
        # Key Insights
        print("\n\n💡 KEY INSIGHTS")
        print("-" * 40)
        
        for insight in self.results['insights']:
            print(f"\n{insight['type']}:")
            print(f"  {insight['description']}")
            
            if isinstance(insight['data'], dict):
                for key, value in insight['data'].items():
                    if isinstance(value, dict):
                        print(f"    {key}:")
                        for k, v in value.items():
                            print(f"      • {k}: {v}")
                    else:
                        print(f"    • {key}: {value}")
                        
    def save_report(self):
        """Save analysis report to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"autonomous_analysis_{timestamp}.json"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'politicians_analyzed': len(self.analyzer.politicians),
                'total_trades': len(self.analyzer.trades),
                'date_range': {
                    'start': str(self.analyzer.trades['transaction_date'].min()),
                    'end': str(self.analyzer.trades['transaction_date'].max())
                }
            },
            'results': self.results
        }
        
        # Convert any remaining pandas objects to dict
        def convert_to_serializable(obj):
            if isinstance(obj, pd.Series):
                return obj.to_dict()
            elif isinstance(obj, pd.DataFrame):
                return obj.to_dict('records')
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj
            
        # Recursively convert the report
        import json
        
        report_str = json.dumps(report, default=convert_to_serializable, indent=2)
        report = json.loads(report_str)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n\n📊 Report saved to: {report_file}")
        
        # Also create a human-readable summary
        summary_file = f"analysis_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write("AUTONOMOUS TRADING ANALYSIS SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Politicians Analyzed: {len(self.analyzer.politicians)}\n")
            f.write(f"Total Trades: {len(self.analyzer.trades)}\n\n")
            
            f.write("KEY FINDINGS:\n")
            f.write("-" * 30 + "\n")
            
            # Write key insights
            for insight in self.results['insights']:
                f.write(f"\n{insight['type']}:\n")
                f.write(f"{insight['description']}\n")
                f.write(f"{json.dumps(insight['data'], indent=2)}\n")
                
        print(f"📝 Summary saved to: {summary_file}")

def main():
    """Main execution function"""
    print("\n🤖 Autonomous Trading Analysis System v1.0")
    print("This system will automatically:")
    print("  1. Fetch or generate trading data")
    print("  2. Analyze patterns and cycles")
    print("  3. Detect correlations")
    print("  4. Generate insights")
    print("  5. Save comprehensive reports")
    
    runner = AutonomousRunner()
    results = runner.run()
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 80)
    print("\nThe system has successfully:")
    print("  • Analyzed trading patterns")
    print("  • Detected cycles and correlations")
    print("  • Generated actionable insights")
    print("  • Saved detailed reports")
    
    print("\n🎯 Next Steps:")
    print("  1. Review the generated reports")
    print("  2. Configure live data sources for real-time analysis")
    print("  3. Set up automated scheduling for regular analysis")
    print("  4. Integrate with notification systems for alerts")
    
    return results

if __name__ == "__main__":
    results = main()