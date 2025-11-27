'use client';

import { useState, useEffect } from 'react';
import { Line, Bar, Scatter } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { motion } from 'framer-motion';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface AnalyticsData {
  politicians: Array<{
    name: string;
    cycle: number;
    strength: number;
    trades: number;
    regime: string;
    changes: number;
    type: string;
  }>;
  topStocks: Array<{
    ticker: string;
    trades: number;
    change: number;
  }>;
  totalTrades: number;
  analysisDate: string;
}

// Fallback data for offline mode
const FALLBACK_DATA: AnalyticsData = {
  politicians: [
    { name: 'Nancy Pelosi', cycle: 8, strength: 0.088, trades: 118, regime: 'High Activity', changes: 13, type: 'Weekly' },
    { name: 'Chuck Schumer', cycle: 60, strength: 0.083, trades: 128, regime: 'High Activity', changes: 3, type: 'Quarterly' },
    { name: 'Elizabeth Warren', cycle: 90, strength: 0.068, trades: 113, regime: 'High Activity', changes: 6, type: 'Quarterly' },
    { name: 'Mitch McConnell', cycle: 45, strength: 0.058, trades: 104, regime: 'High Activity', changes: 4, type: 'Monthly' },
    { name: 'Ted Cruz', cycle: 119, strength: 0.068, trades: 101, regime: 'High Activity', changes: 5, type: 'Extended' }
  ],
  topStocks: [
    { ticker: 'META', trades: 47, change: 8.3 },
    { ticker: 'AMZN', trades: 50, change: 8.9 },
    { ticker: 'NVDA', trades: 14, change: 2.5 },
    { ticker: 'AAPL', trades: 14, change: 2.5 },
    { ticker: 'MSFT', trades: 14, change: 2.5 },
    { ticker: 'UNH', trades: 30, change: 5.3 },
    { ticker: 'TSLA', trades: 14, change: -3.2 },
    { ticker: 'JPM', trades: 13, change: 2.3 }
  ],
  totalTrades: 564,
  analysisDate: '2025-11-26'
};

export default function Home() {
  const [selectedPolitician, setSelectedPolitician] = useState(0);
  const [isAnimated, setIsAnimated] = useState(false);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData>(FALLBACK_DATA);
  const [loading, setLoading] = useState(true);
  const [isLive, setIsLive] = useState(false);

  useEffect(() => {
    setIsAnimated(true);

    // Fetch analytics data from API
    const fetchAnalytics = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/dashboard/analytics');
        if (!response.ok) throw new Error('API unavailable');

        const data = await response.json();
        setAnalyticsData(data);
        setIsLive(true);
        setLoading(false);
      } catch (err) {
        console.warn('API unavailable, using fallback data:', err);
        setAnalyticsData(FALLBACK_DATA);
        setIsLive(false);
        setLoading(false);
      }
    };

    fetchAnalytics();

    // Refresh every 60 seconds
    const interval = setInterval(fetchAnalytics, 60000);
    return () => clearInterval(interval);
  }, []);

  // Main hero graph - Trading Pattern Visualization
  const generatePatternData = () => {
    const politician = analyticsData.politicians[selectedPolitician];
    const days = 365;
    const labels = Array.from({ length: days }, (_, i) => `Day ${i + 1}`);

    // Simulate trading pattern based on detected cycle
    const pattern = Array.from({ length: days }, (_, i) => {
      const cyclicComponent = Math.sin((2 * Math.PI * i) / politician.cycle) * politician.strength * 10;
      const noise = (Math.random() - 0.5) * 0.5;
      const trend = i / days * 2;
      return Math.max(0, cyclicComponent + noise + trend);
    });

    // HMM regime overlay
    const regimes = Array.from({ length: days }, (_, i) => {
      const segment = Math.floor(i / 30);
      return segment % politician.changes > politician.changes / 2 ? 8 : 2;
    });

    return {
      labels: labels.filter((_, i) => i % 7 === 0), // Weekly labels
      datasets: [
        {
          label: `${politician.name} - Trading Activity`,
          data: pattern.filter((_, i) => i % 7 === 0),
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderWidth: 3,
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 6
        },
        {
          label: 'HMM Regime Level',
          data: regimes.filter((_, i) => i % 7 === 0),
          borderColor: 'rgba(251, 146, 60, 0.6)',
          backgroundColor: 'rgba(251, 146, 60, 0.05)',
          borderWidth: 2,
          fill: true,
          tension: 0.3,
          pointRadius: 0,
          borderDash: [5, 5]
        }
      ]
    };
  };

  // Cycle strength comparison
  const cycleComparisonData = {
    labels: analyticsData.politicians.map(p => p.name.split(' ').pop()),
    datasets: [
      {
        label: 'Cycle Length (days)',
        data: analyticsData.politicians.map(p => p.cycle),
        backgroundColor: 'rgba(34, 197, 94, 0.7)',
        borderColor: 'rgb(34, 197, 94)',
        borderWidth: 2
      },
      {
        label: 'Signal Strength (×100)',
        data: analyticsData.politicians.map(p => p.strength * 100),
        backgroundColor: 'rgba(168, 85, 247, 0.7)',
        borderColor: 'rgb(168, 85, 247)',
        borderWidth: 2
      }
    ]
  };

  // Regime volatility scatter
  const regimeScatterData = {
    datasets: [
      {
        label: 'Trading Profile',
        data: analyticsData.politicians.map(p => ({
          x: p.cycle,
          y: p.changes,
          r: p.trades / 10
        })),
        backgroundColor: analyticsData.politicians.map((_, i) =>
          `rgba(${59 + i * 40}, ${130 + i * 20}, ${246 - i * 30}, 0.7)`
        ),
        borderColor: analyticsData.politicians.map((_, i) =>
          `rgb(${59 + i * 40}, ${130 + i * 20}, ${246 - i * 30})`
        ),
        borderWidth: 2
      }
    ]
  };

  // Stock performance
  const stockData = {
    labels: analyticsData.topStocks.map(s => s.ticker),
    datasets: [
      {
        label: 'Number of Trades',
        data: analyticsData.topStocks.map(s => s.trades),
        backgroundColor: analyticsData.topStocks.map(s =>
          s.change > 0 ? 'rgba(34, 197, 94, 0.7)' : 'rgba(239, 68, 68, 0.7)'
        ),
        borderColor: analyticsData.topStocks.map(s =>
          s.change > 0 ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)'
        ),
        borderWidth: 2
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: '#e5e7eb',
          font: {
            size: 12,
            weight: '500'
          }
        }
      },
      tooltip: {
        backgroundColor: 'rgba(17, 24, 39, 0.95)',
        titleColor: '#f3f4f6',
        bodyColor: '#e5e7eb',
        borderColor: '#374151',
        borderWidth: 1,
        padding: 12,
        displayColors: true
      }
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(75, 85, 99, 0.2)',
          drawBorder: false
        },
        ticks: {
          color: '#9ca3af',
          font: {
            size: 10
          },
          maxTicksLimit: 12
        }
      },
      y: {
        grid: {
          color: 'rgba(75, 85, 99, 0.2)',
          drawBorder: false
        },
        ticks: {
          color: '#9ca3af',
          font: {
            size: 10
          }
        }
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 text-white">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        {/* Animated background */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -inset-[10px] opacity-50">
            <div className="absolute top-0 -left-4 w-72 h-72 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
            <div className="absolute top-0 -right-4 w-72 h-72 bg-yellow-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
            <div className="absolute -bottom-8 left-20 w-72 h-72 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
          </div>
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 pb-12">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-8"
          >
            <h1 className="text-5xl md:text-7xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 mb-4">
              Politician Trading Intelligence
            </h1>
            <p className="text-xl md:text-2xl text-gray-300 mb-2">
              Advanced Pattern Recognition & Regime Detection
            </p>
            <div className="flex items-center justify-center gap-6 text-sm text-gray-400">
              <span className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-green-400 animate-pulse' : 'bg-yellow-400'}`}></div>
                {isLive ? 'Live Analysis' : 'Offline Mode'}
              </span>
              <span>{analyticsData.totalTrades} Trades Analyzed</span>
              <span>{analyticsData.politicians.length} Politicians Tracked</span>
              <span>FFT + HMM + DTW Algorithms</span>
            </div>
          </motion.div>

          {/* Main Graph - Hero Section */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: isAnimated ? 1 : 0, scale: isAnimated ? 1 : 0.95 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 shadow-2xl border border-gray-700/50 mb-8"
          >
            {/* Politician Selector */}
            <div className="flex flex-wrap gap-2 mb-6">
              {analyticsData.politicians.map((pol, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedPolitician(idx)}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${
                    selectedPolitician === idx
                      ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/50'
                      : 'bg-gray-700/50 text-gray-300 hover:bg-gray-600/50'
                  }`}
                >
                  {pol.name.split(' ').pop()}
                </button>
              ))}
            </div>

            {/* Selected Politician Stats */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
              {[
                { label: 'Cycle Period', value: `${analyticsData.politicians[selectedPolitician].cycle} days`, sublabel: analyticsData.politicians[selectedPolitician].type },
                { label: 'Signal Strength', value: `${(analyticsData.politicians[selectedPolitician].strength * 100).toFixed(1)}%`, sublabel: 'FFT Power' },
                { label: 'Total Trades', value: analyticsData.politicians[selectedPolitician].trades, sublabel: '2-year period' },
                { label: 'Current Regime', value: 'High', sublabel: analyticsData.politicians[selectedPolitician].regime.split(' ')[1] },
                { label: 'Regime Changes', value: analyticsData.politicians[selectedPolitician].changes, sublabel: 'Last 30 days' }
              ].map((stat, idx) => (
                <div key={idx} className="bg-gray-700/30 rounded-lg p-4 border border-gray-600/30">
                  <div className="text-xs text-gray-400 mb-1">{stat.label}</div>
                  <div className="text-2xl font-bold text-white mb-1">{stat.value}</div>
                  <div className="text-xs text-gray-500">{stat.sublabel}</div>
                </div>
              ))}
            </div>

            {/* Main Chart */}
            <div className="h-96">
              <Line data={generatePatternData()} options={{
                ...chartOptions,
                plugins: {
                  ...chartOptions.plugins,
                  title: {
                    display: true,
                    text: `${analyticsData.politicians[selectedPolitician].name} - Trading Pattern Analysis (365 Days)`,
                    color: '#f3f4f6',
                    font: {
                      size: 16,
                      weight: 'bold'
                    }
                  }
                }
              }} />
            </div>

            <div className="mt-4 text-sm text-gray-400 text-center">
              Blue: Trading activity pattern | Orange (dashed): HMM regime levels
            </div>
          </motion.div>

          {/* Analysis Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            {/* Cycle Comparison */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="lg:col-span-2 bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 shadow-xl border border-gray-700/50"
            >
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <span className="w-1 h-6 bg-gradient-to-b from-green-400 to-purple-400 rounded"></span>
                Cyclical Pattern Comparison
              </h3>
              <div className="h-64">
                <Bar data={cycleComparisonData} options={chartOptions} />
              </div>
            </motion.div>

            {/* Live Stats */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.5 }}
              className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 shadow-xl border border-gray-700/50"
            >
              <h3 className="text-xl font-bold mb-4">Key Insights</h3>
              <div className="space-y-4">
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                  <div className="text-xs text-blue-300 mb-1">Shortest Cycle</div>
                  <div className="text-2xl font-bold">8 days</div>
                  <div className="text-xs text-gray-400">Nancy Pelosi (Weekly)</div>
                </div>
                <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4">
                  <div className="text-xs text-purple-300 mb-1">Longest Cycle</div>
                  <div className="text-2xl font-bold">119 days</div>
                  <div className="text-xs text-gray-400">Ted Cruz (Extended)</div>
                </div>
                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                  <div className="text-xs text-green-300 mb-1">Most Volatile</div>
                  <div className="text-2xl font-bold">13 changes</div>
                  <div className="text-xs text-gray-400">Nancy Pelosi (30 days)</div>
                </div>
                <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4">
                  <div className="text-xs text-orange-300 mb-1">Most Stable</div>
                  <div className="text-2xl font-bold">3 changes</div>
                  <div className="text-xs text-gray-400">Chuck Schumer (30 days)</div>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Bottom Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Stocks */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
              className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 shadow-xl border border-gray-700/50"
            >
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <span className="w-1 h-6 bg-gradient-to-b from-green-400 to-red-400 rounded"></span>
                Most Traded Stocks
              </h3>
              <div className="h-64">
                <Bar data={stockData} options={chartOptions} />
              </div>
              <div className="mt-4 text-sm text-gray-400">
                Green: Positive performance | Red: Negative performance
              </div>
            </motion.div>

            {/* Regime Volatility Scatter */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.7 }}
              className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 shadow-xl border border-gray-700/50"
            >
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <span className="w-1 h-6 bg-gradient-to-b from-blue-400 to-pink-400 rounded"></span>
                Trading Profile Matrix
              </h3>
              <div className="h-64">
                <Scatter
                  data={regimeScatterData}
                  options={{
                    ...chartOptions,
                    scales: {
                      x: {
                        ...chartOptions.scales.x,
                        title: {
                          display: true,
                          text: 'Cycle Length (days)',
                          color: '#9ca3af'
                        }
                      },
                      y: {
                        ...chartOptions.scales.y,
                        title: {
                          display: true,
                          text: 'Regime Changes (30d)',
                          color: '#9ca3af'
                        }
                      }
                    }
                  }}
                />
              </div>
              <div className="mt-4 text-sm text-gray-400">
                Bubble size = Total trades | X = Cycle length | Y = Volatility
              </div>
            </motion.div>
          </div>

          {/* Footer Info */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.8 }}
            className="mt-8 text-center text-sm text-gray-500"
          >
            <p>Analysis powered by FFT Cyclical Detection, Hidden Markov Models, and Dynamic Time Warping</p>
            <p className="mt-1">Data: 564 trades | Period: Jan 2023 - Dec 2024 | Last updated: {analyticsData.analysisDate}</p>
          </motion.div>
        </div>
      </div>

      {/* Custom Animations CSS */}
      <style jsx>{`
        @keyframes blob {
          0% { transform: translate(0px, 0px) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
          100% { transform: translate(0px, 0px) scale(1); }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  );
}
