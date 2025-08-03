import { Link, Route, Switch } from "wouter";
import AnchorComponent from "./routes/anchor";
import CalculatorComponent from "./routes/calculator";
import IndexComponent from "./routes/index";
import PostDetailComponent from "./routes/posts.$postId";
import PostsComponent from "./routes/posts.route";

export default function App() {
  return (
    <>
      <div className="bg-slate-900/95 backdrop-blur-sm border-b border-slate-700 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4 flex gap-8 items-center">
          <Link
            href="/"
            className="text-xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent"
          >
            Portfolio Optimizer
          </Link>
          <nav className="flex gap-6">
            <Link href="/" className="text-slate-300 hover:text-white transition-colors">
              Home
            </Link>
            <Link href="/calculator" className="text-slate-300 hover:text-white transition-colors">
              Calculator
            </Link>
          </nav>
        </div>
      </div>
      <Switch>
        <Route path="/" component={IndexComponent} />
        <Route path="/calculator" component={CalculatorComponent} />
        <Route path="/anchor" component={AnchorComponent} />
        <Route path="/posts" component={PostsComponent} />
        <Route path="/posts/:postId" component={PostDetailComponent} />
      </Switch>
    </>
  );
}
