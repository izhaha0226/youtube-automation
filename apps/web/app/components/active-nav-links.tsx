"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type NavItem = {
  href: string;
  label: string;
  icon: string;
};

function NavIcon({ d }: { d: string }) {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d={d} />
    </svg>
  );
}

function isActivePath(pathname: string, href: string) {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export default function ActiveNavLinks({ items }: { items: NavItem[] }) {
  const pathname = usePathname() || "/";

  return (
    <>
      {items.map((n) => {
        const active = isActivePath(pathname, n.href);
        return (
          <Link
            key={n.label}
            href={n.href}
            aria-current={active ? "page" : undefined}
            className={`flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm font-medium transition lg:flex-col lg:gap-1.5 lg:px-2 lg:py-3 ${
              active
                ? "bg-navy text-white shadow-[0_12px_30px_-18px_rgba(14,30,58,0.85)] ring-1 ring-navy/10"
                : "text-slate-500 hover:bg-slate-100 hover:text-navy"
            }`}
          >
            <NavIcon d={n.icon} />
            <span className="leading-tight lg:text-[11px]">{n.label}</span>
          </Link>
        );
      })}
    </>
  );
}
