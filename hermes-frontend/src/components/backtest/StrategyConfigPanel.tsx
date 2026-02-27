import { useEffect, useMemo, useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import {
  RefreshCw,
  SlidersHorizontal,
  ShieldCheck,
} from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { z } from "zod";
import type { StrategyParamsMap, RiskParamsState } from "./strategyTypes";
import { DEFAULT_RISK_PARAMS } from "./strategyTypes";
export { DEFAULT_RISK_PARAMS } from "./strategyTypes";
export type { StrategyParam, StrategyParamsMap, RiskParamsState } from "./strategyTypes";



// Zod validation schema for risk parameters
const riskParamsSchema = z.object({
  sizing_method: z.enum(["fixed", "pct_equity", "atr_based"]),
  fixed_quantity: z
    .number()
    .min(1, "Quantity must be at least 1")
    .max(10000, "Quantity cannot exceed 10,000"),
  pct_equity: z
    .number()
    .min(0.005, "Risk per trade must be at least 0.5%")
    .max(0.10, "Risk per trade cannot exceed 10% of total capital"),
  atr_multiplier: z
    .number()
    .min(0.5, "ATR multiplier must be at least 0.5")
    .max(5.0, "ATR multiplier cannot exceed 5.0"),
  max_position_pct: z
    .number()
    .min(0.05, "Max position must be at least 5%")
    .max(1.0, "Max position cannot exceed 100%"),
  stop_loss_pct: z
    .number()
    .min(0.005, "Stop loss must be at least 0.5%")
    .max(0.25, "Stop loss cannot exceed 25%"),
});

type RiskValidationErrors = Partial<Record<keyof RiskParamsState, string>>;


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
  // Risk management props
  riskParams?: RiskParamsState;
  onRiskParamsChange?: (params: RiskParamsState) => void;
}

export function StrategyConfigPanel({
  strategyName,
  onParamsChange,
  currentParams,
  riskParams = DEFAULT_RISK_PARAMS,
  onRiskParamsChange,
}: StrategyConfigPanelProps) {
  const [riskErrors, setRiskErrors] = useState<RiskValidationErrors>({});

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

  const validateRiskParams = useCallback(
    (params: RiskParamsState): boolean => {
      const result = riskParamsSchema.safeParse(params);
      if (!result.success) {
        const errors: RiskValidationErrors = {};
        result.error.issues.forEach((issue) => {
          const field = issue.path[0] as keyof RiskParamsState;
          errors[field] = issue.message;
        });
        setRiskErrors(errors);
        return false;
      }
      setRiskErrors({});
      return true;
    },
    [],
  );

  const handleRiskChange = (key: keyof RiskParamsState, value: string | number) => {
    if (onRiskParamsChange) {
      const newParams = {
        ...riskParams,
        [key]: value,
      };
      validateRiskParams(newParams);
      onRiskParamsChange(newParams);
    }
  };

  const renderStrategyParams = () => {
    if (config.length === 0) {
      return (
        <p className="text-xs text-muted-foreground italic">
          No configuration parameters available for this strategy.
        </p>
      );
    }

    return config.map((param) => (
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
    ));
  };

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
          {/* Strategy-specific parameters */}
          {renderStrategyParams()}

          {/* Risk Management Section */}
          <Separator className="my-4" />

          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <ShieldCheck size={14} className="text-amber-500" />
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Risk Management
              </span>
            </div>

            {/* Sizing Method */}
            <div className="space-y-2">
              <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Position Sizing
              </Label>
              <Select
                value={riskParams.sizing_method}
                onValueChange={(val) =>
                  handleRiskChange("sizing_method", val)
                }
              >
                <SelectTrigger
                  id="sizing-method"
                  className="h-8 text-xs"
                >
                  <SelectValue placeholder="Select method" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="fixed">Fixed Quantity</SelectItem>
                  <SelectItem value="pct_equity">% of Equity</SelectItem>
                  <SelectItem value="atr_based">ATR-Based</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Fixed Quantity (visible when sizing_method is 'fixed') */}
            {riskParams.sizing_method === "fixed" && (
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Quantity
                  </Label>
                  <div className="font-mono text-xs text-foreground bg-accent/50 px-1.5 py-0.5 rounded">
                    {riskParams.fixed_quantity}
                  </div>
                </div>
                <Slider
                  id="fixed-quantity"
                  min={1}
                  max={1000}
                  step={1}
                  value={[riskParams.fixed_quantity]}
                  onValueChange={(val: number[]) =>
                    handleRiskChange("fixed_quantity", val[0])
                  }
                  className="w-full"
                />
                <p className="text-[10px] text-muted-foreground/70">
                  Fixed number of shares per trade.
                </p>
                {riskErrors.fixed_quantity && (
                  <p className="text-[10px] text-destructive font-medium mt-1">
                    ⚠ {riskErrors.fixed_quantity}
                  </p>
                )}
              </div>
            )}

            {/* % Equity (visible when sizing_method is 'pct_equity' or 'atr_based') */}
            {(riskParams.sizing_method === "pct_equity" ||
              riskParams.sizing_method === "atr_based") && (
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Capital Allocation
                    </Label>
                    <div className="font-mono text-xs text-foreground bg-accent/50 px-1.5 py-0.5 rounded">
                      {(riskParams.pct_equity * 100).toFixed(1)}%
                    </div>
                  </div>
                  <Slider
                    id="pct-equity"
                    min={0.005}
                    max={0.20}
                    step={0.005}
                    value={[riskParams.pct_equity]}
                    onValueChange={(val: number[]) =>
                      handleRiskChange("pct_equity", val[0])
                    }
                    className="w-full"
                  />
                  <p className="text-[10px] text-muted-foreground/70">
                    Fraction of total equity allocated per trade.
                  </p>
                  {riskErrors.pct_equity && (
                    <p className="text-[10px] text-destructive font-medium mt-1">
                      ⚠ {riskErrors.pct_equity}
                    </p>
                  )}
                </div>
              )}

            {/* ATR Multiplier (visible when sizing_method is 'atr_based') */}
            {riskParams.sizing_method === "atr_based" && (
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    ATR Multiplier
                  </Label>
                  <div className="font-mono text-xs text-foreground bg-accent/50 px-1.5 py-0.5 rounded">
                    {riskParams.atr_multiplier.toFixed(1)}x
                  </div>
                </div>
                <Slider
                  id="atr-multiplier"
                  min={0.5}
                  max={5.0}
                  step={0.1}
                  value={[riskParams.atr_multiplier]}
                  onValueChange={(val: number[]) =>
                    handleRiskChange("atr_multiplier", val[0])
                  }
                  className="w-full"
                />
                <p className="text-[10px] text-muted-foreground/70">
                  ATR multiplier for volatility-based position sizing.
                </p>
                {riskErrors.atr_multiplier && (
                  <p className="text-[10px] text-destructive font-medium mt-1">
                    ⚠ {riskErrors.atr_multiplier}
                  </p>
                )}
              </div>
            )}

            {/* Max Position Size */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Max Position Size
                </Label>
                <div className="font-mono text-xs text-foreground bg-accent/50 px-1.5 py-0.5 rounded">
                  {(riskParams.max_position_pct * 100).toFixed(0)}%
                </div>
              </div>
              <Slider
                id="max-position-pct"
                min={0.05}
                max={1.0}
                step={0.05}
                value={[riskParams.max_position_pct]}
                onValueChange={(val: number[]) =>
                  handleRiskChange("max_position_pct", val[0])
                }
                className="w-full"
              />
              <p className="text-[10px] text-muted-foreground/70">
                Maximum portfolio allocation for a single position.
              </p>
              {riskErrors.max_position_pct && (
                <p className="text-[10px] text-destructive font-medium mt-1">
                  ⚠ {riskErrors.max_position_pct}
                </p>
              )}
            </div>

            {/* Stop Loss */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Stop Loss
                </Label>
                <div className="font-mono text-xs text-foreground bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded">
                  {(riskParams.stop_loss_pct * 100).toFixed(1)}%
                </div>
              </div>
              <Slider
                id="stop-loss-pct"
                min={0.01}
                max={0.25}
                step={0.005}
                value={[riskParams.stop_loss_pct]}
                onValueChange={(val: number[]) =>
                  handleRiskChange("stop_loss_pct", val[0])
                }
                className="w-full"
              />
              <p className="text-[10px] text-muted-foreground/70">
                Hard stop-loss percentage from entry price. Position is
                liquidated if loss exceeds this threshold.
              </p>
              {riskErrors.stop_loss_pct && (
                <p className="text-[10px] text-destructive font-medium mt-1">
                  ⚠ {riskErrors.stop_loss_pct}
                </p>
              )}
            </div>
          </div>
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
            if (onRiskParamsChange) {
              onRiskParamsChange({ ...DEFAULT_RISK_PARAMS });
            }
          }}
        >
          <RefreshCw size={12} /> Reset All Defaults
        </Button>
      </div>
    </Card>
  );
}

