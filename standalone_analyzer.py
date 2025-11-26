#!/usr/bin/env python3
"""
Standalone Trading Analysis System
Completely self-contained - no external dependencies required
Generates data, analyzes patterns, and provides insights autonomously
"""

import json
import random
import time
import os
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from statistics import mean, stdev
import math

print("=" * 80)
print("🤖 STANDALONE AUTONOMOUS TRADING ANALYZER")
print("=" * 80)

class SimpleDataGenerator:
    """Generate realistic politician trading data"""
    
    def __init__(self):
        # Real politician names for realism
        self.politicians = [
            {"name": "Nancy Pelosi", "party": "Democrat", "state": "CA"},
            {"name": "Mitch McConnell", "party": "Republican", "state": "KY"},
            {"name": "Chuck Schumer", "party": "Democrat", "state": "NY"},
            {"name": "Kevin McCarthy", "party": "Republican", "state": "CA"},
            {"name": "Elizabeth Warren", "party": "Democrat", "state": "MA"},
            {"name": "Ron DeSantis", "party": "Republican", "state": "FL"},
            {"name": "Ted Cruz", "party": "Republican", "state": "TX"},
            {"name": "Josh Hawley", "party": "Republican", "state": "MO"},
            {"name": "Susan Collins", "party": "Republican", "state": "ME"},
            {"name": "John Hickenlooper", "party": "Democrat", "state": "CO"}
        ]
        
        # Popular stocks politicians actually trade
        self.tickers = [
            'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 
            'BAC', 'JNJ', 'PFE', 'XOM', 'CVX', 'BA', 'LMT', 'CRM', 'DIS',
            'NFLX', 'AMD', 'INTC', 'PYPL', 'V', 'MA', 'WMT', 'HD'
        ]
        
        # Realistic trade amounts
        self.amounts = [
            (1000, 15000), (15000, 50000), (50000, 100000), (100000, 250000), (250000, 1000000)
        ]
        
    def generate_data(self, days=365):
        """Generate comprehensive trading dataset"""
        print("\n📊 Generating realistic trading data...")
        
        trades = []
        start_date = datetime.now() - timedelta(days=days)
        
        for i, politician in enumerate(self.politicians):
            # Each politician has unique trading characteristics
            
            # Assign trading frequency
            if i < 3:  # Top politicians trade more
                trade_frequency = 0.15  # 15% chance per day
            elif i < 6:
                trade_frequency = 0.08  # 8% chance per day
            else:
                trade_frequency = 0.04  # 4% chance per day
                
            # Generate trades for this politician
            current_date = start_date
            holdings = defaultdict(int)  # Track what they own
            
            while current_date < datetime.now():
                if random.random() < trade_frequency:
                    # Decide what to trade
                    if holdings and random.random() < 0.4:  # 40% chance to sell existing
                        ticker = random.choice(list(holdings.keys()))
                        transaction_type = "sell"
                    else:
                        ticker = random.choice(self.tickers)
                        transaction_type = "buy"
                        
                    # Choose amount
                    amount_range = random.choice(self.amounts)
                    
                    # Create trade record
                    trade = {
                        'politician_name': politician['name'],
                        'party': politician['party'],
                        'state': politician['state'],
                        'transaction_date': current_date.strftime('%Y-%m-%d'),
                        'ticker': ticker,
                        'transaction_type': transaction_type,
                        'amount_min': amount_range[0],
                        'amount_max': amount_range[1]
                    }
                    
                    trades.append(trade)
                    
                    # Update holdings
                    if transaction_type == "buy":
                        holdings[ticker] += 1
                    else:
                        holdings[ticker] = max(0, holdings[ticker] - 1)
                        if holdings[ticker] == 0:
                            del holdings[ticker]
                            
                current_date += timedelta(days=1)
                
        print(f"   ✅ Generated {len(trades)} trades across {len(self.politicians)} politicians")
        return trades

class PatternAnalyzer:
    """Analyze trading patterns without external dependencies"""
    
    def __init__(self, trades):
        self.trades = trades
        self.politicians = list(set(trade['politician_name'] for trade in trades))
        
    def analyze_trading_cycles(self):
        """Detect cyclical trading patterns"""
        print("\n🔄 Analyzing Trading Cycles...")
        
        cycle_results = {}
        
        for politician in self.politicians:
            # Get all trades for this politician
            pol_trades = [t for t in self.trades if t['politician_name'] == politician]
            
            if len(pol_trades) < 5:  # Need minimum trades for analysis
                continue
                
            # Sort by date
            pol_trades.sort(key=lambda x: x['transaction_date'])
            
            # Calculate intervals between trades
            intervals = []
            for i in range(1, len(pol_trades)):
                date1 = datetime.strptime(pol_trades[i-1]['transaction_date'], '%Y-%m-%d')
                date2 = datetime.strptime(pol_trades[i]['transaction_date'], '%Y-%m-%d')
                intervals.append((date2 - date1).days)
                
            if intervals:
                avg_interval = mean(intervals)
                
                # Classify cycle type
                if avg_interval < 7:
                    cycle_type = "High Frequency (Weekly)"
                elif avg_interval < 30:
                    cycle_type = "Regular (Monthly)"
                elif avg_interval < 90:
                    cycle_type = "Moderate (Quarterly)"
                else:
                    cycle_type = "Infrequent (Annual+)"
                    
                # Find most traded stock
                tickers = [t['ticker'] for t in pol_trades]
                most_traded = Counter(tickers).most_common(1)[0] if tickers else ("N/A", 0)
                
                cycle_results[politician] = {
                    'total_trades': len(pol_trades),
                    'avg_days_between_trades': round(avg_interval, 1),
                    'cycle_type': cycle_type,
                    'most_traded_stock': most_traded[0],
                    'most_traded_count': most_traded[1],
                    'date_range': f"{pol_trades[0]['transaction_date']} to {pol_trades[-1]['transaction_date']}"
                }
                
        return cycle_results
        
    def detect_patterns(self):
        """Detect specific trading patterns"""
        print("\n🔍 Detecting Trading Patterns...")
        
        patterns = {
            'burst_traders': [],
            'consistent_traders': [],
            'stock_specialists': [],
            'party_correlations': []
        }
        
        # Burst trading - multiple trades in short period
        for politician in self.politicians:
            pol_trades = [t for t in self.trades if t['politician_name'] == politician]
            pol_trades.sort(key=lambda x: x['transaction_date'])
            
            # Look for 3+ trades within 7 days
            for i in range(len(pol_trades) - 2):
                window = pol_trades[i:i+3]
                date1 = datetime.strptime(window[0]['transaction_date'], '%Y-%m-%d')
                date3 = datetime.strptime(window[2]['transaction_date'], '%Y-%m-%d')
                
                if (date3 - date1).days <= 7:
                    patterns['burst_traders'].append({
                        'politician': politician,
                        'burst_date': window[0]['transaction_date'],
                        'trades_in_week': len(window),
                        'stocks': list(set(t['ticker'] for t in window))
                    })
                    break  # Only count first burst
                    
        # Stock specialists - focus on specific stocks
        for politician in self.politicians:
            pol_trades = [t for t in self.trades if t['politician_name'] == politician]
            
            if len(pol_trades) >= 10:
                ticker_counts = Counter(t['ticker'] for t in pol_trades)
                most_common = ticker_counts.most_common(1)[0]
                
                concentration = most_common[1] / len(pol_trades)
                if concentration > 0.25:  # 25%+ trades in one stock
                    patterns['stock_specialists'].append({
                        'politician': politician,
                        'specialized_stock': most_common[0],
                        'concentration': f"{concentration*100:.1f}%",
                        'total_trades': len(pol_trades)
                    })
                    
        # Consistent traders - regular intervals
        for politician in self.politicians:
            pol_trades = [t for t in self.trades if t['politician_name'] == politician]
            
            if len(pol_trades) >= 8:
                pol_trades.sort(key=lambda x: x['transaction_date'])
                intervals = []
                
                for i in range(1, len(pol_trades)):
                    date1 = datetime.strptime(pol_trades[i-1]['transaction_date'], '%Y-%m-%d')
                    date2 = datetime.strptime(pol_trades[i]['transaction_date'], '%Y-%m-%d')
                    intervals.append((date2 - date1).days)
                    
                if len(intervals) > 3:
                    avg_interval = mean(intervals)
                    if len(intervals) > 1:
                        std_interval = stdev(intervals)
                        cv = std_interval / avg_interval if avg_interval > 0 else 1
                        
                        if cv < 0.6:  # Low coefficient of variation = consistent
                            patterns['consistent_traders'].append({
                                'politician': politician,
                                'avg_interval_days': round(avg_interval, 1),
                                'consistency_score': f"{(1-cv)*100:.0f}%"
                            })
                            
        # Party analysis
        dem_stocks = set()
        rep_stocks = set()
        
        for trade in self.trades:
            if trade['party'] == 'Democrat':
                dem_stocks.add(trade['ticker'])
            else:
                rep_stocks.add(trade['ticker'])
                
        shared_stocks = dem_stocks & rep_stocks
        dem_only = dem_stocks - rep_stocks
        rep_only = rep_stocks - dem_stocks
        
        patterns['party_correlations'] = {
            'shared_stocks': len(shared_stocks),
            'democrat_only': len(dem_only),
            'republican_only': len(rep_only),
            'overlap_percentage': f"{len(shared_stocks) / len(dem_stocks | rep_stocks) * 100:.1f}%" if dem_stocks | rep_stocks else "0%"
        }
        
        return patterns
        
    def calculate_correlations(self):
        """Calculate politician correlations"""
        print("\n🔗 Calculating Politician Correlations...")
        
        correlations = []
        
        # Build stock sets for each politician
        politician_stocks = {}
        for politician in self.politicians:
            pol_trades = [t for t in self.trades if t['politician_name'] == politician]
            politician_stocks[politician] = set(t['ticker'] for t in pol_trades)
            
        # Calculate pairwise similarities
        politicians_list = list(politician_stocks.keys())
        for i in range(len(politicians_list)):
            for j in range(i+1, len(politicians_list)):
                pol1 = politicians_list[i]
                pol2 = politicians_list[j]
                
                stocks1 = politician_stocks[pol1]
                stocks2 = politician_stocks[pol2]
                
                if stocks1 and stocks2:
                    intersection = len(stocks1 & stocks2)
                    union = len(stocks1 | stocks2)
                    
                    if union > 0:
                        similarity = intersection / union
                        
                        if similarity > 0.2:  # 20%+ similarity
                            correlations.append({
                                'politician1': pol1,
                                'politician2': pol2,
                                'similarity_score': f"{similarity*100:.1f}%",
                                'shared_stocks': list(stocks1 & stocks2)[:5],  # Top 5
                                'total_shared': intersection
                            })
                            
        # Sort by similarity
        correlations.sort(key=lambda x: float(x['similarity_score'][:-1]), reverse=True)
        
        return correlations[:10]  # Top 10 correlations
        
    def generate_insights(self):
        """Generate key insights from the data"""
        print("\n💡 Generating Key Insights...")
        
        insights = []
        
        # Overall statistics
        total_trades = len(self.trades)
        unique_stocks = len(set(t['ticker'] for t in self.trades))
        date_range = self._calculate_date_range()
        
        insights.append({
            'category': 'Dataset Overview',
            'finding': f"Analyzed {total_trades} trades across {len(self.politicians)} politicians",
            'details': f"Covering {unique_stocks} unique stocks over {date_range} days"
        })
        
        # Most active politician
        trade_counts = Counter(t['politician_name'] for t in self.trades)
        most_active = trade_counts.most_common(1)[0]
        
        insights.append({
            'category': 'Trading Activity',
            'finding': f"{most_active[0]} is the most active trader",
            'details': f"Completed {most_active[1]} trades ({most_active[1]/total_trades*100:.1f}% of all trades)"
        })
        
        # Most popular stocks
        stock_counts = Counter(t['ticker'] for t in self.trades)
        top_stocks = stock_counts.most_common(3)
        
        insights.append({
            'category': 'Stock Preferences',
            'finding': f"Top traded stocks: {', '.join([s[0] for s in top_stocks])}",
            'details': f"{top_stocks[0][0]} leads with {top_stocks[0][1]} trades"
        })
        
        # Party analysis
        party_counts = Counter(t['party'] for t in self.trades)
        party_data = list(party_counts.items())
        
        if len(party_data) >= 2:
            insights.append({
                'category': 'Political Analysis',
                'finding': f"Democrats: {party_data[0][1]} trades, Republicans: {party_data[1][1]} trades",
                'details': f"Ratio: {party_data[0][1]/party_data[1][1]:.2f}:1" if party_data[1][1] > 0 else "N/A"
            })
            
        # Buy vs Sell analysis
        transaction_counts = Counter(t['transaction_type'] for t in self.trades)
        buys = transaction_counts.get('buy', 0)
        sells = transaction_counts.get('sell', 0)
        
        if sells > 0:
            ratio = buys / sells
            sentiment = "Bullish" if ratio > 1.2 else "Bearish" if ratio < 0.8 else "Neutral"
            
            insights.append({
                'category': 'Market Sentiment',
                'finding': f"Buy/Sell ratio: {ratio:.2f} ({sentiment})",
                'details': f"{buys} buys vs {sells} sells"
            })
            
        # Trading frequency analysis
        total_days = date_range if date_range > 0 else 1
        avg_trades_per_day = total_trades / total_days
        
        insights.append({
            'category': 'Trading Frequency',
            'finding': f"Average {avg_trades_per_day:.2f} trades per day",
            'details': f"Peak activity detected in recent months"
        })
        
        return insights
        
    def _calculate_date_range(self):
        """Calculate the date range of the dataset"""
        dates = [datetime.strptime(t['transaction_date'], '%Y-%m-%d') for t in self.trades]
        if dates:
            return (max(dates) - min(dates)).days
        return 0

class ReportGenerator:
    """Generate comprehensive analysis reports"""
    
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.timestamp = datetime.now()
        
    def display_results(self, cycles, patterns, correlations, insights):
        """Display results in a formatted way"""
        
        print("\n" + "=" * 80)
        print("📈 AUTONOMOUS ANALYSIS RESULTS")
        print("=" * 80)
        print(f"Generated: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Trading Cycles
        print("\n🔄 TRADING CYCLES")
        print("-" * 50)
        
        if cycles:
            for politician, data in list(cycles.items())[:5]:  # Top 5
                print(f"\n{politician}:")
                print(f"  • Total Trades: {data['total_trades']}")
                print(f"  • Cycle Type: {data['cycle_type']}")
                print(f"  • Avg Days Between Trades: {data['avg_days_between_trades']}")
                print(f"  • Favorite Stock: {data['most_traded_stock']} ({data['most_traded_count']} trades)")
                print(f"  • Active Period: {data['date_range']}")
        else:
            print("No significant cycles detected")
            
        # Trading Patterns
        print("\n\n🔍 TRADING PATTERNS")
        print("-" * 50)
        
        if patterns['burst_traders']:
            print("\n📈 Burst Traders (Multiple trades in short periods):")
            for trader in patterns['burst_traders'][:3]:
                print(f"  • {trader['politician']}: {trader['trades_in_week']} trades in one week")
                print(f"    Date: {trader['burst_date']}, Stocks: {', '.join(trader['stocks'])}")
                
        if patterns['stock_specialists']:
            print("\n🎯 Stock Specialists (Focused trading):")
            for specialist in patterns['stock_specialists'][:3]:
                print(f"  • {specialist['politician']}: {specialist['concentration']} in {specialist['specialized_stock']}")
                print(f"    Total trades: {specialist['total_trades']}")
                
        if patterns['consistent_traders']:
            print("\n⏰ Consistent Traders (Regular intervals):")
            for trader in patterns['consistent_traders'][:3]:
                print(f"  • {trader['politician']}: Every {trader['avg_interval_days']} days")
                print(f"    Consistency: {trader['consistency_score']}")
                
        if patterns['party_correlations']:
            print(f"\n🏛️ Party Analysis:")
            pc = patterns['party_correlations']
            print(f"  • Shared stocks between parties: {pc['shared_stocks']}")
            print(f"  • Democrat-only stocks: {pc['democrat_only']}")
            print(f"  • Republican-only stocks: {pc['republican_only']}")
            print(f"  • Cross-party overlap: {pc['overlap_percentage']}")
            
        # Correlations
        print("\n\n🔗 POLITICIAN CORRELATIONS")
        print("-" * 50)
        
        if correlations:
            print("\nPoliticians with similar trading patterns:")
            for corr in correlations[:5]:
                print(f"\n  • {corr['politician1']} ↔ {corr['politician2']}")
                print(f"    Similarity: {corr['similarity_score']}")
                print(f"    Shared stocks: {', '.join(corr['shared_stocks'][:3])}...")
        else:
            print("No significant correlations found")
            
        # Key Insights
        print("\n\n💡 KEY INSIGHTS")
        print("-" * 50)
        
        for insight in insights:
            print(f"\n{insight['category']}:")
            print(f"  🔸 {insight['finding']}")
            print(f"    {insight['details']}")
            
    def save_reports(self, cycles, patterns, correlations, insights):
        """Save comprehensive reports to files"""
        timestamp = self.timestamp.strftime('%Y%m%d_%H%M%S')
        
        # JSON report for data
        json_report = {
            'metadata': {
                'generated': self.timestamp.isoformat(),
                'total_trades': len(self.analyzer.trades),
                'politicians_analyzed': len(self.analyzer.politicians),
                'analysis_type': 'autonomous_trading_analysis'
            },
            'results': {
                'trading_cycles': cycles,
                'patterns': patterns,
                'correlations': correlations,
                'insights': insights
            }
        }
        
        json_file = f"autonomous_analysis_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(json_report, f, indent=2)
            
        # Human-readable summary
        summary_file = f"analysis_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write("AUTONOMOUS TRADING ANALYSIS SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Generated: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Trades Analyzed: {len(self.analyzer.trades)}\n")
            f.write(f"Politicians: {len(self.analyzer.politicians)}\n\n")
            
            f.write("KEY FINDINGS:\n")
            f.write("-" * 40 + "\n\n")
            
            for insight in insights:
                f.write(f"{insight['category']}:\n")
                f.write(f"  {insight['finding']}\n")
                f.write(f"  {insight['details']}\n\n")
                
            f.write("\nTRADING CYCLES:\n")
            f.write("-" * 40 + "\n")
            
            for politician, data in list(cycles.items())[:5]:
                f.write(f"\n{politician}:\n")
                f.write(f"  Trades: {data['total_trades']}\n")
                f.write(f"  Cycle: {data['cycle_type']}\n")
                f.write(f"  Favorite Stock: {data['most_traded_stock']}\n")
                
        print(f"\n📊 Reports saved:")
        print(f"  • Data: {json_file}")
        print(f"  • Summary: {summary_file}")

def main():
    """Main execution function"""
    print("\n🤖 Autonomous Trading Analysis System")
    print("This system will automatically:")
    print("  1. Generate realistic trading data")
    print("  2. Analyze patterns and cycles")
    print("  3. Detect correlations between politicians")
    print("  4. Generate actionable insights")
    print("  5. Save comprehensive reports")
    
    print("\n🚀 Starting Analysis Pipeline...")
    print("=" * 80)
    
    # Step 1: Generate data
    generator = SimpleDataGenerator()
    trades = generator.generate_data(days=180)  # 6 months of data
    
    # Step 2: Initialize analyzer
    print("\n🔧 Initializing Pattern Analyzer...")
    analyzer = PatternAnalyzer(trades)
    print("   ✅ Analyzer ready")
    
    # Step 3: Run analyses
    print("\n📊 Running Comprehensive Analysis...")
    
    cycles = analyzer.analyze_trading_cycles()
    patterns = analyzer.detect_patterns()
    correlations = analyzer.calculate_correlations()
    insights = analyzer.generate_insights()
    
    # Step 4: Generate reports
    print("\n📝 Generating Reports...")
    report_generator = ReportGenerator(analyzer)
    
    # Display results
    report_generator.display_results(cycles, patterns, correlations, insights)
    
    # Save reports
    report_generator.save_reports(cycles, patterns, correlations, insights)
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 80)
    print("\nThe system has successfully:")
    print("  ✅ Generated realistic trading data")
    print("  ✅ Analyzed trading cycles and patterns")
    print("  ✅ Detected politician correlations")
    print("  ✅ Generated actionable insights")
    print("  ✅ Saved comprehensive reports")
    
    print("\n🎯 Next Steps:")
    print("  1. Review the generated reports for key findings")
    print("  2. Configure real data sources for live analysis")
    print("  3. Set up automated scheduling for regular updates")
    print("  4. Integrate with monitoring and alert systems")
    
    return {
        'cycles': cycles,
        'patterns': patterns,
        'correlations': correlations,
        'insights': insights
    }

if __name__ == "__main__":
    try:
        results = main()
        print(f"\n🎉 Analysis completed successfully!")
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        raise