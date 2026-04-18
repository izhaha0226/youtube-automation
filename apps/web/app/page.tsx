"use client";

import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell, Legend,
  LineChart, Line,
} from "recharts";
import { saveDashboard, loadDashboard } from "./store";
import type { TrendData, TopicCandidate, TopicResult, ScenarioOutput } from "./store";

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

function formatViews(n: number) {
  if (n >= 10000) return `${(n / 10000).toFixed(1)}만`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}천`;
  return String(n);
}
function formatDate(raw: string | undefined) {
  if (!raw) return "";
  try {
    const d = new Date(raw);
    return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, "0")}`;
  } catch { return raw.slice(0, 10); }
}

export default function Home() {
  const [trends, setTrends] = useState<TrendData | null>(null);
  const [loadingTrend, setLoadingTrend] = useState(false);
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
  const [loadingScenario, setLoadingScenario] = useState(false);

  const [error, setError] = useState<string | null>(null);

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
      setScenario(saved.scenario);
      setPeriod(saved.period);
    }
  }, []);

  // 상태 변경 시 자동 저장
  useEffect(() => {
    saveDashboard({ trends, selectedIssues, intent, mustTags, topics, selectedTopic, scenario, period });
  }, [trends, selectedIssues, intent, mustTags, topics, selectedTopic, scenario, period]);

  async function scanTrends() {
    setLoadingTrend(true);
    setError(null);
    try {
      let url = `/api/trends?period=${period}`;
      if (period === "custom" && customStart && customEnd) url += `&start=${customStart}&end=${customEnd}`;
      const r = await fetch(url);
      if (!r.ok) throw new Error(`Trend API: ${r.status}`);
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

  async function analyze() {
    setLoadingTopic(true); setError(null); setTopics(null); setScenario(null); setSelectedTopic(null);
    try {
      const r = await fetch("/api/topics", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_intent: intent, must_include: mustTags, current_issues: selectedIssues, trend_keywords: trends?.keywords.slice(0, 15) ?? [] }),
      });
      if (!r.ok) throw new Error(`Topic API: ${r.status}`);
      setTopics(await r.json());
    } catch (e) { setError((e as Error).message); }
    finally { setLoadingTopic(false); }
  }

  async function selectTopic(topic: string) {
    setSelectedTopic(topic); setLoadingScenario(true); setError(null);
    try {
      const r = await fetch("/api/scenarios", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, keywords: mustTags }),
      });
      if (!r.ok) throw new Error(`Scenario API: ${r.status}`);
      setScenario(await r.json());
    } catch (e) { setError((e as Error).message); }
    finally { setLoadingScenario(false); }
  }

  function totalScore(s: TopicCandidate["score"]) {
    return s.popularity + s.economy + s.realestate + s.virality + s.richgo_fit + s.discussion;
  }

  return (
    <div className="space-y-5">
      {/* ═══ Section 1: 실시간 트렌드 ═══ */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-base font-semibold">1. 실시간 트렌드 & 이슈 스캔</h2>
            {trends && <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-500">{trends.period_label} · 뉴스 {trends.news.length}건 · YouTube {trends.youtube.length}건</span>}
          </div>
          <div className="flex items-center gap-2">
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
            <button onClick={scanTrends} disabled={loadingTrend} className="rounded-lg bg-navy px-4 py-1 text-xs font-semibold text-white hover:bg-navy/90 disabled:opacity-40">
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
            {/* 30일 검색 트렌드 (Naver DataLab) */}
            {trends.charts.top3_keywords.length > 0 && trends.charts.top3_timeline.length > 0 && (
              <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <div className="mb-1 text-xs font-semibold text-slate-600">
                  네이버 검색 트렌드 (30일) —
                  {trends.charts.top3_keywords.map((k, i) => (
                    <span key={k} className="ml-1.5 rounded px-1.5 py-0.5 text-[10px] font-bold" style={{ backgroundColor: LINE_COLORS[i] + "20", color: LINE_COLORS[i] }}>
                      #{i + 1} {k}
                    </span>
                  ))}
                </div>
                <div className="mb-1 text-[10px] text-slate-400">출처: {trends.charts.timeline_source}</div>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={trends.charts.top3_timeline} margin={{ left: 10, right: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="date" tick={{ fontSize: 9 }} interval={2} />
                    <YAxis tick={{ fontSize: 9 }} />
                    <Tooltip contentStyle={{ fontSize: 11 }} />
                    <Legend wrapperStyle={{ fontSize: 10 }} />
                    {trends.charts.top3_keywords.map((kw, i) => (
                      <Line key={kw} type="monotone" dataKey={kw} stroke={LINE_COLORS[i]} strokeWidth={2} dot={false} />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Charts row */}
            <div className="grid grid-cols-3 gap-4">
              <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <div className="mb-2 text-xs font-semibold text-slate-600">명사 키워드 빈도</div>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={trends.charts.keyword_frequency.slice(0, 12)} layout="vertical" margin={{ left: 60, right: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis type="number" tick={{ fontSize: 10 }} />
                    <YAxis type="category" dataKey="keyword" tick={{ fontSize: 10 }} width={55} />
                    <Tooltip contentStyle={{ fontSize: 11 }} />
                    <Bar dataKey="count" fill="#0E1E3A" radius={[0, 4, 4, 0]} barSize={14} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <div className="mb-2 text-xs font-semibold text-slate-600">카테고리별 이슈 분포</div>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={trends.charts.category_distribution} cx="50%" cy="50%" outerRadius={70} dataKey="count" nameKey="category" label={false}>
                      {trends.charts.category_distribution.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                    </Pie>
                    <Tooltip contentStyle={{ fontSize: 11 }} />
                    <Legend wrapperStyle={{ fontSize: 10 }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <div className="mb-2 text-xs font-semibold text-slate-600">벤치마크 채널 Top 조회수</div>
                {trends.benchmarks.length > 0 ? (
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={trends.benchmarks.slice(0, 8)} margin={{ left: 10, right: 10 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="channel" tick={{ fontSize: 9 }} />
                      <YAxis tick={{ fontSize: 9 }} tickFormatter={formatViews} />
                      <Tooltip contentStyle={{ fontSize: 11 }} formatter={(v: unknown) => formatViews(Number(v))} />
                      <Bar dataKey="views" fill="#3B82F6" radius={[4, 4, 0, 0]} barSize={20} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-[200px] items-center justify-center text-xs text-slate-400">YouTube API 할당량 초과 — 내일 리셋 후 표시됩니다</div>
                )}
              </div>
            </div>

            {/* 뉴스 피드 — 출처, URL, 날짜 포함 */}
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-slate-700">뉴스 피드</span>
                  <span className="text-[10px] text-slate-400">출처: 네이버 뉴스 API</span>
                </div>
                <div className="space-y-2 max-h-[300px] overflow-y-auto">
                  {trends.news.map((item, i) => {
                    const sel = selectedIssues.includes(item.title);
                    return (
                      <div key={i} className={`rounded-lg border p-2 transition-colors ${sel ? "border-navy bg-blue-50" : "border-slate-200 bg-white hover:border-slate-300"}`}>
                        <div className="flex items-start gap-2">
                          <button onClick={() => toggleIssue(item.title)} className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border text-[9px] ${sel ? "border-navy bg-navy text-white" : "border-slate-300"}`}>
                            {sel ? "✓" : ""}
                          </button>
                          <div className="min-w-0 flex-1">
                            <div className="text-xs font-medium leading-snug text-slate-800">{item.title}</div>
                            <div className="mt-0.5 flex items-center gap-2 text-[10px] text-slate-400">
                              {item.source && <span className="font-medium text-slate-500">{item.source}</span>}
                              {item.pub && <span>{formatDate(item.pub)}</span>}
                              {item.query && <span className="rounded bg-slate-100 px-1 py-0.5">{item.query}</span>}
                            </div>
                            {item.link && <a href={item.link} target="_blank" rel="noreferrer" className="mt-0.5 block truncate text-[10px] text-blue-500 hover:underline">{item.link}</a>}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-slate-700">YouTube 인기 영상</span>
                  <span className="text-[10px] text-slate-400">출처: YouTube Data API v3</span>
                </div>
                <div className="space-y-2 max-h-[300px] overflow-y-auto">
                  {trends.youtube.length === 0 && <div className="py-8 text-center text-xs text-slate-400">YouTube API 할당량 초과 — 내일 리셋 후 표시됩니다</div>}
                  {trends.youtube.map((item, i) => {
                    const sel = selectedIssues.includes(item.title);
                    return (
                      <div key={i} className={`rounded-lg border p-2 transition-colors ${sel ? "border-navy bg-blue-50" : "border-slate-200 bg-white hover:border-slate-300"}`}>
                        <div className="flex items-start gap-2">
                          <button onClick={() => toggleIssue(item.title)} className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border text-[9px] ${sel ? "border-navy bg-navy text-white" : "border-slate-300"}`}>
                            {sel ? "✓" : ""}
                          </button>
                          <div className="min-w-0 flex-1">
                            <div className="text-xs font-medium leading-snug text-slate-800">{item.title}</div>
                            <div className="mt-0.5 flex items-center gap-2 text-[10px] text-slate-400">
                              {item.channel && <span className="font-medium text-slate-500">{item.channel}</span>}
                              {(item.views ?? 0) > 0 && <span className="font-semibold text-navy">{formatViews(item.views!)}</span>}
                              {(item.likes ?? 0) > 0 && <span>♥ {formatViews(item.likes!)}</span>}
                              {item.published && <span>{formatDate(item.published)}</span>}
                            </div>
                            {item.url && <a href={item.url} target="_blank" rel="noreferrer" className="mt-0.5 block truncate text-[10px] text-blue-500 hover:underline">{item.url}</a>}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* 벤치마크 테이블 */}
            {trends.benchmarks.length > 0 && (
              <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-slate-600">YouTube 벤치마크 — 경쟁 채널 인기 영상 (조회수 순)</span>
                  <span className="text-[10px] text-slate-400">출처: YouTube Data API v3 · 삼프로TV / 김작가TV / 부동산김사부 / 리치고</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-slate-200 text-left text-slate-500">
                        <th className="pb-1.5 pr-2 w-6">#</th>
                        <th className="pb-1.5 pr-3">채널</th>
                        <th className="pb-1.5 pr-3">영상 제목</th>
                        <th className="pb-1.5 pr-3 text-right">조회수</th>
                        <th className="pb-1.5 pr-3 text-right">좋아요</th>
                        <th className="pb-1.5 pr-3 text-right">댓글</th>
                        <th className="pb-1.5">발행일</th>
                        <th className="pb-1.5" />
                      </tr>
                    </thead>
                    <tbody>
                      {trends.benchmarks.slice(0, 12).map((v, i) => {
                        const sel = selectedIssues.includes(v.title);
                        return (
                          <tr key={i} className="border-b border-slate-100 last:border-0 hover:bg-white/60">
                            <td className="py-1.5 pr-2 font-bold text-slate-400">{i + 1}</td>
                            <td className="py-1.5 pr-3 font-medium text-slate-700">{v.channel}</td>
                            <td className="max-w-[280px] py-1.5 pr-3">
                              <a href={`https://youtube.com/watch?v=${v.video_id}`} target="_blank" rel="noreferrer" className="truncate block text-slate-600 hover:text-blue-600 hover:underline" title={v.title}>{v.title}</a>
                            </td>
                            <td className="py-1.5 pr-3 text-right font-semibold text-navy">{formatViews(v.views)}</td>
                            <td className="py-1.5 pr-3 text-right text-slate-500">{formatViews(v.likes)}</td>
                            <td className="py-1.5 pr-3 text-right text-slate-500">{formatViews(v.comments)}</td>
                            <td className="py-1.5 text-slate-400">{formatDate(v.published)}</td>
                            <td className="py-1.5 pl-2">
                              <button onClick={() => toggleIssue(v.title)} className={`rounded px-2 py-0.5 text-[10px] ${sel ? "bg-navy text-white" : "bg-slate-200 text-slate-600 hover:bg-slate-300"}`}>
                                {sel ? "선택됨" : "참고"}
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </section>

      {/* ═══ Row 2: 사용자 입력 + AI 주제 + 시나리오 ═══ */}
      <div className="grid grid-cols-[1fr_1fr_380px] gap-5">
        <section className="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="text-base font-semibold">2. 프로젝트 입력</h2>
          <label className="mt-4 block text-xs font-medium text-slate-500">사용자 의도 입력</label>
          <textarea value={intent} onChange={(e) => setIntent(e.target.value)} rows={3}
            placeholder="부동산 시장 폭락 시 시나리오 분석..."
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
          {selectedIssues.length > 0 && (
            <div className="mt-3">
              <div className="text-xs font-medium text-slate-500">선택된 이슈 ({selectedIssues.length}건)</div>
              <div className="mt-1 flex flex-wrap gap-1">
                {selectedIssues.map((s) => (
                  <span key={s} className="flex items-center gap-1 rounded bg-navy/10 px-2 py-0.5 text-[10px] text-navy">
                    {s.slice(0, 25)}...
                    <button onClick={() => toggleIssue(s)} className="text-navy/40 hover:text-navy">x</button>
                  </span>
                ))}
              </div>
            </div>
          )}
          <button disabled={loadingTopic || (!intent && selectedIssues.length === 0)} onClick={analyze}
            className="mt-5 w-full rounded-lg bg-navy py-2.5 text-sm font-semibold text-white disabled:opacity-40">
            {loadingTopic ? "분석 중..." : "분석 실행"}
          </button>
          {error && <p className="mt-3 text-xs text-red-600">{error}</p>}
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="text-base font-semibold">3. AI 주제 추천</h2>
          {!topics && !loadingTopic && <div className="mt-6 text-center text-sm text-slate-400">트렌드에서 이슈 선택 + 의도 입력 후<br />분석 실행하면 주제가 추천됩니다.</div>}
          {loadingTopic && <div className="mt-6 text-center text-sm text-slate-400">선택한 트렌드 기반 주제 분석 중...</div>}
          {topics && (
            <div className="mt-3 grid grid-cols-2 gap-3">
              {topics.recommended_topics.map((t, i) => {
                const score = totalScore(t.score);
                const isSel = selectedTopic === t.title;
                return (
                  <div key={i} className={`rounded-xl border p-3 ${isSel ? "border-navy bg-blue-50" : "border-slate-200 hover:border-slate-300"}`}>
                    <div className="text-[10px] font-semibold text-slate-400">Topic {i + 1}</div>
                    <h3 className="mt-0.5 text-xs font-bold leading-snug text-navy">{t.title}</h3>
                    <div className="mt-1 text-base font-bold text-navy">Score: {score}점</div>
                    <p className="mt-1 line-clamp-2 text-[10px] text-slate-500">{t.reason}</p>
                    <button onClick={() => selectTopic(t.title)} disabled={loadingScenario}
                      className={`mt-2 w-full rounded-lg py-1.5 text-xs font-semibold ${isSel ? "bg-navy text-white" : "border border-slate-300 text-slate-600 hover:bg-slate-50"} disabled:opacity-40`}>
                      {isSel ? "선택됨" : "선택하기"}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="text-base font-semibold">4. AI 시나리오 생성</h2>
          {!scenario && !loadingScenario && <div className="mt-8 text-center text-sm text-slate-400">주제를 선택하면<br />시나리오가 생성됩니다.</div>}
          {loadingScenario && <div className="mt-8 text-center text-sm text-slate-400">시나리오 생성 중...</div>}
          {scenario && selectedTopic && (
            <div className="mt-3">
              <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm font-medium">{selectedTopic}</div>
              <div className="mt-4 space-y-4">
                {[scenario.hook, ...scenario.body, scenario.conclusion].map((text, i) => (
                  <div key={i} className="border-l-2 border-slate-200 pl-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-700">{i + 1}. {SECTION_LABELS[i] ?? `섹션 ${i + 1}`}</span>
                      <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-400">AI Generated</span>
                    </div>
                    <p className="mt-1 text-xs leading-relaxed text-slate-600">{text}</p>
                  </div>
                ))}
                {scenario.cta && (
                  <div className="border-l-2 border-slate-200 pl-3">
                    <span className="text-xs font-semibold text-slate-700">CTA</span>
                    <p className="mt-1 text-xs text-slate-600">{scenario.cta}</p>
                  </div>
                )}
              </div>
              <div className="mt-5 flex gap-2">
                <button className="flex-1 rounded-lg bg-navy py-2 text-sm font-semibold text-white">생성하기</button>
                <button className="flex-1 rounded-lg border border-slate-300 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50">수정하기</button>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
