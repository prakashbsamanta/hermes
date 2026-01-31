import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useBacktest } from './hooks/useBacktest';
import { ChartComponent } from './components/ChartComponent';
import { MetricCard } from './components/MetricCard';
import { TrendingUp, Activity, DollarSign, AlertTriangle } from 'lucide-react';

function App() {
  const [symbol, setSymbol] = useState("AARTIIND");
  const [strategy, setStrategy] = useState("RSIStrategy");

  const backtestMutation = useBacktest();

  const handleRun = () => {
    backtestMutation.mutate({
      symbol,
      strategy,
      params: {}
    });
  };

  const data = backtestMutation.data;

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

          <motion.input
            whileFocus={{ scale: 1.05 }}
            type="text" value={symbol} onChange={e => setSymbol(e.target.value)}
            className="bg-surface border border-slate-700 rounded px-4 py-2 w-32 text-center outline-none focus:border-primary"
          />

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
            {data ? (
              <motion.div
                key="chart"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="h-full"
              >
                <ChartComponent data={data.equity_curve} signals={data.signals} />
              </motion.div>
            ) : (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 flex items-center justify-center text-slate-500"
              >
                Select a strategy and run backtest to visualize results.
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
            {data && (
              <>
                <MetricCard
                  label="Total Return"
                  value={data.metrics["Total Return"]}
                  icon={<TrendingUp className="text-accent" />}
                  idx={0}
                />
                <MetricCard
                  label="Final Equity"
                  value={data.metrics["Final Equity"]}
                  icon={<DollarSign className="text-success" />}
                  idx={1}
                />
                <MetricCard
                  label="Sharpe Ratio"
                  value={data.metrics["Sharpe Ratio"]}
                  icon={<Activity className="text-primary" />}
                  idx={2}
                />
                <MetricCard
                  label="Max Drawdown"
                  value={data.metrics["Max Drawdown"]}
                  icon={<AlertTriangle className="text-danger" />}
                  idx={3}
                />
              </>
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
