import React from 'react';
import { motion } from 'framer-motion';
import { CountUp } from './CountUp';

interface MetricCardProps {
    label: string;
    value: string;
    icon: React.ReactNode;
    idx: number;
}

export const MetricCard: React.FC<MetricCardProps> = ({ label, value, icon, idx }) => {
    return (
        <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.1 }}
            whileHover={{ scale: 1.02, backgroundColor: 'rgba(30, 41, 59, 1)' }}
            className="bg-surface p-4 rounded-xl border border-slate-700 flex items-center justify-between hover:border-slate-500 transition cursor-default shadow-lg"
        >
            <div>
                <p className="text-sm text-slate-400">{label}</p>
                <CountUp value={value} />
            </div>
            <div className="p-3 bg-slate-900 rounded-full shadow-inner">
                {icon}
            </div>
        </motion.div>
    )
};
