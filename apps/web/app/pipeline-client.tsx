"use client";

import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell, Legend,
  LineChart, Line,
} from "recharts";
import { saveDashboard, loadDashboard } from "./store";
import type { TrendData, TopicCandidate, TopicResult, ScenarioOutput, ResearchSession } from "./store";

const SECTION_LABELS: Record<number, string> = { 0: "Hook (오프닝)", 1: "문제 제기 (현상)", 2: "핵심 분석 (데이터 연결)", 3: "경제 연계 (거시 관점)", 4: "부동산 전망 & 대응" };
const PIE_COLORS = ["#0E1E3A", "#10B981", "#3B82F6", "#E6B43C"];
const LINE_COLORS = ["#0E1E3A", "#3B82F6", "#E6B43C"];
const PERIODS = [
  { value: "today", label: "오늘" },
  { value: "3d", label: "최근 3일" },
  { value: "7d", label: "최근 7일" },
  { value: "30d", label: "최근 30일" },
  { value: "custom", label: "사용자 지정" },
];

type TrendSourceFilter = "all" | "naver" | "google" | "youtube";
const TREND_SOURCE_TABS: { id: TrendSourceFilter; label: string }[] = [
  { id: "all", label: "전체" },
  { id: "naver", label: "네이버" },
  { id: "google", label: "구글" },
  { id: "youtube", label: "유튜브" },
];
const SOURCE_SHORT_LABELS: Record<string, string> = { naver: "네이버", google: "구글", youtube: "유튜브" };

function compactUrl(raw?: string) {
  if (!raw) return "";
  try {
    const url = new URL(raw);
    const host = url.hostname.replace(/^www\./, "");
    if (host.includes("news.google.com")) return "news.google.com · 기사 링크";
    if (host.includes("youtube.com") || host.includes("youtu.be")) return `${host} · 영상 링크`;
    const path = url.pathname && url.pathname !== "/" ? `${url.pathname.split("/").filter(Boolean).slice(0, 2).join("/")}…` : "";
    return path ? `${host}/${path}` : host;
  } catch {
    return raw.length > 42 ? `${raw.slice(0, 39)}…` : raw;
  }
}

function formatViews(n: number) {
  if (n >= 10000) return `${(n / 10000).toFixed(1)}만`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}천`;
  return String(n);
}
function formatDate(raw: string | undefined) {
  if (!raw) return "";
  if (/\d+\s*(일|시간|분|개월|년) 전/.test(raw)) return raw;
  try {
    const d = new Date(raw);
    return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, "0")}`;
  } catch { return raw.slice(0, 10); }
}
function hookLabel(type?: string) {
  const labels: Record<string, string> = { warning: "경고형", question: "질문형", opportunity: "기회형", informational: "정보형" };
  return labels[type ?? ""] ?? type ?? "";
}
function patternLabel(pattern: string) {
  const labels: Record<string, string> = { risk_warning: "위기", question_hook: "질문", opportunity_signal: "기회", numbered: "숫자", expert_authority: "전문가", checklist: "체크리스트", short_title: "짧은제목", emotional_punctuation: "감정부호" };
  return labels[pattern] ?? pattern;
}

type PipelineView = "dashboard" | "trends" | "topics" | "scenario";
type ProductionDraft = { title: string; meta: string; status: string };

export default function PipelineClient({ view = "dashboard" }: { view?: PipelineView }) {
  const [trends, setTrends] = useState<TrendData | null>(null);
  const [loadingTrend, setLoadingTrend] = useState(false);
  const [selectedTrendSource, setSelectedTrendSource] = useState<TrendSourceFilter>("all");
  const [selectedIssues, setSelectedIssues] = useState<string[]>([]);
  const [period, setPeriod] = useState("7d");
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");

  const [intent, setIntent] = useState("");
  const [mustTags, setMustTags] = useState<string[]>([]);
  const [mustInput, setMustInput] = useState("");

  const [topics, setTopics] = useState<TopicResult | null>(null);
  const [loadingTopic, setLoadingTopic] = useState(false);

  const [scenario, setScenario] = useState<ScenarioOutput | null>(null);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [selectedTopicArchetype, setSelectedTopicArchetype] = useState<TopicCandidate["archetype"] | null>(null);
  const [loadingScenario, setLoadingScenario] = useState(false);

  const [researchMode, setResearchMode] = useState<"url" | "category">("category");
  const [researchUrl, setResearchUrl] = useState("");
  const [researchCategory, setResearchCategory] = useState("부동산");
  const [research, setResearch] = useState<ResearchSession | null>(null);
  const [selectedArticleIds, setSelectedArticleIds] = useState<string[]>([]);
  const [selectedVideoIds, setSelectedVideoIds] = useState<string[]>([]);
  const [loadingResearch, setLoadingResearch] = useState(false);
  const [showAllKeywords, setShowAllKeywords] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [productionEdits, setProductionEdits] = useState<Record<string, ProductionDraft>>({});
  const [hiddenProductionKeys, setHiddenProductionKeys] = useState<string[]>([]);
  const [selectedProductionKey, setSelectedProductionKey] = useState<string>("new-video");
  const [editingProductionKey, setEditingProductionKey] = useState<string | null>(null);
  const [productionDraft, setProductionDraft] = useState<ProductionDraft>({ title: "", meta: "", status: "" });
  const [deleteProductionKey, setDeleteProductionKey] = useState<string | null>(null);

  // 페이지 로드 시 세션 복원
  useEffect(() => {
    const saved = loadDashboard();
    if (saved) {
      setTrends(saved.trends);
      setSelectedIssues(saved.selectedIssues);
      setIntent(saved.intent);
      setMustTags(saved.mustTags);
      setTopics(saved.topics);
      setSelectedTopic(saved.selectedTopic);
      setSelectedTopicArchetype(saved.selectedTopicArchetype ?? null);
      setScenario(saved.scenario);
      setPeriod(saved.period);
      setResearchMode(saved.researchMode ?? "category");
      setResearchUrl(saved.researchUrl ?? "");
      setResearchCategory(saved.researchCategory ?? "부동산");
      setResearch(saved.research ?? null);
      setSelectedArticleIds(saved.selectedArticleIds ?? []);
      setSelectedVideoIds(saved.selectedVideoIds ?? []);
      setProductionEdits(saved.productionEdits ?? {});
      setHiddenProductionKeys(saved.hiddenProductionKeys ?? []);

      const sessionId = saved.research?.session_id;
      if (sessionId) {
        fetch(`/api/research/sessions/${sessionId}`)
          .then((r) => (r.ok ? r.json() : null))
          .then((data) => { if (data) setResearch(data); })
          .catch(() => {});
        fetch(`/api/scenarios/workspace/${sessionId}`)
          .then((r) => (r.ok ? r.json() : null))
          .then((data) => {
            if (data) {
              setSelectedTopic(data.selected_topic);
              setSelectedTopicArchetype(data.scenario?.archetype ?? null);
              setSelectedArticleIds(data.selected_article_ids ?? []);
              setSelectedVideoIds(data.selected_video_ids ?? []);
              setScenario(data.scenario ?? null);
            }
          })
          .catch(() => {});
      }
    }
  }, []);

  // 상태 변경 시 자동 저장
  useEffect(() => {
    saveDashboard({ trends, selectedIssues, intent, mustTags, topics, selectedTopic, selectedTopicArchetype, scenario, period, researchMode, researchUrl, researchCategory, research, selectedArticleIds, selectedVideoIds, productionEdits, hiddenProductionKeys });
  }, [trends, selectedIssues, intent, mustTags, topics, selectedTopic, selectedTopicArchetype, scenario, period, researchMode, researchUrl, researchCategory, research, selectedArticleIds, selectedVideoIds, productionEdits, hiddenProductionKeys]);

  async function scanTrends() {
    setLoadingTrend(true);
    setError(null);
    try {
      let url = `/api/trends?period=${period}`;
      if (period === "custom" && customStart && customEnd) url += `&start=${customStart}&end=${customEnd}`;
      const r = await fetch(url);
      if (!r.ok) throw new Error(`Trend API: ${r.status}`);
      setShowAllKeywords(false);
      setTrends(await r.json());
    } catch (e) { setError((e as Error).message); }
    finally { setLoadingTrend(false); }
  }

  function toggleIssue(title: string) {
    setSelectedIssues((prev) => prev.includes(title) ? prev.filter((t) => t !== title) : [...prev, title]);
  }
  function addMust(tag: string) {
    const t = tag.trim();
    if (t && !mustTags.includes(t)) setMustTags([...mustTags, t]);
    setMustInput("");
  }

  async function runResearch() {
    setLoadingResearch(true);
    setError(null);
    try {
      const payload = selectedIssues.length > 0
        ? { mode: "trend", category: researchCategory, selected_articles: selectedIssues, trend_keywords: trends?.keywords.slice(0, 20) ?? [] }
        : researchMode === "url"
          ? { mode: "url", url: researchUrl, category: researchCategory }
          : { mode: "category", category: researchCategory };
      const r = await fetch("/api/research/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!r.ok) throw new Error(`Research API: ${r.status}`);
      const data = await r.json();
      setResearch(data);
      setSelectedArticleIds([]);
      setSelectedVideoIds([]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoadingResearch(false);
    }
  }


  function toggleVideo(id: string) {
    setSelectedVideoIds((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);
  }

  async function analyze() {
    setLoadingTopic(true); setError(null); setTopics(null); setScenario(null); setSelectedTopic(null);
    try {
      const r = await fetch("/api/topics", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_intent: intent,
          must_include: mustTags,
          current_issues: [
            ...selectedIssues,
            ...(research?.articles.filter((a) => selectedArticleIds.includes(a.id)).map((a) => `[ARTICLE] ${a.title}`) ?? []),
            ...(research?.videos.filter((v) => selectedVideoIds.includes(v.id)).map((v) => `[VIDEO] ${v.title}`) ?? []),
          ],
          trend_keywords: [
            ...(trends?.keywords.slice(0, 15) ?? []),
            ...((research?.source.keywords ?? []).slice(0, 10)),
          ],
        }),
      });
      if (!r.ok) throw new Error(`Topic API: ${r.status}`);
      setTopics(await r.json());
      setSelectedTopic(null);
      setSelectedTopicArchetype(null);
    } catch (e) { setError((e as Error).message); }
    finally { setLoadingTopic(false); }
  }

  function selectTopic(topic: string, archetype?: TopicCandidate["archetype"]) {
    setSelectedTopic(topic);
    setSelectedTopicArchetype(archetype ?? topics?.selected_archetype ?? "판단형");
    setScenario(null);
  }

  async function generateScenario() {
    if (!selectedTopic) return;
    setLoadingScenario(true); setError(null);
    try {
      const r = await fetch("/api/scenarios", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: selectedTopic,
          archetype: selectedTopicArchetype ?? topics?.selected_archetype ?? "판단형",
          keywords: mustTags,
          selected_articles: research?.articles.filter((a) => selectedArticleIds.includes(a.id)) ?? [],
          selected_videos: research?.videos.filter((v) => selectedVideoIds.includes(v.id)) ?? [],
          target_duration_min: 10,
          target_duration_max: 12,
          session_id: research?.session_id ?? undefined,
        }),
      });
      if (!r.ok) throw new Error(`Scenario API: ${r.status}`);
      const data = await r.json();
      setScenario(data);
      saveDashboard({ trends, selectedIssues, intent, mustTags, topics, selectedTopic, selectedTopicArchetype, scenario: data, period, researchMode, researchUrl, researchCategory, research, selectedArticleIds, selectedVideoIds, productionEdits, hiddenProductionKeys });
      window.location.href = "/scenario";
    } catch (e) { setError((e as Error).message); }
    finally { setLoadingScenario(false); }
  }

  function totalScore(s: TopicCandidate["score"]) {
    return s.popularity + s.economy + s.realestate + s.virality + s.richgo_fit + s.discussion;
  }

  function labelTone(label?: TopicCandidate["decision_label"]) {
    switch (label) {
      case "scale": return "bg-emerald-50 text-emerald-700 border-emerald-200";
      case "iterate": return "bg-blue-50 text-blue-700 border-blue-200";
      case "stop": return "bg-rose-50 text-rose-700 border-rose-200";
      default: return "bg-slate-100 text-slate-500 border-slate-200";
    }
  }

  function beginProductionEdit(item: ProductionDraft & { key: string }) {
    setSelectedProductionKey(item.key);
    setEditingProductionKey(item.key);
    setDeleteProductionKey(null);
    setProductionDraft({ title: item.title, meta: item.meta, status: item.status });
  }

  function saveProductionEdit() {
    if (!editingProductionKey) return;
    setProductionEdits((prev) => ({
      ...prev,
      [editingProductionKey]: {
        title: productionDraft.title.trim() || "제목 없음",
        meta: productionDraft.meta.trim() || "설명 없음",
        status: productionDraft.status.trim() || "대기",
      },
    }));
    setEditingProductionKey(null);
  }

  function deleteSelectedProduction() {
    if (!deleteProductionKey) return;
    setHiddenProductionKeys((prev) => prev.includes(deleteProductionKey) ? prev : [...prev, deleteProductionKey]);
    setSelectedProductionKey("new-video");
    setDeleteProductionKey(null);
    setEditingProductionKey(null);
  }

  function restoreProductions() {
    setHiddenProductionKeys([]);
    setDeleteProductionKey(null);
  }

  const selectedSourceCount = selectedArticleIds.length + selectedVideoIds.length + selectedIssues.length;
  const trendSections = trends?.source_sections ?? [];
  const allTrendSourceItems = trendSections.flatMap((section) =>
    section.items.map((item, index) => ({
      ...item,
      itemKey: `${section.id}-${index}-${item.title}`,
      sourceId: section.id,
      sourceLabel: SOURCE_SHORT_LABELS[section.id] ?? section.label,
    }))
  );
  const filteredTrendSourceItems = selectedTrendSource === "all"
    ? allTrendSourceItems
    : allTrendSourceItems.filter((item) => item.sourceId === selectedTrendSource);
  const displayedTrendSourceItems = selectedIssues.length > 0
    ? filteredTrendSourceItems.filter((item) => selectedIssues.includes(item.title))
    : filteredTrendSourceItems;
  const activeTrendKeywords = Array.from(new Set(
    trendSections
      .filter((section) => selectedTrendSource === "all" || section.id === selectedTrendSource)
      .flatMap((section) => section.keywords)
  )).slice(0, 16);
  const activeTrendTitle = selectedTrendSource === "all" ? "전체 트렌드" : `${SOURCE_SHORT_LABELS[selectedTrendSource]} 트렌드`;
  const activeTrendSubtext = selectedIssues.length > 0
    ? `체크한 항목 ${displayedTrendSourceItems.length}건만 표시 중`
    : `${selectedTrendSource === "all" ? "네이버·구글·유튜브" : SOURCE_SHORT_LABELS[selectedTrendSource]} 항목 ${displayedTrendSourceItems.length}건`;
  const trendKeywordRows = trends?.keyword_map?.keywords ?? [];
  const displayedTrendKeywordRows = showAllKeywords ? trendKeywordRows : trendKeywordRows.slice(0, 10);
  const keywordFrequencyRows = trends?.charts?.keyword_frequency?.slice(0, 10) ?? [];
  const keywordChartHeight = Math.max(300, keywordFrequencyRows.length * 32);
  const trendLineKeywords = trends?.charts?.top3_keywords ?? [];
  const trendLineRows = trends?.charts?.top3_timeline ?? [];
  const trendCorrelationRows = (trends?.keyword_map?.correlations?.slice(0, 12) ?? []).map((row) => ({
    pair: `${row.source} × ${row.target}`,
    score: Number((row.score * 100).toFixed(1)),
    cluster: row.cluster,
  }));
  const trendClusters = trends?.keyword_map?.clusters ?? [];
  const benchmarkTopByChannel = trends
    ? Object.values(trends.benchmarks.reduce<Record<string, TrendData["benchmarks"][number]>>((acc, item) => {
      const key = item.channel || "채널 미상";
      if (!acc[key] || item.views > acc[key].views) acc[key] = item;
      return acc;
    }, {})).sort((a, b) => b.views - a.views)
    : [];

  if (view === "dashboard") {
    const baseProductions: (ProductionDraft & { key: string; href: string })[] = [
      { key: "new-video", href: "/trends", title: selectedTopic ?? "신규 영상 제작", status: scenario ? "시나리오 완료" : topics ? "주제 선정" : research ? "리서치 완료" : "대기", meta: selectedTopic ? `근거 ${selectedSourceCount}개` : "트렌드 → 주제 → 시나리오" },
      { key: "trend-issue", href: "/trends", title: "트렌드 기반 부동산 이슈", status: trends ? "트렌드 저장됨" : "미수집", meta: trends ? `${trends.period_label} · 뉴스 ${trends.news.length}건` : "트렌드분석에서 시작" },
      { key: "richgo-topic", href: "/topics", title: "리치고 가치 반영 주제", status: topics ? "후보 생성" : "준비", meta: topics ? `${topics.recommended_topics.length}개 후보` : "주제자동화에서 고도화" },
    ];
    const productions = baseProductions
      .filter((item) => !hiddenProductionKeys.includes(item.key))
      .map((item) => ({ ...item, ...(productionEdits[item.key] ?? {}) }));
    const selectedProduction = productions.find((item) => item.key === selectedProductionKey) ?? productions[0] ?? null;

    return (
      <div className="space-y-5">
        <section className="rounded-[28px] border border-white/70 bg-white/95 p-5 shadow-[0_24px_80px_-48px_rgba(15,23,42,0.35)] sm:p-8">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="inline-flex rounded-full bg-navy/5 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-navy/70">Dashboard</div>
              <h2 className="mt-4 text-2xl font-semibold tracking-[-0.03em] text-slate-950 sm:text-4xl">리치고 유튜브 제작 대시보드</h2>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500 sm:text-base">제작 리스트를 관리하고, 신규 영상 제작은 파이프라인 순서대로 진행합니다.</p>
            </div>
            <a href="/trends" className="inline-flex min-h-[52px] items-center justify-center rounded-2xl bg-navy px-5 py-3 text-sm font-semibold text-white">신규 영상 제작</a>
          </div>
        </section>

        <section className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div className="rounded-3xl border border-slate-200 bg-white p-5"><div className="text-xs font-semibold text-slate-400">제작 리스트</div><div className="mt-2 text-2xl font-semibold">{productions.length}</div></div>
          <div className="rounded-3xl border border-slate-200 bg-white p-5"><div className="text-xs font-semibold text-slate-400">선택 근거</div><div className="mt-2 text-2xl font-semibold">{selectedSourceCount}</div></div>
          <div className="rounded-3xl border border-slate-200 bg-white p-5"><div className="text-xs font-semibold text-slate-400">현재 단계</div><div className="mt-2 text-lg font-semibold">{scenario ? "시나리오" : topics ? "주제" : trends ? "트렌드" : "시작 전"}</div></div>
        </section>

        <section className="rounded-[24px] border border-slate-200/90 bg-white/95 p-5 shadow-[0_16px_40px_-32px_rgba(15,23,42,0.25)] sm:p-6">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h3 className="text-base font-semibold">제작 리스트</h3>
              {selectedProduction && <p className="mt-1 text-xs text-slate-400">선택됨: {selectedProduction.title}</p>}
            </div>
            <div className="flex gap-2 text-xs">
              {editingProductionKey ? (
                <>
                  <button onClick={saveProductionEdit} className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 font-semibold text-emerald-700">저장</button>
                  <button onClick={() => setEditingProductionKey(null)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-slate-500">취소</button>
                </>
              ) : deleteProductionKey ? (
                <>
                  <button onClick={deleteSelectedProduction} className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-1.5 font-semibold text-rose-600">삭제 확인</button>
                  <button onClick={() => setDeleteProductionKey(null)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-slate-500">취소</button>
                </>
              ) : (
                <>
                  <button disabled={!selectedProduction} onClick={() => selectedProduction && beginProductionEdit(selectedProduction)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-slate-500 disabled:opacity-40">수정</button>
                  <button disabled={!selectedProduction} onClick={() => selectedProduction && setDeleteProductionKey(selectedProduction.key)} className="rounded-lg border border-rose-100 px-3 py-1.5 text-rose-500 disabled:opacity-40">삭제</button>
                </>
              )}
              {hiddenProductionKeys.length > 0 && <button onClick={restoreProductions} className="rounded-lg border border-blue-100 px-3 py-1.5 text-blue-600">복구</button>}
            </div>
          </div>
          {editingProductionKey && (
            <div className="mt-4 grid gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:grid-cols-3">
              <label className="text-xs font-semibold text-slate-500">제목<input value={productionDraft.title} onChange={(e) => setProductionDraft((prev) => ({ ...prev, title: e.target.value }))} className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-navy" /></label>
              <label className="text-xs font-semibold text-slate-500">설명<input value={productionDraft.meta} onChange={(e) => setProductionDraft((prev) => ({ ...prev, meta: e.target.value }))} className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-navy" /></label>
              <label className="text-xs font-semibold text-slate-500">상태<input value={productionDraft.status} onChange={(e) => setProductionDraft((prev) => ({ ...prev, status: e.target.value }))} className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-navy" /></label>
            </div>
          )}
          <div className="mt-4 space-y-3">
            {productions.length === 0 && <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-5 text-sm text-slate-500">삭제된 항목만 있습니다. 복구를 누르면 기본 제작 리스트가 다시 표시됩니다.</div>}
            {productions.map((item) => (
              <button key={item.key} type="button" onClick={() => { setSelectedProductionKey(item.key); setDeleteProductionKey(null); }} className={`w-full rounded-2xl border p-4 text-left transition sm:flex sm:items-center sm:justify-between ${selectedProduction?.key === item.key ? "border-navy bg-blue-50/40" : "border-slate-200 bg-slate-50 hover:border-slate-300"}`}>
                <div>
                  <div className="text-sm font-semibold text-slate-900">{item.title}</div>
                  <div className="mt-1 text-xs text-slate-500">{item.meta}</div>
                </div>
                <div className="mt-3 inline-flex rounded-full bg-white px-3 py-1 text-xs font-semibold text-navy sm:mt-0">{item.status}</div>
              </button>
            ))}
          </div>
        </section>

        <section className="grid grid-cols-1 gap-3 lg:grid-cols-3">
          <a href="/trends" className="rounded-3xl border border-slate-200 bg-white p-5"><div className="text-xs font-semibold text-slate-400">STEP 1</div><div className="mt-2 font-semibold">트렌드분석 → 내용 저장</div><p className="mt-2 text-sm text-slate-500">네이버·구글·유튜브 신호를 분리해서 저장합니다.</p></a>
          <a href="/topics" className="rounded-3xl border border-slate-200 bg-white p-5"><div className="text-xs font-semibold text-slate-400">STEP 2</div><div className="mt-2 font-semibold">주제 자동화 및 고도화</div><p className="mt-2 text-sm text-slate-500">선정 사유와 리치고 관점을 함께 평가합니다.</p></a>
          <a href="/scenario" className="rounded-3xl border border-slate-200 bg-white p-5"><div className="text-xs font-semibold text-slate-400">STEP 3</div><div className="mt-2 font-semibold">선택 주제 시나리오</div><p className="mt-2 text-sm text-slate-500">선택된 주제로 대본과 후속 제작물을 만듭니다.</p></a>
        </section>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <section className="overflow-hidden rounded-[28px] border border-white/70 bg-white/95 shadow-[0_24px_80px_-48px_rgba(15,23,42,0.35)] backdrop-blur">
        <div className="grid gap-6 px-5 py-6 sm:px-6 lg:grid-cols-[1.35fr_0.85fr] lg:px-8 lg:py-8">
          <div className="space-y-5">
            <div className="inline-flex items-center gap-2 rounded-full bg-navy/5 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-navy/70">
              White Product Draft · Mobile First
            </div>
            <div className="space-y-3">
              <h2 className="max-w-3xl text-2xl font-semibold tracking-[-0.03em] text-slate-950 sm:text-3xl lg:text-4xl">
                리치고 유튜브 컨트롤 타워
              </h2>
              <p className="mt-4 max-w-2xl text-base leading-7 text-slate-500 sm:text-lg">
                트렌드 발굴부터 주제 선정, 시나리오 작성까지 한 화면에서 바로 실행합니다.
              </p>
            </div>

            <div className="rounded-2xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm font-medium text-blue-800">
              분석 버튼을 누르기 전에는 주제 분석을 실행하지 않습니다.
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            <div className="rounded-3xl border border-slate-200 bg-slate-50/90 p-4">
              <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">현재 단계</div>
              <div className="mt-2 text-lg font-semibold text-slate-900">{scenario ? "시나리오 완료" : topics ? "주제 선택 완료" : research ? "리서치 완료" : trends ? "트렌드 준비" : "시작 전"}</div>
              <p className="mt-2 text-sm leading-6 text-slate-500">다음 행동이 버튼 하나로 이어지게 설계했어.</p>
            </div>
            <div className="rounded-3xl border border-slate-200 bg-white p-4">
              <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">선택된 근거</div>
              <div className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-slate-950">{selectedSourceCount}</div>
              <p className="mt-2 text-sm text-slate-500">이슈 {selectedIssues.length} · 기사 {selectedArticleIds.length} · 영상 {selectedVideoIds.length}</p>
            </div>
            <div className="rounded-3xl border border-slate-200 bg-white p-4">
              <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">상태</div>
              <div className="mt-2 flex flex-wrap gap-2">
                <span className={`rounded-full px-3 py-1 text-xs font-semibold ${trends ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>트렌드</span>
                <span className={`rounded-full px-3 py-1 text-xs font-semibold ${research ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>리서치</span>
                <span className={`rounded-full px-3 py-1 text-xs font-semibold ${topics ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>주제</span>
                <span className={`rounded-full px-3 py-1 text-xs font-semibold ${scenario ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>시나리오</span>
              </div>
            </div>
          </div>
        </div>
      </section>
      {/* ═══ Section 1: 실시간 트렌드 ═══ */}
      {view === "trends" && (
      <section className="rounded-[24px] border border-slate-200/90 bg-white/95 p-5 shadow-[0_16px_40px_-32px_rgba(15,23,42,0.25)] sm:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="flex flex-col gap-3">
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-base font-semibold sm:text-lg">1. 실시간 트렌드 & 이슈 스캔</h2>
              {trends && <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-500">{trends.period_label} · 뉴스 {trends.news.length}건 · YouTube {trends.youtube.length}건</span>}
            </div>
            <p className="text-sm text-slate-500">트렌드 스캔부터 주제 후보까지 이어지는 첫 단계야. 모바일에서도 버튼이 먼저 보이게 정리했어.</p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">
            {PERIODS.map((p) => (
              <button key={p.value} onClick={() => setPeriod(p.value)}
                className={`rounded-lg px-3 py-1 text-xs font-medium transition-colors ${period === p.value ? "bg-navy text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}>
                {p.label}
              </button>
            ))}
            {period === "custom" && (
              <div className="flex items-center gap-1">
                <input type="date" value={customStart} onChange={(e) => setCustomStart(e.target.value)} className="rounded border border-slate-300 px-2 py-0.5 text-xs" />
                <span className="text-xs text-slate-400">~</span>
                <input type="date" value={customEnd} onChange={(e) => setCustomEnd(e.target.value)} className="rounded border border-slate-300 px-2 py-0.5 text-xs" />
              </div>
            )}
            <button onClick={scanTrends} disabled={loadingTrend} className="rounded-lg bg-blue-600 px-4 py-1 text-xs font-semibold text-white hover:bg-blue-700 disabled:opacity-40">
              {loadingTrend ? "스캔 중..." : "트렌드 스캔 실행"}
            </button>
          </div>
        </div>

        {loadingTrend && <div className="mt-8 py-12 text-center text-sm text-slate-400">실시간 데이터 수집 중... (네이버 뉴스 / YouTube / Naver DataLab)</div>}

        {!trends && !loadingTrend && (
          <div className="mt-8 py-12 text-center text-sm text-slate-400">기간을 선택하고 [트렌드 스캔 실행] 버튼을 클릭하세요.</div>
        )}

        {trends && (
          <div className="mt-4 space-y-5">
            <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
              <div className="mb-1 flex flex-wrap items-center gap-2 text-xs font-semibold text-slate-600">
                <span>트렌드 분석 차트</span>
                {trendLineKeywords.map((k, i) => (
                  <span key={k} className="rounded px-1.5 py-0.5 text-[10px] font-bold" style={{ backgroundColor: LINE_COLORS[i] + "20", color: LINE_COLORS[i] }}>
                    #{i + 1} {k}
                  </span>
                ))}
              </div>
              <div className="mb-1 text-[10px] text-slate-400">출처: {trends.charts.timeline_source}</div>
              {trendLineKeywords.length > 0 && trendLineRows.length > 0 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={trendLineRows} margin={{ left: 10, right: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="date" tick={{ fontSize: 9 }} interval={2} />
                    <YAxis tick={{ fontSize: 9 }} />
                    <Tooltip contentStyle={{ fontSize: 11 }} />
                    <Legend wrapperStyle={{ fontSize: 10 }} />
                    {trendLineKeywords.map((kw, i) => (
                      <Line key={kw} type="monotone" dataKey={kw} stroke={LINE_COLORS[i]} strokeWidth={2} dot={false} />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-[200px] items-center justify-center rounded-lg border border-dashed border-slate-200 bg-white text-xs text-slate-400">
                  차트 데이터가 비어 있습니다. 트렌드 스캔을 다시 실행하세요.
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.25fr_1fr]">
              <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <div className="text-xs font-semibold text-slate-600">트렌드 소스 필터</div>
                    <div className="mt-1 text-[11px] text-slate-400">전체 / 네이버 / 구글 / 유튜브만 표시하고, 체크하면 체크 항목만 보여줍니다.</div>
                  </div>
                  <div className="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap sm:items-center">
                    {TREND_SOURCE_TABS.map((tab) => (
                      <button key={tab.id} onClick={() => setSelectedTrendSource(tab.id)} className={`rounded-lg px-3 py-2 text-left text-xs font-semibold sm:py-1 ${selectedTrendSource === tab.id ? "bg-navy text-white" : "bg-white text-slate-600 border border-slate-200"}`}>
                        {tab.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="mt-4 space-y-3">
                  <div className="grid grid-cols-1 gap-3 rounded-xl border border-slate-200 bg-white p-3 sm:grid-cols-[1fr_auto]">
                    <div>
                      <div className="text-sm font-semibold text-slate-800">{activeTrendTitle}</div>
                      <div className="mt-1 text-[11px] text-slate-500">{activeTrendSubtext}</div>
                    </div>
                    <div className="text-left text-[11px] text-slate-500 sm:text-right">
                      <div className="font-semibold text-slate-700">선택 상태</div>
                      <div>{selectedIssues.length ? `선택 ${selectedIssues.length}건` : "전체 표시"}</div>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {activeTrendKeywords.map((keyword) => (
                      <span key={keyword} className="rounded-full bg-white px-2.5 py-1 text-[11px] font-medium text-slate-700 border border-slate-200">
                        #{keyword}
                      </span>
                    ))}
                  </div>

                  {selectedIssues.length > 0 && (
                    <button onClick={() => setSelectedIssues([])} className="rounded-lg border border-blue-100 bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">
                      선택 해제하고 전체 보기
                    </button>
                  )}

                  <div className="max-h-[360px] space-y-2 overflow-y-auto">
                    {displayedTrendSourceItems.length === 0 && (
                      <div className="rounded-lg border border-dashed border-slate-200 bg-white p-4 text-center text-xs text-slate-400">표시할 항목이 없습니다.</div>
                    )}
                    {displayedTrendSourceItems.map((item) => {
                      const selected = selectedIssues.includes(item.title);
                      const href = item.link || item.url;
                      return (
                        <div key={item.itemKey} className={`rounded-lg border p-3 ${selected ? "border-navy bg-blue-50" : "border-slate-200 bg-white"}`}>
                          <div className="flex items-start gap-2">
                            <button onClick={() => toggleIssue(item.title)} className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border text-[9px] ${selected ? "border-navy bg-navy text-white" : "border-slate-300"}`}>
                              {selected ? "✓" : ""}
                            </button>
                            <div className="min-w-0 flex-1">
                              <div className="flex flex-wrap items-center gap-1.5">
                                <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-600">{item.sourceLabel}</span>
                                <div className="text-xs font-medium leading-snug text-slate-800">{item.title}</div>
                              </div>
                              <div className="mt-1 flex flex-wrap items-center gap-2 text-[10px] text-slate-400">
                                {item.source && <span className="font-medium text-slate-500">{item.source}</span>}
                                {item.channel && <span className="font-medium text-slate-500">{item.channel}</span>}
                                {item.pub && <span>{formatDate(item.pub)}</span>}
                                {item.published && <span>{formatDate(item.published)}</span>}
                                {(item.views ?? 0) > 0 && <span className="font-semibold text-navy">조회 {formatViews(item.views!)}</span>}
                                {item.query && <span className="rounded bg-slate-100 px-1 py-0.5">{item.query}</span>}
                                {item.creative_analysis?.hook_type && <span className="rounded bg-amber-50 px-1 py-0.5 font-semibold text-amber-700">{hookLabel(item.creative_analysis.hook_type)}</span>}
                                {typeof item.creative_analysis?.score === "number" && <span className="rounded bg-emerald-50 px-1 py-0.5 font-semibold text-emerald-700">소재 {item.creative_analysis.score}/10</span>}
                              </div>
                              {(item.creative_analysis?.patterns?.length ?? 0) > 0 && (
                                <div className="mt-1 flex flex-wrap gap-1">
                                  {item.creative_analysis!.patterns!.slice(0, 4).map((p) => <span key={p} className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-500">{patternLabel(p)}</span>)}
                                </div>
                              )}
                              {href && (
                                <a href={href} target="_blank" rel="noreferrer" className="mt-1 block truncate text-[10px] text-blue-500 hover:underline">
                                  {compactUrl(href)}
                                </a>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  <div className="rounded-xl border border-emerald-100 bg-emerald-50 p-3">
                    <div className="mb-2 text-[11px] text-emerald-800">뉴스를 선택한 뒤 다음 단계로 넘어가 관련 유튜브를 찾습니다. 현재 선택 {selectedIssues.length}건</div>
                    <a
                      href="/topics"
                      className={`block rounded-lg px-4 py-2 text-center text-xs font-semibold ${selectedIssues.length ? "bg-emerald-600 text-white hover:bg-emerald-700" : "pointer-events-none bg-white text-slate-400"}`}
                    >
                      선택한 뉴스로 다음 단계 이동
                    </a>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                  <div className="mb-2 text-xs font-semibold text-slate-600">키워드 차트 Top 10</div>
                  <ResponsiveContainer width="100%" height={keywordChartHeight}>
                    <BarChart data={keywordFrequencyRows} layout="vertical" margin={{ left: 8, right: 10, top: 6, bottom: 6 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis type="number" tick={{ fontSize: 10 }} />
                      <YAxis type="category" dataKey="keyword" tick={{ fontSize: 10 }} width={150} interval={0} minTickGap={0} />
                      <Tooltip contentStyle={{ fontSize: 11 }} />
                      <Bar dataKey="count" fill="#0E1E3A" radius={[0, 4, 4, 0]} barSize={14} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                  <div className="mb-1 text-xs font-semibold text-slate-600">함께 자주 언급된 키워드</div>
                  <div className="mb-2 text-[10px] text-slate-400">같은 뉴스/영상 안에서 함께 나온 키워드 조합입니다.</div>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={trendCorrelationRows} layout="vertical" margin={{ left: 88, right: 12 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis type="number" tick={{ fontSize: 10 }} unit="%" />
                      <YAxis type="category" dataKey="pair" tick={{ fontSize: 9 }} width={84} />
                      <Tooltip contentStyle={{ fontSize: 11 }} formatter={(value: unknown) => `${value}%`} />
                      <Bar dataKey="score" fill="#10B981" radius={[0, 4, 4, 0]} barSize={12} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
              <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-600">키워드 순위 Top 10</span>
                  <span className="text-[10px] text-slate-400">기본 10개 · 더보기로 전체 확인</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-slate-200 text-left text-slate-500">
                        <th className="pb-2 pr-3">키워드</th>
                        <th className="pb-2 pr-3 text-right">네이버</th>
                        <th className="pb-2 pr-3 text-right">구글</th>
                        <th className="pb-2 pr-3 text-right">유튜브</th>
                        <th className="pb-2 pr-3 text-right">총합</th>
                        <th className="pb-2">클러스터</th>
                      </tr>
                    </thead>
                    <tbody>
                      {displayedTrendKeywordRows.map((row) => (
                        <tr key={row.keyword} className="border-b border-slate-100 last:border-0">
                          <td className="py-1.5 pr-3 font-medium text-slate-800">{row.keyword}</td>
                          <td className="py-1.5 pr-3 text-right text-slate-500">{row.naver}</td>
                          <td className="py-1.5 pr-3 text-right text-slate-500">{row.google}</td>
                          <td className="py-1.5 pr-3 text-right text-slate-500">{row.youtube}</td>
                          <td className="py-1.5 pr-3 text-right font-semibold text-navy">{row.count}</td>
                          <td className="py-1.5">
                            <span className="rounded-full bg-white px-2 py-0.5 text-[10px] text-slate-600 border border-slate-200">{row.cluster}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {trendKeywordRows.length > 10 && (
                  <button
                    onClick={() => setShowAllKeywords((prev) => !prev)}
                    className="mt-3 w-full rounded-lg border border-slate-200 bg-white py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                  >
                    {showAllKeywords ? "접기" : `더보기 (${trendKeywordRows.length - 10}개)`}
                  </button>
                )}
              </div>

              <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <div className="mb-2 text-xs font-semibold text-slate-600">키워드 클러스터</div>
                <div className="space-y-2">
                  {trendClusters.map((cluster) => (
                    <div key={cluster.name} className="rounded-lg border border-slate-200 bg-white p-3">
                      <div className="flex items-center justify-between">
                        <div className="text-xs font-semibold text-slate-800">{cluster.name}</div>
                        <div className="text-[10px] text-slate-400">{cluster.count}개</div>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {cluster.keywords.map((keyword) => (
                          <span key={keyword} className="rounded bg-slate-100 px-2 py-0.5 text-[10px] text-slate-600">{keyword}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <div className="mb-2 text-xs font-semibold text-slate-600">카테고리별 이슈 분포</div>
                <ResponsiveContainer width="100%" height={240}>
                  <PieChart>
                    <Pie data={trends.charts.category_distribution} cx="50%" cy="50%" outerRadius={70} dataKey="count" nameKey="category" label={false}>
                      {trends.charts.category_distribution.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                    </Pie>
                    <Tooltip contentStyle={{ fontSize: 11 }} />
                    <Legend wrapperStyle={{ fontSize: 10 }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {benchmarkTopByChannel.length > 0 && (
                <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                  <div className="mb-1 text-xs font-semibold text-slate-600">유튜브 벤치마크 채널별 최고 조회수</div>
                  <div className="mb-2 text-[10px] text-slate-400">동일 채널 반복을 막기 위해 채널당 최고 영상 1개만 표시합니다.</div>
                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={benchmarkTopByChannel.slice(0, 6)} margin={{ left: 10, right: 10, bottom: 8 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="channel" tick={{ fontSize: 9 }} interval={0} />
                      <YAxis tick={{ fontSize: 9 }} tickFormatter={formatViews} />
                      <Tooltip contentStyle={{ fontSize: 11 }} formatter={(v: unknown) => formatViews(Number(v))} />
                      <Bar dataKey="views" fill="#3B82F6" radius={[4, 4, 0, 0]} barSize={18} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          </div>
        )}
      </section>
      )}

      {/* ═══ Row 2: 입력 + 리서치 + 주제 추천 ═══ */}
      {view === "topics" && (
      <div className="space-y-5">
        <section className="rounded-[24px] border border-slate-200/90 bg-white/95 p-5 shadow-[0_16px_40px_-32px_rgba(15,23,42,0.25)] sm:p-6">
          <h2 className="text-base font-semibold">2. 선택 뉴스 기반 유튜브 찾기</h2>
          {selectedIssues.length > 0 && (
            <div className="mt-3 rounded-xl border border-emerald-100 bg-emerald-50 p-3 text-xs text-emerald-800">
              트렌드분석에서 선택한 뉴스 {selectedIssues.length}건을 기준으로 관련 유튜브 리스트를 만듭니다.
            </div>
          )}
          <div className="mt-4 flex items-center gap-2">
            <button onClick={() => setResearchMode("category")} className={`rounded-lg px-3 py-1 text-xs font-semibold ${researchMode === "category" ? "bg-navy text-white" : "bg-slate-100 text-slate-600"}`}>카테고리 기반</button>
            <button onClick={() => setResearchMode("url")} className={`rounded-lg px-3 py-1 text-xs font-semibold ${researchMode === "url" ? "bg-navy text-white" : "bg-slate-100 text-slate-600"}`}>URL 기반</button>
          </div>
          <label className="mt-4 block text-xs font-medium text-slate-500">카테고리</label>
          <select value={researchCategory} onChange={(e) => setResearchCategory(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-navy focus:outline-none">
            <option>부동산</option>
            <option>경제</option>
            <option>AI</option>
          </select>
          {researchMode === "url" && (
            <>
              <label className="mt-3 block text-xs font-medium text-slate-500">분석할 URL</label>
              <input value={researchUrl} onChange={(e) => setResearchUrl(e.target.value)} placeholder="https://..." className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-navy focus:outline-none" />
            </>
          )}
          <button disabled={loadingResearch || (selectedIssues.length === 0 && researchMode === "url" && !researchUrl)} onClick={runResearch} className="mt-4 w-full rounded-lg bg-navy py-2.5 text-sm font-semibold text-white disabled:opacity-40">
            {loadingResearch ? "유튜브 찾는 중..." : selectedIssues.length ? "선택 뉴스로 관련 유튜브 찾기" : "기사/유튜브 찾기"}
          </button>

          <label className="mt-4 block text-xs font-medium text-slate-500">사용자 의도 입력</label>
          <textarea value={intent} onChange={(e) => setIntent(e.target.value)} rows={3}
            placeholder="예: 오늘 금리/부동산 이슈를 빠르게 해설하는 영상"
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm placeholder:text-slate-400 focus:border-navy focus:outline-none" />
          <label className="mt-3 block text-xs font-medium text-slate-500">꼭 포함할 관점</label>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            {mustTags.map((t) => (
              <span key={t} className="flex items-center gap-1 rounded bg-blue-100 px-2 py-0.5 text-xs text-blue-700">
                {t} <button onClick={() => setMustTags(mustTags.filter((x) => x !== t))} className="text-blue-400 hover:text-blue-600">x</button>
              </span>
            ))}
            <input value={mustInput} onChange={(e) => setMustInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addMust(mustInput); } }}
              placeholder="Enter로 추가" className="rounded border border-slate-200 px-2 py-0.5 text-xs focus:outline-none" />
          </div>
          {error && <p className="mt-3 text-xs text-red-600">{error}</p>}
        </section>
      <div className="space-y-4">
        <section className="rounded-[24px] border border-slate-200/90 bg-white/95 p-5 shadow-[0_16px_40px_-32px_rgba(15,23,42,0.25)] sm:p-6">
          <h2 className="text-base font-semibold">3. 관련 유튜브</h2>
          {!research && <div className="mt-6 text-center text-sm text-slate-400">리서치 후 관련 유튜브를 여기서 따로 선택해.</div>}
          {research && (
            <>
              <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400">
                <span>영상 {research.videos.length}개</span>
                <span>선택 {selectedVideoIds.length}개</span>
              </div>
              <div className="mt-3 max-h-[420px] space-y-2 overflow-y-auto">
                {research.videos.length === 0 && (
                  <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 p-4 text-xs text-slate-400">
                    아직 불러온 유튜브가 없어. 이 경우는 API 키가 없거나 검색 결과가 비어있는 경우야.
                  </div>
                )}
                {research.videos.map((item) => {
                  const selected = selectedVideoIds.includes(item.id);
                  return (
                    <div key={item.id} className={`rounded-lg border p-3 ${selected ? "border-navy bg-blue-50" : "border-slate-200 bg-white"}`}>
                      <div className="flex items-start gap-2">
                        <button onClick={() => toggleVideo(item.id)} className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border text-[9px] ${selected ? "border-navy bg-navy text-white" : "border-slate-300"}`}>{selected ? "✓" : ""}</button>
                        <div className="min-w-0 flex-1">
                          <div className="text-xs font-medium text-slate-800">{item.title}</div>
                          <div className="mt-1 flex items-center gap-2 text-[10px] text-slate-400">
                            {item.channel && <span className="font-medium text-slate-500">{item.channel}</span>}
                            {(item.views ?? 0) > 0 && <span className="font-semibold text-navy">{formatViews(item.views!)}</span>}
                            {item.published_at && <span>{formatDate(item.published_at)}</span>}
                            {item.creative_analysis?.hook_type && <span className="rounded bg-amber-50 px-1 py-0.5 font-semibold text-amber-700">{hookLabel(item.creative_analysis.hook_type)}</span>}
                            {typeof item.creative_analysis?.score === "number" && <span className="rounded bg-emerald-50 px-1 py-0.5 font-semibold text-emerald-700">소재 {item.creative_analysis.score}/10</span>}
                          </div>
                          {(item.creative_analysis?.patterns?.length ?? 0) > 0 && (
                            <div className="mt-1 flex flex-wrap gap-1">
                              {item.creative_analysis!.patterns!.slice(0, 4).map((p) => <span key={p} className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-500">{patternLabel(p)}</span>)}
                            </div>
                          )}
                          {item.url && <a href={item.url} target="_blank" rel="noreferrer" className="mt-1 block truncate text-[10px] text-blue-500 hover:underline">{item.url}</a>}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </section>
      </div>

      <section className="rounded-[24px] border border-slate-200/90 bg-white/95 p-5 shadow-[0_16px_40px_-32px_rgba(15,23,42,0.25)] sm:p-6">
        <h2 className="text-base font-semibold">4. 선택 영상 분석 → 주제 만들기</h2>
        {!research && !topics && <div className="mt-6 text-center text-sm text-slate-400">관련 유튜브를 고른 뒤 분석 버튼을 눌러 우리 주제를 만듭니다.</div>}
        {research && (
          <div className="mt-3">
            <button disabled={loadingTopic || (!intent && !selectedArticleIds.length && !selectedVideoIds.length && selectedIssues.length === 0)} onClick={analyze} className="w-full rounded-lg bg-navy py-2 text-sm font-semibold text-white disabled:opacity-40">{loadingTopic ? "분석 중..." : "선택 영상 분석해서 주제 만들기"}</button>
          </div>
        )}
        {topics && (
          <div className="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-3">
            {topics.recommended_topics.map((t, i) => {
              const score = totalScore(t.score);
              const isSel = selectedTopic === t.title;
              return (
                <button
                  key={i}
                  onClick={() => selectTopic(t.title, t.archetype)}
                  className={`w-full rounded-2xl border p-4 text-left transition ${isSel ? "border-navy bg-blue-50" : "border-slate-200 bg-white hover:border-blue-200"}`}
                >
                  <div className="text-[10px] font-semibold text-slate-400">Topic {i + 1}</div>
                  <h3 className="mt-0.5 text-xs font-bold leading-snug text-navy">{t.title}</h3>
                  <div className="mt-1 text-base font-bold text-navy">Score: {score}점</div>
                  <p className="mt-1 line-clamp-2 text-[10px] text-slate-500">{t.reason}</p>
                  <div className="mt-2 grid gap-2 text-[10px] text-slate-600">
                    <div className="rounded-xl border border-slate-200 bg-slate-50 p-2">
                      <div className="font-semibold text-slate-500">가설 카드</div>
                      <p className="mt-1 line-clamp-2">{t.discovery_hypothesis || t.strategy_hypothesis || t.reason}</p>
                    </div>
                    <div className="rounded-xl border border-slate-200 bg-white p-2">
                      <div className="font-semibold text-slate-500">검증 카드</div>
                      <p className="mt-1 line-clamp-2">{(t.verification_signals ?? []).length ? (t.verification_signals ?? []).join(" · ") : "CTR / 유지율 / 댓글 / 저장 / 공유 / 전환"}</p>
                    </div>
                    <div className="rounded-xl border border-slate-200 bg-white p-2">
                      <div className="font-semibold text-slate-500">판정 라벨</div>
                      <div className={`mt-1 inline-flex rounded-full border px-2 py-0.5 font-semibold ${labelTone(t.decision_label)}`}>{t.decision_label ?? "data_missing"}</div>
                    </div>
                  </div>
                  <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                    <span className="rounded-full bg-slate-100 px-2 py-0.5">총점 {score}</span>
                    {t.archetype && <span className="rounded-full bg-amber-50 px-2 py-0.5 text-amber-700">{t.archetype}</span>}
                    {t.keywords.slice(0, 3).map((k) => <span key={k} className="rounded-full bg-slate-100 px-2 py-0.5">#{k}</span>)}
                  </div>
                  <div className={`mt-3 inline-flex rounded-lg px-3 py-1.5 text-xs font-semibold ${isSel ? "bg-navy text-white" : "border border-slate-300 text-slate-600"}`}>
                    {isSel ? "선택됨" : "선택하기"}
                  </div>
                </button>
              );
            })}
          </div>
        )}
        {topics && selectedTopic && (
          <div className="mt-4 space-y-3 rounded-2xl border border-blue-100 bg-blue-50 p-4">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <div className="text-[10px] font-semibold text-blue-500">선택된 우리 주제</div>
                <div className="mt-1 text-sm font-bold text-navy">{selectedTopic}</div>
              </div>
              <button
                onClick={generateScenario}
                disabled={loadingScenario}
                className="rounded-lg bg-navy px-4 py-2 text-sm font-semibold text-white disabled:opacity-40"
              >
                {loadingScenario ? "시나리오 생성 중..." : "시나리오 뽑기"}
              </button>
            </div>
            {(() => {
              const selected = topics.recommended_topics.find((item) => item.title === selectedTopic);
              if (!selected) return null;
              return (
                <div className="grid gap-2 text-xs text-slate-600 sm:grid-cols-3">
                  <div className="rounded-xl border border-white bg-white/80 p-3">
                    <div className="font-semibold text-slate-500">가설 카드</div>
                    <p className="mt-1 leading-relaxed">{selected.discovery_hypothesis || selected.strategy_hypothesis || selected.reason}</p>
                  </div>
                  <div className="rounded-xl border border-white bg-white/80 p-3">
                    <div className="font-semibold text-slate-500">검증 카드</div>
                    <p className="mt-1 leading-relaxed">{(selected.verification_signals ?? []).length ? (selected.verification_signals ?? []).join(" · ") : "CTR / 유지율 / 댓글 / 저장 / 공유 / 전환"}</p>
                  </div>
                  <div className="rounded-xl border border-white bg-white/80 p-3">
                    <div className="font-semibold text-slate-500">판정 라벨</div>
                    <span className={`mt-1 inline-flex rounded-full border px-2 py-0.5 text-[11px] font-semibold ${labelTone(selected.decision_label)}`}>{selected.decision_label ?? "data_missing"}</span>
                  </div>
                  <div className="rounded-xl border border-white bg-white/80 p-3 sm:col-span-3">
                    <div className="font-semibold text-slate-500">다음 루프 / 실패 기준</div>
                    <p className="mt-1 leading-relaxed">{selected.next_loop || (selected.failure_criteria ?? []).join(" · ") || "다음 루프는 선택된 영상의 실제 성과로 재검증한다."}</p>
                  </div>
                </div>
              );
            })()}
          </div>
        )}
      </section>
    </div>
      )}

      {/* ═══ Row 3: 시나리오 독립 컨테이너 ═══ */}
      {view === "scenario" && (
      <section className="rounded-[24px] border border-slate-200/90 bg-white/95 p-5 shadow-[0_16px_40px_-32px_rgba(15,23,42,0.25)] sm:p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold">5. AI 시나리오 워크스페이스</h2>
          <div className="flex items-center gap-2">
            {research?.session_id && scenario && (
              <a
                href={`/workspace/${research.session_id}`}
                className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
              >
                전체 워크스페이스 열기
              </a>
            )}
            {scenario?.archetype && <span className="rounded bg-amber-50 px-2 py-0.5 text-xs text-amber-700">{scenario.archetype}</span>}
            {scenario?.estimated_duration_min && <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-500">예상 길이 {scenario.estimated_duration_min}분</span>}
          </div>
        </div>
        {!scenario && !loadingScenario && <div className="mt-8 text-center text-sm text-slate-400">주제를 선택하면 시나리오가 이 독립 컨테이너에 생성됩니다.</div>}
        {loadingScenario && <div className="mt-8 text-center text-sm text-slate-400">시나리오 생성 중...</div>}
        {scenario && selectedTopic && (
          <div className="mt-4 space-y-5">
            <div className="rounded-xl bg-slate-50 px-4 py-3">
              <div className="text-[10px] font-semibold text-slate-400">선택 주제</div>
              <div className="mt-1 text-sm font-bold text-navy">{selectedTopic}</div>
            </div>
            {scenario.opening_title && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 p-4">
                <div className="text-xs font-semibold text-rose-500">제목 설명형 오프닝</div>
                <p className="mt-1 text-sm font-bold leading-relaxed text-rose-700">{scenario.opening_title}</p>
              </div>
            )}
            {scenario.hook_30s && (
              <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
                <div className="text-xs font-semibold text-amber-600">0~30초 Hook</div>
                <p className="mt-1 text-sm leading-relaxed text-amber-900">{scenario.hook_30s}</p>
              </div>
            )}
            {scenario.bridge_3min && (
              <div className="rounded-xl border border-blue-200 bg-blue-50 p-4">
                <div className="text-xs font-semibold text-blue-600">30초~3분 전개</div>
                <p className="mt-1 text-sm leading-relaxed text-blue-900">{scenario.bridge_3min}</p>
              </div>
            )}
            <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
              <div className="rounded-xl border border-slate-200 p-4">
                <div className="text-xs font-semibold text-slate-500">본문 섹션</div>
                <div className="mt-3 space-y-3">
                  {(scenario.body_sections?.length ? scenario.body_sections : scenario.body.map((text, i) => ({ heading: SECTION_LABELS[i + 1] ?? `섹션 ${i + 1}`, script: text }))).map((section, i) => (
                    <div key={i} className="border-l-2 border-slate-200 pl-3">
                      <div className="text-xs font-bold text-slate-700">{section.heading}</div>
                      <p className="mt-1 text-xs leading-relaxed text-slate-600">{section.script}</p>
                    </div>
                  ))}
                </div>
              </div>
              <div className="space-y-4">
                <div className="rounded-xl border border-slate-200 p-4">
                  <div className="text-xs font-semibold text-slate-500">액션 포인트</div>
                  <ul className="mt-2 space-y-1 text-xs text-slate-600 list-disc pl-4">
                    {(scenario.action_takeaways ?? []).map((item, i) => <li key={i}>{item}</li>)}
                  </ul>
                </div>
                <div className="rounded-xl border border-slate-200 p-4">
                  <div className="text-xs font-semibold text-slate-500">제목 후보</div>
                  <ul className="mt-2 space-y-1 text-xs text-slate-600 list-disc pl-4">
                    {scenario.title_candidates.map((item, i) => <li key={i}>{item}</li>)}
                  </ul>
                </div>
                <div className="rounded-xl border border-slate-200 p-4">
                  <div className="text-xs font-semibold text-slate-500">썸네일 후보</div>
                  <ul className="mt-2 space-y-1 text-xs text-slate-600 list-disc pl-4">
                    {scenario.thumbnail_candidates.map((item, i) => <li key={i}>{item}</li>)}
                  </ul>
                </div>
                {scenario.cta && (
                  <div className="rounded-xl border border-slate-200 p-4">
                    <div className="text-xs font-semibold text-slate-500">CTA</div>
                    <p className="mt-1 text-xs text-slate-600">{scenario.cta}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </section>
      )}
    </div>
  );
}
