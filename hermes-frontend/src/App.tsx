import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from './services/api';
import type { BacktestRequest, BacktestResponse } from './services/api';
import { ChartComponent } from './components/ChartComponent';
import { TrendingUp, Activity, DollarSign, AlertTriangle } from 'lucide-react';
// clsx removed as unused

function App() {
  const [symbol, setSymbol] = useState("AARTIIND");
  const [strategy, setStrategy] = useState("RSIStrategy");

  const backtestMutation = useMutation({
    mutationFn: (req: BacktestRequest) => api.runBacktest(req)
  });

  const handleRun = () => {
    backtestMutation.mutate({
      symbol,
      strategy,
      params: {} // Defaults for now, could add inputs later
    });
  };

  const data = backtestMutation.data;

  return (
    <div className="min-h-screen bg-background text-white p-6 flex flex-col gap-6">

      {/* Header */}
      <header className="flex justify-between items-center">
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-accent">
          Hermes <span className="text-white text-lg font-normal opacity-50">Quantitative Engine</span>
        </h1>
        <div className="flex gap-4">
          <select
            value={strategy} onChange={e => setStrategy(e.target.value)}
            className="bg-surface border border-slate-700 rounded px-4 py-2"
          >
            <option value="SMAStrategy">SMA Crossover</option>
            <option value="RSIStrategy">RSI Strategy</option>
            <option value="BollingerBandsStrategy">Bollinger Bands</option>
            <option value="MACDStrategy">MACD</option>
            <option value="MTFTrendFollowingStrategy">MTF Trend Following</option>
          </select>

          <input
            type="text" value={symbol} onChange={e => setSymbol(e.target.value)}
            className="bg-surface border border-slate-700 rounded px-4 py-2 w-32 text-center"
          />

          <button
            onClick={handleRun}
            disabled={backtestMutation.isPending}
            className="bg-primary hover:bg-blue-600 px-6 py-2 rounded font-semibold transition disabled:opacity-50"
          >
            {backtestMutation.isPending ? "Running..." : "Run Backtest"}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-full flex-1">

        {/* Chart Area */}
        <div className="lg:col-span-3 bg-surface rounded-xl border border-slate-700 p-4 shadow-xl relative min-h-[500px]">
          {data ? (
            <ChartComponent data={data.equity_curve} signals={data.signals} />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center text-slate-500">
              Select a strategy and run backtest to visualize results.
            </div>
          )}
        </div>

        {/* Metrics Panel */}
        <div className="lg:col-span-1 flex flex-col gap-4">
          <h2 className="text-xl font-bold text-slate-400">Performance Metrics</h2>

          {data && (
            <>
              <MetricCard
                label="Total Return"
                value={data.metrics["Total Return"]}
                icon={<TrendingUp className="text-accent" />}
              />
              <MetricCard
                label="Final Equity"
                value={data.metrics["Final Equity"]}
                icon={<DollarSign className="text-success" />}
              />
              <MetricCard
                label="Sharpe Ratio"
                value={data.metrics["Sharpe Ratio"]}
                icon={<Activity className="text-primary" />}
              />
              <MetricCard
                label="Max Drawdown"
                value={data.metrics["Max Drawdown"]}
                icon={<AlertTriangle className="text-danger" />}
              />
            </>
          )}
        </div>

      </div>

      {backtestMutation.isError && (
        <div className="p-4 bg-red-900/30 border border-red-500/50 rounded text-red-200">
          Error: {backtestMutation.error.message}
        </div>
      )}

    </div>
  );
}

const MetricCard = ({ label, value, icon }: { label: string, value: string, icon: React.ReactNode }) => (
  <div className="bg-surface p-4 rounded-xl border border-slate-700 flex items-center justify-between hover:border-slate-500 transition cursor-default">
    <div>
      <p className="text-sm text-slate-400">{label}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
    </div>
    <div className="p-3 bg-slate-900 rounded-full">
      {icon}
    </div>
  </div>
)

export default App;
