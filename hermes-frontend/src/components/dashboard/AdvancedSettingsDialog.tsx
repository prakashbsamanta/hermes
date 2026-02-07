import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Settings } from "lucide-react";

interface AdvancedSettingsDialogProps {
  slippage: number;
  setSlippage: (val: number) => void;
  commission: number;
  setCommission: (val: number) => void;
}

export function AdvancedSettingsDialog({
  slippage,
  setSlippage,
  commission,
  setCommission,
}: AdvancedSettingsDialogProps) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="icon" className="shadow-sm">
          <Settings size={18} className="text-muted-foreground" />
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Advanced Backtest Settings</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="slippage" className="text-right">
              Slippage (%)
            </Label>
            <Input
              id="slippage"
              type="number"
              step="0.01"
              value={slippage}
              onChange={(e) => setSlippage(parseFloat(e.target.value) || 0)}
              className="col-span-3"
            />
            <p className="col-span-4 text-xs text-muted-foreground text-right">
              Simulated price impact per trade (e.g., 0.01 = 1%).
            </p>
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="commission" className="text-right">
              Commission ($)
            </Label>
            <Input
              id="commission"
              type="number"
              step="0.01"
              value={commission}
              onChange={(e) => setCommission(parseFloat(e.target.value) || 0)}
              className="col-span-3"
            />
            <p className="col-span-4 text-xs text-muted-foreground text-right">
              Fixed cost per unit/share traded.
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
