import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "리치고 자동화 대시보드",
  description: "YouTube automation — 주제/시나리오/자막/썸네일/업로드/성과",
};

const NAV_MAIN = [
  { href: "/", label: "대시보드", icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0h4" },
  { href: "/runs", label: "프로젝트", icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" },
  { href: "/content", label: "콘텐츠", icon: "M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" },
  { href: "/channels", label: "채널", icon: "M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z M21 12a9 9 0 11-18 0 9 9 0 0118 0z" },
  { href: "/settings", label: "설정", icon: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z" },
];

const NAV_BOTTOM = [
  { href: "/performance", label: "성과", icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" },
  { href: "/support", label: "고객지원", icon: "M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" },
];

function NavIcon({ d }: { d: string }) {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d={d} />
    </svg>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="flex h-screen overflow-hidden">
        <aside className="flex w-16 flex-col items-center border-r border-slate-200 bg-white py-4">
          <div className="mb-6 flex h-9 w-9 items-center justify-center rounded-lg bg-navy text-sm font-bold text-white">R</div>
          <nav className="flex flex-1 flex-col items-center gap-1">
            {NAV_MAIN.map((n) => (
              <Link key={n.label} href={n.href} className="flex w-full flex-col items-center gap-0.5 rounded-lg px-1 py-2 text-slate-500 hover:bg-slate-50 hover:text-navy">
                <NavIcon d={n.icon} />
                <span className="text-[10px] leading-tight">{n.label}</span>
              </Link>
            ))}
          </nav>
          <div className="flex flex-col items-center gap-1 border-t border-slate-100 pt-3">
            {NAV_BOTTOM.map((n) => (
              <Link key={n.label} href={n.href} className="flex w-full flex-col items-center gap-0.5 rounded-lg px-1 py-2 text-slate-400 hover:bg-slate-50 hover:text-navy">
                <NavIcon d={n.icon} />
                <span className="text-[10px] leading-tight">{n.label}</span>
              </Link>
            ))}
          </div>
        </aside>

        <div className="flex flex-1 flex-col overflow-hidden">
          <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
            <h1 className="text-lg font-semibold">YouTube 자동화프로젝트</h1>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1.5">
                <div className="h-6 w-6 rounded-full bg-navy" />
                <span className="text-sm font-medium">리치고</span>
                <svg className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
              </div>
              <div className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1.5 text-sm font-medium text-emerald-700">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                자율 실행
              </div>
              <button className="relative text-slate-400 hover:text-slate-600">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>
                <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] text-white">1</span>
              </button>
              <div className="h-8 w-8 rounded-full bg-slate-300" />
            </div>
          </header>
          <main className="flex-1 overflow-y-auto p-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
