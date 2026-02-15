import * as React from "react";
import {
  format,
  addMonths,
  subMonths,
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  eachDayOfInterval,
  isSameMonth,
  isSameDay,
  isToday,
  isAfter,
  isValid,
  parse,
  setMonth,
  setYear,
  startOfYear,
  addYears,
  subYears,
  eachMonthOfInterval,
  endOfYear,
} from "date-fns";
import { ChevronLeft, ChevronRight, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface CalendarProps {
  selected?: Date;
  onSelect?: (date: Date | undefined) => void;
  className?: string;
  disableFuture?: boolean;
}

type CalendarView = "dates" | "months" | "years";

export function Calendar({
  selected,
  onSelect,
  className,
  disableFuture = true,
}: CalendarProps) {
  const [currentMonth, setCurrentMonth] = React.useState<Date>(
    selected || new Date(),
  );
  const [view, setView] = React.useState<CalendarView>("dates");
  const [inputValue, setInputValue] = React.useState("");

  // Sync with selected prop
  React.useEffect(() => {
    if (selected) {
      setInputValue(format(selected, "MMMM d, yyyy"));
      setCurrentMonth(selected);
    } else {
      setInputValue("");
    }
  }, [selected]);

  const handleDateClick = (day: Date) => {
    if (disableFuture && isAfter(day, new Date())) return;
    onSelect?.(day);
  };

  const handleMonthSelect = (monthIndex: number) => {
    const newDate = setMonth(currentMonth, monthIndex);
    if (disableFuture && isAfter(newDate, new Date())) {
      // If whole month is in future?
      // Logic: if newDate (same day of month) is future?
      // We should just check start of month vs today?
      // Or if month > current month.
      // Let's allow selecting past months even if `currentMonth.getDate()` makes it future (e.g. 31st vs 30th).
      // setMonth handles days overflow by clamping.
    }
    setCurrentMonth(newDate);
    setView("dates");
  };

  const handleYearSelect = (year: number) => {
    const newDate = setYear(currentMonth, year);
    setCurrentMonth(newDate);
    setView("months"); // Go to months view after year select? Or dates? User request says "panel to select year and month". Usually Year -> Month -> Date.
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setInputValue(val);

    // Try parse
    let parsed = parse(val, "MMMM d, yyyy", new Date());
    if (!isValid(parsed)) {
      parsed = parse(
        `${val}, ${new Date().getFullYear()}`,
        "MMMM d, yyyy",
        new Date(),
      );
    }

    if (isValid(parsed)) {
      if (disableFuture && isAfter(parsed, new Date())) return;
      setCurrentMonth(parsed);
      onSelect?.(parsed);
    }
  };

  // Content Generation
  const renderDates = () => {
    const monthStart = startOfMonth(currentMonth);
    const monthEnd = endOfMonth(monthStart);
    const startDate = startOfWeek(monthStart);
    const endDate = endOfWeek(monthEnd);
    const calendarDays = eachDayOfInterval({ start: startDate, end: endDate });
    const weekDays = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

    return (
      <>
        <div className="grid grid-cols-7 mb-2">
          {weekDays.map((day) => (
            <div
              key={day}
              className="text-center text-xs font-medium text-muted-foreground py-1"
            >
              {day}
            </div>
          ))}
        </div>
        <div className="grid grid-cols-7 gap-y-1 gap-x-1">
          {calendarDays.map((day) => {
            const isSelected = selected && isSameDay(day, selected);
            const isCurrentMonth = isSameMonth(day, currentMonth);
            const isTodayDate = isToday(day);
            const isDisabled = disableFuture && isAfter(day, new Date());

            return (
              <button
                key={day.toString()}
                onClick={() => handleDateClick(day)}
                disabled={isDisabled}
                className={cn(
                  "h-9 w-9 text-sm rounded-full flex items-center justify-center transition-all relative",
                  !isCurrentMonth && "text-muted-foreground/30 opacity-50",
                  isCurrentMonth &&
                    !isSelected &&
                    !isTodayDate &&
                    "hover:bg-accent hover:text-accent-foreground text-foreground",
                  isSelected &&
                    "bg-primary text-primary-foreground shadow-md shadow-primary/20 hover:bg-primary/90 font-semibold",
                  !isSelected &&
                    isTodayDate &&
                    !isDisabled &&
                    "ring-1 ring-primary/50 text-foreground font-medium",
                  isDisabled &&
                    "opacity-30 cursor-not-allowed hover:bg-transparent",
                )}
              >
                {format(day, "d")}
                {isTodayDate && !isSelected && (
                  <span className="absolute bottom-1 w-1 h-1 bg-primary rounded-full" />
                )}
              </button>
            );
          })}
        </div>
      </>
    );
  };

  const renderMonths = () => {
    // Show months of current year
    const months = eachMonthOfInterval({
      start: startOfYear(currentMonth),
      end: endOfYear(currentMonth),
    });

    return (
      <div className="grid grid-cols-3 gap-2 py-4">
        {months.map((month, idx) => {
          const isSelectedMonth = isSameMonth(month, selected || new Date(0)); // Visual indicator for selected date's month?
          const isCurrentMonth = isSameMonth(month, new Date()); // Today's month
          const isDisabled = disableFuture && isAfter(month, new Date());

          return (
            <button
              key={idx}
              onClick={() => handleMonthSelect(idx)}
              disabled={isDisabled}
              className={cn(
                "h-10 text-sm rounded-md hover:bg-accent hover:text-accent-foreground transition-colors",
                isSelectedMonth && "bg-primary/10 text-primary font-medium",
                isCurrentMonth &&
                  !isSelectedMonth &&
                  "text-primary font-medium",
                isDisabled &&
                  "opacity-30 cursor-not-allowed hover:bg-transparent",
              )}
            >
              {format(month, "MMM")}
            </button>
          );
        })}
      </div>
    );
  };

  const renderYears = () => {
    // Show range of years around current year. E.g., 12 years.
    const currentYear = currentMonth.getFullYear();
    const startYear = currentYear - 6;
    const endYear = currentYear + 5;
    const years = [];
    for (let y = startYear; y <= endYear; y++) {
      years.push(y);
    }

    return (
      <div className="grid grid-cols-3 gap-2 py-4">
        {years.map((year) => {
          const isSelectedYear = selected && selected.getFullYear() === year;
          const isCurrentYear = new Date().getFullYear() === year;
          const isDisabled = disableFuture && year > new Date().getFullYear();

          return (
            <button
              key={year}
              onClick={() => handleYearSelect(year)}
              disabled={isDisabled}
              className={cn(
                "h-10 text-sm rounded-md hover:bg-accent hover:text-accent-foreground transition-colors",
                isSelectedYear && "bg-primary/10 text-primary font-medium",
                isCurrentYear && !isSelectedYear && "text-primary font-medium",
                isDisabled &&
                  "opacity-30 cursor-not-allowed hover:bg-transparent",
              )}
            >
              {year}
            </button>
          );
        })}
      </div>
    );
  };

  // Navigation Logic
  const handlePrev = () => {
    if (view === "dates") setCurrentMonth(subMonths(currentMonth, 1));
    if (view === "months") setCurrentMonth(subYears(currentMonth, 1));
    if (view === "years") setCurrentMonth(subYears(currentMonth, 12));
  };

  const handleNext = () => {
    if (view === "dates") setCurrentMonth(addMonths(currentMonth, 1));
    if (view === "months") setCurrentMonth(addYears(currentMonth, 1));
    if (view === "years") setCurrentMonth(addYears(currentMonth, 12));
  };

  // Header Text Logic
  const renderHeader = () => {
    if (view === "years") {
      const currentYear = currentMonth.getFullYear();
      return `${currentYear - 6} - ${currentYear + 5}`;
    }
    if (view === "months") {
      return (
        <button
          onClick={() => setView("years")}
          className="hover:text-primary transition-colors"
        >
          {format(currentMonth, "yyyy")}
        </button>
      );
    }
    // Dates view
    return (
      <div className="flex items-center gap-1">
        <button
          onClick={() => setView("months")}
          className="hover:bg-secondary px-2 py-0.5 rounded-md transition-colors font-semibold"
        >
          {format(currentMonth, "MMMM")}
        </button>
        <button
          onClick={() => setView("years")}
          className="hover:bg-secondary px-2 py-0.5 rounded-md transition-colors font-semibold"
        >
          {format(currentMonth, "yyyy")}
        </button>
      </div>
    );
  };

  return (
    <div
      className={cn(
        "p-4 w-[340px] bg-card text-card-foreground rounded-xl shadow-xl border border-border/50 font-sans",
        className,
      )}
    >
      {/* Target Input - only show in dates view? Or always? Always is fine. */}
      <div className="mb-4 space-y-1.5">
        <label className="text-xs text-muted-foreground font-medium ml-1">
          Target date
        </label>
        <div className="relative group">
          <input
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            placeholder="Select date"
            className="w-full bg-secondary/50 border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all placeholder:text-muted-foreground/50 h-10"
          />
          {inputValue && (
            <button
              onClick={() => {
                setInputValue("");
                onSelect?.(undefined);
              }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between mb-4 px-1 h-8">
        <button
          onClick={handlePrev}
          className="p-1 hover:bg-secondary rounded-md text-muted-foreground hover:text-foreground transition-colors"
        >
          <ChevronLeft size={16} />
        </button>

        <div className="text-sm font-semibold tracking-wide">
          {renderHeader()}
        </div>

        <button
          onClick={handleNext}
          className="p-1 hover:bg-secondary rounded-md text-muted-foreground hover:text-foreground transition-colors"
          disabled={
            disableFuture &&
            view === "dates" &&
            isSameMonth(currentMonth, new Date())
          } // Simple disable logic
        >
          <ChevronRight size={16} />
        </button>
      </div>

      {/* Content */}
      <div className="min-h-[240px]">
        {view === "dates" && renderDates()}
        {view === "months" && renderMonths()}
        {view === "years" && renderYears()}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between mt-4 pt-2 border-t border-border/50">
        <button
          onClick={() => {
            setInputValue("");
            onSelect?.(undefined);
          }}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          Clear
        </button>
        <button
          onClick={() => {
            const today = new Date();
            setCurrentMonth(today);
            onSelect?.(today);
            setView("dates");
          }}
          className="text-xs text-primary font-medium hover:text-primary/80 transition-colors"
        >
          Today
        </button>
      </div>
    </div>
  );
}
