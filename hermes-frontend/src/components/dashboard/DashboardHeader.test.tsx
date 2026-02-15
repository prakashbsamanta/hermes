import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { DashboardHeader } from "./DashboardHeader";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// Mock AssetSelector if needed, or rely on implementation being renderable
// Since AssetSelector uses complex UI (Command, Popover), real rendering is better integration test.

describe("DashboardHeader", () => {
  const mockProps = {
    strategies: ["SMAStrategy", "RSIStrategy"],
    selectedStrategy: "SMAStrategy",
    onStrategyChange: vi.fn(),
    instruments: ["ABB", "21STCENMGM"],
    selectedAssets: ["ABB"], // Updated prop
    onAssetsChange: vi.fn(), // Updated prop
    onRunBacktest: vi.fn(),
    isRunning: false,
    mode: "vector" as "vector" | "event", // Explicit type
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
    // Render with needed providers if any? No, standard components.
    render(<DashboardHeader {...mockProps} />);

    expect(screen.getByText("Backtest Configuration")).toBeInTheDocument();
    expect(screen.getByText("ENGINE: READY")).toBeInTheDocument();

    // Strategy Select (shows selected strategy)
    // "SMA" because replace("Strategy", "") used in code?
    // strategy="SMAStrategy" -> "SMA".
    // Wait, code: strategies.find(...)?.replace("Strategy", "")
    expect(screen.getAllByText(/SMA/i)[0]).toBeInTheDocument();

    // Asset Select (shows selected asset badge)
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

  // Skipped interaction tests for Date/Asset complex components here to focus on Header integration
});
