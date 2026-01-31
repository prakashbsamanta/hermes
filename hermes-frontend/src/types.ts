export interface BacktestRequest {
    symbol: string;
    strategy: string;
    params: Record<string, any>;
    initial_cash?: number;
}

export interface ChartPoint {
    time: number;
    value: number;
}

export interface SignalPoint {
    time: number;
    type: 'buy' | 'sell';
    price: number;
}
