import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { type ScanResponse } from "@/services/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Search,
  ArrowUpDown,
  TrendingUp,
  TrendingDown,
  Loader2,
  ChevronUp,
  ChevronDown,
} from "lucide-react";
import { Card } from "@/components/ui/card";

interface ScannerViewProps {
  onNavigateToSymbol: (symbol: string) => void;
  data: ScanResponse | null;
  isLoading: boolean;
  isRefreshing: boolean;
  error: string | null;
  onScan: (isBackground?: boolean) => void;
}

type SortField = "symbol" | "return" | "sharpe" | "drawdown" | "signals";
type SortDir = "asc" | "desc";

function extractNumeric(val: string | number | undefined): number {
  if (val === undefined || val === null) return 0;
  if (typeof val === "number") return val;
  const cleaned = String(val).replace("%", "").replace(",", "").trim();
  const num = parseFloat(cleaned);
  return isNaN(num) ? 0 : num;
}

function SortIcon({
  field,
  activeField,
  direction,
}: {
  field: SortField;
  activeField: SortField;
  direction: SortDir;
}) {
  if (field !== activeField)
    return <ArrowUpDown size={14} className="opacity-30" />;
  return direction === "desc" ? (
    <ChevronDown size={14} className="text-primary" />
  ) : (
    <ChevronUp size={14} className="text-primary" />
  );
}

export function ScannerView({
  onNavigateToSymbol,
  data: scanData,
  isLoading: isScanning,
  isRefreshing,
  error,
  onScan,
}: ScannerViewProps) {
  const [sortField, setSortField] = useState<SortField>("return");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === "desc" ? "asc" : "desc"));
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  };

  const sortedResults = (() => {
    if (!scanData?.results) return [];
    const results = [...scanData.results];
    results.sort((a, b) => {
      let aVal = 0;
      let bVal = 0;
      switch (sortField) {
        case "symbol":
          return sortDir === "asc"
            ? a.symbol.localeCompare(b.symbol)
            : b.symbol.localeCompare(a.symbol);
        case "return":
          aVal = extractNumeric(a.metrics["Total Return"]);
          bVal = extractNumeric(b.metrics["Total Return"]);
          break;
        case "sharpe":
          aVal = extractNumeric(a.metrics["Sharpe Ratio"]);
          bVal = extractNumeric(b.metrics["Sharpe Ratio"]);
          break;
        case "drawdown":
          aVal = extractNumeric(a.metrics["Max Drawdown"]);
          bVal = extractNumeric(b.metrics["Max Drawdown"]);
          break;
        case "signals":
          aVal = a.signal_count;
          bVal = b.signal_count;
          break;
      }
      return sortDir === "desc" ? bVal - aVal : aVal - bVal;
    });
    return results;
  })();

  return (
    <div className="flex flex-col h-full gap-4">
      <Card className="flex-1 overflow-hidden flex flex-col border border-border bg-surface">
        <AnimatePresence mode="wait">
          {isScanning && !scanData ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 flex flex-col items-center justify-center text-muted-foreground gap-4"
            >
              <Loader2 size={48} className="animate-spin opacity-30" />
              <p>Running analysis...</p>
            </motion.div>
          ) : error ? (
            <motion.div
              key="error"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 flex flex-col items-center justify-center gap-4 p-8"
            >
              <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm max-w-md text-center">
                {error}
              </div>
              <Button variant="outline" onClick={() => onScan(false)}>
                Retry
              </Button>
            </motion.div>
          ) : scanData && scanData.results.length > 0 ? (
            <motion.div
              key="results"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 overflow-auto"
            >
              {isRefreshing && (
                <div className="sticky top-0 z-10 bg-primary/10 border-b border-primary/20 px-4 py-1.5 text-xs text-primary font-mono flex items-center gap-2">
                  <Loader2 size={12} className="animate-spin" />
                  Updating results in background...
                </div>
              )}
              <Table>
                <TableHeader className="sticky top-0 bg-card z-10">
                  <TableRow>
                    <TableHead className="w-[100px]">
                      <button
                        className="flex items-center gap-1 hover:text-foreground transition-colors"
                        onClick={() => handleSort("symbol")}
                      >
                        Symbol
                        <SortIcon
                          field="symbol"
                          activeField={sortField}
                          direction={sortDir}
                        />
                      </button>
                    </TableHead>
                    <TableHead>
                      <button
                        className="flex items-center gap-1 hover:text-foreground transition-colors"
                        onClick={() => handleSort("return")}
                      >
                        Total Return
                        <SortIcon
                          field="return"
                          activeField={sortField}
                          direction={sortDir}
                        />
                      </button>
                    </TableHead>
                    <TableHead>
                      <button
                        className="flex items-center gap-1 hover:text-foreground transition-colors"
                        onClick={() => handleSort("sharpe")}
                      >
                        Sharpe
                        <SortIcon
                          field="sharpe"
                          activeField={sortField}
                          direction={sortDir}
                        />
                      </button>
                    </TableHead>
                    <TableHead>
                      <button
                        className="flex items-center gap-1 hover:text-foreground transition-colors"
                        onClick={() => handleSort("drawdown")}
                      >
                        Max Drawdown
                        <SortIcon
                          field="drawdown"
                          activeField={sortField}
                          direction={sortDir}
                        />
                      </button>
                    </TableHead>
                    <TableHead>
                      <button
                        className="flex items-center gap-1 hover:text-foreground transition-colors"
                        onClick={() => handleSort("signals")}
                      >
                        Signals
                        <SortIcon
                          field="signals"
                          activeField={sortField}
                          direction={sortDir}
                        />
                      </button>
                    </TableHead>
                    <TableHead>Last Signal</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedResults.map((result, i) => {
                    const totalReturn = extractNumeric(
                      result.metrics["Total Return"],
                    );
                    const isPositive = totalReturn >= 0;
                    const isError = result.status === "error";

                    return (
                      <TableRow
                        key={result.symbol}
                        className={`cursor-pointer transition-colors ${
                          isError ? "opacity-50" : "hover:bg-secondary/30"
                        }`}
                        onClick={() => onNavigateToSymbol(result.symbol)}
                      >
                        <TableCell className="font-mono font-bold">
                          <motion.span
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.02 }}
                          >
                            {result.symbol}
                          </motion.span>
                        </TableCell>
                        <TableCell>
                          {isError ? (
                            <span className="text-destructive text-xs">—</span>
                          ) : (
                            <span
                              className={`font-mono font-bold flex items-center gap-1 ${
                                isPositive ? "text-green-500" : "text-red-500"
                              }`}
                            >
                              {isPositive ? (
                                <TrendingUp size={14} />
                              ) : (
                                <TrendingDown size={14} />
                              )}
                              {result.metrics["Total Return"] || "0%"}
                            </span>
                          )}
                        </TableCell>
                        <TableCell className="font-mono">
                          {isError
                            ? "—"
                            : result.metrics["Sharpe Ratio"] || "—"}
                        </TableCell>
                        <TableCell className="font-mono text-red-400">
                          {isError
                            ? "—"
                            : result.metrics["Max Drawdown"] || "—"}
                        </TableCell>
                        <TableCell className="font-mono">
                          {isError ? "—" : result.signal_count}
                        </TableCell>
                        <TableCell>
                          {result.last_signal ? (
                            <Badge
                              variant={
                                result.last_signal === "buy"
                                  ? "default"
                                  : "destructive"
                              }
                              className={`text-[10px] ${
                                result.last_signal === "buy"
                                  ? "bg-green-500/20 text-green-400 border-green-500/30"
                                  : ""
                              }`}
                            >
                              {result.last_signal.toUpperCase()}
                            </Badge>
                          ) : (
                            <span className="text-xs text-muted-foreground">
                              —
                            </span>
                          )}
                        </TableCell>
                        <TableCell>
                          {isError ? (
                            <Badge
                              variant="destructive"
                              className="text-[10px]"
                            >
                              ERROR
                            </Badge>
                          ) : result.cached ? (
                            <Badge
                              variant="outline"
                              className="text-[10px] text-blue-400 border-blue-400/30"
                            >
                              CACHED
                            </Badge>
                          ) : (
                            <Badge
                              variant="outline"
                              className="text-[10px] text-green-400 border-green-400/30"
                            >
                              FRESH
                            </Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </motion.div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground gap-4">
              <Search size={48} className="opacity-20" />
              <p>Click "RUN BACKTEST" to begin.</p>
            </div>
          )}
        </AnimatePresence>
      </Card>
    </div>
  );
}
