import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useBacktest } from './hooks/useBacktest';
import { api, type MarketDataResponse } from './services/api';
import { ChartComponent } from './components/ChartComponent';
import { MetricCard } from './components/MetricCard';
import { TrendingUp, Activity, DollarSign, AlertTriangle } from 'lucide-react';

function App() {
  // --- View State (Chart) ---
  const [viewSymbol, setViewSymbol] = useState("AARTIIND");
  const [viewTimeframe, setViewTimeframe] = useState("1h");
  const [marketData, setMarketData] = useState<MarketDataResponse | null>(null);

  // --- Backtest State (Header Config) ---
  const [backtestSymbol, setBacktestSymbol] = useState("AARTIIND");
  const [backtestStrategy, setBacktestStrategy] = useState("RSIStrategy");

  // --- Shared Data ---
  const [instruments, setInstruments] = useState<string[]>([]);

  const backtestMutation = useBacktest();

  // Load Market Data (for View Mode)
  const loadMarketData = async (sym: string, tf: string) => {
    try {
      // If we are loading market data explicitly, we probably want to see it,
      // so we should clear the backtest result to "return to home".
      backtestMutation.reset();
      const data = await api.getMarketData(sym, tf);
      setMarketData(data);
    } catch (err) {
      console.error("Failed to load market data", err);
    }
  };

  // Initial Load
  useEffect(() => {
    api.getInstruments().then(data => {
      setInstruments(data);
      if (data.length > 0) {
        if (!data.includes(viewSymbol)) {
          // Default to first available
          const defaultSym = data[0];
          setViewSymbol(defaultSym);
          setBacktestSymbol(defaultSym); // Sync backtest default initially
          loadMarketData(defaultSym, viewTimeframe);
        } else {
          loadMarketData(viewSymbol, viewTimeframe);
        }
      }
    }).catch(err => console.error("Failed to fetch instruments:", err));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Handlers for Chart Interaction (Immediate Update)
  const handleViewSymbolChange = (newSym: string) => {
    setViewSymbol(newSym);
    loadMarketData(newSym, viewTimeframe);
  };

  const handleViewTimeframeChange = (newTf: string) => {
    setViewTimeframe(newTf);
    loadMarketData(viewSymbol, newTf);
  };

  // Handler for Backtest Execution
  const handleRunBacktest = () => {
    backtestMutation.mutate({
      symbol: backtestSymbol,
      strategy: backtestStrategy,
      params: {}
    });
  };

  // Determine Active Data Source
  // Priority: Backtest Result > Raw Market Data
  const isBacktestMode = !!backtestMutation.data;

  const activeData = isBacktestMode
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
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  };

  return (
    <div className="min-h-screen bg-background text-white p-6 flex flex-col gap-6 overflow-hidden">

      {/* Header: Backtest Configuration Only */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex justify-between items-center bg-surface p-4 rounded-xl border border-slate-700 shadow-lg"
      >
        <div className="flex flex-col">
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-accent">
            Hermes <span className="text-white text-base font-normal opacity-50">Backtest Config</span>
          </h1>
          <span className="text-xs text-slate-500">Configure strategy parameters below</span>
        </div>

        <div className="flex gap-4 items-center">
          <div className="flex flex-col">
            <label className="text-xs text-slate-500 mb-1 ml-1">Strategy</label>
            <motion.select
              whileHover={{ scale: 1.02 }}
              value={backtestStrategy} onChange={e => setBacktestStrategy(e.target.value)}
              className="bg-background border border-slate-600 rounded px-4 py-2 cursor-pointer outline-none focus:border-primary min-w-[180px]"
            >
              <option value="SMAStrategy">SMA Crossover</option>
              <option value="RSIStrategy">RSI Strategy</option>
              <option value="BollingerBandsStrategy">Bollinger Bands</option>
              <option value="MACDStrategy">MACD</option>
              <option value="MTFTrendFollowingStrategy">MTF Trend Following</option>
            </motion.select>
          </div>

          <div className="flex flex-col">
            <label className="text-xs text-slate-500 mb-1 ml-1">Backtest Symbol</label>
            {instruments.length > 0 ? (
              <motion.select
                whileHover={{ scale: 1.02 }}
                value={backtestSymbol} onChange={e => setBacktestSymbol(e.target.value)}
                className="bg-background border border-slate-600 rounded px-4 py-2 cursor-pointer outline-none focus:border-primary min-w-[140px]"
              >
                {instruments.map(inst => (
                  <option key={inst} value={inst}>{inst}</option>
                ))}
              </motion.select>
            ) : (
              <motion.input
                whileFocus={{ scale: 1.05 }}
                type="text" value={backtestSymbol} onChange={e => setBacktestSymbol(e.target.value)}
                className="bg-background border border-slate-600 rounded px-4 py-2 w-32 text-center outline-none focus:border-primary"
                placeholder="Symbol"
              />
            )}
          </div>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleRunBacktest}
            disabled={backtestMutation.isPending}
            className="mt-5 bg-primary hover:bg-blue-600 px-8 py-2 rounded font-semibold transition disabled:opacity-50 shadow-lg shadow-blue-500/20"
          >
            {backtestMutation.isPending ? "Running..." : "Run Backtest"}
          </motion.button>
        </div>
      </motion.header>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-full flex-1 min-h-0">

        {/* Chart Area */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="lg:col-span-3 bg-surface rounded-xl border border-slate-700 shadow-xl relative overflow-hidden flex flex-col"
        >
          <AnimatePresence mode='wait'>
            {activeData ? (
              <motion.div
                key={isBacktestMode ? "backtest-chart" : "market-chart"} // Animate transition between modes
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex-1 w-full h-full"
              >
                <ChartComponent
                  candles={activeData.candles}
                  indicators={activeData.indicators}
                  signals={activeData.signals}

                  // Interactive Props (Active only in Market Mode, or allowing override?)
                  // UX Decision: Even in backtest mode, showing the controls allows user to "break out" back to view mode easily
                  // just by changing the symbol on the chart.
                  symbol={isBacktestMode ? backtestSymbol : viewSymbol} // Show actual displayed symbol
                  onSymbolChange={handleViewSymbolChange} // Switching symbol resets to View Mode

                  timeframe={viewTimeframe}
                  onTimeframeChange={handleViewTimeframeChange}

                  instruments={instruments}
                  className="flex-1 w-full h-full"
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
          className="lg:col-span-1 flex flex-col gap-4 overflow-y-auto pr-2"
        >
          <motion.h2 variants={itemVariants} className="text-xl font-bold text-slate-400">
            {isBacktestMode ? "Strategy Results" : "Live Market Metrics"}
          </motion.h2>

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
                Select a strategy and run backtest to see performance metrics.
                <br /><br />
                Current View: <strong>{viewSymbol}</strong> ({viewTimeframe})
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
