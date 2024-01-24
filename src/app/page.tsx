import { SP500Graph } from "./_components/SP500Graph";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between">
      <SP500Graph />
    </main>
  );
}
