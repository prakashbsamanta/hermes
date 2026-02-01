import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { BarChart3, FlaskConical, Settings, Wallet } from "lucide-react";

interface NavItemProps {
    to: string;
    icon: React.ReactNode;
    label: string;
}

function NavItem({ to, icon, label }: NavItemProps) {
    return (
        <NavLink to={to} className={({ isActive }) => cn("w-full transition-all duration-200", isActive ? "scale-105" : "scale-100 opacity-70 hover:opacity-100")}>
            {({ isActive }) => (
                <Button
                    variant={isActive ? "secondary" : "ghost"}
                    className={cn("w-full justify-start gap-3", isActive ? "shadow-md bg-secondary/80 border-l-4 border-primary rounded-l-none" : "")}
                >
                    {icon}
                    <span className={cn("font-medium", isActive ? "text-foreground" : "")}>{label}</span>
                </Button>
            )}
        </NavLink>
    );
}

export function AppNavigation() {
    return (
        <div className="flex flex-col gap-2 py-4 h-full border-r border-border bg-card/30 backdrop-blur-sm w-[240px]">
            <div className="px-6 py-4 mb-4">
                <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
                    <span className="bg-gradient-to-r from-primary to-ring bg-clip-text text-transparent">Hermes</span>
                </h1>
                <p className="text-xs text-muted-foreground font-mono mt-1">PRO TERMINAL v1.0</p>
            </div>

            <nav className="flex flex-col gap-1 px-3">
                <NavItem to="/" icon={<BarChart3 size={20} />} label="Market" />
                <NavItem to="/backtest" icon={<FlaskConical size={20} />} label="Backtest Lab" />
                <NavItem to="/portfolio" icon={<Wallet size={20} />} label="Portfolio" />
                <NavItem to="/settings" icon={<Settings size={20} />} label="Settings" />
            </nav>
        </div>
    );
}
