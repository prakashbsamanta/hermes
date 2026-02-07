import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PieChart, Wallet, ArrowUpRight } from "lucide-react";

export function PortfolioPage() {
  return (
    <DashboardLayout
      header={
        <div className="flex items-center justify-between p-4 bg-card/50 backdrop-blur border-b border-border rounded-lg mb-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Portfolio</h1>
            <p className="text-sm text-muted-foreground">
              Manage your positions and performance.
            </p>
          </div>
        </div>
      }
      sidebar={
        <div className="flex flex-col gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Value
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">$124,592.00</div>
              <div className="text-xs text-green-500 flex items-center mt-1">
                <ArrowUpRight size={12} className="mr-1" /> +2.5%
              </div>
            </CardContent>
          </Card>
        </div>
      }
    >
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 h-full content-start">
        <Card className="col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="h-4 w-4" /> Asset Allocation
            </CardTitle>
          </CardHeader>
          <CardContent className="h-[300px] flex items-center justify-center text-muted-foreground bg-muted/20 rounded-md m-4 border border-dashed">
            Chart Visualization Coming Soon
          </CardContent>
        </Card>

        <Card className="col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wallet className="h-4 w-4" /> Open Positions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center p-2 border rounded hover:bg-muted/50 transition-colors">
              <div>
                <div className="font-bold">AAPL</div>
                <div className="text-xs text-muted-foreground">150 Shares</div>
              </div>
              <div className="text-right">
                <div className="font-mono">$182.50</div>
                <div className="text-xs text-green-500">+12.4%</div>
              </div>
            </div>
            <div className="flex justify-between items-center p-2 border rounded hover:bg-muted/50 transition-colors">
              <div>
                <div className="font-bold">TSLA</div>
                <div className="text-xs text-muted-foreground">50 Shares</div>
              </div>
              <div className="text-right">
                <div className="font-mono">$240.20</div>
                <div className="text-xs text-red-500">-3.2%</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
