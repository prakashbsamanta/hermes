import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { DashboardHeader } from "./DashboardHeader";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// Mock resize observer for some UI components
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock ScrollIntoView for cmdk
Element.prototype.scrollIntoView = vi.fn();

// Mock pointer capture for Radix UI
Element.prototype.hasPointerCapture = vi.fn(() => false);
Element.prototype.setPointerCapture = vi.fn();
Element.prototype.releasePointerCapture = vi.fn();

// Mock ScrollArea to avoid layout issues in tests
vi.mock("@/components/ui/scroll-area", () => ({
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ScrollArea: ({ children }: any) => <div>{children}</div>,
}));

// Mock framer-motion to avoid animation issues (pointer-events: none)
vi.mock("framer-motion", () => ({
  motion: {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    span: ({ children, ...props }: any) => <span {...props}>{children}</span>,
  },
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

describe("DashboardHeader", () => {
  const mockProps = {
    strategies: ["SMAStrategy", "RSIStrategy"],
    selectedStrategy: "SMAStrategy",
    onStrategyChange: vi.fn(),
    instruments: ["ABB", "21STCENMGM"],
    selectedAssets: ["ABB"],
    onAssetsChange: vi.fn(),
    onRunBacktest: vi.fn(),
    isRunning: false,
    mode: "vector" as "vector" | "event",
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

    // Strategy Select (shows selected strategy)
    // strategy="SMAStrategy" -> "SMA".
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

  it("allows changing strategy", async () => {
    const user = userEvent.setup();
    render(<DashboardHeader {...mockProps} />);

    // Open popover (button role combobox)
    // Find by expected text inside the button and get closest button
    const strategyText = screen.getByText("SMA");
    const strategyBtn = strategyText.closest("button") || strategyText;
    await user.click(strategyBtn);

    // Select RSI
    // RSIStrategy -> RSI
    const rsiOption = await screen.findByText("RSI");
    await user.click(rsiOption);

    expect(mockProps.onStrategyChange).toHaveBeenCalledWith("RSIStrategy");
  });

  it("allows changing engine mode", async () => {
    const user = userEvent.setup();
    render(<DashboardHeader {...mockProps} />);

    const modeText = screen.getByText("Fast Vector");
    const modeTrigger = modeText.closest("button") || modeText;
    await user.click(modeTrigger);

    const eventOption = await screen.findByText("Event Driven");
    await user.click(eventOption);

    expect(mockProps.onModeChange).toHaveBeenCalledWith("event");
  });

  it("renders date inputs", () => {
    render(<DashboardHeader {...mockProps} />);
    // DateInput renders text "dd/MM/yyyy"
    // 2024-01-01 -> 01/01/2024
    expect(screen.getByText("01/01/2024")).toBeInTheDocument();
    // 2024-03-01 -> 01/03/2024
    expect(screen.getByText("01/03/2024")).toBeInTheDocument();
  });
});
