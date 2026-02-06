export interface BacktestRequest {
    symbol: string;
    strategy: string;
    params: Record<string, unknown>;
    initial_cash?: number;
    mode?: 'vector' | 'event';
    slippage?: number;
    commission?: number;
    start_date?: string;
    end_date?: string;
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
