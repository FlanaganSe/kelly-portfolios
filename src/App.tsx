import { Link, Route, Switch } from "wouter";
import AnchorComponent from "./routes/anchor";
import IndexComponent from "./routes/index";
import PostDetailComponent from "./routes/posts.$postId";
import PostsComponent from "./routes/posts.route";

export default function App() {
  return (
    <>
      <div className="p-2 flex gap-2 text-lg border-b">
        <Link href="/" className="hover:font-bold">
          Home
        </Link>
        <Link href="/posts" className="hover:font-bold">
          Posts
        </Link>
        <Link href="/anchor" className="hover:font-bold">
          Anchor
        </Link>
      </div>
      <hr />
      <Switch>
        <Route path="/" component={IndexComponent} />
        <Route path="/anchor" component={AnchorComponent} />
        <Route path="/posts" component={PostsComponent} />
        <Route path="/posts/:postId" component={PostDetailComponent} />
      </Switch>
    </>
  );
}
