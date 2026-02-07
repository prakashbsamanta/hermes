import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { BacktestPage } from "./BacktestPage";
import { api } from "@/services/api";

// Mock Modules
vi.mock("@/hooks/useBacktest");
vi.mock("@/services/api");
vi.mock("@/components/ChartComponent", () => ({
  ChartComponent: () => <div data-testid="chart-component">Mock Chart</div>,
}));
vi.mock("@/components/dashboard/DashboardHeader", () => ({
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  DashboardHeader: (props: any) => (
    <div data-testid="dashboard-header">
      <button onClick={props.onRunBacktest}>Run Mock</button>
      <input
        data-testid="symbol-select"
        value={props.selectedSymbol}
        onChange={(e) => props.onSymbolChange(e.target.value)}
      />
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
}));

// Import hook after mocking
import { useBacktest } from "@/hooks/useBacktest";

describe("BacktestPage", () => {
  const mockMutate = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();

    // Mock API
    // eslint-disable-next-line
    (api.getInstruments as any).mockResolvedValue(["AAPL", "GOOGL"]);

    // Mock Hook Default State
    // eslint-disable-next-line
    (useBacktest as any).mockReturnValue({
      mutate: mockMutate,
      isPending: false,
      data: null,
      isError: false,
      error: null,
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

    // Wait for inputs to be populated from API
    await waitFor(() => {
      const input = screen.getByTestId("symbol-select") as HTMLInputElement;
      expect(input.value).toBe("AAPL");
    });

    // Simulate click from the mocked header
    const runBtn = screen.getByText("Run Mock");
    runBtn.click();

    expect(mockMutate).toHaveBeenCalledWith(
      expect.objectContaining({
        symbol: "AAPL",
        strategy: "RSIStrategy",
      }),
    );
  });

  it("displays metrics when data is available", () => {
    // eslint-disable-next-line
    (useBacktest as any).mockReturnValue({
      mutate: mockMutate,
      data: {
        metrics: {
          "Total Return": "10%",
          "Final Equity": "11000",
          "Sharpe Ratio": "1.5",
          "Max Drawdown": "-5%",
        },
        candles: [],
        indicators: [],
        signals: [],
      },
    });

    render(<BacktestPage />);
    expect(screen.getByText("Total Return: 10%")).toBeInTheDocument();
    expect(screen.getByText("Final Equity: 11000")).toBeInTheDocument();
    expect(screen.getByTestId("chart-component")).toBeInTheDocument();
  });

  it("displays error message on failure", () => {
    // eslint-disable-next-line
    (useBacktest as any).mockReturnValue({
      mutate: mockMutate,
      isError: true,
      error: { message: "Backtest Failed" },
    });

    render(<BacktestPage />);
    expect(screen.getByText("Error: Backtest Failed")).toBeInTheDocument();
  });
});
