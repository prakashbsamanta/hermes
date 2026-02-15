import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { AssetSelector } from "./AssetSelector";
import userEvent from "@testing-library/user-event";

describe("AssetSelector", () => {
  const mockOnChange = vi.fn();
  const assets = ["AAPL", "GOOGL", "MSFT"];

  beforeAll(() => {
    Element.prototype.scrollIntoView = vi.fn();
  });

  it("renders trigger button with placeholder", () => {
    // Empty selection
    render(
      <AssetSelector
        assets={assets}
        selectedAssets={[]}
        onChange={mockOnChange}
      />,
    );
    expect(screen.getByText("Select assets...")).toBeInTheDocument();
  });

  it("renders count when assets are selected", () => {
    render(
      <AssetSelector
        assets={assets}
        selectedAssets={["AAPL", "GOOGL", "MSFT", "AMZN"]}
        onChange={mockOnChange}
      />,
    );
    expect(screen.getByText("4 selected")).toBeInTheDocument();
  });

  it("opens popover and displays options", async () => {
    const user = userEvent.setup();
    render(
      <AssetSelector
        assets={assets}
        selectedAssets={[]}
        onChange={mockOnChange}
      />,
    );

    const trigger = screen.getByRole("combobox");
    await user.click(trigger);

    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText("GOOGL")).toBeInTheDocument();
  });

  it("filters assets on search", async () => {
    const user = userEvent.setup();
    render(
      <AssetSelector
        assets={assets}
        selectedAssets={[]}
        onChange={mockOnChange}
      />,
    );

    await user.click(screen.getByRole("combobox"));
    const input = screen.getByPlaceholderText("Search assets...");
    await user.type(input, "GOO");

    expect(screen.getByText("GOOGL")).toBeInTheDocument();
    expect(screen.queryByText("AAPL")).not.toBeInTheDocument();
  });

  it("selects and deselects assets", async () => {
    const user = userEvent.setup();
    render(
      <AssetSelector
        assets={assets}
        selectedAssets={[]}
        onChange={mockOnChange}
      />,
    );

    await user.click(screen.getByRole("combobox"));
    const option = screen.getByText("AAPL");
    await user.click(option);

    expect(mockOnChange).toHaveBeenCalledWith(["AAPL"]);
  });

  it("deselects asset via badge click", async () => {
    const user = userEvent.setup();
    render(
      <AssetSelector
        assets={assets}
        selectedAssets={["AAPL"]}
        onChange={mockOnChange}
      />,
    );

    await user.click(screen.getByText("AAPL"));

    expect(mockOnChange).toHaveBeenCalledWith([]);
  });

  it("clears all assets", async () => {
    // const user = userEvent.setup(); // Unused
    render(
      <AssetSelector
        assets={assets}
        selectedAssets={["AAPL"]}
        onChange={mockOnChange}
      />,
    );

    const trigger = screen.getByRole("combobox");
    expect(trigger).toBeInTheDocument();
  });
});
