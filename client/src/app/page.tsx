import { SP500Graph } from "./_components/SP500Graph";

export default function Home() {
  return (
    <div>
      <SP500Graph />
      <div className="mt-2">
        <h1 className="text-2xl">What is this?</h1>
        <p>
          This is... to become v2 of my research on optimizing investment
          portfolio returns. Mathematical principals are to be used to improve
          risk-adjusted returns.
        </p>
        <div className="pt-2">
          <h1 className="text-2xl">How is this achieved?</h1>
          <p>
            Primarily by attempting to use the{" "}
            <a
              className="text-blue-600 underline hover:text-blue-400 transition"
              href="https://en.wikipedia.org/wiki/Kelly_criterion"
            >
              Kelly Criterion
            </a>
            . More on this later.......
          </p>
        </div>
      </div>
    </div>
  );
}
