'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { 
  ChartBarIcon, 
  UserGroupIcon, 
  TrendingUpIcon,
  ExclamationTriangleIcon,
  BellIcon,
  ArrowUpIcon,
  ArrowDownIcon
} from '@heroicons/react/24/outline';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Dashboard() {
  const [selectedTimeRange, setSelectedTimeRange] = useState('7d');
  const [alerts, setAlerts] = useState([]);

  // Fetch statistics
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE}/api/v1/stats`);
      return response.data;
    }
  });

  // Fetch politicians
  const { data: politicians, isLoading: politiciansLoading } = useQuery({
    queryKey: ['politicians'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE}/api/v1/politicians?limit=10`);
      return response.data;
    }
  });

  // Fetch recent trades
  const { data: trades, isLoading: tradesLoading } = useQuery({
    queryKey: ['trades'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE}/api/v1/trades?limit=20`);
      return response.data;
    }
  });

  // Fetch patterns
  const { data: patterns, isLoading: patternsLoading } = useQuery({
    queryKey: ['patterns'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE}/api/v1/analysis/patterns`);
      return response.data;
    }
  });

  // Fetch alerts
  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const response = await axios.get(`${API_BASE}/api/v1/alerts`);
        setAlerts(response.data.alerts || []);
      } catch (error) {
        console.error('Error fetching alerts:', error);
      }
    };

    fetchAlerts();
    const interval = setInterval(fetchAlerts, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, []);

  // Chart data for top traded stocks
  const stockChartData = {
    labels: patterns?.patterns?.[0]?.data ? Object.keys(patterns.patterns[0].data).slice(0, 10) : [],
    datasets: [
      {
        label: 'Number of Trades',
        data: patterns?.patterns?.[0]?.data ? Object.values(patterns.patterns[0].data).slice(0, 10) : [],
        backgroundColor: 'rgba(59, 130, 246, 0.5)',
        borderColor: 'rgb(59, 130, 246)',
        borderWidth: 1
      }
    ]
  };

  // Performance chart data
  const performanceData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [
      {
        label: 'Politician Trades',
        data: [12, 19, 3, 5, 2, 3],
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        tension: 0.4
      },
      {
        label: 'S&P 500',
        data: [8, 12, 5, 3, 7, 5],
        borderColor: 'rgb(156, 163, 175)',
        backgroundColor: 'rgba(156, 163, 175, 0.1)',
        tension: 0.4
      }
    ]
  };

  // Sector distribution data
  const sectorData = {
    labels: ['Technology', 'Healthcare', 'Finance', 'Energy', 'Defense', 'Other'],
    datasets: [
      {
        data: [30, 20, 15, 10, 10, 15],
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(34, 197, 94, 0.8)',
          'rgba(251, 146, 60, 0.8)',
          'rgba(163, 230, 53, 0.8)',
          'rgba(168, 85, 247, 0.8)',
          'rgba(156, 163, 175, 0.8)'
        ]
      }
    ]
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">
                Politician Trading Dashboard
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <button className="relative p-2 text-gray-600 hover:text-gray-900">
                <BellIcon className="h-6 w-6" />
                {alerts.length > 0 && (
                  <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white bg-red-500 rounded-full">
                    {alerts.length}
                  </span>
                )}
              </button>
              <select 
                className="border rounded-lg px-3 py-1 text-sm"
                value={selectedTimeRange}
                onChange={(e) => setSelectedTimeRange(e.target.value)}
              >
                <option value="24h">24 Hours</option>
                <option value="7d">7 Days</option>
                <option value="30d">30 Days</option>
                <option value="90d">90 Days</option>
              </select>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Trades"
            value={stats?.total_trades || 0}
            icon={<ChartBarIcon className="h-6 w-6" />}
            change="+12.5%"
            isPositive={true}
          />
          <StatCard
            title="Politicians Tracked"
            value={stats?.unique_politicians || 0}
            icon={<UserGroupIcon className="h-6 w-6" />}
            change="+3"
            isPositive={true}
          />
          <StatCard
            title="Stocks Analyzed"
            value={stats?.unique_stocks || 0}
            icon={<TrendingUpIcon className="h-6 w-6" />}
            change="+8.2%"
            isPositive={true}
          />
          <StatCard
            title="Active Alerts"
            value={alerts.length}
            icon={<ExclamationTriangleIcon className="h-6 w-6" />}
            change={alerts.length > 0 ? `${alerts.length} new` : "None"}
            isPositive={alerts.length === 0}
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Performance Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Performance Comparison</h2>
            <Line data={performanceData} options={{
              responsive: true,
              plugins: {
                legend: {
                  position: 'top' as const,
                }
              }
            }} />
          </div>

          {/* Top Stocks Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Most Traded Stocks</h2>
            <Bar data={stockChartData} options={{
              responsive: true,
              plugins: {
                legend: {
                  display: false
                }
              }
            }} />
          </div>
        </div>

        {/* Tables Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Top Politicians */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b">
              <h2 className="text-lg font-semibold">Most Active Politicians</h2>
            </div>
            <div className="p-6">
              {politiciansLoading ? (
                <div>Loading...</div>
              ) : (
                <div className="space-y-3">
                  {politicians?.slice(0, 5).map((politician: any, index: number) => (
                    <div key={index} className="flex justify-between items-center">
                      <div>
                        <p className="font-medium">{politician.name}</p>
                        <p className="text-sm text-gray-500">
                          {politician.party}-{politician.state}
                        </p>
                      </div>
                      <span className="text-sm font-semibold">
                        {politician.trade_count} trades
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Recent Trades */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b">
              <h2 className="text-lg font-semibold">Recent Trades</h2>
            </div>
            <div className="p-6">
              {tradesLoading ? (
                <div>Loading...</div>
              ) : (
                <div className="space-y-3">
                  {trades?.slice(0, 5).map((trade: any, index: number) => (
                    <div key={index} className="flex justify-between items-center">
                      <div>
                        <p className="font-medium">{trade.ticker}</p>
                        <p className="text-sm text-gray-500">
                          {trade.politician_name?.split(' ').slice(0, 2).join(' ')}
                        </p>
                      </div>
                      <div className="text-right">
                        <span className={`text-sm font-semibold ${
                          trade.transaction_type === 'Purchase' ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {trade.transaction_type}
                        </span>
                        <p className="text-xs text-gray-500">
                          {trade.amount_range}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Sector Distribution */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b">
              <h2 className="text-lg font-semibold">Sector Distribution</h2>
            </div>
            <div className="p-6">
              <Doughnut data={sectorData} options={{
                responsive: true,
                plugins: {
                  legend: {
                    position: 'bottom' as const,
                  }
                }
              }} />
            </div>
          </div>
        </div>

        {/* Alerts Section */}
        {alerts.length > 0 && (
          <div className="bg-white rounded-lg shadow mb-8">
            <div className="px-6 py-4 border-b">
              <h2 className="text-lg font-semibold">Active Alerts</h2>
            </div>
            <div className="p-6">
              <div className="space-y-3">
                {alerts.map((alert: any) => (
                  <div key={alert.id} className={`p-4 rounded-lg border-l-4 ${
                    alert.severity === 'critical' ? 'border-red-500 bg-red-50' :
                    alert.severity === 'warning' ? 'border-yellow-500 bg-yellow-50' :
                    'border-blue-500 bg-blue-50'
                  }`}>
                    <div className="flex justify-between">
                      <div>
                        <p className="font-medium">{alert.title}</p>
                        <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                      </div>
                      <span className="text-xs text-gray-500">
                        {new Date(alert.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

// Stat Card Component
function StatCard({ title, value, icon, change, isPositive }: any) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-2xl font-bold mt-2">{value.toLocaleString()}</p>
          <div className="flex items-center mt-2">
            {isPositive ? (
              <ArrowUpIcon className="h-4 w-4 text-green-500 mr-1" />
            ) : (
              <ArrowDownIcon className="h-4 w-4 text-red-500 mr-1" />
            )}
            <span className={`text-sm ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
              {change}
            </span>
          </div>
        </div>
        <div className="text-blue-500">{icon}</div>
      </div>
    </div>
  );
}