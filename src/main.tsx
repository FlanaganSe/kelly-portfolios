import { render } from "preact";
import { Router } from "wouter";
import App from "./App";
import "./styles.css";

const rootElement = document.getElementById("app");

if (rootElement && !rootElement.innerHTML) {
  render(
    <Router>
      <App />
    </Router>,
    rootElement
  );
}
