import "@testing-library/jest-dom";

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock pointer capture methods
Element.prototype.setPointerCapture = () => {};
Element.prototype.releasePointerCapture = () => {};
