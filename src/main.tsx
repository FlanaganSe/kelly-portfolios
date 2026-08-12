import { render } from "solid-js/web";
import App from "~/App";
import "~/styles.css";

const root = document.getElementById("app");

if (!root) {
  throw new Error("Root element #app not found");
}

// `index.html` carries a title and description so the tab reads correctly before
// this bundle runs. @solidjs/meta keeps its own tags as singletons but cannot
// claim static ones, so leaving them would give the page two <title> elements
// and the browser honours the first. Drop them here; App re-declares both
// through <Title> and <Meta> in the same synchronous render, so nothing flashes.
for (const stale of document.head.querySelectorAll('title, meta[name="description"]')) {
  stale.remove();
}

render(() => <App />, root);
