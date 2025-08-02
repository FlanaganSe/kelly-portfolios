export type PostType = {
  id: string;
  title: string;
  body: string;
};

export const fetchPost = async (postId: string) => {
  console.info(`Fetching post with id ${postId}...`);
  await new Promise((r) => setTimeout(r, 500));

  return fetch(`https://jsonplaceholder.typicode.com/posts/${postId}`)
    .then((res) => res.json() as Promise<PostType>)
    .then((data) => data);
};

export const fetchPosts = async () => {
  console.info("Fetching posts...");
  await new Promise((r) => setTimeout(r, 500));
  return fetch("https://jsonplaceholder.typicode.com/posts")
    .then((response) => response.json() as Promise<Array<PostType>>)
    .then((data) => data.slice(0, 10));
};
