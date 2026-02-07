import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  Minus,
  Plus,
  Maximize,
  Check,
  ChevronsUpDown,
  Settings2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

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
  onFullscreen,
}) => {
  const [openSymbol, setOpenSymbol] = useState(false);
  const [openIndicators, setOpenIndicators] = useState(false);

  return (
    <motion.div className="absolute top-4 left-4 z-50 flex flex-wrap gap-2 items-center bg-background/90 backdrop-blur-md p-1.5 rounded-lg border border-border shadow-md">
      {/* Symbol Searchable Combobox */}
      <Popover open={openSymbol} onOpenChange={setOpenSymbol}>
        <PopoverTrigger asChild>
          <Button
            variant="ghost"
            role="combobox"
            aria-expanded={openSymbol}
            className="w-[140px] justify-between font-bold hover:bg-accent/50"
          >
            {symbol || "Select symbol..."}
            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[200px] p-0">
          <Command>
            <CommandInput placeholder="Search symbol..." />
            <CommandList>
              <CommandEmpty>No symbol found.</CommandEmpty>
              <CommandGroup>
                {instruments.map((inst) => (
                  <CommandItem
                    key={inst}
                    value={inst}
                    onSelect={(currentValue: string) => {
                      onSymbolChange(currentValue);
                      setOpenSymbol(false);
                    }}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        symbol === inst ? "opacity-100" : "opacity-0",
                      )}
                    />
                    {inst}
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>

      <Separator orientation="vertical" className="h-4" />

      {/* Timeframe Selector (Standard Select is fine here, typically short list) */}
      <Select value={timeframe} onValueChange={onTimeframeChange}>
        <SelectTrigger className="h-8 w-[80px] bg-transparent border-transparent focus:ring-0 text-muted-foreground hover:text-foreground hover:bg-accent/50">
          <SelectValue placeholder="Interval" />
        </SelectTrigger>
        <SelectContent>
          {["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"].map((tf) => (
            <SelectItem key={tf} value={tf}>
              {tf}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Separator orientation="vertical" className="h-4" />

      {/* Indicators Searchable Dropdown */}
      <Popover open={openIndicators} onOpenChange={setOpenIndicators}>
        <PopoverTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 gap-2 text-muted-foreground hover:text-foreground"
          >
            <Settings2 size={16} />
            <span className="text-xs">Indicators</span>
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[200px] p-0" align="start">
          <Command>
            <CommandInput placeholder="Search indicators..." />
            <CommandList>
              <CommandEmpty>No indicator found.</CommandEmpty>
              <CommandGroup heading="Overlays">
                <CommandItem onSelect={onToggleSMA}>
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      showSMA ? "opacity-100" : "opacity-0",
                    )}
                  />
                  SMA (20)
                </CommandItem>
              </CommandGroup>
              <CommandGroup heading="Oscillators/Volume">
                <CommandItem onSelect={onToggleVolume}>
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      showVolume ? "opacity-100" : "opacity-0",
                    )}
                  />
                  Volume
                </CommandItem>
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>

      <Separator orientation="vertical" className="h-4" />

      {/* Zoom & Fullscreen */}
      <div className="flex items-center gap-0.5">
        <Button
          variant="ghost"
          size="icon"
          onClick={onZoomOut}
          className="h-8 w-8 text-muted-foreground"
          title="Zoom Out"
        >
          <Minus size={16} />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={onZoomIn}
          className="h-8 w-8 text-muted-foreground"
          title="Zoom In"
        >
          <Plus size={16} />
        </Button>
        <Separator orientation="vertical" className="h-4 mx-1" />
        <Button
          variant="ghost"
          size="icon"
          onClick={onFullscreen}
          className="h-8 w-8 text-muted-foreground"
          title="Fullscreen"
        >
          <Maximize size={16} />
        </Button>
      </div>
    </motion.div>
  );
};
