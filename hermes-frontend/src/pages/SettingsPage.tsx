import { DashboardLayout } from "@/components/layout/DashboardLayout";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { useTheme } from "next-themes";
import { Monitor, Moon, Sun, Bell, Shield, Eye } from "lucide-react";
import { cn } from "@/lib/utils";

export function SettingsPage() {
  const { setTheme, theme } = useTheme();

  return (
    <DashboardLayout
      header={
        <div className="flex items-center justify-between p-4 bg-card/50 backdrop-blur border-b border-border rounded-lg mb-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
            <p className="text-sm text-muted-foreground">
              Manage your preferences and application configuration.
            </p>
          </div>
        </div>
      }
      sidebar={
        <div className="flex flex-col gap-4">
          <Card className="p-4 bg-muted/20 border-l-4 border-l-primary">
            <h3 className="text-sm font-semibold mb-1">Pro Tip</h3>
            <p className="text-xs text-muted-foreground">
              Use the system theme to automatically sync with your OS
              preferences for the best experience.
            </p>
          </Card>
        </div>
      }
    >
      <div className="space-y-6 max-w-4xl">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Eye className="h-5 w-5" /> Appearance
            </CardTitle>
            <CardDescription>
              Customize how Hermes looks on your device.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="space-y-4">
              <Label>Theme Preference</Label>
              <div className="grid grid-cols-3 gap-4">
                <ThemeCard
                  name="Abyss (Dark)"
                  icon={<Moon size={24} />}
                  isActive={theme === "dark"}
                  onClick={() => setTheme("dark")}
                />
                <ThemeCard
                  name="Glacier (Light)"
                  icon={<Sun size={24} />}
                  isActive={theme === "light"}
                  onClick={() => setTheme("light")}
                />
                <ThemeCard
                  name="System"
                  icon={<Monitor size={24} />}
                  isActive={theme === "system"}
                  onClick={() => setTheme("system")}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" /> Notifications
            </CardTitle>
            <CardDescription>Configure how you receive alerts.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Trade Executed</Label>
                <p className="text-xs text-muted-foreground">
                  Receive a toast notification when a trade is filled.
                </p>
              </div>
              <Switch checked={true} />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Backtest Complete</Label>
                <p className="text-xs text-muted-foreground">
                  Play a sound when a long-running backtest finishes.
                </p>
              </div>
              <Switch checked={false} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" /> API & Data
            </CardTitle>
            <CardDescription>
              Manage your connection to the Hermes Engine.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2">
              <Label>Endpoint</Label>
              <div className="p-3 bg-muted rounded font-mono text-sm">
                http://localhost:8000
              </div>
              <p className="text-xs text-muted-foreground">
                To change connection settings, please update your environment
                configuration.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}

function ThemeCard({
  name,
  icon,
  isActive,
  onClick,
}: {
  name: string;
  icon: React.ReactNode;
  isActive: boolean;
  onClick: () => void;
}) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "cursor-pointer rounded-xl border-2 p-6 flex flex-col items-center gap-4 transition-all duration-200 hover:scale-[1.02]",
        isActive
          ? "border-primary bg-primary/5 shadow-lg shadow-primary/10"
          : "border-muted bg-card hover:bg-accent/50",
      )}
    >
      <div
        className={cn(
          "p-3 rounded-full",
          isActive
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-muted-foreground",
        )}
      >
        {icon}
      </div>
      <span
        className={cn(
          "font-semibold",
          isActive ? "text-primary" : "text-muted-foreground",
        )}
      >
        {name}
      </span>
    </div>
  );
}
