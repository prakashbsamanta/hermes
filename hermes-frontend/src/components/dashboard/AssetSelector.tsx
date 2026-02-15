import * as React from "react";
import { Check, ChevronsUpDown, X } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
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
import { Badge } from "@/components/ui/badge";

interface AssetSelectorProps {
  assets: string[];
  selectedAssets: string[];
  onChange: (val: string[]) => void;
}

export function AssetSelector({
  assets,
  selectedAssets,
  onChange,
}: AssetSelectorProps) {
  const [open, setOpen] = React.useState(false);
  const [search, setSearch] = React.useState("");

  const filteredAssets = React.useMemo(() => {
    if (!search) return assets.slice(0, 50);
    const upperSearch = search.toUpperCase();
    return assets.filter((a) => a.includes(upperSearch)).slice(0, 50);
  }, [assets, search]);

  const handleSelect = (currentValue: string) => {
    const newSelected = selectedAssets.includes(currentValue)
      ? selectedAssets.filter((item) => item !== currentValue)
      : [...selectedAssets, currentValue];
    onChange(newSelected);
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange([]);
    setSearch("");
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between min-w-[200px] h-auto py-2"
        >
          <div className="flex flex-wrap gap-1 items-center">
            {selectedAssets.length === 0 ? (
              <span className="text-muted-foreground">Select assets...</span>
            ) : selectedAssets.length <= 3 ? (
              selectedAssets.map((asset) => (
                <Badge
                  key={asset}
                  variant="secondary"
                  className="mr-1 text-[10px] px-1 py-0 h-5"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleSelect(asset);
                  }}
                >
                  {asset}
                  <X className="ml-1 h-3 w-3 hover:text-destructive cursor-pointer" />
                </Badge>
              ))
            ) : (
              <Badge variant="secondary" className="mr-1">
                {selectedAssets.length} selected
              </Badge>
            )}
          </div>
          <div className="flex items-center opacity-50 shrink-0">
            {selectedAssets.length > 0 && (
              <X
                className="mr-2 h-4 w-4 cursor-pointer hover:opacity-100 z-50 text-foreground"
                onClick={handleClear}
                onPointerDown={(e) => e.stopPropagation()}
              />
            )}
            <ChevronsUpDown className="h-4 w-4" />
          </div>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[300px] p-0" align="start">
        <Command shouldFilter={false}>
          <CommandInput
            placeholder="Search assets..."
            value={search}
            onValueChange={setSearch}
          />
          <CommandList>
            <CommandEmpty>No asset found.</CommandEmpty>
            <CommandGroup>
              {filteredAssets.map((asset) => (
                <CommandItem
                  key={asset}
                  value={asset}
                  onSelect={() => handleSelect(asset)}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      selectedAssets.includes(asset)
                        ? "opacity-100"
                        : "opacity-0",
                    )}
                  />
                  {asset}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
