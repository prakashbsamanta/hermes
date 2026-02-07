import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { DashboardHeader } from "./DashboardHeader";
import userEvent from "@testing-library/user-event";

describe("DashboardHeader", () => {
  const mockProps = {
    strategies: ["SMAStrategy", "RSIStrategy"],
    selectedStrategy: "SMAStrategy",
    onStrategyChange: vi.fn(),
    instruments: ["ABB", "21STCENMGM"],
    selectedSymbol: "ABB",
    onSymbolChange: vi.fn(),
    onRunBacktest: vi.fn(),
    isRunning: false,
    mode: "vector" as const,
    onModeChange: vi.fn(),
    start_date: "2024-01-01",
    setStartDate: vi.fn(),
    end_date: "2024-03-01",
    setEndDate: vi.fn(),
    slippage: 0,
    setSlippage: vi.fn(),
    commission: 0,
    setCommission: vi.fn(),
  };

  it("renders necessary controls", () => {
    render(<DashboardHeader {...mockProps} />);

    expect(screen.getByText("Backtest Configuration")).toBeInTheDocument();
    expect(screen.getByText("ENGINE: READY")).toBeInTheDocument();
    // Strategy Select
    expect(screen.getByText(/SMA/)).toBeInTheDocument();
    // Asset Select
    expect(screen.getByText("ABB")).toBeInTheDocument();
    // Mode Select
    expect(screen.getByText("Fast Vector")).toBeInTheDocument();
    // Run Button
    expect(screen.getByRole("button", { name: "RUN BACKTEST" })).toBeEnabled();
  });

  it("displays running state correctly", () => {
    render(<DashboardHeader {...mockProps} isRunning={true} />);
    expect(screen.getByText("ENGINE: RUNNING...")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "EXECUTING" })).toBeDisabled();
  });

  it("calls onRunBacktest when button is clicked", async () => {
    const user = userEvent.setup();
    render(<DashboardHeader {...mockProps} />);

    const runButton = screen.getByRole("button", { name: "RUN BACKTEST" });
    await user.click(runButton);

    expect(mockProps.onRunBacktest).toHaveBeenCalledTimes(1);
  });

  it("updates start and end dates", async () => {
    // const user = userEvent.setup(); // Unused here, using fireEvent below
    render(<DashboardHeader {...mockProps} />);

    const startInput = screen.getByLabelText("Start Date");
    const endInput = screen.getByLabelText("End Date");

    await fireEvent.change(startInput, { target: { value: "2024-02-01" } });
    expect(mockProps.setStartDate).toHaveBeenCalledWith("2024-02-01");

    await fireEvent.change(endInput, { target: { value: "2024-04-01" } });
    expect(mockProps.setEndDate).toHaveBeenCalledWith("2024-04-01");
  });

  it("renders input for symbol when instruments list is empty", async () => {
    const user = userEvent.setup();
    render(<DashboardHeader {...mockProps} instruments={[]} />);

    const input = screen.getByPlaceholderText("Symbol");
    await user.type(input, "GOOGL");

    expect(mockProps.onSymbolChange).toHaveBeenCalled();
  });
});
