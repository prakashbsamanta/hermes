import { describe, it, expect, vi, beforeEach } from "vitest";
import { api } from "./api";
import axios from "axios";

vi.mock("axios");

describe("API Service", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("getInstruments calls correct endpoint", async () => {
    vi.mocked(axios.get).mockResolvedValue({ data: ["AAPL", "GOOGL"] });
    const data = await api.getInstruments();
    expect(axios.get).toHaveBeenCalledWith("http://localhost:8000/instruments");
    expect(data).toEqual(["AAPL", "GOOGL"]);
  });

  it("runBacktest calls correct endpoint with payload", async () => {
    const mockResponse = { metrics: {}, candles: [] };
    vi.mocked(axios.post).mockResolvedValue({ data: mockResponse });

    const payload = {
      symbol: "AAPL",
      strategy: "RSI",
      params: {},
    };

    const data = await api.runBacktest(
      payload as unknown as import("./api").BacktestRequest,
    );
    expect(axios.post).toHaveBeenCalledWith(
      "http://localhost:8000/backtest",
      payload,
    );
    expect(data).toEqual(mockResponse);
  });

  it("runBacktestAsync calls correct endpoint", async () => {
    const mockResponse = { task_id: "test-task-123", status: "processing" };
    vi.mocked(axios.post).mockResolvedValue({ data: mockResponse });

    const payload = {
      symbol: "AAPL",
      strategy: "RSI",
      params: {},
    };

    const data = await api.runBacktestAsync(
      payload as unknown as import("./api").BacktestRequest,
    );
    expect(axios.post).toHaveBeenCalledWith(
      "http://localhost:8000/backtest/async",
      payload,
    );
    expect(data).toEqual(mockResponse);
  });

  it("pollBacktestStatus calls correct endpoint", async () => {
    const mockResponse = { task_id: "test-task-123", status: "completed" };
    vi.mocked(axios.get).mockResolvedValue({ data: mockResponse });

    const data = await api.pollBacktestStatus("test-task-123");
    expect(axios.get).toHaveBeenCalledWith(
      "http://localhost:8000/backtest/status/test-task-123",
    );
    expect(data).toEqual(mockResponse);
  });

  it("runScan calls correct endpoint", async () => {
    const mockResponse = { results: [] };
    vi.mocked(axios.post).mockResolvedValue({ data: mockResponse });

    const payload = { strategy: "RSI", params: {} };
    await api.runScan(payload as unknown as import("./api").ScanRequest);

    expect(axios.post).toHaveBeenCalledWith(
      "http://localhost:8000/scan",
      payload,
    );
  });

  it("getMarketData calls correct endpoint with params", async () => {
    vi.mocked(axios.get).mockResolvedValue({
      data: { symbol: "AAPL", candles: [] },
    });
    await api.getMarketData("AAPL", "1h");
    expect(axios.get).toHaveBeenCalledWith("http://localhost:8000/data/AAPL", {
      params: { timeframe: "1h" },
    });
  });

  it("getStorageSettings calls correct endpoint", async () => {
    vi.mocked(axios.get).mockResolvedValue({ data: { provider: "local" } });
    const data = await api.getStorageSettings();
    expect(axios.get).toHaveBeenCalledWith(
      "http://localhost:8000/settings/storage",
    );
    expect(data).toEqual({ provider: "local" });
  });

  it("updateStorageSettings calls correct endpoint", async () => {
    vi.mocked(axios.post).mockResolvedValue({ data: { success: true } });
    await api.updateStorageSettings("s3");
    expect(axios.post).toHaveBeenCalledWith(
      "http://localhost:8000/settings/storage",
      {
        provider: "s3",
      },
    );
  });

  it("handles errors correctly", async () => {
    vi.mocked(axios.get).mockRejectedValue(new Error("API Error"));
    await expect(api.getInstruments()).rejects.toThrow("API Error");
  });
});
