import type { ReactNode } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { motion } from "framer-motion";

interface MetricCardProps {
    label: string;
    value: string | number;
    icon: ReactNode;
    idx?: number;
}

export function MetricCard({ label, value, icon, idx = 0 }: MetricCardProps) {
    return (
        <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.1, duration: 0.4 }}
        >
            <Card className="overflow-hidden border-l-4 border-l-primary/50 hover:border-l-primary transition-all duration-300">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 p-4">
                    <CardTitle className="text-sm font-medium text-muted-foreground font-mono uppercase tracking-wider">
                        {label}
                    </CardTitle>
                    {icon}
                </CardHeader>
                <CardContent className="p-4 pt-0">
                    <div className="text-2xl font-bold tracking-tight font-mono">{value}</div>
                </CardContent>
            </Card>
        </motion.div>
    );
}
