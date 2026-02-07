import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Button } from "./button";
import { Card, CardHeader, CardContent } from "./card";
import { Input } from "./input";
import { Label } from "./label";
import { Switch } from "./switch";
import { ScrollArea } from "./scroll-area";

describe("UI Components", () => {
  it("renders Button", () => {
    render(<Button>Click Me</Button>);
    expect(screen.getByText("Click Me")).toBeInTheDocument();
  });

  it("renders Card", () => {
    render(
      <Card>
        <CardHeader>Header</CardHeader>
        <CardContent>Content</CardContent>
      </Card>,
    );
    expect(screen.getByText("Header")).toBeInTheDocument();
    expect(screen.getByText("Content")).toBeInTheDocument();
  });

  it("renders Input", () => {
    render(<Input placeholder="Type here" />);
    expect(screen.getByPlaceholderText("Type here")).toBeInTheDocument();
  });

  it("renders Label", () => {
    render(<Label>Label Text</Label>);
    expect(screen.getByText("Label Text")).toBeInTheDocument();
  });

  it("renders Switch", () => {
    render(<Switch />);
    expect(screen.getByRole("switch")).toBeInTheDocument();
  });

  it("renders ScrollArea", () => {
    render(<ScrollArea>Scrollable Content</ScrollArea>);
    expect(screen.getByText("Scrollable Content")).toBeInTheDocument();
  });
});
