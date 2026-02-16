import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { Calendar } from "./calendar";
import { format, addMonths, subMonths } from "date-fns";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

describe("Calendar Component", () => {
  const mockOnSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders correctly with default props", () => {
    render(<Calendar />);
    expect(screen.getByText("Target date")).toBeInTheDocument();
    expect(screen.getByText("Today")).toBeInTheDocument();
    expect(screen.getByText("Clear")).toBeInTheDocument();
    // Default selected date input is empty if no prop provided
    const input = screen.getByPlaceholderText(
      "Select date",
    ) as HTMLInputElement;
    expect(input.value).toBe("");
  });

  it("renders with selected date", () => {
    const date = new Date(2023, 0, 15); // Jan 15 2023
    render(<Calendar selected={date} onSelect={mockOnSelect} />);

    // Input should show formatted date
    const input = screen.getByPlaceholderText(
      "Select date",
    ) as HTMLInputElement;
    expect(input.value).toBe(format(date, "MMMM d, yyyy"));

    // Check if the date is highlighted (has bg-primary class)
    // The button containing text "15" should have primary background
    // We get all buttons with text "15" (could be multiple if adjacent months overlap, but 15 is usually safe)
    // Actually calendar days are buttons.
    const dayButtons = screen.getAllByRole("button", { name: "15" });
    const selectedDay = dayButtons.find((btn) =>
      btn.classList.contains("bg-primary"),
    );
    expect(selectedDay).toBeInTheDocument();
  });

  it("navigates next month", () => {
    const date = new Date(2023, 0, 15);
    const { container } = render(
      <Calendar selected={date} disableFuture={false} />,
    );

    // Navigate Next
    const nextBtn = container
      .querySelector(".lucide-chevron-right")
      ?.closest("button");
    expect(nextBtn).toBeInTheDocument();
    fireEvent.click(nextBtn!);

    expect(screen.getByText("February")).toBeInTheDocument();
    expect(screen.getByText("2023")).toBeInTheDocument();
  });

  it("navigates prev month", () => {
    const date = new Date(2023, 0, 15);
    const { container } = render(
      <Calendar selected={date} disableFuture={false} />,
    );

    // Navigate Prev
    const prevBtn = container
      .querySelector(".lucide-chevron-left")
      ?.closest("button");
    expect(prevBtn).toBeInTheDocument();
    fireEvent.click(prevBtn!);

    expect(screen.getByText("December")).toBeInTheDocument();
    expect(screen.getByText("2022")).toBeInTheDocument();
  });

  it("switches to months view and selects a month", async () => {
    const user = userEvent.setup();
    const date = new Date(2023, 0, 15);
    render(<Calendar selected={date} onSelect={mockOnSelect} />);

    // Click Month name in header (January)
    await user.click(screen.getByText("January"));

    // Should see month abbreviations like "Jun"
    expect(screen.getByText("Jun")).toBeInTheDocument();

    // Select June
    await user.click(screen.getByText("Jun"));

    // Should return to dates view with June selected as current month
    expect(screen.getByText("June")).toBeInTheDocument();
    expect(screen.getByText("2023")).toBeInTheDocument();
  });

  it("switches to years view and selects a year", async () => {
    const user = userEvent.setup();
    const date = new Date(2023, 0, 15);
    render(
      <Calendar
        selected={date}
        onSelect={mockOnSelect}
        disableFuture={false}
      />,
    );

    // Click Year in header (2023)
    await user.click(screen.getByText("2023"));

    // Select 2025
    const targetYear = screen.getByRole("button", { name: "2025" });
    await user.click(targetYear);

    // Should return to months view
    // Expect month names
    expect(screen.getByText("Jan")).toBeInTheDocument();

    // Select Jan to verify interaction chain
    await user.click(screen.getByText("Jan"));
    expect(screen.getByText("2025")).toBeInTheDocument();
  });

  it("selects a date", async () => {
    const user = userEvent.setup();
    const date = new Date(2023, 0, 15);
    render(<Calendar selected={date} onSelect={mockOnSelect} />);

    // Select 20th
    const day20 = screen.getByRole("button", { name: "20" });
    await user.click(day20);

    expect(mockOnSelect).toHaveBeenCalledWith(expect.any(Date));
    const calledDate = mockOnSelect.mock.calls[0][0];
    expect(calledDate.getDate()).toBe(20);
    expect(calledDate.getMonth()).toBe(0); // Jan
    expect(calledDate.getFullYear()).toBe(2023);
  });

  it("handles manual input interaction", async () => {
    const user = userEvent.setup();
    render(<Calendar onSelect={mockOnSelect} />);

    const input = screen.getByPlaceholderText("Select date");
    await user.clear(input);
    await user.type(input, "January 20, 2023");

    // Check call logic (it calls heavily on change, or debounced? code says onChange immediately parses)
    expect(mockOnSelect).toHaveBeenCalled();
    const lastCall =
      mockOnSelect.mock.calls[mockOnSelect.mock.calls.length - 1][0];
    expect(lastCall.getDate()).toBe(20);
    expect(lastCall.getMonth()).toBe(0); // Jan is 0
    expect(lastCall.getFullYear()).toBe(2023);
  });

  it("clears selection via Footer Clear button", async () => {
    const user = userEvent.setup();
    render(<Calendar selected={new Date()} onSelect={mockOnSelect} />);

    // Footer clear button
    const clearBtn = screen.getByText("Clear");
    await user.click(clearBtn);
    expect(mockOnSelect).toHaveBeenCalledWith(undefined);
    const input = screen.getByPlaceholderText(
      "Select date",
    ) as HTMLInputElement;
    expect(input.value).toBe("");
  });

  it("selects Today via Footer Today button", async () => {
    const user = userEvent.setup();
    render(<Calendar onSelect={mockOnSelect} />);

    const todayBtn = screen.getByText("Today");
    await user.click(todayBtn);

    const now = new Date();
    expect(mockOnSelect).toHaveBeenCalled();
    const lastCall =
      mockOnSelect.mock.calls[mockOnSelect.mock.calls.length - 1][0];
    expect(lastCall.getDate()).toBe(now.getDate());
    expect(lastCall.getMonth()).toBe(now.getMonth());
    expect(lastCall.getFullYear()).toBe(now.getFullYear());
  });

  describe("Future Logic", () => {
    it("disables next button on current month when disableFuture is true", () => {
      const today = new Date();
      const { container } = render(
        <Calendar selected={today} disableFuture={true} />,
      );

      const nextBtn = container
        .querySelector(".lucide-chevron-right")
        ?.closest("button");
      expect(nextBtn).toBeDisabled();
    });

    it("allows next button on past month", () => {
      const past = subMonths(new Date(), 1);
      const { container } = render(
        <Calendar selected={past} disableFuture={true} />,
      );

      const nextBtn = container
        .querySelector(".lucide-chevron-right")
        ?.closest("button");
      expect(nextBtn).not.toBeDisabled();
    });

    it("disables future dates in grid", () => {
      const today = new Date();
      // If today is 15th, 16th should be disabled?
      // Only if current month.
      render(<Calendar selected={today} disableFuture={true} />);

      const tomorrow = new Date();
      tomorrow.setDate(today.getDate() + 1);

      // If tomorrow is next month, we can't test it easily on this view unless we are end of month.
      // Let's assume most days have a tomorrow in same month.
      if (tomorrow.getMonth() === today.getMonth()) {
        const dayStr = tomorrow.getDate().toString();
        const dayBtn = screen
          .getAllByRole("button", { name: dayStr })
          .find((b) => !b.classList.contains("opacity-50")); // Current month day

        // Check if disabled
        if (dayBtn) expect(dayBtn).toBeDisabled();
      }
    });

    it("disables future months in month view", async () => {
      const user = userEvent.setup();
      const today = new Date();
      render(<Calendar selected={today} disableFuture={true} />);

      // Go to months view
      const currentMonthBtn = screen.getByText(format(today, "MMMM"));
      await user.click(currentMonthBtn);

      // Next month should be disabled?
      const nextMonth = addMonths(today, 1);
      const nextMonthName = format(nextMonth, "MMM");

      // Only if next month is truly future (it is).
      const nextMonthBtn = screen.getByRole("button", { name: nextMonthName });
      expect(nextMonthBtn).toBeDisabled();
    });
  });
});
