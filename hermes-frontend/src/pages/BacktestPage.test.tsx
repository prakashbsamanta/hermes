import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { BacktestPage } from "./BacktestPage";
import { api } from "@/services/api";
import { toast } from "sonner";

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

// Import hook after mocking
import { useBacktest } from "@/hooks/useBacktest";

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

  it("displays error message via toast on failure", () => {
    // eslint-disable-next-line
    (useBacktest as any).mockReturnValue({
      mutate: mockMutate,
      reset: mockReset,
      isError: true,
      error: { message: "Backtest Failed" },
    });

    render(<BacktestPage />);
    expect(toast.error).toHaveBeenCalledWith(
      "Backtest failed: Backtest Failed",
    );
  });
});
