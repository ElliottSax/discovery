"""
Advanced Quantitative Pattern Detection
Sophisticated statistical and financial analysis methods
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
import logging
from scipy import stats
from itertools import combinations

logger = logging.getLogger(__name__)


class QuantitativePatternDetector:
    """Advanced quantitative pattern detection using statistical methods"""

    def __init__(self):
        self.confidence_threshold = 0.95  # 95% confidence for statistical tests
        self.min_sample_size = 10

    def detect_all_quant_patterns(self, trades: List[Dict]) -> Dict[str, Any]:
        """Run all quantitative analyses"""

        results = {
            "timestamp": datetime.now().isoformat(),
            "total_trades": len(trades),
            "statistical_patterns": [],
            "anomalies": [],
            "correlations": [],
            "timing_patterns": [],
            "volume_patterns": [],
            "risk_metrics": {}
        }

        # Statistical patterns
        results["statistical_patterns"] = self._detect_statistical_patterns(trades)

        # Anomaly detection
        results["anomalies"] = self._detect_statistical_anomalies(trades)

        # Correlation analysis
        results["correlations"] = self._analyze_correlations(trades)

        # Timing patterns
        results["timing_patterns"] = self._analyze_timing_patterns(trades)

        # Volume analysis
        results["volume_patterns"] = self._analyze_volume_patterns(trades)

        # Risk metrics
        results["risk_metrics"] = self._calculate_risk_metrics(trades)

        return results

    def _detect_statistical_patterns(self, trades: List[Dict]) -> List[Dict]:
        """Detect patterns using statistical tests"""

        patterns = []

        # Group by politician
        pol_trades = defaultdict(list)
        for trade in trades:
            pol = trade.get('politician_name')
            if pol:
                pol_trades[pol].append(trade)

        for politician, pol_trade_list in pol_trades.items():
            if len(pol_trade_list) < self.min_sample_size:
                continue

            # Test 1: Chi-square test for trade type distribution
            pattern = self._test_trade_type_bias(politician, pol_trade_list)
            if pattern:
                patterns.append(pattern)

            # Test 2: Runs test for randomness in timing
            pattern = self._test_timing_randomness(politician, pol_trade_list)
            if pattern:
                patterns.append(pattern)

            # Test 3: Kolmogorov-Smirnov test for amount distribution
            pattern = self._test_amount_distribution(politician, pol_trade_list)
            if pattern:
                patterns.append(pattern)

        return patterns

    def _test_trade_type_bias(self, politician: str, trades: List[Dict]) -> Optional[Dict]:
        """Chi-square test for buy/sell bias"""

        buy_count = sum(1 for t in trades if t.get('transaction_type', '').lower() in ['purchase', 'buy'])
        sell_count = len(trades) - buy_count

        if buy_count == 0 or sell_count == 0:
            return None

        # Expected is 50/50
        observed = [buy_count, sell_count]
        expected = [len(trades) / 2, len(trades) / 2]

        chi2, p_value = stats.chisquare(observed, expected)

        if p_value < (1 - self.confidence_threshold):
            return {
                "type": "statistical_bias",
                "politician": politician,
                "test": "chi_square",
                "metric": "trade_type",
                "chi2_statistic": float(chi2),
                "p_value": float(p_value),
                "buy_ratio": buy_count / len(trades),
                "significance": "high" if p_value < 0.01 else "medium",
                "interpretation": f"Non-random trade type distribution (p={p_value:.4f})"
            }

        return None

    def _test_timing_randomness(self, politician: str, trades: List[Dict]) -> Optional[Dict]:
        """Runs test for randomness in trade timing"""

        # Sort by date
        sorted_trades = sorted(trades, key=lambda x: x.get('transaction_date', ''))

        # Calculate intervals between trades
        intervals = []
        for i in range(1, len(sorted_trades)):
            try:
                date1 = datetime.fromisoformat(sorted_trades[i-1].get('transaction_date', ''))
                date2 = datetime.fromisoformat(sorted_trades[i].get('transaction_date', ''))
                interval = (date2 - date1).days
                intervals.append(interval)
            except:
                continue

        if len(intervals) < self.min_sample_size:
            return None

        # Runs test: count runs above/below median
        median_interval = np.median(intervals)
        runs = 1
        for i in range(1, len(intervals)):
            if (intervals[i] > median_interval) != (intervals[i-1] > median_interval):
                runs += 1

        # Expected runs under randomness
        n1 = sum(1 for x in intervals if x > median_interval)
        n2 = len(intervals) - n1

        if n1 == 0 or n2 == 0:
            return None

        expected_runs = (2 * n1 * n2) / len(intervals) + 1
        variance = (2 * n1 * n2 * (2 * n1 * n2 - len(intervals))) / (len(intervals)**2 * (len(intervals) - 1))
        std_dev = np.sqrt(variance)

        z_score = (runs - expected_runs) / std_dev if std_dev > 0 else 0

        # Two-tailed test
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))

        if p_value < (1 - self.confidence_threshold):
            return {
                "type": "timing_pattern",
                "politician": politician,
                "test": "runs_test",
                "metric": "trade_intervals",
                "z_score": float(z_score),
                "p_value": float(p_value),
                "observed_runs": runs,
                "expected_runs": float(expected_runs),
                "significance": "high" if abs(z_score) > 2.58 else "medium",
                "interpretation": "Non-random timing pattern detected" if z_score < -1 else "Clustered trading detected"
            }

        return None

    def _test_amount_distribution(self, politician: str, trades: List[Dict]) -> Optional[Dict]:
        """KS test for unusual amount distributions"""

        amounts = []
        for trade in trades:
            amt_min = trade.get('amount_min', 0)
            amt_max = trade.get('amount_max', 0)
            if amt_min and amt_max:
                avg_amt = (amt_min + amt_max) / 2
                amounts.append(avg_amt)

        if len(amounts) < self.min_sample_size:
            return None

        # Test against log-normal distribution (typical for trading amounts)
        log_amounts = np.log(amounts)
        mu = np.mean(log_amounts)
        sigma = np.std(log_amounts)

        ks_stat, p_value = stats.kstest(log_amounts, 'norm', args=(mu, sigma))

        if p_value < (1 - self.confidence_threshold):
            return {
                "type": "amount_distribution",
                "politician": politician,
                "test": "kolmogorov_smirnov",
                "metric": "trade_amounts",
                "ks_statistic": float(ks_stat),
                "p_value": float(p_value),
                "mean_amount": float(np.mean(amounts)),
                "median_amount": float(np.median(amounts)),
                "significance": "high" if p_value < 0.01 else "medium",
                "interpretation": "Unusual amount distribution pattern"
            }

        return None

    def _detect_statistical_anomalies(self, trades: List[Dict]) -> List[Dict]:
        """Detect statistical anomalies using outlier detection"""

        anomalies = []

        # Group by politician
        pol_trades = defaultdict(list)
        for trade in trades:
            pol = trade.get('politician_name')
            if pol:
                pol_trades[pol].append(trade)

        for politician, pol_trade_list in pol_trades.items():
            # Anomaly 1: Unusually large trades (>3 std devs)
            amounts = []
            for trade in pol_trade_list:
                amt_min = trade.get('amount_min', 0)
                amt_max = trade.get('amount_max', 0)
                if amt_min and amt_max:
                    amounts.append((amt_min + amt_max) / 2)

            if len(amounts) >= self.min_sample_size:
                mean_amt = np.mean(amounts)
                std_amt = np.std(amounts)

                for i, amt in enumerate(amounts):
                    z_score = (amt - mean_amt) / std_amt if std_amt > 0 else 0

                    if abs(z_score) > 3:  # >3 sigma event
                        anomalies.append({
                            "type": "outlier_amount",
                            "politician": politician,
                            "trade_index": i,
                            "amount": float(amt),
                            "z_score": float(z_score),
                            "probability": float(1 - stats.norm.cdf(abs(z_score))),
                            "significance": "very_high",
                            "interpretation": f"{abs(z_score):.1f} standard deviations from mean"
                        })

            # Anomaly 2: Unusual timing gaps
            sorted_trades = sorted(pol_trade_list, key=lambda x: x.get('transaction_date', ''))
            for i in range(1, len(sorted_trades)):
                try:
                    date1 = datetime.fromisoformat(sorted_trades[i-1].get('transaction_date', ''))
                    date2 = datetime.fromisoformat(sorted_trades[i].get('transaction_date', ''))
                    gap_days = (date2 - date1).days

                    # Flag gaps > 90 days or < 1 day
                    if gap_days > 90:
                        anomalies.append({
                            "type": "timing_gap",
                            "politician": politician,
                            "gap_days": gap_days,
                            "date_before": date1.isoformat(),
                            "date_after": date2.isoformat(),
                            "significance": "medium",
                            "interpretation": "Unusually long gap between trades"
                        })
                    elif gap_days == 0:
                        anomalies.append({
                            "type": "same_day_trades",
                            "politician": politician,
                            "date": date1.isoformat(),
                            "significance": "medium",
                            "interpretation": "Multiple trades on same day"
                        })
                except:
                    continue

        return anomalies

    def _analyze_correlations(self, trades: List[Dict]) -> List[Dict]:
        """Analyze correlations between politicians' trading patterns"""

        correlations = []

        # Build time series for each politician
        pol_series = defaultdict(list)

        for trade in trades:
            pol = trade.get('politician_name')
            date = trade.get('transaction_date')
            ticker = trade.get('ticker')

            if pol and date and ticker:
                pol_series[pol].append({
                    'date': date,
                    'ticker': ticker,
                    'type': trade.get('transaction_type', '')
                })

        # Calculate correlation for each pair
        politicians = list(pol_series.keys())

        for pol1, pol2 in combinations(politicians, 2):
            # Count overlapping trades (same ticker within 7 days)
            series1 = pol_series[pol1]
            series2 = pol_series[pol2]

            overlaps = 0
            total_comparisons = 0

            for t1 in series1:
                for t2 in series2:
                    total_comparisons += 1

                    if t1['ticker'] == t2['ticker']:
                        try:
                            date1 = datetime.fromisoformat(t1['date'])
                            date2 = datetime.fromisoformat(t2['date'])
                            if abs((date1 - date2).days) <= 7:
                                overlaps += 1
                        except:
                            continue

            if total_comparisons > 0:
                correlation_score = overlaps / total_comparisons

                if correlation_score > 0.1:  # >10% overlap
                    correlations.append({
                        "type": "trading_correlation",
                        "politician_1": pol1,
                        "politician_2": pol2,
                        "correlation_score": float(correlation_score),
                        "overlapping_trades": overlaps,
                        "total_comparisons": total_comparisons,
                        "significance": "high" if correlation_score > 0.3 else "medium",
                        "interpretation": f"{correlation_score*100:.1f}% correlation in trading"
                    })

        return sorted(correlations, key=lambda x: x['correlation_score'], reverse=True)

    def _analyze_timing_patterns(self, trades: List[Dict]) -> List[Dict]:
        """Analyze day-of-week, time-of-month patterns"""

        timing_patterns = []

        # Group by politician
        pol_trades = defaultdict(list)
        for trade in trades:
            pol = trade.get('politician_name')
            if pol:
                pol_trades[pol].append(trade)

        for politician, pol_trade_list in pol_trades.items():
            # Day of week analysis
            day_counts = defaultdict(int)
            for trade in pol_trade_list:
                try:
                    date = datetime.fromisoformat(trade.get('transaction_date', ''))
                    day_counts[date.strftime('%A')] += 1
                except:
                    continue

            if sum(day_counts.values()) >= self.min_sample_size:
                # Chi-square test for uniformity
                observed = list(day_counts.values())
                expected = [sum(observed) / len(observed)] * len(observed)

                if len(observed) >= 2:
                    chi2, p_value = stats.chisquare(observed, expected)

                    if p_value < 0.05:  # Significant pattern
                        most_common_day = max(day_counts, key=day_counts.get)

                        timing_patterns.append({
                            "type": "day_of_week_pattern",
                            "politician": politician,
                            "day_distribution": dict(day_counts),
                            "most_common_day": most_common_day,
                            "chi2_statistic": float(chi2),
                            "p_value": float(p_value),
                            "significance": "high",
                            "interpretation": f"Prefers trading on {most_common_day}"
                        })

            # Time of month analysis (beginning, middle, end)
            period_counts = {"early": 0, "mid": 0, "late": 0}
            for trade in pol_trade_list:
                try:
                    date = datetime.fromisoformat(trade.get('transaction_date', ''))
                    day = date.day
                    if day <= 10:
                        period_counts["early"] += 1
                    elif day <= 20:
                        period_counts["mid"] += 1
                    else:
                        period_counts["late"] += 1
                except:
                    continue

            if sum(period_counts.values()) >= self.min_sample_size:
                observed = list(period_counts.values())
                expected = [sum(observed) / 3] * 3

                chi2, p_value = stats.chisquare(observed, expected)

                if p_value < 0.05:
                    most_common_period = max(period_counts, key=period_counts.get)

                    timing_patterns.append({
                        "type": "month_period_pattern",
                        "politician": politician,
                        "period_distribution": period_counts,
                        "most_common_period": most_common_period,
                        "chi2_statistic": float(chi2),
                        "p_value": float(p_value),
                        "significance": "medium",
                        "interpretation": f"Prefers {most_common_period} month trading"
                    })

        return timing_patterns

    def _analyze_volume_patterns(self, trades: List[Dict]) -> List[Dict]:
        """Analyze trading volume patterns"""

        volume_patterns = []

        # Group by ticker
        ticker_trades = defaultdict(list)
        for trade in trades:
            ticker = trade.get('ticker')
            if ticker:
                ticker_trades[ticker].append(trade)

        for ticker, ticker_trade_list in ticker_trades.items():
            if len(ticker_trade_list) < 5:
                continue

            # Count unique politicians trading this ticker
            politicians = set(t.get('politician_name') for t in ticker_trade_list)

            # Calculate total volume
            total_volume = len(ticker_trade_list)

            # Calculate concentration (what % is one politician)
            pol_counts = defaultdict(int)
            for trade in ticker_trade_list:
                pol_counts[trade.get('politician_name')] += 1

            max_concentration = max(pol_counts.values()) / total_volume if total_volume > 0 else 0

            if max_concentration > 0.6:  # One politician dominates >60%
                dominant_pol = max(pol_counts, key=pol_counts.get)

                volume_patterns.append({
                    "type": "concentrated_trading",
                    "ticker": ticker,
                    "dominant_politician": dominant_pol,
                    "concentration_ratio": float(max_concentration),
                    "total_trades": total_volume,
                    "unique_politicians": len(politicians),
                    "significance": "high",
                    "interpretation": f"{dominant_pol} dominates {ticker} trading ({max_concentration*100:.0f}%)"
                })

        return volume_patterns

    def _calculate_risk_metrics(self, trades: List[Dict]) -> Dict[str, Any]:
        """Calculate portfolio risk metrics"""

        metrics = {}

        # Group by politician
        pol_trades = defaultdict(list)
        for trade in trades:
            pol = trade.get('politician_name')
            if pol:
                pol_trades[pol].append(trade)

        for politician, pol_trade_list in pol_trades.items():
            # Diversification: unique tickers / total trades
            tickers = set(t.get('ticker') for t in pol_trade_list if t.get('ticker'))
            diversification = len(tickers) / len(pol_trade_list) if pol_trade_list else 0

            # Concentration: largest position
            ticker_counts = defaultdict(int)
            for trade in pol_trade_list:
                ticker = trade.get('ticker')
                if ticker:
                    ticker_counts[ticker] += 1

            max_position = max(ticker_counts.values()) if ticker_counts else 0
            concentration = max_position / len(pol_trade_list) if pol_trade_list else 0

            # Trade frequency (trades per month)
            if len(pol_trade_list) >= 2:
                try:
                    dates = sorted([datetime.fromisoformat(t.get('transaction_date', ''))
                                   for t in pol_trade_list if t.get('transaction_date')])
                    if len(dates) >= 2:
                        days_range = (dates[-1] - dates[0]).days
                        frequency = len(pol_trade_list) / (days_range / 30) if days_range > 0 else 0
                    else:
                        frequency = 0
                except:
                    frequency = 0
            else:
                frequency = 0

            metrics[politician] = {
                "diversification_score": float(diversification),
                "concentration_ratio": float(concentration),
                "trade_frequency_per_month": float(frequency),
                "total_positions": len(tickers),
                "total_trades": len(pol_trade_list),
                "risk_profile": "aggressive" if concentration > 0.3 else "moderate" if concentration > 0.15 else "diversified"
            }

        return metrics


__all__ = ['QuantitativePatternDetector']
