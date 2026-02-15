import * as React from "react";
import { format, parse, isValid } from "date-fns";
import { Calendar as CalendarIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

interface DateInputProps {
  value: string | undefined;
  onChange: (val: string) => void;
  placeholder?: string;
  className?: string;
}

export function DateInput({
  value,
  onChange,
  placeholder,
  className,
}: DateInputProps) {
  const [open, setOpen] = React.useState(false);

  const date = React.useMemo(() => {
    if (!value) return undefined;
    // Handle YYYY-MM-DD format from backend
    const d = parse(value, "yyyy-MM-dd", new Date());
    return isValid(d) ? d : undefined;
  }, [value]);

  const handleSelect = (d: Date | undefined) => {
    if (d) {
      onChange(format(d, "yyyy-MM-dd"));
      setOpen(false);
    } else {
      onChange("");
      // Keep open if clearing? Or close?
      // setOpen(false);
    }
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant={"outline"}
          className={cn(
            "w-full justify-start text-left font-normal text-xs h-9 px-3",
            !date && "text-muted-foreground",
            className,
          )}
        >
          <CalendarIcon className="mr-2 h-3.5 w-3.5" />
          {date ? (
            format(date, "dd/MM/yyyy")
          ) : (
            <span>{placeholder || "Pick date"}</span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="w-auto p-0 bg-transparent border-none shadow-none"
        align="start"
      >
        <Calendar
          selected={date}
          onSelect={handleSelect}
          disableFuture={true}
        />
      </PopoverContent>
    </Popover>
  );
}
