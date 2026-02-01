import { motion } from "framer-motion";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface DashboardHeaderProps {
    strategies: string[];
    selectedStrategy: string;
    onStrategyChange: (val: string) => void;

    instruments: string[];
    selectedSymbol: string;
    onSymbolChange: (val: string) => void;

    onRunBacktest: () => void;
    isRunning: boolean;
}

export function DashboardHeader({
    strategies = ["SMAStrategy", "RSIStrategy", "BollingerBandsStrategy", "MACDStrategy", "MTFTrendFollowingStrategy"],
    selectedStrategy,
    onStrategyChange,
    instruments,
    selectedSymbol,
    onSymbolChange,
    onRunBacktest,
    isRunning
}: DashboardHeaderProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
        >
            <Card className="p-4 flex flex-col md:flex-row justify-between items-center gap-4 bg-surface border-border shadow-sm">

                {/* Title Section */}
                <div className="flex flex-col gap-1">
                    <h1 className="text-xl font-bold tracking-tight text-foreground">
                        Backtest Configuration
                    </h1>
                    <p className="text-xs text-muted-foreground font-mono">
                        {isRunning ? "ENGINE: RUNNING..." : "ENGINE: READY"}
                    </p>
                </div>

                {/* Controls Section */}
                <div className="flex flex-wrap items-end gap-4">

                    {/* Strategy Selector */}
                    <div className="flex flex-col gap-1.5">
                        <Label className="text-xs text-muted-foreground font-mono uppercase">Strategy</Label>
                        <Select value={selectedStrategy} onValueChange={onStrategyChange}>
                            <SelectTrigger className="w-[180px] bg-background">
                                <SelectValue placeholder="Select Strategy" />
                            </SelectTrigger>
                            <SelectContent>
                                {strategies.map((strat) => (
                                    <SelectItem key={strat} value={strat}>{strat.replace("Strategy", "")}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Symbol Selector */}
                    <div className="flex flex-col gap-1.5">
                        <Label className="text-xs text-muted-foreground font-mono uppercase">Asset</Label>
                        {instruments.length > 0 ? (
                            <Select value={selectedSymbol} onValueChange={onSymbolChange}>
                                <SelectTrigger className="w-[140px] bg-background">
                                    <SelectValue placeholder="Symbol" />
                                </SelectTrigger>
                                <SelectContent>
                                    {instruments.map((inst) => (
                                        <SelectItem key={inst} value={inst}>{inst}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        ) : (
                            <Input
                                value={selectedSymbol}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => onSymbolChange(e.target.value)}
                                className="w-[140px] bg-background"
                                placeholder="Symbol"
                            />
                        )}
                    </div>

                    {/* Action Button */}
                    <div className="flex items-center gap-2">
                        <Button
                            onClick={onRunBacktest}
                            disabled={isRunning}
                            className="w-[140px] font-semibold tracking-wide shadow-lg shadow-primary/20"
                        >
                            {isRunning ? "EXECUTING" : "RUN BACKTEST"}
                        </Button>
                    </div>

                </div>
            </Card>
        </motion.div>
    );
}

