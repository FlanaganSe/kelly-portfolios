import Link from "next/link";

export const Header = () => {
  return (
    <header className="flex top-0 gap-8 p-8 justify-between items-center">
      <div className="h-full flex flex-col gap-4 justify-between">
        <nav className="flex gap-8 justify-between">
          <Link href="/">
            <div className="hover:underline transition">About</div>
          </Link>
          <Link href="research">
            <div className="hover:underline transition">Research</div>
          </Link>
          <Link href="blog">
            <div className="hover:underline transition">Blog</div>
          </Link>
          <Link href="now">
            <div className="hover:underline transition">Now</div>
          </Link>
        </nav>
      </div>
      <Link href="now">
        <div className="hover:underline transition">Login</div>
      </Link>
    </header>
  );
};
