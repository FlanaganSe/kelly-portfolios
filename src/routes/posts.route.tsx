import { useEffect, useState } from "preact/hooks";
import { Link } from "wouter";
import { fetchPosts, type PostType } from "../posts";

export default function PostsComponent() {
  const [posts, setPosts] = useState<PostType[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPosts().then((data) => {
      setPosts(data);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <div className="p-2">Loading posts...</div>;
  }

  return (
    <div className="p-2 flex gap-2">
      <ul className="list-disc pl-4">
        {[...posts, { id: "i-do-not-exist", title: "Non-existent Post" }].map((post) => {
          return (
            <li key={post.id} className="whitespace-nowrap">
              <Link href={`/posts/${post.id}`} className="block py-1 text-blue-600 hover:opacity-75">
                <div>{post.title.substring(0, 20)}</div>
              </Link>
            </li>
          );
        })}
      </ul>
      <hr />
      <div>Select a post.</div>
    </div>
  );
}
