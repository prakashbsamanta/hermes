import axios from 'axios';

const API_URL = 'http://localhost:8000';

export interface BacktestRequest {
    symbol: string;
    strategy: string;
    params: Record<string, unknown>;
    initial_cash?: number;
}

export interface ChartPoint {
    time: number; // unix seconds
    value: number;
}

export interface SignalPoint {
    time: number;
    type: 'buy' | 'sell';
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

export const api = {
    runBacktest: async (req: BacktestRequest): Promise<BacktestResponse> => {
        const response = await axios.post<BacktestResponse>(`${API_URL}/backtest`, req);
        return response.data;
    },
    getInstruments: async (): Promise<string[]> => {
        const response = await axios.get<string[]>(`${API_URL}/instruments`);
        return response.data;
    },
    getMarketData: async (symbol: string, timeframe: string = "1h"): Promise<MarketDataResponse> => {
        const response = await axios.get<MarketDataResponse>(`${API_URL}/data/${symbol}`, {
            params: { timeframe }
        });
        return response.data;
    }
};
