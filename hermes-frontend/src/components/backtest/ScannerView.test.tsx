import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ScannerView } from "./ScannerView";
import { ScanResponse } from "@/services/api";
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

    // Default is usually not sorted or specific order? Component sets return/desc default
    // Let's verify initial order. AAPL: 10%, GOOGL: -5%, MSFT: 15%
    // Desc order: MSFT (15), AAPL (10), GOOGL (-5)

    // We can get rows and check symbol text
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
    await user.click(totalReturnHeader); // Click once to reverse default desc to asc

    // Asc order: GOOGL (-5), AAPL (10), MSFT (15)
    const rows = screen.getAllByRole("row");
    expect(rows[1]).toHaveTextContent("GOOGL");
    expect(rows[2]).toHaveTextContent("AAPL");
    expect(rows[3]).toHaveTextContent("MSFT");
  });

  it("sorts by Sharpe Ratio when clicked", async () => {
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
    await user.click(sharpeRatioHeader); // Click once for default desc

    // Sharpe Ratios: AAPL: 0.8, GOOGL: 0.2, MSFT: 1.5
    // Desc: MSFT (1.5), AAPL (0.8), GOOGL (0.2)
    const rows = screen.getAllByRole("row");
    expect(rows[1]).toHaveTextContent("MSFT");
    expect(rows[2]).toHaveTextContent("AAPL");
    expect(rows[3]).toHaveTextContent("GOOGL");

    await user.click(sharpeRatioHeader); // Click again for asc

    // Asc: GOOGL (0.2), AAPL (0.8), MSFT (1.5)
    const rowsAsc = screen.getAllByRole("row");
    expect(rowsAsc[1]).toHaveTextContent("GOOGL");
    expect(rowsAsc[2]).toHaveTextContent("AAPL");
    expect(rowsAsc[3]).toHaveTextContent("MSFT");
  });

  it("sorts by Symbol when clicked", async () => {
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

    // Click on Symbol header
    const symbolHeader = screen.getByText("Symbol");
    await user.click(symbolHeader);

    // Default sort dir set to desc on new field or asc?
    // Code says: if sortField !== field -> setSortDir("desc")
    // Let's check.
    // Symbols: AAPL, GOOGL, MSFT.
    // Desc: MSFT, GOOGL, AAPL.

    const rows = screen.getAllByRole("row");
    expect(rows[1]).toHaveTextContent("MSFT");
    expect(rows[2]).toHaveTextContent("GOOGL");
    expect(rows[3]).toHaveTextContent("AAPL");

    // Click again to toggle asc
    await user.click(symbolHeader);
    const rowsAsc = screen.getAllByRole("row");
    expect(rowsAsc[1]).toHaveTextContent("AAPL");
    expect(rowsAsc[2]).toHaveTextContent("GOOGL");
    expect(rowsAsc[3]).toHaveTextContent("MSFT");
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

  it("renders data table", () => {
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
    expect(screen.getAllByText("-5%")).toHaveLength(2);
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
