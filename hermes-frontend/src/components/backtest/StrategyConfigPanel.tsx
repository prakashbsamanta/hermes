import { useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { RefreshCw, SlidersHorizontal } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";

export interface StrategyParam {
  key: string;
  label: string;
  type: "number" | "boolean"; // extend to "select" if needed
  defaultValue: number | boolean;
  min?: number;
  max?: number;
  step?: number;
  description?: string;
}

export type StrategyParamsMap = Record<string, StrategyParam[]>;

// Configuration Schema for Supported Strategies
const STRATEGY_CONFIGS: StrategyParamsMap = {
  RSIStrategy: [
    {
      key: "period",
      label: "RSI Period",
      type: "number",
      defaultValue: 14,
      min: 2,
      max: 50,
      step: 1,
      description: "Lookback period for RSI calculation.",
    },
    {
      key: "overbought",
      label: "Overbought Level",
      type: "number",
      defaultValue: 70,
      min: 50,
      max: 95,
      step: 1,
      description:
        "Level above which asset is considered overbought (Sell Signal).",
    },
    {
      key: "oversold",
      label: "Oversold Level",
      type: "number",
      defaultValue: 30,
      min: 5,
      max: 50,
      step: 1,
      description:
        "Level below which asset is considered oversold (Buy Signal).",
    },
  ],
  SMAStrategy: [
    {
      key: "fast_window",
      label: "Fast MA Period",
      type: "number",
      defaultValue: 10,
      min: 2,
      max: 100,
      step: 1,
    },
    {
      key: "slow_window",
      label: "Slow MA Period",
      type: "number",
      defaultValue: 50,
      min: 5,
      max: 200,
      step: 1,
    },
  ],
  BollingerBandsStrategy: [
    {
      key: "window",
      label: "Period",
      type: "number",
      defaultValue: 20,
      min: 5,
      max: 50,
      step: 1,
    },
    {
      key: "num_std",
      label: "Std Dev Multiplier",
      type: "number",
      defaultValue: 2,
      min: 0.5,
      max: 4,
      step: 0.1,
    },
  ],
  MACDStrategy: [
    {
      key: "fast_period",
      label: "Fast Period",
      type: "number",
      defaultValue: 12,
      min: 2,
      max: 50,
    },
    {
      key: "slow_period",
      label: "Slow Period",
      type: "number",
      defaultValue: 26,
      min: 5,
      max: 100,
    },
    {
      key: "signal_period",
      label: "Signal Period",
      type: "number",
      defaultValue: 9,
      min: 2,
      max: 30,
    },
  ],
  MTFTrendFollowingStrategy: [
    {
      key: "fast_ema",
      label: "Fast EMA",
      type: "number",
      defaultValue: 50,
      min: 10,
      max: 200,
    },
    {
      key: "slow_ema",
      label: "Slow EMA",
      type: "number",
      defaultValue: 200,
      min: 50,
      max: 400,
    },
    {
      key: "risk_percent",
      label: "Risk Percent",
      type: "number",
      defaultValue: 0.02,
      min: 0.01,
      max: 0.1,
      step: 0.01,
    },
  ],
};

interface StrategyConfigPanelProps {
  strategyName: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onParamsChange: (params: Record<string, any>) => void;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  currentParams: Record<string, any>;
}

export function StrategyConfigPanel({
  strategyName,
  onParamsChange,
  currentParams,
}: StrategyConfigPanelProps) {
  const config = useMemo(
    () => STRATEGY_CONFIGS[strategyName] || [],
    [strategyName],
  );

  useEffect(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const defaults: Record<string, any> = {};
    let needsUpdate = false;

    config.forEach((p) => {
      defaults[p.key] = p.defaultValue;
      if (currentParams[p.key] === undefined) {
        needsUpdate = true;
      }
    });

    if (needsUpdate || Object.keys(currentParams).length === 0) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const finalParams: Record<string, any> = {};
      config.forEach((p) => {
        finalParams[p.key] =
          currentParams[p.key] !== undefined
            ? currentParams[p.key]
            : p.defaultValue;
      });

      if (JSON.stringify(finalParams) !== JSON.stringify(currentParams)) {
        onParamsChange(finalParams);
      }
    }
  }, [strategyName, config, currentParams, onParamsChange]);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleChange = (key: string, value: any) => {
    onParamsChange({
      ...currentParams,
      [key]: value,
    });
  };

  if (config.length === 0) {
    return (
      <Card className="h-full border-l rounded-none border-y-0 border-r-0 shadow-none bg-card/50 w-full">
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2 text-muted-foreground">
            <SlidersHorizontal size={16} /> Configuration
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground italic">
            No configuration parameters available for this strategy.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full border-l rounded-none border-y-0 border-r-0 shadow-none bg-card/30 backdrop-blur-sm w-full flex flex-col">
      <CardHeader className="pb-3 px-4 pt-4 shrink-0">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          <SlidersHorizontal size={16} />
          Strategy Parameters
        </CardTitle>
      </CardHeader>
      <ScrollArea className="flex-1">
        <CardContent className="space-y-6 px-4 pb-4">
          {config.map((param) => (
            <div key={param.key} className="space-y-3">
              <div className="flex justify-between items-center">
                <Label
                  htmlFor={param.key}
                  className="text-xs font-medium text-muted-foreground uppercase tracking-wider"
                >
                  {param.label}
                </Label>
                <div className="font-mono text-xs text-foreground bg-accent/50 px-1.5 py-0.5 rounded min-w-[30px] text-right">
                  {currentParams[param.key]}
                </div>
              </div>

              {param.type === "number" && (
                <div className="space-y-3">
                  <Slider
                    id={param.key}
                    min={param.min}
                    max={param.max}
                    step={param.step || 1}
                    value={[
                      Number(currentParams[param.key] || param.defaultValue),
                    ]}
                    onValueChange={(val: number[]) =>
                      handleChange(param.key, val[0])
                    }
                    className="w-full"
                  />
                </div>
              )}

              {param.type === "boolean" && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    {param.description || param.label}
                  </span>
                  <Switch
                    checked={Boolean(currentParams[param.key])}
                    onCheckedChange={(val) => handleChange(param.key, val)}
                  />
                </div>
              )}

              {param.description && param.type !== "boolean" && (
                <p className="text-[10px] text-muted-foreground/70">
                  {param.description}
                </p>
              )}
            </div>
          ))}
        </CardContent>
      </ScrollArea>
      <div className="p-4 border-t border-border bg-card/50 shrink-0">
        <Button
          variant="outline"
          size="sm"
          className="w-full gap-2 text-xs"
          onClick={() => {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const defaults: Record<string, any> = {};
            config.forEach((p) => (defaults[p.key] = p.defaultValue));
            onParamsChange(defaults);
          }}
        >
          <RefreshCw size={12} /> Reset Defaults
        </Button>
      </div>
    </Card>
  );
}
