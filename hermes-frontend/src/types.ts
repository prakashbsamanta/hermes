export interface RiskParams {
  sizing_method: "fixed" | "pct_equity" | "atr_based";
  fixed_quantity: number;
  pct_equity: number;
  atr_multiplier: number;
  max_position_pct: number;
  stop_loss_pct: number;
}

export interface BacktestRequest {
  symbol: string;
  strategy: string;
  params: Record<string, unknown>;
  initial_cash?: number;
  mode?: "vector" | "event";
  timeframe?: string;
  slippage?: number;
  commission?: number;
  start_date?: string;
  end_date?: string;
  risk_params?: RiskParams;
}

export interface ChartPoint {
  time: number;
  value: number;
}

export interface SignalPoint {
  time: number;
  type: "buy" | "sell";
  price: number;
}

export interface CandlePoint {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface IndicatorPoint {
  time: number;
  value: number;
}

export interface BacktestTaskResponse {
  task_id: string;
  status: string;
  message: string;
}

export interface BacktestStatusResponse {
  task_id: string;
  status: "processing" | "completed" | "failed";
  progress?: number;
  result?: {
    symbol: string;
    strategy: string;
    metrics: Record<string, string>;
    equity_curve: ChartPoint[];
    signals: SignalPoint[];
    candles: CandlePoint[];
    indicators: Record<string, IndicatorPoint[]>;
    status: string;
    error?: string;
  };
  error?: string;
}
