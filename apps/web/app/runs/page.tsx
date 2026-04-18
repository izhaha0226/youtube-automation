"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8787";

type Run = {
  run_id: string;
  intent: string;
  status: string;
  created_at: string;
  meta: Record<string, unknown>;
};

type RunDetail = Run & {
  channel: string;
  updated_at: string;
  topics: { id: string; title: string; reason: string; score: number; risk: string; selected: boolean }[];
  scenarios: { id: string; title: string; hook: string; body: string[]; conclusion: string; cta: string; title_candidates: string[]; thumbnail_candidates: string[] }[];
  reviews: { id: string; passed: boolean; issues: string[]; fix_suggestions: string[] }[];
  assets: { id: string; kind: string; path: string; meta: Record<string, unknown> }[];
  uploads: { id: string; video_id: string | null; url: string | null; status: string }[];
};

const STATUS_STYLE: Record<string, string> = {
  done: "bg-emerald-100 text-emerald-700",
  pending: "bg-slate-100 text-slate-500",
  topic: "bg-yellow-100 text-yellow-700",
  scenario: "bg-blue-100 text-blue-700",
  review: "bg-purple-100 text-purple-700",
  failed: "bg-rose-100 text-rose-700",
};

const STATUS_LABEL: Record<string, string> = {
  pending: "대기중",
  topic: "주제선정",
  scenario: "시나리오",
  review: "검수중",
  done: "완료",
  failed: "실패",
};

export default function RunsPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<RunDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editIntent, setEditIntent] = useState("");
  const [editStatus, setEditStatus] = useState("");
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  useEffect(() => {
    fetchRuns();
  }, []);

  async function fetchRuns() {
    setLoading(true);
    try {
      const r = await fetch(`${API}/pipeline/runs?limit=50`);
      if (r.ok) setRuns(await r.json());
    } catch { /* */ }
    setLoading(false);
  }

  async function openDetail(runId: string) {
    setDetailLoading(true);
    setEditing(false);
    try {
      const r = await fetch(`${API}/pipeline/runs/${runId}`);
      if (r.ok) {
        const d = await r.json();
        setSelected(d);
        setEditIntent(d.intent);
        setEditStatus(d.status);
      }
    } catch { /* */ }
    setDetailLoading(false);
  }

  async function saveEdit() {
    if (!selected) return;
    try {
      const r = await fetch(`${API}/pipeline/runs/${selected.run_id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ intent: editIntent, status: editStatus }),
      });
      if (r.ok) {
        setEditing(false);
        await openDetail(selected.run_id);
        await fetchRuns();
      }
    } catch { /* */ }
  }

  async function deleteRun(runId: string) {
    try {
      const r = await fetch(`${API}/pipeline/runs/${runId}`, { method: "DELETE" });
      if (r.ok) {
        setSelected(null);
        setDeleteConfirm(null);
        await fetchRuns();
      }
    } catch { /* */ }
  }

  return (
    <div className="grid gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">프로젝트 관리</h2>
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-500">{runs.length}건</span>
          <button onClick={fetchRuns} className="rounded-lg bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-200 transition">새로고침</button>
        </div>
      </div>

      {/* 상태 요약 */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-6">
        {["pending", "topic", "scenario", "review", "done", "failed"].map((st) => {
          const cnt = runs.filter((r) => r.status === st).length;
          return (
            <div key={st} className="rounded-xl border border-slate-200 bg-white p-3 text-center shadow-sm">
              <div className={`mx-auto mb-1 inline-block rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLE[st] ?? "bg-slate-100 text-slate-500"}`}>{STATUS_LABEL[st] ?? st}</div>
              <div className="text-lg font-bold text-slate-800">{cnt}</div>
            </div>
          );
        })}
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_1.2fr]">
        {/* 목록 */}
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 bg-slate-50 px-4 py-2.5 text-xs font-medium text-slate-500">실행 이력</div>
          {loading ? (
            <div className="p-10 text-center text-sm text-slate-400">로딩중...</div>
          ) : runs.length === 0 ? (
            <div className="p-10 text-center text-sm text-slate-400">실행 이력이 없습니다. 홈에서 파이프라인을 실행하세요.</div>
          ) : (
            <div className="max-h-[600px] overflow-y-auto divide-y divide-slate-100">
              {runs.map((r) => (
                <button
                  key={r.run_id}
                  onClick={() => openDetail(r.run_id)}
                  className={`w-full text-left px-4 py-3 hover:bg-blue-50 transition ${selected?.run_id === r.run_id ? "bg-blue-50 border-l-2 border-blue-500" : ""}`}
                >
                  <div className="flex items-center gap-2">
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${STATUS_STYLE[r.status] ?? "bg-slate-100 text-slate-500"}`}>{STATUS_LABEL[r.status] ?? r.status}</span>
                    <span className="font-mono text-[10px] text-slate-400">{r.run_id.slice(0, 8)}</span>
                  </div>
                  <div className="mt-1 text-sm text-slate-700 truncate">{r.intent || "(의도 없음)"}</div>
                  <div className="mt-0.5 text-[10px] text-slate-400">{new Date(r.created_at).toLocaleString("ko-KR")}</div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* 상세 */}
        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 bg-slate-50 px-4 py-2.5 text-xs font-medium text-slate-500">상세 정보</div>
          {detailLoading ? (
            <div className="p-10 text-center text-sm text-slate-400">로딩중...</div>
          ) : !selected ? (
            <div className="p-10 text-center text-sm text-slate-400">좌측 목록에서 프로젝트를 선택하세요</div>
          ) : (
            <div className="p-4 space-y-5 max-h-[600px] overflow-y-auto">
              {/* 기본 정보 + 수정/삭제 */}
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLE[selected.status] ?? "bg-slate-100 text-slate-500"}`}>{STATUS_LABEL[selected.status] ?? selected.status}</span>
                    <span className="font-mono text-xs text-slate-400">{selected.run_id}</span>
                  </div>
                  {!editing ? (
                    <p className="text-sm text-slate-700">{selected.intent || "(의도 없음)"}</p>
                  ) : (
                    <div className="space-y-2 mt-2">
                      <input value={editIntent} onChange={(e) => setEditIntent(e.target.value)} className="w-full rounded-lg border border-slate-200 px-3 py-1.5 text-sm" placeholder="의도" />
                      <select value={editStatus} onChange={(e) => setEditStatus(e.target.value)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm">
                        {["pending", "topic", "scenario", "review", "done", "failed"].map((s) => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
                      </select>
                    </div>
                  )}
                  <div className="mt-1 text-[10px] text-slate-400">생성: {new Date(selected.created_at).toLocaleString("ko-KR")} | 수정: {new Date(selected.updated_at).toLocaleString("ko-KR")}</div>
                </div>
                <div className="flex gap-2 shrink-0">
                  {editing ? (
                    <>
                      <button onClick={saveEdit} className="rounded-lg bg-blue-500 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-600 transition">저장</button>
                      <button onClick={() => setEditing(false)} className="rounded-lg bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-200 transition">취소</button>
                    </>
                  ) : (
                    <>
                      <button onClick={() => setEditing(true)} className="rounded-lg bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-200 transition">수정</button>
                      {deleteConfirm === selected.run_id ? (
                        <div className="flex gap-1">
                          <button onClick={() => deleteRun(selected.run_id)} className="rounded-lg bg-rose-500 px-3 py-1.5 text-xs font-medium text-white hover:bg-rose-600 transition">확인 삭제</button>
                          <button onClick={() => setDeleteConfirm(null)} className="rounded-lg bg-slate-100 px-2 py-1.5 text-xs text-slate-600">취소</button>
                        </div>
                      ) : (
                        <button onClick={() => setDeleteConfirm(selected.run_id)} className="rounded-lg bg-rose-50 px-3 py-1.5 text-xs font-medium text-rose-600 hover:bg-rose-100 transition">삭제</button>
                      )}
                    </>
                  )}
                </div>
              </div>

              {/* 주제 */}
              {selected.topics.length > 0 && (
                <section>
                  <h4 className="text-xs font-semibold text-slate-500 mb-2">주제 후보 ({selected.topics.length})</h4>
                  <div className="space-y-2">
                    {selected.topics.map((t) => (
                      <div key={t.id} className={`rounded-lg border p-3 text-sm ${t.selected ? "border-blue-300 bg-blue-50" : "border-slate-200 bg-slate-50"}`}>
                        <div className="flex items-center gap-2">
                          {t.selected && <span className="rounded bg-blue-500 px-1.5 py-0.5 text-[10px] text-white font-medium">선택됨</span>}
                          <span className="font-medium text-slate-800">{t.title}</span>
                          <span className="ml-auto text-xs text-slate-400">점수 {t.score} | 리스크 {t.risk}</span>
                        </div>
                        <p className="mt-1 text-xs text-slate-500">{t.reason}</p>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* 시나리오 */}
              {selected.scenarios.length > 0 && (
                <section>
                  <h4 className="text-xs font-semibold text-slate-500 mb-2">시나리오 ({selected.scenarios.length})</h4>
                  {selected.scenarios.map((sc) => (
                    <div key={sc.id} className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm space-y-2">
                      <div className="font-medium text-slate-800">{sc.title}</div>
                      <div><span className="text-xs font-medium text-slate-500">Hook:</span> <span className="text-xs text-slate-700">{sc.hook}</span></div>
                      {sc.body.length > 0 && (
                        <div>
                          <span className="text-xs font-medium text-slate-500">본문:</span>
                          <ul className="mt-1 list-disc list-inside text-xs text-slate-600 space-y-0.5">{sc.body.map((b, i) => <li key={i}>{b}</li>)}</ul>
                        </div>
                      )}
                      <div><span className="text-xs font-medium text-slate-500">결론:</span> <span className="text-xs text-slate-700">{sc.conclusion}</span></div>
                      <div><span className="text-xs font-medium text-slate-500">CTA:</span> <span className="text-xs text-slate-700">{sc.cta}</span></div>
                      {sc.title_candidates.length > 0 && (
                        <div><span className="text-xs font-medium text-slate-500">제목 후보:</span> <span className="text-xs text-slate-600">{sc.title_candidates.join(" / ")}</span></div>
                      )}
                      {sc.thumbnail_candidates.length > 0 && (
                        <div><span className="text-xs font-medium text-slate-500">썸네일 후보:</span> <span className="text-xs text-slate-600">{sc.thumbnail_candidates.join(" / ")}</span></div>
                      )}
                    </div>
                  ))}
                </section>
              )}

              {/* 검수 */}
              {selected.reviews.length > 0 && (
                <section>
                  <h4 className="text-xs font-semibold text-slate-500 mb-2">검수 결과</h4>
                  {selected.reviews.map((rv) => (
                    <div key={rv.id} className={`rounded-lg border p-3 text-sm ${rv.passed ? "border-emerald-200 bg-emerald-50" : "border-rose-200 bg-rose-50"}`}>
                      <span className={`text-xs font-medium ${rv.passed ? "text-emerald-700" : "text-rose-700"}`}>{rv.passed ? "통과" : "미통과"}</span>
                      {rv.issues.length > 0 && <ul className="mt-1 list-disc list-inside text-xs text-slate-600">{rv.issues.map((is, i) => <li key={i}>{is}</li>)}</ul>}
                      {rv.fix_suggestions.length > 0 && <ul className="mt-1 list-disc list-inside text-xs text-blue-600">{rv.fix_suggestions.map((fs, i) => <li key={i}>{fs}</li>)}</ul>}
                    </div>
                  ))}
                </section>
              )}

              {/* 에셋 */}
              {selected.assets.length > 0 && (
                <section>
                  <h4 className="text-xs font-semibold text-slate-500 mb-2">생성 에셋 ({selected.assets.length})</h4>
                  <div className="rounded-lg border border-slate-200 overflow-hidden">
                    <table className="w-full text-xs">
                      <thead className="bg-slate-50 text-slate-500"><tr><th className="p-2 text-left">종류</th><th className="p-2 text-left">경로</th></tr></thead>
                      <tbody>{selected.assets.map((a) => <tr key={a.id} className="border-t border-slate-100"><td className="p-2 font-medium">{a.kind}</td><td className="p-2 font-mono text-slate-500 truncate max-w-[200px]">{a.path}</td></tr>)}</tbody>
                    </table>
                  </div>
                </section>
              )}

              {/* 업로드 */}
              {selected.uploads.length > 0 && (
                <section>
                  <h4 className="text-xs font-semibold text-slate-500 mb-2">업로드</h4>
                  {selected.uploads.map((u) => (
                    <div key={u.id} className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs space-y-1">
                      <div><span className="font-medium text-slate-500">상태:</span> <span className={u.status === "done" ? "text-emerald-600" : "text-slate-600"}>{u.status}</span></div>
                      {u.video_id && <div><span className="font-medium text-slate-500">Video ID:</span> <span className="font-mono">{u.video_id}</span></div>}
                      {u.url && <div><a href={u.url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">{u.url}</a></div>}
                    </div>
                  ))}
                </section>
              )}

              {/* 메타 */}
              {Object.keys(selected.meta).length > 0 && (
                <section>
                  <h4 className="text-xs font-semibold text-slate-500 mb-2">메타데이터</h4>
                  <pre className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-[10px] text-slate-600 overflow-auto max-h-40">{JSON.stringify(selected.meta, null, 2)}</pre>
                </section>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
