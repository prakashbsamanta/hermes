import axios from 'axios';

const API_URL = 'http://localhost:8000';

export interface BacktestRequest {
    symbol: string;
    strategy: string;
    params: Record<string, any>;
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

export interface BacktestResponse {
    symbol: string;
    strategy: string;
    metrics: Record<string, string>;
    equity_curve: ChartPoint[];
    signals: SignalPoint[];
    status: string;
    error?: string;
}

export const api = {
    runBacktest: async (req: BacktestRequest): Promise<BacktestResponse> => {
        const response = await axios.post<BacktestResponse>(`${API_URL}/backtest`, req);
        return response.data;
    }
};
