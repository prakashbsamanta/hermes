import { motion } from "framer-motion";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { AdvancedSettingsDialog } from "./AdvancedSettingsDialog";
import { AssetSelector } from "./AssetSelector";
import { DateInput } from "@/components/ui/date-input";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Check, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { useState } from "react";

interface DashboardHeaderProps {
  strategies: string[];
  selectedStrategy: string;
  onStrategyChange: (val: string) => void;

  instruments: string[];
  selectedAssets: string[];
  onAssetsChange: (val: string[]) => void;

  onRunBacktest: () => void;
  isRunning: boolean;

  mode: "vector" | "event";
  onModeChange: (val: "vector" | "event") => void;

  start_date: string | undefined;
  setStartDate: (val: string) => void;
  end_date: string | undefined;
  setEndDate: (val: string) => void;
  slippage: number;
  setSlippage: (val: number) => void;
  commission: number;
  setCommission: (val: number) => void;
}

export function DashboardHeader({
  strategies = [],
  selectedStrategy,
  onStrategyChange,
  instruments,
  selectedAssets = [],
  onAssetsChange,
  onRunBacktest,
  isRunning,
  mode = "vector",
  onModeChange,
  start_date,
  setStartDate,
  end_date,
  setEndDate,
  slippage,
  setSlippage,
  commission,
  setCommission,
}: DashboardHeaderProps) {
  const [openStrategy, setOpenStrategy] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      <Card className="p-4 flex flex-col md:flex-row justify-between items-center gap-4 bg-surface border-border shadow-sm">
        {/* Title Section */}
        <div className="flex flex-col gap-1">
          <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Backtest Configuration
          </h1>
          <p className="text-xs text-muted-foreground font-mono">
            {isRunning ? "ENGINE: RUNNING..." : "ENGINE: READY"}
          </p>
        </div>

        {/* Controls Section */}
        <div className="flex flex-wrap items-end gap-4">
          {/* Strategy Selector (Searchable) */}
          <div className="flex flex-col gap-1.5">
            <Label className="text-xs text-muted-foreground font-mono uppercase">
              Strategy
            </Label>
            <Popover open={openStrategy} onOpenChange={setOpenStrategy}>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  role="combobox"
                  aria-expanded={openStrategy}
                  className="w-[200px] justify-between text-xs h-9 px-3"
                >
                  {selectedStrategy
                    ? strategies
                        .find((s) => s === selectedStrategy)
                        ?.replace("Strategy", "")
                    : "Select strategy..."}
                  <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-[200px] p-0">
                <Command>
                  <CommandInput placeholder="Search strategy..." />
                  <CommandList>
                    <CommandEmpty>No strategy found.</CommandEmpty>
                    <CommandGroup>
                      {strategies.map((strat) => (
                        <CommandItem
                          key={strat}
                          value={strat}
                          onSelect={(currentValue) => {
                            onStrategyChange(
                              currentValue === selectedStrategy
                                ? ""
                                : currentValue,
                            );
                            setOpenStrategy(false);
                          }}
                        >
                          <Check
                            className={cn(
                              "mr-2 h-4 w-4",
                              selectedStrategy === strat
                                ? "opacity-100"
                                : "opacity-0",
                            )}
                          />
                          {strat.replace("Strategy", "")}
                        </CommandItem>
                      ))}
                    </CommandGroup>
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>
          </div>

          {/* Asset Selector (Multi) */}
          <div className="flex flex-col gap-1.5">
            <Label className="text-xs text-muted-foreground font-mono uppercase">
              Assets {selectedAssets.length > 0 && `(${selectedAssets.length})`}
            </Label>
            <AssetSelector
              assets={instruments}
              selectedAssets={selectedAssets}
              onChange={onAssetsChange}
            />
          </div>

          {/* Date Controls (New DateInput) */}
          <div className="flex flex-col gap-1.5 w-[140px]">
            <Label className="text-xs text-muted-foreground font-mono uppercase">
              Start Date
            </Label>
            <DateInput
              value={start_date}
              onChange={setStartDate}
              placeholder="dd/mm/yyyy"
            />
          </div>
          <div className="flex flex-col gap-1.5 w-[140px]">
            <Label className="text-xs text-muted-foreground font-mono uppercase">
              End Date
            </Label>
            <DateInput
              value={end_date}
              onChange={setEndDate}
              placeholder="dd/mm/yyyy"
            />
          </div>

          {/* Mode Selector */}
          <div className="flex flex-col gap-1.5">
            <Label className="text-xs text-muted-foreground font-mono uppercase">
              Engine
            </Label>
            <Select
              value={mode}
              onValueChange={(val) => onModeChange(val as "vector" | "event")}
            >
              <SelectTrigger className="w-[120px] bg-background h-9 text-xs">
                <SelectValue placeholder="Mode" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="vector">Fast Vector</SelectItem>
                <SelectItem value="event">Event Driven</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Action Button */}
          <div className="flex items-center gap-2">
            <Button
              onClick={onRunBacktest}
              disabled={isRunning}
              className="w-[140px] font-semibold tracking-wide shadow-lg shadow-primary/20 h-9"
            >
              {isRunning ? "EXECUTING" : "RUN BACKTEST"}
            </Button>
            <AdvancedSettingsDialog
              slippage={slippage}
              setSlippage={setSlippage}
              commission={commission}
              setCommission={setCommission}
            />
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
