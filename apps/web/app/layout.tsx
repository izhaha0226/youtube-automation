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

function NavLinks({ items }: { items: typeof NAV_MAIN | typeof NAV_BOTTOM }) {
  return (
    <>
      {items.map((n) => (
        <Link
          key={n.label}
          href={n.href}
          className="flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm font-medium text-slate-500 transition hover:bg-slate-100 hover:text-navy lg:flex-col lg:gap-1.5 lg:px-2 lg:py-3"
        >
          <NavIcon d={n.icon} />
          <span className="leading-tight lg:text-[11px]">{n.label}</span>
        </Link>
      ))}
    </>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-[#f5f7fb] text-slate-900">
        <div className="flex min-h-screen">
          <aside className="hidden w-[92px] flex-col border-r border-slate-200/80 bg-white/90 px-3 py-5 shadow-sm backdrop-blur lg:flex">
            <div className="mb-8 flex h-11 w-11 items-center justify-center rounded-2xl bg-navy text-sm font-bold text-white shadow-sm">R</div>
            <nav className="flex flex-1 flex-col gap-2">
              <NavLinks items={NAV_MAIN} />
            </nav>
            <div className="mt-6 flex flex-col gap-2 border-t border-slate-100 pt-4">
              <NavLinks items={NAV_BOTTOM} />
            </div>
          </aside>

          <div className="flex min-h-screen min-w-0 flex-1 flex-col">
            <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/92 backdrop-blur">
              <div className="flex items-center justify-between gap-4 px-4 py-4 sm:px-6">
                <div className="min-w-0">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-navy text-sm font-bold text-white shadow-sm lg:hidden">R</div>
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">Richgo Automation</p>
                      <h1 className="truncate text-base font-semibold text-slate-900 sm:text-lg">YouTube 자동화 프로젝트</h1>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 sm:gap-3">
                  <div className="hidden items-center gap-2 rounded-full bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-700 sm:flex">
                    <div className="h-6 w-6 rounded-full bg-navy" />
                    리치고
                  </div>
                  <div className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700 sm:text-sm">
                    <span className="h-2 w-2 rounded-full bg-emerald-500" />
                    자율 실행
                  </div>
                  <div className="hidden h-9 w-9 rounded-full bg-slate-200 sm:block" />
                </div>
              </div>

              <div className="overflow-x-auto border-t border-slate-100 px-4 py-2 lg:hidden">
                <nav className="flex w-max gap-2">
                  <NavLinks items={NAV_MAIN} />
                  <NavLinks items={NAV_BOTTOM} />
                </nav>
              </div>
            </header>

            <main className="flex-1 overflow-y-auto px-4 py-5 sm:px-6 sm:py-6">
              <div className="mx-auto w-full max-w-[1600px]">{children}</div>
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
