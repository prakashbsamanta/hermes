import { DashboardLayout } from "@/components/layout/DashboardLayout";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useTheme } from "next-themes";
import {
  Monitor,
  Moon,
  Sun,
  Bell,
  Shield,
  Eye,
  Database,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useState, useEffect } from "react";
import { api } from "@/services/api";

export function SettingsPage() {
  const { setTheme, theme } = useTheme();
  const [provider, setProvider] = useState<string>("local");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    api
      .getStorageSettings()
      .then((res) => setProvider(res.provider))
      .catch(console.error);
  }, []);

  const handleProviderChange = async (val: string) => {
    setIsLoading(true);
    try {
      await api.updateStorageSettings(val);
      setProvider(val);
    } catch (err) {
      console.error("Failed to update provider:", err);
    } finally {
      setIsLoading(false);
    }
  };

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
              preferences.
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

        {/* Storage Settings */}
        <Card className="border-l-4 border-l-blue-500">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5 text-blue-500" /> Data Storage
            </CardTitle>
            <CardDescription>
              Configure where Hermes reads historical market data from.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-2">
              <Label>Storage Provider</Label>
              <div className="flex items-center gap-4">
                <Select
                  value={provider}
                  onValueChange={handleProviderChange}
                  disabled={isLoading}
                >
                  <SelectTrigger className="w-[240px]">
                    <SelectValue placeholder="Select Provider" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="local">Local Filesystem</SelectItem>
                    <SelectItem value="cloudflare_r2">Cloudflare R2</SelectItem>
                    <SelectItem value="oracle_object_storage">
                      Oracle Object Storage
                    </SelectItem>
                  </SelectContent>
                </Select>
                {isLoading && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Updating...
                  </div>
                )}
              </div>
              <p className="text-xs text-muted-foreground max-w-md">
                Switching providers requires valid credentials in your .env
                file. Using "Local Filesystem" reads parquets from ./data
                directory.
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" /> API Connection
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
