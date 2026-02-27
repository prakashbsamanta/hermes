/**
 * Shared types and constants for strategy configuration.
 * Extracted into a separate file so StrategyConfigPanel.tsx can satisfy
 * the react-refresh/only-export-components eslint rule (component files
 * must only export components, not constants or interfaces).
 */

export interface StrategyParam {
    key: string;
    label: string;
    type: "number" | "boolean";
    defaultValue: number | boolean;
    min?: number;
    max?: number;
    step?: number;
    description?: string;
}

export type StrategyParamsMap = Record<string, StrategyParam[]>;

export interface RiskParamsState {
    sizing_method: "fixed" | "pct_equity" | "atr_based";
    fixed_quantity: number;
    pct_equity: number;
    atr_multiplier: number;
    max_position_pct: number;
    stop_loss_pct: number;
}

export const DEFAULT_RISK_PARAMS: RiskParamsState = {
    sizing_method: "fixed",
    fixed_quantity: 10,
    pct_equity: 0.02,
    atr_multiplier: 1.5,
    max_position_pct: 0.25,
    stop_loss_pct: 0.05,
};
