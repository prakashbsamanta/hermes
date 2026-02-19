import axios from "axios";

const API_URL = "http://localhost:8000";

export interface BacktestRequest {
  symbol: string;
  strategy: string;
  params: Record<string, unknown>;
  initial_cash?: number;
  mode?: "vector" | "event";
  timeframe?: string;
  start_date?: string;
  end_date?: string;
  slippage?: number;
  commission?: number;
}

export interface ChartPoint {
  time: number; // unix seconds
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

export interface BacktestResponse {
  symbol: string;
  strategy: string;
  metrics: Record<string, string>;
  equity_curve: ChartPoint[];
  signals: SignalPoint[];
  candles: CandlePoint[];
  indicators: Record<string, IndicatorPoint[]>;
  status: string;
  error?: string;
}

export interface MarketDataResponse {
  symbol: string;
  candles: CandlePoint[];
  timeframe: string;
}

export interface ScanRequest {
  strategy: string;
  params?: Record<string, unknown>;
  symbols?: string[];
  initial_cash?: number;
  mode?: "vector" | "event";
  start_date?: string;
  end_date?: string;
  max_concurrency?: number;
}

export interface ScanResult {
  symbol: string;
  metrics: Record<string, string | number>;
  signal_count: number;
  last_signal: string | null;
  last_signal_time: number | null;
  status: string;
  error: string | null;
  cached: boolean;
}

export interface ScanResponse {
  strategy: string;
  total_symbols: number;
  completed: number;
  failed: number;
  cached_count: number;
  fresh_count: number;
  results: ScanResult[];
  elapsed_ms: number;
}

export const api = {
  runBacktest: async (req: BacktestRequest): Promise<BacktestResponse> => {
    const response = await axios.post<BacktestResponse>(
      `${API_URL}/backtest`,
      req,
    );
    return response.data;
  },
  getInstruments: async (): Promise<string[]> => {
    const response = await axios.get<string[]>(`${API_URL}/instruments`);
    return response.data;
  },
  getMarketData: async (
    symbol: string,
    timeframe: string = "1h",
  ): Promise<MarketDataResponse> => {
    const response = await axios.get<MarketDataResponse>(
      `${API_URL}/data/${symbol}`,
      {
        params: { timeframe },
      },
    );
    return response.data;
  },
  runScan: async (req: ScanRequest): Promise<ScanResponse> => {
    const response = await axios.post<ScanResponse>(`${API_URL}/scan`, req);
    return response.data;
  },
  getStorageSettings: async (): Promise<{ provider: string }> => {
    const response = await axios.get(`${API_URL}/settings/storage`);
    return response.data;
  },
  updateStorageSettings: async (provider: string): Promise<unknown> => {
    const response = await axios.post(`${API_URL}/settings/storage`, {
      provider,
    });
    return response.data;
  },
};
