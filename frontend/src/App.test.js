import { render, screen } from "@testing-library/react";
import App from "./App";

test("renders sign in", async () => {
  render(<App />);
  expect(await screen.findByRole("heading", { name: /sign in/i })).toBeInTheDocument();
});
