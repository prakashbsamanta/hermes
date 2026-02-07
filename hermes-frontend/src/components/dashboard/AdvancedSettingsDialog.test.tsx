import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { AdvancedSettingsDialog } from "./AdvancedSettingsDialog";

// Mock UI components that rely on Radix/Framer to simplify testing
vi.mock("@/components/ui/dialog", () => ({
  // eslint-disable-next-line
  Dialog: ({ children }: any) => <div>{children}</div>,
  // eslint-disable-next-line
  DialogTrigger: ({ children }: any) => <div>{children}</div>,
  // eslint-disable-next-line
  DialogContent: ({ children }: any) => <div>{children}</div>,
  // eslint-disable-next-line
  DialogHeader: ({ children }: any) => <div>{children}</div>,
  // eslint-disable-next-line
  DialogTitle: ({ children }: any) => <h2>{children}</h2>,
}));

describe("AdvancedSettingsDialog", () => {
  it("renders trigger button", () => {
    const props = {
      slippage: 0.1,
      setSlippage: vi.fn(),
      commission: 0.0,
      setCommission: vi.fn(),
    };
    render(<AdvancedSettingsDialog {...props} />);
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("renders input fields with correct values", () => {
    const props = {
      slippage: 0.5,
      setSlippage: vi.fn(),
      commission: 1.5,
      setCommission: vi.fn(),
    };
    render(<AdvancedSettingsDialog {...props} />);

    const slippageInput = screen.getByLabelText(
      "Slippage (%)",
    ) as HTMLInputElement;
    const commissionInput = screen.getByLabelText(
      "Commission ($)",
    ) as HTMLInputElement;

    expect(slippageInput.value).toBe("0.5");
    expect(commissionInput.value).toBe("1.5");
  });

  it("updates slippage on change", () => {
    const setSlippage = vi.fn();
    const props = {
      slippage: 0.1,
      setSlippage,
      commission: 0.0,
      setCommission: vi.fn(),
    };
    render(<AdvancedSettingsDialog {...props} />);

    const input = screen.getByLabelText("Slippage (%)");
    fireEvent.change(input, { target: { value: "0.2" } });
    expect(setSlippage).toHaveBeenCalledWith(0.2);
  });

  it("updates commission on change", () => {
    const setCommission = vi.fn();
    const props = {
      slippage: 0.1,
      setSlippage: vi.fn(),
      commission: 0.0,
      setCommission,
    };
    render(<AdvancedSettingsDialog {...props} />);

    const input = screen.getByLabelText("Commission ($)");
    fireEvent.change(input, { target: { value: "2.0" } });
    expect(setCommission).toHaveBeenCalledWith(2.0);
  });
});
