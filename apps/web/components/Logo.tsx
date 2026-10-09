import Link from "next/link";

export function LogoMark({ size = 24 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" className="logo-mark">
      <defs>
        <linearGradient id="dm-logo" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
          <stop stopColor="#6366f1" />
          <stop offset="0.55" stopColor="#a855f7" />
          <stop offset="1" stopColor="#ec4899" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="8" fill="url(#dm-logo)" />
      <path d="M10 8.5h6.5a7.5 7.5 0 0 1 0 15H10z" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinejoin="round" />
      <path d="M14 13.5h3.2a2.5 2.5 0 0 1 0 5H14z" fill="#fff" />
    </svg>
  );
}

export function Logo() {
  return (
    <Link href="/" className="logo" aria-label="DocMorph AI home">
      <LogoMark />
      <span>
        DocMorph <em>AI</em>
      </span>
    </Link>
  );
}
