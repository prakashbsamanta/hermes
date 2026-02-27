import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { BacktestPage } from "./BacktestPage";
import { api } from "@/services/api";
import { toast } from "sonner";
import { useBacktest } from "@/hooks/useBacktest";

// Mock Modules
vi.mock("@/hooks/useBacktest");
vi.mock("@/services/api");
vi.mock("sonner", () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
    info: vi.fn(),
  },
}));

vi.mock("@/components/ChartComponent", () => ({
  ChartComponent: () => <div data-testid="chart-component">Mock Chart</div>,
}));

vi.mock("@/components/backtest/ScannerView", () => ({
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ScannerView: ({ onNavigateToSymbol, onScan }: any) => (
    <div data-testid="scanner-view">
      <button onClick={() => onNavigateToSymbol("AAPL")}>Navigate AAPL</button>
      <button onClick={() => onScan()}>Run Scan</button>
    </div>
  ),
}));

vi.mock("@/components/dashboard/DashboardHeader", () => ({
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  DashboardHeader: (props: any) => (
    <div data-testid="dashboard-header">
      <button onClick={props.onRunBacktest}>Run Mock</button>
      <button onClick={() => props.onAssetsChange(["AAPL"])}>
        Select AAPL
      </button>
      <div data-testid="selected-assets">
        {JSON.stringify(props.selectedAssets)}
      </div>
    </div>
  ),
}));
vi.mock("@/components/dashboard/MetricCard", () => ({
  // eslint-disable-next-line
  MetricCard: ({ label, value }: any) => (
    <div>
      {label}: {value}
    </div>
  ),
}));
vi.mock("@/components/layout/DashboardLayout", () => ({
  // eslint-disable-next-line
  DashboardLayout: ({ header, sidebar, children }: any) => (
    <div>
      {header}
      {sidebar}
      {children}
    </div>
  ),
}));
vi.mock("@/components/backtest/StrategyConfigPanel", () => ({
  StrategyConfigPanel: () => <div>Config Panel</div>,
  StrategyParamInput: () => <div>Param Input</div>,
  DEFAULT_RISK_PARAMS: {
    sizing_method: "pct_equity",
    risk_pct: 1,
    fixed_quantity: 1,
    atr_period: 14,
    atr_multiplier: 1,
    hard_stop_loss_pct: null,
    hard_take_profit_pct: null,
  },
}));

vi.mock("@/components/backtest/strategyTypes", () => ({
  DEFAULT_RISK_PARAMS: {
    sizing_method: "pct_equity",
    risk_pct: 1,
    fixed_quantity: 1,
    atr_period: 14,
    atr_multiplier: 1,
    hard_stop_loss_pct: null,
    hard_take_profit_pct: null,
  },
}));

vi.mock("framer-motion", () => ({
  motion: {
    div: ({
      children,
      ...props
    }: {
      children: React.ReactNode;
      [key: string]: unknown;
    }) => <div {...(props as object)}>{children}</div>,
    span: ({
      children,
      ...props
    }: {
      children: React.ReactNode;
      [key: string]: unknown;
    }) => <span {...(props as object)}>{children}</span>,
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
}));

describe("BacktestPage", () => {
  const mockMutate = vi.fn();
  const mockReset = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();

    // Mock API
    // eslint-disable-next-line
    (api.getInstruments as any).mockResolvedValue(["AAPL", "GOOGL"]);

    // Mock Hook Default State
    // eslint-disable-next-line
    (useBacktest as any).mockReturnValue({
      mutate: mockMutate,
      reset: mockReset,
      isPending: false,
      data: null,
      isError: false,
      error: null,
      isSuccess: false,
    });
  });

  it("loads instruments on mount", async () => {
    render(<BacktestPage />);
    await waitFor(() => {
      expect(api.getInstruments).toHaveBeenCalled();
    });
  });

  it("triggers backtest mutation when driven by header", async () => {
    render(<BacktestPage />);

    // Select asset
    const selectBtn = screen.getByText("Select AAPL");
    fireEvent.click(selectBtn);

    // Wait for state update
    await waitFor(() => {
      expect(screen.getByTestId("selected-assets")).toHaveTextContent(
        '["AAPL"]',
      );
    });

    // Simulate click from the mocked header
    const runBtn = screen.getByText("Run Mock");
    fireEvent.click(runBtn);

    expect(mockMutate).toHaveBeenCalledWith(
      expect.objectContaining({
        symbol: "AAPL",
        strategy: "RSIStrategy",
      }),
    );
  });

  it("displays metrics when data is available", async () => {
    // eslint-disable-next-line
    (useBacktest as any).mockReturnValue({
      mutate: mockMutate,
      reset: mockReset,
      data: {
        metrics: {
          "Total Return": "10%",
          "Final Equity": "11000",
          "Sharpe Ratio": "1.5",
          "Max Drawdown": "-5%",
        },
        candles: [],
        indicators: {},
        signals: [],
      },
    });

    render(<BacktestPage />);

    // Must switch to Single Mode (select one asset) to see metrics
    const selectBtn = screen.getByText("Select AAPL");
    fireEvent.click(selectBtn);

    // Wait for update
    await waitFor(() => {
      expect(screen.getByText("Total Return: 10%")).toBeInTheDocument();
    });

    expect(screen.getByText("Final Equity: 11000")).toBeInTheDocument();
    expect(screen.getByTestId("chart-component")).toBeInTheDocument();
  });

  it("displays error message via toast on failure", async () => {
    // eslint-disable-next-line
    (useBacktest as any).mockReturnValue({
      mutate: mockMutate,
      reset: mockReset,
      isError: true,
      error: { message: "Backtest Failed" },
    });

    render(<BacktestPage />);
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Backtest failed: Backtest Failed",
      );
    });
  });

  it("displays success message via toast on success", async () => {
    // eslint-disable-next-line
    (useBacktest as any).mockReturnValue({
      mutate: mockMutate,
      reset: mockReset,
      isSuccess: true,
      data: { metrics: {} },
    });

    render(<BacktestPage />);

    // Select an asset to define singleSymbol so the toast fires
    const selectBtn = screen.getByText("Select AAPL");
    fireEvent.click(selectBtn);

    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith(
        expect.stringContaining("Backtest completed for AAPL"),
      );
    });
  });

  it("handles instrument load failure", async () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    // eslint-disable-next-line
    (api.getInstruments as any).mockRejectedValue(new Error("Network Error"));

    render(<BacktestPage />);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "Failed to load instruments. Check backend connection.",
      );
    });
    consoleSpy.mockRestore();
  });

  it("handles scanning via handleScan", async () => {
    // Mock runScan
    // eslint-disable-next-line
    (api.runScan as any).mockResolvedValue({
      results: [],
      completed: 10,
      failed: 0,
      cached_count: 5,
      fresh_count: 5,
    });

    render(<BacktestPage />);

    // To trigger handleScan, we must be in batch mode (default) and click Run
    const runBtn = screen.getByText("Run Mock");
    fireEvent.click(runBtn);

    await waitFor(() => {
      expect(api.runScan).toHaveBeenCalled();
    });

    expect(toast.success).toHaveBeenCalledWith(
      expect.stringContaining("Scan completed"),
    );
  });

  it("handles scan failure via handleScan", async () => {
    // eslint-disable-next-line
    (api.runScan as any).mockRejectedValue(new Error("Database error"));

    render(<BacktestPage />);
    const runBtn = screen.getByText("Run Mock");
    fireEvent.click(runBtn);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Database error");
    });
  });

  it("handles navigation to symbol from scanner", async () => {
    // Mock scan to ensure we are in a state where scanner is potentially usable
    // eslint-disable-next-line
    (api.runScan as any).mockResolvedValue({
      results: [],
      completed: 0,
      failed: 0,
      cached_count: 0,
      fresh_count: 0,
    });

    render(<BacktestPage />);

    // The ScannerView mock (added earlier) exposes "Navigate AAPL" button
    const navBtn = screen.getByText("Navigate AAPL");
    fireEvent.click(navBtn);

    // Should switch to single mode (selectedAssets = ["AAPL"])
    // Verify by checking if dashboard header shows selected assets
    await waitFor(() => {
      expect(screen.getByTestId("selected-assets")).toHaveTextContent(
        '["AAPL"]',
      );
    });
  });
});
