import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useBacktest } from './hooks/useBacktest';
import { api, type MarketDataResponse } from './services/api';
import { ChartComponent } from './components/ChartComponent';
import { MetricCard } from './components/MetricCard';
import { TrendingUp, Activity, DollarSign, AlertTriangle } from 'lucide-react';

function App() {
  const [symbol, setSymbol] = useState("AARTIIND");
  // State for raw data vs backtest results
  const [marketData, setMarketData] = useState<MarketDataResponse | null>(null);
  const [instruments, setInstruments] = useState<string[]>([]);
  const [strategy, setStrategy] = useState("RSIStrategy");

  const backtestMutation = useBacktest();

  const loadMarketData = async (sym: string) => {
    try {
      // Clear backtest results so we show raw data only
      backtestMutation.reset();
      const data = await api.getMarketData(sym);
      setMarketData(data);
    } catch (err) {
      console.error("Failed to load market data", err);
    }
  };

  // Fetch Instruments on Mount
  useEffect(() => {
    api.getInstruments().then(data => {
      setInstruments(data);
      if (data.length > 0) {
        // If default symbol is not in list, pick first available
        if (!data.includes(symbol)) {
          setSymbol(data[0]);
          loadMarketData(data[0]); // Load market data for the new default
        } else {
          // Load default
          loadMarketData(symbol);
        }
      }
    }).catch(err => console.error("Failed to fetch instruments:", err));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // When symbol changes, load pure market data.
  // We do NOT auto-run backtest anymore per user request.
  const handleSymbolChange = (newSymbol: string) => {
    setSymbol(newSymbol);
    loadMarketData(newSymbol);
  };

  const handleRun = () => {
    backtestMutation.mutate({
      symbol,
      strategy,
      params: {}
    });
  };

  // Determine what to show
  // If mutation has data -> Show Backtest Results (Candles + Indicators + Signals)
  // If mutation is idle/reset -> Show Market Data (Candles Only)

  const activeData = backtestMutation.data
    ? {
      candles: backtestMutation.data.candles,
      indicators: backtestMutation.data.indicators,
      signals: backtestMutation.data.signals,
      metrics: backtestMutation.data.metrics
    }
    : marketData
      ? {
        candles: marketData.candles,
        indicators: undefined, // No indicators in raw mode
        signals: [], // No signals in raw mode
        metrics: undefined
      }
      : null;

  // Staggered Animation Variants
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  };

  return (
    <div className="min-h-screen bg-background text-white p-6 flex flex-col gap-6 overflow-hidden">

      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex justify-between items-center"
      >
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-accent">
          Hermes <span className="text-white text-lg font-normal opacity-50">Quantitative Engine</span>
        </h1>
        <div className="flex gap-4">
          <motion.select
            whileHover={{ scale: 1.02 }}
            value={strategy} onChange={e => setStrategy(e.target.value)}
            className="bg-surface border border-slate-700 rounded px-4 py-2 cursor-pointer outline-none focus:border-primary"
          >
            <option value="SMAStrategy">SMA Crossover</option>
            <option value="RSIStrategy">RSI Strategy</option>
            <option value="BollingerBandsStrategy">Bollinger Bands</option>
            <option value="MACDStrategy">MACD</option>
            <option value="MTFTrendFollowingStrategy">MTF Trend Following</option>
          </motion.select>

          {/* Instrument Selector */}
          {instruments.length > 0 ? (
            <motion.select
              whileHover={{ scale: 1.02 }}
              value={symbol} onChange={e => handleSymbolChange(e.target.value)}
              className="bg-surface border border-slate-700 rounded px-4 py-2 cursor-pointer outline-none focus:border-primary"
            >
              {instruments.map(inst => (
                <option key={inst} value={inst}>{inst}</option>
              ))}
            </motion.select>
          ) : (
            <motion.input
              whileFocus={{ scale: 1.05 }}
              type="text" value={symbol} onChange={e => handleSymbolChange(e.target.value)}
              className="bg-surface border border-slate-700 rounded px-4 py-2 w-32 text-center outline-none focus:border-primary"
              placeholder="Symbol"
            />
          )}

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleRun}
            disabled={backtestMutation.isPending}
            className="bg-primary hover:bg-blue-600 px-6 py-2 rounded font-semibold transition disabled:opacity-50 shadow-lg shadow-blue-500/20"
          >
            {backtestMutation.isPending ? "Running..." : "Run Backtest"}
          </motion.button>
        </div>
      </motion.header>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-full flex-1">

        {/* Chart Area */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="lg:col-span-3 bg-surface rounded-xl border border-slate-700 p-4 shadow-xl relative min-h-[500px]"
        >
          <AnimatePresence mode='wait'>
            {activeData ? (
              <motion.div
                key="chart"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="h-full"
              >
                <ChartComponent
                  candles={activeData.candles}
                  indicators={activeData.indicators}
                  signals={activeData.signals}
                />
              </motion.div>
            ) : (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 flex items-center justify-center text-slate-500"
              >
                Loading Market Data...
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Metrics Panel */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="lg:col-span-1 flex flex-col gap-4"
        >
          <motion.h2 variants={itemVariants} className="text-xl font-bold text-slate-400">Performance Metrics</motion.h2>

          <AnimatePresence>
            {activeData && activeData.metrics ? (
              <>
                <MetricCard
                  label="Total Return"
                  value={activeData.metrics["Total Return"]}
                  icon={<TrendingUp className="text-accent" />}
                  idx={0}
                />
                <MetricCard
                  label="Final Equity"
                  value={activeData.metrics["Final Equity"]}
                  icon={<DollarSign className="text-success" />}
                  idx={1}
                />
                <MetricCard
                  label="Sharpe Ratio"
                  value={activeData.metrics["Sharpe Ratio"]}
                  icon={<Activity className="text-primary" />}
                  idx={2}
                />
                <MetricCard
                  label="Max Drawdown"
                  value={activeData.metrics["Max Drawdown"]}
                  icon={<AlertTriangle className="text-danger" />}
                  idx={3}
                />
              </>
            ) : (
              <div className="text-slate-500 text-sm italic p-4 border border-dashed border-slate-700 rounded-lg">
                Run a backtest to see strategy performance metrics.
              </div>
            )}
          </AnimatePresence>
        </motion.div>

      </div>

      {backtestMutation.isError && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-red-900/30 border border-red-500/50 rounded text-red-200"
        >
          Error: {backtestMutation.error.message}
        </motion.div>
      )}

    </div>
  );
}

export default App;
