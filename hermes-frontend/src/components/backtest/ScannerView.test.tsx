import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ScannerView } from "./ScannerView";
import type { ScanResponse } from "@/services/api";
import userEvent from "@testing-library/user-event";

describe("ScannerView", () => {
  const mockNavigate = vi.fn();
  const mockScan = vi.fn();

  const mockData: ScanResponse = {
    strategy: "RSIStrategy",
    total_symbols: 3,
    completed: 3,
    failed: 0,
    cached_count: 0,
    fresh_count: 3,
    results: [
      {
        symbol: "AAPL",
        metrics: {
          "Total Return": "10%",
          "Sharpe Ratio": "0.8",
          "Max Drawdown": "-5%",
        },
        signal_count: 5,
        last_signal: "Buy",
        last_signal_time: 1234567890,
        status: "success",
        error: null,
        cached: false,
      },
      {
        symbol: "GOOGL",
        metrics: {
          "Total Return": "-5%",
          "Sharpe Ratio": "0.2",
          "Max Drawdown": "-10%",
        },
        signal_count: 2,
        last_signal: "Sell",
        last_signal_time: 1234567890,
        status: "success",
        error: null,
        cached: false,
      },
      {
        symbol: "MSFT",
        metrics: {
          "Total Return": "15%",
          "Sharpe Ratio": "1.5",
          "Max Drawdown": "-2%",
        },
        signal_count: 8,
        last_signal: "Buy",
        last_signal_time: 1234567895,
        status: "success",
        error: null,
        cached: false,
      },
    ],
    elapsed_ms: 100,
  };

  it("renders loading state", () => {
    render(
      <ScannerView
        data={null}
        isLoading={true}
        isRefreshing={false}
        error={null}
        onNavigateToSymbol={mockNavigate}
        onScan={mockScan}
      />,
    );
    expect(screen.getByText("Running analysis...")).toBeInTheDocument();
  });

  it("renders empty state", () => {
    render(
      <ScannerView
        data={null}
        isLoading={false}
        isRefreshing={false}
        error={null}
        onNavigateToSymbol={mockNavigate}
        onScan={mockScan}
      />,
    );
    expect(
      screen.getByText('Click "RUN BACKTEST" to begin.'),
    ).toBeInTheDocument();
  });

  it("sorts by Total Return (descending by default)", async () => {
    render(
      <ScannerView
        data={mockData}
        isLoading={false}
        isRefreshing={false}
        error={null}
        onNavigateToSymbol={mockNavigate}
        onScan={mockScan}
      />,
    );

    // Default: Total Return Desc
    // MSFT (15%), AAPL (10%), GOOGL (-5%)
    const rows = screen.getAllByRole("row");
    // Row 0 is header.
    expect(rows[1]).toHaveTextContent("MSFT");
    expect(rows[2]).toHaveTextContent("AAPL");
    expect(rows[3]).toHaveTextContent("GOOGL");
  });

  it("sorts by Total Return (ascending)", async () => {
    const user = userEvent.setup();
    render(
      <ScannerView
        data={mockData}
        isLoading={false}
        isRefreshing={false}
        error={null}
        onNavigateToSymbol={mockNavigate}
        onScan={mockScan}
      />,
    );

    const totalReturnHeader = screen.getByText("Total Return");
    await user.click(totalReturnHeader); // Toggle to ASC

    // Asc order: GOOGL (-5), AAPL (10), MSFT (15)
    const rows = screen.getAllByRole("row");
    expect(rows[1]).toHaveTextContent("GOOGL");
    expect(rows[2]).toHaveTextContent("AAPL");
    expect(rows[3]).toHaveTextContent("MSFT");
  });

  it("sorts by Sharpe Ratio", async () => {
    const user = userEvent.setup();
    render(
      <ScannerView
        data={mockData}
        isLoading={false}
        isRefreshing={false}
        error={null}
        onNavigateToSymbol={mockNavigate}
        onScan={mockScan}
      />,
    );

    const sharpeRatioHeader = screen.getByText("Sharpe");
    await user.click(sharpeRatioHeader); // Set to Sharpe Desc

    // Sharpe: MSFT (1.5), AAPL (0.8), GOOGL (0.2)
    const rows = screen.getAllByRole("row");
    expect(rows[1]).toHaveTextContent("MSFT");
    expect(rows[2]).toHaveTextContent("AAPL");
    expect(rows[3]).toHaveTextContent("GOOGL");

    await user.click(sharpeRatioHeader); // Toggle ASC
    const rowsAsc = screen.getAllByRole("row");
    expect(rowsAsc[1]).toHaveTextContent("GOOGL");
    expect(rowsAsc[2]).toHaveTextContent("AAPL");
    expect(rowsAsc[3]).toHaveTextContent("MSFT");
  });

  it("sorts by Symbol", async () => {
    const user = userEvent.setup();
    render(
      <ScannerView
        data={mockData}
        isLoading={false}
        isRefreshing={false}
        error={null}
        onNavigateToSymbol={mockNavigate}
        onScan={mockScan}
      />,
    );

    const symbolHeader = screen.getByText("Symbol");
    await user.click(symbolHeader); // Set to Symbol Desc

    // Desc: MSFT, GOOGL, AAPL
    const rows = screen.getAllByRole("row");
    expect(rows[1]).toHaveTextContent("MSFT");
    expect(rows[2]).toHaveTextContent("GOOGL");
    expect(rows[3]).toHaveTextContent("AAPL");
  });

  it("sorts by Max Drawdown", async () => {
    const user = userEvent.setup();
    render(
      <ScannerView
        data={mockData}
        isLoading={false}
        isRefreshing={false}
        error={null}
        onNavigateToSymbol={mockNavigate}
        onScan={mockScan}
      />,
    );

    const ddHeader = screen.getByText("Max Drawdown");
    await user.click(ddHeader); // Set to DD Desc (Less negative is higher/better? No, usually numeric sort.)
    // -2 > -5 > -10.
    // So Desc: MSFT (-2), AAPL (-5), GOOGL (-10).

    const rows = screen.getAllByRole("row");
    expect(rows[1]).toHaveTextContent("MSFT");
    expect(rows[2]).toHaveTextContent("AAPL");
    expect(rows[3]).toHaveTextContent("GOOGL");
  });

  it("sorts by Signals Count", async () => {
    const user = userEvent.setup();
    render(
      <ScannerView
        data={mockData}
        isLoading={false}
        isRefreshing={false}
        error={null}
        onNavigateToSymbol={mockNavigate}
        onScan={mockScan}
      />,
    );

    const signalsHeader = screen.getByText("Signals");
    await user.click(signalsHeader); // Set to Signals Desc

    // Signals: MSFT (8), AAPL (5), GOOGL (2)
    const rows = screen.getAllByRole("row");
    expect(rows[1]).toHaveTextContent("MSFT");
    expect(rows[2]).toHaveTextContent("AAPL");
    expect(rows[3]).toHaveTextContent("GOOGL");
  });

  it("navigates to symbol on row click", async () => {
    const user = userEvent.setup();
    render(
      <ScannerView
        data={mockData}
        isLoading={false}
        isRefreshing={false}
        error={null}
        onNavigateToSymbol={mockNavigate}
        onScan={mockScan}
      />,
    );

    const aaplRow = screen.getByText("AAPL").closest("tr");
    if (!aaplRow) throw new Error("Row not found");

    await user.click(aaplRow);
    expect(mockNavigate).toHaveBeenCalledWith("AAPL");
  });

  it("renders status badges correctly", () => {
    const mixedData = {
      ...mockData,
      results: [
        { ...mockData.results[0], cached: false },
        { ...mockData.results[1], cached: true },
      ],
    };

    render(
      <ScannerView
        data={mixedData}
        isLoading={false}
        isRefreshing={false}
        error={null}
        onNavigateToSymbol={mockNavigate}
        onScan={mockScan}
      />,
    );

    expect(screen.getByText("FRESH")).toBeInTheDocument();
    expect(screen.getByText("CACHED")).toBeInTheDocument();
  });

  it("renders data table with correct values", () => {
    render(
      <ScannerView
        data={mockData}
        isLoading={false}
        isRefreshing={false}
        error={null}
        onNavigateToSymbol={mockNavigate}
        onScan={mockScan}
      />,
    );
    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText("10%")).toBeInTheDocument();
    expect(screen.getByText("GOOGL")).toBeInTheDocument();
    expect(screen.getAllByText("-5%")).toHaveLength(2); // One for Google Return, one for AAPL DD
  });

  it("renders error state", () => {
    render(
      <ScannerView
        data={null}
        isLoading={false}
        isRefreshing={false}
        error="Scan Failed"
        onNavigateToSymbol={mockNavigate}
        onScan={mockScan}
      />,
    );
    expect(screen.getByText("Scan Failed")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });
});
