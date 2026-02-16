import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { DateInput } from "./date-input";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// Mock Calendar to isolate DateInput logic
vi.mock("@/components/ui/calendar", () => ({
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  Calendar: ({ onSelect, selected }: any) => (
    <div data-testid="mock-calendar">
      <button onClick={() => onSelect(new Date(2023, 0, 15))}>
        Select Jan 15
      </button>
      <button onClick={() => onSelect(undefined)}>Clear Date</button>
      <div data-testid="selected-date">
        {selected ? selected.toISOString() : "None"}
      </div>
    </div>
  ),
}));

describe("DateInput Component", () => {
  const mockOnChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders placeholder when empty", () => {
    render(
      <DateInput value="" onChange={mockOnChange} placeholder="Test Date" />,
    );
    expect(screen.getByText("Test Date")).toBeInTheDocument();
  });

  it("renders formatted date when value is provided", () => {
    render(<DateInput value="2023-01-15" onChange={mockOnChange} />);
    expect(screen.getByText("15/01/2023")).toBeInTheDocument();
  });

  it("opens popover on click", async () => {
    const user = userEvent.setup();
    render(<DateInput value="" onChange={mockOnChange} />);

    await user.click(screen.getByRole("button"));
    expect(screen.getByTestId("mock-calendar")).toBeVisible();
  });

  it("calls onChange with formatted date on selection", async () => {
    const user = userEvent.setup();
    render(<DateInput value="" onChange={mockOnChange} />);

    await user.click(screen.getByRole("button"));
    await user.click(screen.getByText("Select Jan 15"));

    expect(mockOnChange).toHaveBeenCalledWith("2023-01-15");
  });

  it("calls onChange with empty string on clear", async () => {
    const user = userEvent.setup();
    render(<DateInput value="2023-01-15" onChange={mockOnChange} />);

    await user.click(screen.getByRole("button")); // Open
    await user.click(screen.getByText("Clear Date")); // Select undefined

    expect(mockOnChange).toHaveBeenCalledWith("");
  });
});
