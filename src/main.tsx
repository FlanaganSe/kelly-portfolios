import { hydrate, prerender as ssr } from "preact-iso";
import { Router } from "wouter";
import App from "./App";
import "./styles.css";

const AppWithRouter = () => (
  <Router>
    <App />
  </Router>
);

if (typeof window !== "undefined") {
  const rootElement = document.getElementById("app");
  if (rootElement) {
    hydrate(<AppWithRouter />, rootElement);
  }
}

export async function prerender(_data?: unknown) {
  const { html, ...rest } = await ssr(<AppWithRouter />);

  return { html: `<div id="app">${html}</div>`, ...rest };
}
