import React from 'react';
import { motion } from 'framer-motion';
import { Settings, BarChart2, Activity } from 'lucide-react';

interface ChartControlsProps {
    symbol: string;
    onSymbolChange: (sym: string) => void;
    timeframe: string;
    onTimeframeChange: (tf: string) => void;
    instruments: string[];
    showVolume: boolean;
    onToggleVolume: () => void;
    showSMA: boolean;
    onToggleSMA: () => void;
    onZoomIn: () => void;
    onZoomOut: () => void;
    onFullscreen: () => void;
}

export const ChartControls: React.FC<ChartControlsProps> = ({
    symbol,
    onSymbolChange,
    timeframe,
    onTimeframeChange,
    instruments,
    showVolume,
    onToggleVolume,
    showSMA,
    onToggleSMA,
    onZoomIn,
    onZoomOut,
    onFullscreen
}) => {
    return (
        <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute top-4 left-4 z-20 flex flex-wrap gap-2 items-center bg-slate-900/80 backdrop-blur-md p-2 rounded-lg border border-slate-700 shadow-xl"
        >
            {/* Symbol Selector */}
            <div className="relative group">
                <select
                    value={symbol}
                    onChange={(e) => onSymbolChange(e.target.value)}
                    className="bg-transparent text-white font-bold outline-none cursor-pointer appearance-none pr-6 pl-2 py-1 hover:text-primary transition"
                >
                    {instruments.map(inst => (
                        <option key={inst} value={inst} className="bg-slate-800 text-white">
                            {inst}
                        </option>
                    ))}
                </select>
                {/* Custom arrow if needed, but standard select is fine for MVP */}
            </div>

            <div className="w-px h-6 bg-slate-700 mx-1" />

            {/* Timeframe Selector */}
            <select
                value={timeframe}
                onChange={(e) => onTimeframeChange(e.target.value)}
                className="bg-transparent text-sm text-slate-300 outline-none cursor-pointer appearance-none px-2 py-1 hover:text-white transition"
            >
                {['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'].map(tf => (
                    <option key={tf} value={tf} className="bg-slate-800 text-slate-300">
                        {tf}
                    </option>
                ))}
            </select>

            <div className="w-px h-6 bg-slate-700 mx-1" />

            {/* Indicators */}
            <button
                onClick={onToggleVolume}
                className={`p-1.5 rounded transition ${showVolume ? 'bg-primary/20 text-primary' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
                title="Toggle Volume"
            >
                <BarChart2 size={16} />
            </button>
            <button
                onClick={onToggleSMA}
                className={`p-1.5 rounded transition ${showSMA ? 'bg-primary/20 text-primary' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
                title="Toggle SMA 20"
            >
                <Activity size={16} />
            </button>

            <div className="w-px h-6 bg-slate-700 mx-1" />

            {/* Zoom & Fullscreen */}
            <div className="flex bg-slate-800/50 rounded overflow-hidden border border-slate-700">
                <button
                    onClick={onZoomOut}
                    className="p-1.5 hover:bg-white/10 text-slate-300 hover:text-white transition"
                    title="Zoom Out"
                >
                    -
                </button>
                <button
                    onClick={onZoomIn}
                    className="p-1.5 hover:bg-white/10 text-slate-300 hover:text-white transition border-l border-slate-700"
                    title="Zoom In"
                >
                    +
                </button>
            </div>

            <button
                onClick={onFullscreen}
                className="p-1.5 rounded transition text-slate-400 hover:text-white hover:bg-white/5 ml-1"
                title="Fullscreen"
            >
                <Settings size={16} /> {/* Using Settings icon for now as a placeholder or could use Maximize if available from lucide-react */}
            </button>

        </motion.div>
    );
};
