import { Welcome } from "../welcome/welcome";
import type { Route } from "./+types/home";

export function meta({ ...props }: Route.MetaArgs) {
  console.log(props);
  return [{ title: "New React Router App" }, { name: "description", content: "Welcome to React Router!" }];
}

export default function Home() {
  return <Welcome />;
}
