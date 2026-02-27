import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useBacktest } from "@/hooks/useBacktest";
import { api, type ScanResponse } from "@/services/api";
import { ChartComponent } from "@/components/ChartComponent";
import { ScannerView } from "@/components/backtest/ScannerView";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { StrategyConfigPanel } from "@/components/backtest/StrategyConfigPanel";
import { Card } from "@/components/ui/card";
import { TrendingUp, Activity, DollarSign, AlertTriangle } from "lucide-react";
import { toast } from "sonner";

export function BacktestPage() {
  const [selectedAssets, setSelectedAssets] = useState<string[]>([]);
  const [strategy, setStrategy] = useState("RSIStrategy");
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [strategyParams, setStrategyParams] = useState<Record<string, any>>({});
  const [instruments, setInstruments] = useState<string[]>([]);
  const [mode, setMode] = useState<"vector" | "event">("vector");
  const [timeframe, setTimeframe] = useState<string>("1h");

  // Filter State
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");
  const [slippage, setSlippage] = useState<number>(0.0);
  const [commission, setCommission] = useState<number>(0.0);

  // Scanner State
  const [scanData, setScanData] = useState<ScanResponse | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const backtestMutation = useBacktest();

  // Derived State
  const viewMode = selectedAssets.length === 1 ? "single" : "batch";
  const singleSymbol = selectedAssets.length === 1 ? selectedAssets[0] : "";

  useEffect(() => {
    api
      .getInstruments()
      .then((data) => {
        setInstruments(data);
        // Default: No changes on selection, starts empty (Batch Mode)
      })
      .catch((err) => {
        console.error(err);
        toast.error("Failed to load instruments. Check backend connection.");
      });
  }, []);

  // Clear backtest/scan data when switching modes
  useEffect(() => {
    if (viewMode === "single") {
      setScanData(null);
    } else {
      backtestMutation.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [viewMode]);

  // Handle Backtest Errors with Toast
  useEffect(() => {
    if (backtestMutation.isError) {
      toast.error(`Backtest failed: ${backtestMutation.error.message}`);
    }
  }, [backtestMutation.isError, backtestMutation.error]);

  // Handle Backtest Success with Toast
  useEffect(() => {
    if (backtestMutation.isSuccess) {
      toast.success(`Backtest completed for ${singleSymbol}`);
    }
  }, [backtestMutation.isSuccess, singleSymbol]);

  const handleRunBacktest = () => {
    if (!singleSymbol) return;

    // Toast is handled by effects or mutation callbacks,
    // but we can add a 'Starting...' toast if desired, but mutation is fast usually.
    // Let's keep it simple.

    backtestMutation.mutate({
      symbol: singleSymbol,
      strategy: strategy,
      params: strategyParams,
      mode: mode,
      timeframe: timeframe,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
      slippage: slippage,
      commission: commission,
    });
  };

  const handleScan = async (isBackground = false) => {
    if (!isBackground) setIsScanning(true);
    else setIsRefreshing(true);

    // If selection is empty, scan ALL. If selection exists, scan only those.
    const symbolsToScan =
      selectedAssets.length > 0 ? selectedAssets : undefined;

    try {
      if (!isBackground)
        toast.info(
          symbolsToScan
            ? `Scanning ${symbolsToScan.length} assets...`
            : "Scanning all market assets...",
        );

      const result = await api.runScan({
        strategy: strategy,
        params: strategyParams,
        mode: mode,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        symbols: symbolsToScan,
        max_concurrency: 5,
        initial_cash: 100000,
      });
      setScanData(result);
      if (!isBackground)
        toast.success(`Scan completed: ${result.results.length} results.`);
    } catch (err) {
      console.error("Scan failed:", err);
      const msg = err instanceof Error ? err.message : "Scan failed.";
      toast.error(msg);
    } finally {
      setIsScanning(false);
      setIsRefreshing(false);
    }
  };

  const handleNavigateToSymbol = (sym: string) => {
    setSelectedAssets([sym]); // Switches to single mode
  };

  const handleRun = () => {
    if (viewMode === "single") handleRunBacktest();
    else handleScan();
  };

  const activeData = backtestMutation.data;

  // Animation Variants
  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } },
  };

  return (
    <DashboardLayout
      header={
        <DashboardHeader
          instruments={instruments}
          selectedStrategy={strategy}
          onStrategyChange={setStrategy}
          selectedAssets={selectedAssets}
          onAssetsChange={setSelectedAssets}
          onRunBacktest={handleRun}
          isRunning={
            viewMode === "single" ? backtestMutation.isPending : isScanning
          }
          strategies={[
            "SMAStrategy",
            "RSIStrategy",
            "BollingerBandsStrategy",
            "MACDStrategy",
            "MTFTrendFollowingStrategy",
          ]}
          mode={mode}
          onModeChange={setMode}
          timeframe={timeframe}
          setTimeframe={setTimeframe}
          start_date={startDate}
          setStartDate={setStartDate}
          end_date={endDate}
          setEndDate={setEndDate}
          slippage={slippage}
          setSlippage={setSlippage}
          commission={commission}
          setCommission={setCommission}
        />
      }
      sidebar={
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="flex flex-col gap-4 h-full"
        >
          {/* Strategy Configuration Panel */}
          <div className="flex-1 min-h-0 bg-background rounded-lg border border-border shadow-sm overflow-hidden flex flex-col">
            <StrategyConfigPanel
              strategyName={strategy}
              currentParams={strategyParams}
              onParamsChange={setStrategyParams}
            />
          </div>

          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-2 mt-2 px-1">
            Backtest Results
          </h2>

          <AnimatePresence mode="popLayout">
            {viewMode === "single" && activeData && activeData.metrics ? (
              <>
                <MetricCard
                  label="Total Return"
                  value={activeData.metrics["Total Return"]}
                  icon={
                    <TrendingUp
                      className="text-secondary-foreground"
                      size={18}
                    />
                  }
                  idx={0}
                />
                <MetricCard
                  label="Final Equity"
                  value={activeData.metrics["Final Equity"]}
                  icon={<DollarSign className="text-green-500" size={18} />}
                  idx={1}
                />
                <MetricCard
                  label="Sharpe Ratio"
                  value={activeData.metrics["Sharpe Ratio"]}
                  icon={<Activity className="text-primary" size={18} />}
                  idx={2}
                />
                <MetricCard
                  label="Max Drawdown"
                  value={activeData.metrics["Max Drawdown"]}
                  icon={
                    <AlertTriangle className="text-destructive" size={18} />
                  }
                  idx={3}
                />
              </>
            ) : viewMode === "single" ? (
              <Card className="p-6 border-dashed border-2 flex flex-col items-center justify-center text-center gap-2 bg-transparent">
                <Activity
                  className="text-muted-foreground opacity-20"
                  size={40}
                />
                <p className="text-sm text-muted-foreground">
                  Run a strategy to see metrics.
                </p>
              </Card>
            ) : null}
          </AnimatePresence>

          {/* Scanner Info Sidebar (if batch mode) */}
          {viewMode === "batch" && scanData && (
            <div className="mt-4 p-4 bg-secondary/10 border border-border rounded-md">
              <h3 className="text-sm font-semibold mb-2">Scan Summary</h3>
              <div className="text-xs space-y-1 text-muted-foreground">
                <div>Completed: {scanData.completed}</div>
                <div>Failed: {scanData.failed}</div>
                <div>Cached: {scanData.cached_count}</div>
                <div>Fresh: {scanData.fresh_count}</div>
              </div>
            </div>
          )}
        </motion.div>
      }
    >
      <Card className="h-full w-full border border-border shadow-sm overflow-hidden flex flex-col p-1 bg-surface">
        <AnimatePresence mode="wait">
          {viewMode === "batch" ? (
            <motion.div
              key="scanner-view"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 w-full h-full"
            >
              <ScannerView
                onNavigateToSymbol={handleNavigateToSymbol}
                data={scanData}
                isLoading={isScanning}
                isRefreshing={isRefreshing}
                error={null} // Error handled by toast
                onScan={handleScan}
              />
            </motion.div>
          ) : activeData ? (
            <motion.div
              key="backtest-results"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 w-full h-full"
            >
              <ChartComponent
                candles={activeData.candles}
                indicators={activeData.indicators}
                signals={activeData.signals}
                symbol={singleSymbol}
              />
            </motion.div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground gap-4">
              <Activity size={48} className="opacity-20" />
              <p>Configure and run a strategy to visualize results.</p>
            </div>
          )}
        </AnimatePresence>
      </Card>
    </DashboardLayout>
  );
}
