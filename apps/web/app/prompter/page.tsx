"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { loadDashboard } from "../store";
import type { ScenarioOutput } from "../store";

function buildPrompterSections(scenario: ScenarioOutput | null) {
  if (!scenario) return [];
  const sections: { title: string; text: string }[] = [];

  if (scenario.opening_title) sections.push({ title: "제목 설명형 오프닝", text: scenario.opening_title });
  if (scenario.hook_30s) sections.push({ title: "0~30초 Hook", text: scenario.hook_30s });
  if (scenario.bridge_3min) sections.push({ title: "30초~3분 전개", text: scenario.bridge_3min });
  if (scenario.opening) sections.push({ title: "오프닝", text: scenario.opening });

  const bodySections = scenario.body_sections?.length
    ? scenario.body_sections
    : scenario.body.map((script, index) => ({ heading: `본문 ${index + 1}`, script }));
  bodySections.forEach((section, index) => {
    sections.push({ title: section.heading || `본문 ${index + 1}`, text: section.script });
  });

  if (scenario.conclusion) sections.push({ title: "결론", text: scenario.conclusion });
  if (scenario.cta) sections.push({ title: "CTA", text: scenario.cta });

  return sections.filter((section) => section.text?.trim());
}

export default function PrompterPage() {
  const [scenario, setScenario] = useState<ScenarioOutput | null>(null);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [scrollSpeed, setScrollSpeed] = useState(38);
  const [fontSize, setFontSize] = useState(40);
  const [mirrorMode, setMirrorMode] = useState(false);
  const [visibleSectionCount, setVisibleSectionCount] = useState(3);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const frameRef = useRef<number | null>(null);
  const lastTickRef = useRef<number | null>(null);

  useEffect(() => {
    const saved = loadDashboard();
    setScenario(saved?.scenario ?? null);
    setSelectedTopic(saved?.selectedTopic ?? null);
  }, []);

  const sections = useMemo(() => buildPrompterSections(scenario), [scenario]);
  const visibleSections = useMemo(() => sections.slice(0, visibleSectionCount), [sections, visibleSectionCount]);
  const hasMoreSections = visibleSectionCount < sections.length;

  useEffect(() => {
    setVisibleSectionCount(Math.min(3, Math.max(1, sections.length || 1)));
    resetScroll();
    setIsPlaying(false);
  }, [sections.length]);

  const ensureSectionsLoadedForViewport = useCallback(() => {
    const el = scrollRef.current;
    if (!el || visibleSectionCount >= sections.length) return;
    const remainingPx = el.scrollHeight - (el.scrollTop + el.clientHeight);
    if (remainingPx < el.clientHeight * 1.2) {
      setVisibleSectionCount((count) => Math.min(sections.length, count + 1));
    }
  }, [sections.length, visibleSectionCount]);

  useEffect(() => {
    if (!isPlaying) {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
      lastTickRef.current = null;
      return;
    }

    const step = (timestamp: number) => {
      if (!scrollRef.current) return;
      if (lastTickRef.current === null) lastTickRef.current = timestamp;
      const deltaSeconds = Math.min((timestamp - lastTickRef.current) / 1000, 0.08);
      lastTickRef.current = timestamp;
      scrollRef.current.scrollTop += scrollSpeed * deltaSeconds;
      ensureSectionsLoadedForViewport();

      const reachedEnd = scrollRef.current.scrollTop + scrollRef.current.clientHeight >= scrollRef.current.scrollHeight - 8 && visibleSectionCount >= sections.length;
      if (reachedEnd) {
        setIsPlaying(false);
        return;
      }
      frameRef.current = requestAnimationFrame(step);
    };

    frameRef.current = requestAnimationFrame(step);
    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
    };
  }, [ensureSectionsLoadedForViewport, isPlaying, scrollSpeed, sections.length, visibleSectionCount]);

  function resetScroll() {
    if (scrollRef.current) scrollRef.current.scrollTop = 0;
    lastTickRef.current = null;
  }

  function handlePromptScroll() {
    ensureSectionsLoadedForViewport();
  }

  return (
    <div className="fixed inset-0 z-[80] flex flex-col bg-slate-950 text-white">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 bg-slate-950/95 px-4 py-3 backdrop-blur sm:px-6">
        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-white">프롬프터 모드</p>
          <h1 className="truncate text-lg font-bold sm:text-2xl">{selectedTopic ?? "저장된 시나리오"}</h1>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs sm:text-sm">
          <button
            onClick={() => setIsPlaying((prev) => !prev)}
            disabled={sections.length === 0}
            className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 font-bold text-white shadow-lg shadow-white/10 disabled:opacity-40"
          >
            <span aria-hidden>{isPlaying ? "⏸" : "▶"}</span>
            {isPlaying ? "일시정지" : "재생"}
          </button>
          <button onClick={resetScroll} className="rounded-full border border-white/15 px-3 py-2 font-semibold text-white/80 hover:bg-white/10">처음으로</button>
          <button onClick={() => setMirrorMode((prev) => !prev)} className="rounded-full border border-white/15 px-3 py-2 font-semibold text-white/80 hover:bg-white/10">{mirrorMode ? "일반" : "미러"}</button>
          <Link href="/scenario" className="rounded-full border border-white/15 px-3 py-2 font-semibold text-white/80 hover:bg-white/10">닫기</Link>
        </div>
      </header>

      <div className="grid gap-3 border-b border-white/10 bg-slate-900/80 px-4 py-3 text-xs text-white/75 sm:grid-cols-2 sm:px-6">
        <label className="flex items-center gap-3">
          <span className="w-20 font-semibold text-white">올라가는 속도</span>
          <input className="w-full accent-white" type="range" min="12" max="120" step="2" value={scrollSpeed} onChange={(e) => setScrollSpeed(Number(e.target.value))} />
          <span className="w-16 text-right tabular-nums">{scrollSpeed}px/s</span>
        </label>
        <label className="flex items-center gap-3">
          <span className="w-20 font-semibold text-white">글자 크기</span>
          <input className="w-full accent-white" type="range" min="28" max="72" step="2" value={fontSize} onChange={(e) => setFontSize(Number(e.target.value))} />
          <span className="w-12 text-right tabular-nums">{fontSize}px</span>
        </label>
      </div>

      <main ref={scrollRef} onScroll={handlePromptScroll} className="flex-1 overflow-y-auto scroll-smooth px-5 text-white sm:px-10 lg:px-20">
        <div className="mx-auto max-w-5xl py-[45vh]">
          {sections.length === 0 ? (
            <div className="rounded-3xl border border-white/10 bg-white/5 p-8 text-center">
              <p className="text-xl font-semibold">저장된 시나리오가 없습니다.</p>
              <p className="mt-3 text-sm text-white/60">시나리오를 먼저 생성한 뒤 프롬프터 모드를 실행하세요.</p>
              <Link href="/scenario" className="mt-6 inline-flex rounded-full border border-white/20 bg-white/10 px-5 py-2 text-sm font-bold text-white">시나리오로 돌아가기</Link>
            </div>
          ) : (
            <article className={mirrorMode ? "scale-x-[-1]" : ""} style={{ fontSize: `${fontSize}px` }}>
              {visibleSections.map((section, index) => (
                <section key={`${section.title}-${index}`} className="mb-16 rounded-[32px] border border-white/10 bg-white/[0.03] p-8 text-white shadow-[0_30px_80px_-50px_rgba(255,255,255,0.22)]">
                  <div className="mb-6 inline-flex rounded-full border border-white/15 bg-white/5 px-4 py-1 text-sm font-bold uppercase tracking-[0.2em] text-white">{section.title}</div>
                  <p className="whitespace-pre-wrap break-keep font-semibold leading-[1.75] tracking-[-0.03em] text-white">{section.text}</p>
                </section>
              ))}
              {hasMoreSections && (
                <div className="mb-16 rounded-[28px] border border-white/10 bg-white/[0.03] p-6 text-center text-base font-semibold text-white">
                  더 읽는 중 · 섹션 단위로 이어서 불러옵니다 ({visibleSectionCount}/{sections.length})
                </div>
              )}
            </article>
          )}
        </div>
      </main>
    </div>
  );
}
