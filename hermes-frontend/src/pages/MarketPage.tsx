import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api, type MarketDataResponse } from "@/services/api";
import { ChartComponent } from "@/components/ChartComponent";
import { Card } from "@/components/ui/card";
import { DashboardLayout } from "@/components/layout/DashboardLayout";

export function MarketPage() {
    const [symbol, setSymbol] = useState("AARTIIND");
    const [timeframe, setTimeframe] = useState("1h");
    const [marketData, setMarketData] = useState<MarketDataResponse | null>(null);
    const [instruments, setInstruments] = useState<string[]>([]);
    // const [isLoading, setIsLoading] = useState(true);

    const loadMarketData = async (sym: string, tf: string) => {
        try {
            // setIsLoading(true);
            const data = await api.getMarketData(sym, tf);
            setMarketData(data);
        } catch (err) {
            console.error("Failed to load market data", err);
        } finally {
            // setIsLoading(false);
        }
    };

    useEffect(() => {
        api.getInstruments().then(data => {
            setInstruments(data);
            if (data.length > 0 && !data.includes(symbol)) {
                setSymbol(data[0]);
            }
        }).catch(console.error);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        if (symbol) {
            loadMarketData(symbol, timeframe);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [symbol, timeframe]);

    return (
        <DashboardLayout
            header={
                <div className="flex items-center justify-between p-4 bg-card/50 backdrop-blur border-b border-border rounded-lg mb-4">
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">Market Overview</h1>
                        <p className="text-sm text-muted-foreground">Real-time market analysis and charting.</p>
                    </div>
                    <div className="flex gap-4">
                        {/* Placeholder for future top-level market stats */}
                        <div className="text-right">
                            <p className="text-xs text-muted-foreground font-mono">STATUS</p>
                            <p className="text-sm font-bold text-green-500">LIVE</p>
                        </div>
                    </div>
                </div>
            }
            sidebar={
                <div className="flex flex-col gap-4">
                    <Card className="p-4 bg-card/50">
                        <h3 className="text-sm font-semibold mb-2">Watchlist</h3>
                        <div className="text-sm text-muted-foreground italic">Coming Soon...</div>
                    </Card>
                    <Card className="p-4 bg-card/50">
                        <h3 className="text-sm font-semibold mb-2">Order Book</h3>
                        <div className="text-sm text-muted-foreground italic">Coming Soon...</div>
                    </Card>
                </div>
            }
        >
            <Card className="h-full w-full border border-border shadow-sm overflow-hidden flex flex-col p-1 bg-surface">
                <AnimatePresence mode="wait">
                    {marketData ? (
                        <motion.div
                            key={symbol + timeframe}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="flex-1 w-full h-full"
                        >
                            <ChartComponent
                                candles={marketData.candles}
                                signals={[]}
                                symbol={symbol}
                                onSymbolChange={setSymbol}
                                timeframe={timeframe}
                                onTimeframeChange={setTimeframe}
                                instruments={instruments}
                                className="flex-1 w-full h-full rounded-lg overflow-hidden"
                            />
                        </motion.div>
                    ) : (
                        <div className="flex-1 flex items-center justify-center text-muted-foreground animate-pulse">
                            Loading Market Data...
                        </div>
                    )}
                </AnimatePresence>
            </Card>
        </DashboardLayout>
    );
}
