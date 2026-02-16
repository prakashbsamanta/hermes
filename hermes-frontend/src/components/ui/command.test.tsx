import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import {
  Command,
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandShortcut,
  CommandSeparator,
} from "./command";
import "@testing-library/jest-dom";

// Mock resize observer
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock scrollIntoView
Element.prototype.scrollIntoView = vi.fn();

// Mock pointer capture methods
Element.prototype.hasPointerCapture = vi.fn(() => false);
Element.prototype.setPointerCapture = vi.fn();
Element.prototype.releasePointerCapture = vi.fn();

describe("Command Component", () => {
  it("renders CommandDialog correctly", () => {
    render(
      <CommandDialog open={true} onOpenChange={vi.fn()}>
        <CommandInput placeholder="Type a command or search..." />
        <CommandList>
          <CommandEmpty>No results found.</CommandEmpty>
          <CommandGroup heading="Suggestions">
            <CommandItem>Calendar</CommandItem>
          </CommandGroup>
        </CommandList>
      </CommandDialog>,
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Type a command or search..."),
    ).toBeInTheDocument();
  });

  it("renders CommandShortcut correctly", () => {
    render(
      <Command>
        <CommandList>
          <CommandItem>
            Profile
            <CommandShortcut>⌘P</CommandShortcut>
          </CommandItem>
        </CommandList>
      </Command>,
    );
    expect(screen.getByText("⌘P")).toBeInTheDocument();
    expect(screen.getByText("⌘P")).toHaveClass("text-xs");
  });

  it("renders CommandSeparator correctly", () => {
    const { container } = render(
      <Command>
        <CommandList>
          <CommandItem>Item 1</CommandItem>
          <CommandSeparator />
          <CommandItem>Item 2</CommandItem>
        </CommandList>
      </Command>,
    );
    expect(container.querySelector("[cmdk-separator]")).toBeInTheDocument();
  });
});
