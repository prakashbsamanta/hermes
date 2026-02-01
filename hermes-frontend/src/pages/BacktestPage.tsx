import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useBacktest } from "@/hooks/useBacktest";
import { api } from "@/services/api";
import { ChartComponent } from "@/components/ChartComponent";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { StrategyConfigPanel } from "@/components/backtest/StrategyConfigPanel";
import { Card } from "@/components/ui/card";
import { TrendingUp, Activity, DollarSign, AlertTriangle } from "lucide-react";

export function BacktestPage() {
    const [symbol, setSymbol] = useState("AARTIIND");
    const [strategy, setStrategy] = useState("RSIStrategy");
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const [strategyParams, setStrategyParams] = useState<Record<string, any>>({});
    const [instruments, setInstruments] = useState<string[]>([]);

    const backtestMutation = useBacktest();

    useEffect(() => {
        api.getInstruments().then(data => {
            setInstruments(data);
            if (data.length > 0 && !data.includes(symbol)) {
                setSymbol(data[0]);
            }
        }).catch(console.error);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleRunBacktest = () => {
        backtestMutation.mutate({
            symbol: symbol,
            strategy: strategy,
            params: strategyParams
        });
    };

    const activeData = backtestMutation.data;

    // Animation Variants
    const containerVariants = {
        hidden: { opacity: 0 },
        show: { opacity: 1, transition: { staggerChildren: 0.1 } }
    };

    const itemVariants = {
        hidden: { opacity: 0, x: 20 },
        show: { opacity: 1, x: 0 }
    };

    return (
        <DashboardLayout
            header={
                <DashboardHeader
                    instruments={instruments}
                    selectedStrategy={strategy}
                    onStrategyChange={setStrategy}
                    selectedSymbol={symbol}
                    onSymbolChange={setSymbol}
                    onRunBacktest={handleRunBacktest}
                    isRunning={backtestMutation.isPending}
                    strategies={["SMAStrategy", "RSIStrategy", "BollingerBandsStrategy", "MACDStrategy", "MTFTrendFollowingStrategy"]}
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
                    <div className="flex-1 min-h-0 bg-background rounded-lg border border-border shadow-sm overflow-hidden">
                        <StrategyConfigPanel
                            strategyName={strategy}
                            currentParams={strategyParams}
                            onParamsChange={setStrategyParams}
                        />
                    </div>

                    <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-2 mt-2">
                        Backtest Results
                    </h2>

                    <AnimatePresence mode="popLayout">
                        {activeData && activeData.metrics ? (
                            <>
                                <MetricCard
                                    label="Total Return"
                                    value={activeData.metrics["Total Return"]}
                                    icon={<TrendingUp className="text-secondary-foreground" size={18} />}
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
                                    icon={<AlertTriangle className="text-destructive" size={18} />}
                                    idx={3}
                                />
                            </>
                        ) : (
                            <Card className="p-6 border-dashed border-2 flex flex-col items-center justify-center text-center gap-2 bg-transparent">
                                <Activity className="text-muted-foreground opacity-20" size={40} />
                                <p className="text-sm text-muted-foreground">
                                    Run a strategy to see metrics.
                                </p>
                            </Card>
                        )}
                    </AnimatePresence>

                    {backtestMutation.isError && (
                        <motion.div
                            variants={itemVariants}
                            className="p-4 bg-destructive/10 border border-destructive/20 rounded-md text-destructive text-sm"
                        >
                            Error: {backtestMutation.error.message}
                        </motion.div>
                    )}
                </motion.div>
            }
        >
            <Card className="h-full w-full border border-border shadow-sm overflow-hidden flex flex-col p-1 bg-surface">
                <AnimatePresence mode="wait">
                    {activeData ? (
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
                                symbol={symbol}
                            // View-only in backtest mode regarding symbol changes usually, 
                            // but we might want to let them inspect. 
                            // For now, let's PASS the controls but strictly they just change local view state if we wanted
                            // Actually, in BacktestPage, changing symbol via ChartControl might be confusing if it doesn't re-run backtest.
                            // Let's hide the ChartControls on BacktestPage for now and rely on the Header for control/re-run.
                            // OR pass null for onSymbolChange to hide the toolbar.
                            // Let's keep it simple: No toolbar inside the chart for Backtest Results to avoid confusion.
                            // The Header *is* the control for the backtest.
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
