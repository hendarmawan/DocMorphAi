"use client";

import { Plus } from "lucide-react";
import Link from "next/link";
import { Logo } from "./Logo";
import { ThemeToggle } from "./ThemeToggle";

export function TopNav({ onNew }: { onNew?: () => void }) {
  return (
    <header className="topnav">
      <div className="topnav__inner">
        <Logo />
        <nav aria-label="Main" className="topnav__links">
          <Link href="/" aria-current="page">
            Documents
          </Link>
          <Link href="/#templates">Templates</Link>
          <Link href="/#how-it-works">How it works</Link>
        </nav>
        <div className="topnav__actions">
          <ThemeToggle />
          {onNew && (
            <button type="button" className="dm-btn dm-btn--primary dm-btn--sm" onClick={onNew}>
              <Plus size={15} aria-hidden /> New document
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
