import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { StrategyConfigPanel } from "./StrategyConfigPanel";

describe("StrategyConfigPanel", () => {
  it("renders strategy config header", () => {
    render(
      <StrategyConfigPanel
        strategyName="SMAStrategy"
        currentParams={{}}
        onParamsChange={vi.fn()}
      />,
    );
    expect(screen.getByText("Strategy Parameters")).toBeInTheDocument();
  });

  it("renders parameters for SMAStrategy", () => {
    const mockChange = vi.fn();
    render(
      <StrategyConfigPanel
        strategyName="SMAStrategy"
        currentParams={{ period: 10 }}
        onParamsChange={mockChange}
      />,
    );

    expect(screen.getByText("Fast MA Period")).toBeInTheDocument();
    expect(screen.getByText("Slow MA Period")).toBeInTheDocument();
  });

  // Additional tests would need to handle Radix UI slider interaction which is complex
  // For coverage purposes, rendering the different strategy types is key

  it("renders parameters for RSIStrategy", () => {
    render(
      <StrategyConfigPanel
        strategyName="RSIStrategy"
        currentParams={{ period: 14 }}
        onParamsChange={vi.fn()}
      />,
    );
    expect(screen.getByText("RSI Period")).toBeInTheDocument();
    expect(screen.getByText("Overbought Level")).toBeInTheDocument();
    expect(screen.getByText("Oversold Level")).toBeInTheDocument();
  });

  it("renders parameters for BollingerBandsStrategy", () => {
    render(
      <StrategyConfigPanel
        strategyName="BollingerBandsStrategy"
        currentParams={{}}
        onParamsChange={vi.fn()}
      />,
    );
    expect(screen.getByText("Period")).toBeInTheDocument();
    expect(screen.getByText("Std Dev Multiplier")).toBeInTheDocument();
  });

  it("renders parameters for MacdStrategy", () => {
    render(
      <StrategyConfigPanel
        strategyName="MACDStrategy"
        currentParams={{}}
        onParamsChange={vi.fn()}
      />,
    );
    expect(screen.getByText("Fast Period")).toBeInTheDocument();
    expect(screen.getByText("Slow Period")).toBeInTheDocument();
    expect(screen.getByText("Signal Period")).toBeInTheDocument();
  });

  it("resets to defaults when reset button is clicked", () => {
    const mockOnParamsChange = vi.fn();
    render(
      <StrategyConfigPanel
        strategyName="SMAStrategy"
        currentParams={{ period: 100 }}
        onParamsChange={mockOnParamsChange}
      />,
    );

    const resetButton = screen.getByText("Reset Defaults");
    fireEvent.click(resetButton);

    // SMA default for fast_window is 10, slow_window is 50. Wait, SMAStrategy config: fast_window=10, slow_window=50 is crossover?
    // Let's check the config in source.
    // fast_window: 10, slow_window: 50.
    expect(mockOnParamsChange).toHaveBeenCalledWith(
      expect.objectContaining({
        fast_window: 10,
        slow_window: 50,
      }),
    );
  });

  it("renders empty for unknown strategy", () => {
    render(
      <StrategyConfigPanel
        strategyName="Unknown"
        currentParams={{}}
        onParamsChange={vi.fn()}
      />,
    );
    // The component might not render "Running: Unknown", check actual content
    expect(
      screen.getByText(
        "No configuration parameters available for this strategy.",
      ),
    ).toBeInTheDocument();
    // Should not have any slider/inputs
    expect(screen.queryByRole("slider")).not.toBeInTheDocument();
  });
});
