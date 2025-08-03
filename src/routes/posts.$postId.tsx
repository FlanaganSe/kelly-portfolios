import { useEffect, useState } from "preact/hooks";
import { useParams } from "wouter";
import { fetchPost, type PostType } from "../posts";

export default function PostDetailComponent() {
  const params = useParams();
  const postId = params.postId;
  const [post, setPost] = useState<PostType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!postId) return;

    setLoading(true);
    setError(null);

    fetchPost(postId)
      .then((data) => {
        setPost(data);
        setLoading(false);
      })
      .catch(() => {
        setError("Post not found");
        setLoading(false);
      });
  }, [postId]);

  if (loading) {
    return <div className="p-2">Loading post...</div>;
  }

  if (error) {
    return <div className="p-2 text-red-600">{error}</div>;
  }

  if (!post) {
    return <div className="p-2">Post not found</div>;
  }

  return (
    <div className="p-2 space-y-2">
      <h4 className="text-xl font-bold underline">{post.title}</h4>
      <div className="text-sm">{post.body}</div>
    </div>
  );
}
