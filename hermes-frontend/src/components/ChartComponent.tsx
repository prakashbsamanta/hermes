import React, { useEffect, useRef } from 'react';
import { createChart, ColorType, CandlestickSeries, LineSeries } from 'lightweight-charts';
import type { IChartApi, Time } from 'lightweight-charts';
import type { CandlePoint, IndicatorPoint, SignalPoint } from '../services/api';

interface ChartProps {
    candles: CandlePoint[];
    indicators?: Record<string, IndicatorPoint[]>;
    signals: SignalPoint[];
}

export const ChartComponent: React.FC<ChartProps> = ({ candles, indicators, signals }) => {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;
        if (!candles || candles.length === 0) return;

        console.log("Initializing Candlestick Chart...");

        let chart: IChartApi;

        try {
            // Initialize Chart
            chart = createChart(chartContainerRef.current, {
                layout: {
                    background: { type: ColorType.Solid, color: 'transparent' },
                    textColor: '#94a3b8', // Slate 400
                },
                grid: {
                    vertLines: { color: '#334155' }, // Slate 700
                    horzLines: { color: '#334155' },
                },
                width: chartContainerRef.current.clientWidth,
                height: 400,
                timeScale: {
                    timeVisible: true,
                    secondsVisible: false,
                }
            });

            chartRef.current = chart;

            // 1. Candlestick Series (Main Price)
            const candleSeries = chart.addSeries(CandlestickSeries, {
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderVisible: false,
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350',
            });

            const candleData = candles.map(c => ({
                time: c.time as Time,
                open: c.open,
                high: c.high,
                low: c.low,
                close: c.close
            }));

            // Sort by time
            candleData.sort((a, b) => (a.time as number) - (b.time as number));

            candleSeries.setData(candleData);

            // 2. Indicators (Overlays)
            // e.g. SMA, Bollinger
            // TODO: In future, separate pane for RSI. For now, we plot EVERYTHING on main chart.
            // If values are ~ price (like SMA), it looks good.
            // If values are 0-100 (RSI), it will flatten the candle chart.
            // Heuristic: Check if first value is close to price?

            if (indicators) {
                const colors = ['#2962FF', '#E91E63', '#FF9800', '#9C27B0', '#00BCD4'];
                let cIdx = 0;

                Object.entries(indicators).forEach(([name, data]) => {
                    // Simple heuristic: If avg value < 200 and price > 1000, probably separate scale needed.
                    // For now, let's just plot them all and see.
                    // LightWeight Charts supports right/left axis or overlays.

                    const lineSeries = chart.addSeries(LineSeries, {
                        color: colors[cIdx % colors.length],
                        lineWidth: 2,
                        title: name,
                        // crosshairMarkerVisible: true,
                    });

                    const lineData = data.map(d => ({
                        time: d.time as Time,
                        value: d.value
                    }));

                    lineData.sort((a, b) => (a.time as number) - (b.time as number));
                    lineSeries.setData(lineData);
                    cIdx++;
                });
            }

            // 3. Signals (Markers)
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const markers: any[] = signals.map(s => ({
                time: s.time as Time,
                position: s.type === 'buy' ? 'belowBar' : 'aboveBar',
                color: s.type === 'buy' ? '#10b981' : '#ef4444',
                shape: s.type === 'buy' ? 'arrowUp' : 'arrowDown',
                text: s.type.toUpperCase(),
                size: 1,
            }));

            markers.sort((a, b) => (a.time as number) - (b.time as number));

            if (markers.length > 0) {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                (candleSeries as any).setMarkers(markers);
            }

            chart.timeScale().fitContent();

            const handleResize = () => {
                if (chartContainerRef.current) {
                    chart.applyOptions({ width: chartContainerRef.current.clientWidth });
                }
            };

            window.addEventListener('resize', handleResize);

            return () => {
                window.removeEventListener('resize', handleResize);
                chart.remove();
            };

        } catch (err) {
            console.error("Chart Rendering Error:", err);
        }
    }, [candles, indicators, signals]);

    return (
        <div ref={chartContainerRef} className="w-full h-[400px]" />
    );
};
