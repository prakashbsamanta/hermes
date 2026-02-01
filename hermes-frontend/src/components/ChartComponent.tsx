import React, { useEffect, useRef, useState, useMemo } from 'react';
import { createChart, ColorType } from 'lightweight-charts';
import type { IChartApi, Time } from 'lightweight-charts';
import type { CandlePoint, IndicatorPoint, SignalPoint } from '../services/api';
import { ChartControls } from './ChartControls';

interface ChartProps {
    candles: CandlePoint[];
    indicators?: Record<string, IndicatorPoint[]>;
    signals: SignalPoint[];

    // View Props (Home Screen)
    symbol?: string;
    onSymbolChange?: (sym: string) => void;
    timeframe?: string;
    onTimeframeChange?: (tf: string) => void;
    instruments?: string[];

    className?: string;
}

// Helper to calculate simple SMA
const calculateSMA = (data: CandlePoint[], period: number) => {
    const sma = [];
    for (let i = 0; i < data.length; i++) {
        if (i < period - 1) continue;
        let sum = 0;
        for (let j = 0; j < period; j++) {
            sum += data[i - j].close;
        }
        sma.push({ time: data[i].time, value: sum / period });
    }
    return sma;
};

export const ChartComponent: React.FC<ChartProps> = ({
    candles,
    indicators,
    signals,
    symbol,
    onSymbolChange,
    timeframe,
    onTimeframeChange,
    instruments,
    className
}) => {
    const wrapperRef = useRef<HTMLDivElement>(null);
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);

    const [showVolume, setShowVolume] = useState(false);
    const [showSMA, setShowSMA] = useState(false);

    // Tooltip State
    const [tooltipData, setTooltipData] = useState<{
        visible: boolean;
        x: number;
        y: number;
        type: 'buy' | 'sell';
        price: number;
        time: number;
    } | null>(null);

    // Calculate Client-Side SMA if enabled
    const smaData = useMemo(() => {
        if (!showSMA || !candles) return [];
        return calculateSMA(candles, 20);
    }, [candles, showSMA]);

    useEffect(() => {
        if (!chartContainerRef.current) return;
        if (!candles || candles.length === 0) return;

        console.log("Initializing Candlestick Chart (v4)...");

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
                height: chartContainerRef.current.clientHeight, // Use container height
                timeScale: {
                    timeVisible: true,
                    secondsVisible: false,
                },
                crosshair: {
                    // We need crosshair to detect hover pos
                    mode: 1 // Magnet
                }
            });

            chartRef.current = chart;

            // 1. Candlestick Series (Main Price)
            const candleSeries = chart.addCandlestickSeries({
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

            // 2. Volume Series (Client Toggle)
            if (showVolume) {
                const volumeSeries = chart.addHistogramSeries({
                    color: '#26a69a',
                    priceFormat: {
                        type: 'volume',
                    },
                    priceScaleId: '', // Overlay on main chart (bottom)
                });

                // Scale volume to sit at bottom 20%
                volumeSeries.priceScale().applyOptions({
                    scaleMargins: {
                        top: 0.8,
                        bottom: 0,
                    },
                });

                const volumeData = candles.map(c => ({
                    time: c.time as Time,
                    value: c.volume,
                    color: c.close >= c.open ? 'rgba(38, 166, 154, 0.5)' : 'rgba(239, 83, 80, 0.5)'
                }));
                volumeSeries.setData(volumeData);
            }

            // 3. Client-Side SMA (Client Toggle)
            if (showSMA && smaData.length > 0) {
                const smaSeries = chart.addLineSeries({
                    color: '#fbbf24', // Amber 400
                    lineWidth: 2,
                    title: 'SMA 20 (Client)',
                    priceScaleId: 'right', // Same as candles
                });
                smaSeries.setData(smaData.map(d => ({ time: d.time as Time, value: d.value })));
            }

            // 4. Backtest Indicators (Server Provided)
            if (indicators) {
                const colors = ['#2962FF', '#E91E63', '#FF9800', '#9C27B0', '#00BCD4'];
                let cIdx = 0;

                Object.entries(indicators).forEach(([name, data]) => {
                    const lineSeries = chart.addLineSeries({
                        color: colors[cIdx % colors.length],
                        lineWidth: 2,
                        title: name,
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

            // 5. Signals (Markers)
            //eslint-disable-next-line @typescript-eslint/no-explicit-any
            const markers: any[] = signals.map(s => ({
                time: s.time as Time,
                position: s.type === 'buy' ? 'belowBar' : 'aboveBar',
                color: s.type === 'buy' ? '#10b981' : '#ef4444',
                shape: s.type === 'buy' ? 'arrowUp' : 'arrowDown',
                // Text removed as requested
                // text: s.type.toUpperCase(), 
                size: 1,
            }));

            markers.sort((a, b) => (a.time as number) - (b.time as number));

            if (markers.length > 0) {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                (candleSeries as any).setMarkers(markers);
            }

            // 6. Tooltip Logic (Crosshair Subscription)
            chart.subscribeCrosshairMove(param => {
                if (
                    !param.time ||
                    param.point === undefined ||
                    !param.point.x ||
                    !param.point.y ||
                    param.point.x < 0 ||
                    param.point.y < 0
                ) {
                    setTooltipData(null);
                    return;
                }

                const time = param.time as number;
                // Find visible signal at this time
                // Since markers are typically exactly on the candle time
                const signalAtTime = signals.find(s => s.time === time);

                if (signalAtTime) {
                    // Calculate tooltip position near the marker
                    // Markers are above/below bars.
                    // We can use param.point (cursor) or calculate Y position of the bar.
                    // Using cursor X and fixed Y offset from cursor might be easiest, 
                    // or better: anchor to the series price if possible.
                    // For simplicity, let's float near the cursor but ensure visibility.

                    const price = signalAtTime.price || 0; // Fallback if price missing

                    setTooltipData({
                        visible: true,
                        x: param.point.x,
                        y: param.point.y,
                        type: signalAtTime.type,
                        price: price,
                        time: signalAtTime.time
                    });
                } else {
                    setTooltipData(null);
                }
            });

            chart.timeScale().fitContent();

            const handleResize = () => {
                if (chartContainerRef.current) {
                    chart.applyOptions({
                        width: chartContainerRef.current.clientWidth,
                        height: chartContainerRef.current.clientHeight
                    });
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
    }, [candles, indicators, signals, showVolume, showSMA, smaData]);

    // Handlers
    const handleZoomIn = () => {
        if (!chartRef.current) return;
        const currentRange = chartRef.current.timeScale().getVisibleLogicalRange();
        if (!currentRange) return;

        // Zoom In = Smaller Range
        const barsToZoom = (currentRange.to - currentRange.from) * 0.2; // Zoom 20%
        chartRef.current.timeScale().setVisibleLogicalRange({
            from: currentRange.from + barsToZoom / 2,
            to: currentRange.to - barsToZoom / 2
        });
    };

    const handleZoomOut = () => {
        if (!chartRef.current) return;
        const currentRange = chartRef.current.timeScale().getVisibleLogicalRange();
        if (!currentRange) return;

        // Zoom Out = Larger Range
        const barsToZoom = (currentRange.to - currentRange.from) * 0.2; // Zoom 20%
        chartRef.current.timeScale().setVisibleLogicalRange({
            from: currentRange.from - barsToZoom / 2,
            to: currentRange.to + barsToZoom / 2
        });
    };

    const handleFullscreen = () => {
        if (wrapperRef.current) {
            if (!document.fullscreenElement) {
                wrapperRef.current.requestFullscreen().catch(err => {
                    console.error(`Error attempting to enable fullscreen mode: ${err.message} (${err.name})`);
                });
            } else {
                document.exitFullscreen();
            }
        }
    };

    return (
        <div ref={wrapperRef} className={`relative ${className || 'w-full h-full'} bg-surface`}>
            {/* Chart Toolbar (Only show if interactive props provided) */}
            {symbol && onSymbolChange && timeframe && onTimeframeChange && instruments && (
                <ChartControls
                    symbol={symbol}
                    onSymbolChange={onSymbolChange}
                    timeframe={timeframe}
                    onTimeframeChange={onTimeframeChange}
                    instruments={instruments}
                    showVolume={showVolume}
                    onToggleVolume={() => setShowVolume(!showVolume)}
                    showSMA={showSMA}
                    onToggleSMA={() => setShowSMA(!showSMA)}
                    onZoomIn={handleZoomIn}
                    onZoomOut={handleZoomOut}
                    onFullscreen={handleFullscreen}
                />
            )}
            <div ref={chartContainerRef} className="w-full h-full" id="tv-chart-container" />

            {/* Tooltip */}
            {tooltipData && tooltipData.visible && (
                <div
                    className="absolute z-50 p-2 rounded shadow-lg border text-xs font-mono pointer-events-none transition-opacity duration-75"
                    style={{
                        left: tooltipData.x + 10, // Offset from mouse
                        top: tooltipData.y + 10,
                        backgroundColor: 'var(--card)', // Use CSS variable
                        borderColor: tooltipData.type === 'buy' ? '#10b981' : '#ef4444',
                        color: 'var(--foreground)'
                    }}
                >
                    <div className="font-bold uppercase mb-1" style={{ color: tooltipData.type === 'buy' ? '#10b981' : '#ef4444' }}>
                        {tooltipData.type} SIGNAL
                    </div>
                    <div>Price: {tooltipData.price.toFixed(2)}</div>
                    <div className="text-muted-foreground text-[10px]">
                        {new Date(tooltipData.time * 1000).toLocaleString()}
                    </div>
                </div>
            )}
        </div>
    );
};
