import { useState } from "react";
import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  BarChart3,
  FlaskConical,
  Settings,
  Wallet,
  PanelLeftClose,
  PanelLeftOpen,
  Pin,
  PinOff,
} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface NavItemProps {
  to: string;
  icon: React.ReactNode;
  label: string;
  isCollapsed: boolean;
}

function NavItem({ to, icon, label, isCollapsed }: NavItemProps) {
  const content = (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          "flex items-center transition-all duration-200 rounded-md",
          isActive
            ? "scale-105 bg-accent text-accent-foreground"
            : "scale-100 opacity-70 hover:opacity-100 hover:bg-muted",
        )
      }
    >
      {({ isActive }) => (
        <div
          className={cn(
            "flex items-center w-full p-2 gap-3",
            isCollapsed ? "justify-center" : "justify-start",
            isActive && !isCollapsed
              ? "bg-accent/50 border-l-4 border-primary rounded-l-none"
              : "",
          )}
        >
          <div className="shrink-0">{icon}</div>
          {!isCollapsed && (
            <span
              className={cn(
                "font-medium whitespace-nowrap overflow-hidden transition-all duration-300",
                isActive ? "text-foreground" : "",
              )}
            >
              {label}
            </span>
          )}
        </div>
      )}
    </NavLink>
  );

  if (isCollapsed) {
    return (
      <TooltipProvider>
        <Tooltip delayDuration={0}>
          <TooltipTrigger asChild>{content}</TooltipTrigger>
          <TooltipContent side="right" className="font-medium">
            {label}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return content;
}

export function AppNavigation() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [mode, setMode] = useState<"fixed" | "hover">("fixed"); // 'fixed' means manual toggle, 'hover' means auto-collapse

  // In 'hover' mode, sidebar is collapsed by default and expands on hover
  // In 'fixed' mode, sidebar stays in 'isCollapsed' state until toggled

  const isSidebarCollapsed = mode === "hover" ? isCollapsed : isCollapsed;

  const handleMouseEnter = () => {
    if (mode === "hover") {
      setIsCollapsed(false);
    }
  };

  const handleMouseLeave = () => {
    if (mode === "hover") {
      setIsCollapsed(true);
    }
  };

  const toggleCollapse = () => {
    if (mode === "hover") {
      // If in hover mode, clicking toggle switches to fixed mode (expanded)
      setMode("fixed");
      setIsCollapsed(false);
    } else {
      // In fixed mode, toggle collapse
      setIsCollapsed(!isCollapsed);
    }
  };

  const toggleMode = () => {
    // Toggle between Fixed and Hover mode
    const newMode = mode === "fixed" ? "hover" : "fixed";
    setMode(newMode);
    setIsCollapsed(newMode === "hover"); // Default to collapsed in hover mode
  };

  return (
    <div
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={cn(
        "flex flex-col py-4 h-full border-r border-border bg-card/30 backdrop-blur-sm transition-all duration-300 ease-in-out z-50",
        isSidebarCollapsed ? "w-[64px]" : "w-[240px]",
      )}
    >
      <div
        className={cn(
          "px-4 py-4 mb-4 flex items-center gap-2",
          isSidebarCollapsed ? "justify-center" : "justify-between",
        )}
      >
        {!isSidebarCollapsed && (
          <div className="overflow-hidden whitespace-nowrap">
            <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <span className="bg-gradient-to-r from-primary to-ring bg-clip-text text-transparent">
                Hermes
              </span>
            </h1>
            <p className="text-[10px] text-muted-foreground font-mono mt-1">
              PRO TERMINAL v1.0
            </p>
          </div>
        )}

        {/* Toggle Button */}
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-muted-foreground hover:text-foreground shrink-0"
          onClick={toggleCollapse}
          title={isSidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          {isSidebarCollapsed ? (
            <PanelLeftOpen size={18} />
          ) : (
            <PanelLeftClose size={18} />
          )}
        </Button>
      </div>

      <nav className="flex flex-col gap-1 px-2 flex-1">
        <NavItem
          to="/"
          icon={<BarChart3 size={20} />}
          label="Market"
          isCollapsed={isSidebarCollapsed}
        />
        <NavItem
          to="/backtest"
          icon={<FlaskConical size={20} />}
          label="Backtest Lab"
          isCollapsed={isSidebarCollapsed}
        />
        <NavItem
          to="/portfolio"
          icon={<Wallet size={20} />}
          label="Portfolio"
          isCollapsed={isSidebarCollapsed}
        />
        <NavItem
          to="/settings"
          icon={<Settings size={20} />}
          label="Settings"
          isCollapsed={isSidebarCollapsed}
        />
      </nav>

      {/* Mode Toggle at bottom */}
      <div
        className={cn(
          "p-2 border-t border-border flex justify-center",
          !isSidebarCollapsed && "justify-end px-4",
        )}
      >
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-muted-foreground/50 hover:text-foreground"
          onClick={toggleMode}
          title={
            mode === "fixed" ? "Switch to Hover Mode" : "Switch to Fixed Mode"
          }
        >
          {mode === "fixed" ? <Pin size={16} /> : <PinOff size={16} />}
        </Button>
      </div>
    </div>
  );
}
