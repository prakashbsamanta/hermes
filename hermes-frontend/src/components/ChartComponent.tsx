import React, { useEffect, useRef } from 'react';
import { createChart, ColorType, AreaSeries } from 'lightweight-charts';
import type { IChartApi, Time } from 'lightweight-charts';
import type { ChartPoint, SignalPoint } from '../services/api';

interface ChartProps {
    data: ChartPoint[];
    signals: SignalPoint[];
}

export const ChartComponent: React.FC<ChartProps> = ({ data, signals }) => {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        console.log("Initializing Chart (v5)...");

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
            });

            chartRef.current = chart;

            // v5 API: Use addSeries(SeriesType, Options)
            const areaSeries = chart.addSeries(AreaSeries, {
                lineColor: '#2962FF',
                topColor: '#2962FF',
                bottomColor: 'rgba(41, 98, 255, 0.28)',
            });

            // Process Data
            const chartData = data.map(d => ({
                time: d.time as Time,
                value: d.value
            }));

            // Sort Data (Required by Lightweight Charts)
            chartData.sort((a, b) => (a.time as number) - (b.time as number));

            if (chartData.length > 0) {
                areaSeries.setData(chartData);
            }

            // Process Signals (Markers)
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const markers: any[] = signals.map(s => ({
                time: s.time as Time,
                position: s.type === 'buy' ? 'belowBar' : 'aboveBar',
                color: s.type === 'buy' ? '#10b981' : '#ef4444',
                shape: s.type === 'buy' ? 'arrowUp' : 'arrowDown',
                text: s.type.toUpperCase(),
                size: 1,
            }));

            // Sort Markers
            markers.sort((a, b) => (a.time as number) - (b.time as number));

            if (markers.length > 0) {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                (areaSeries as any).setMarkers(markers);
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
            console.error("Stats Chart Rendering Error:", err);
        }
    }, [data, signals]);

    return (
        <div ref={chartContainerRef} className="w-full h-[400px]" />
    );
};
