import Link from "next/link";

export function TopNav() {
  return (
    <header className="topnav">
      <Link href="/" className="topnav__brand">
        DOCMORPH <span>AI</span>
      </Link>
      <nav aria-label="Main">
        <Link href="/" aria-current="page">
          Projects
        </Link>
        <Link href="/#templates">Templates</Link>
        <Link href="/#library">Library</Link>
      </nav>
      <span className="muted">Account</span>
    </header>
  );
}
