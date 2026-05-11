"use client";

import { useState } from "react";
import StatusModal from "../../components/status-modal";

type NarrationOutput = {
  text_ko: string;
  sentences: string[];
  audio_path?: string | null;
  timeline: { idx: number; text: string; start_ms: number; end_ms: number }[];
};

export default function WorkspaceNarrationAction({
  sessionId,
  initialNarration,
}: {
  sessionId: string;
  initialNarration?: NarrationOutput | null;
}) {
  const [loading, setLoading] = useState(false);
  const [narration, setNarration] = useState<NarrationOutput | null>(initialNarration ?? null);
  const [error, setError] = useState<string | null>(null);

  async function runNarration() {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`/api/scenarios/workspace/${sessionId}/narrate`, { method: "POST" });
      if (!r.ok) throw new Error(`Narration API: ${r.status}`);
      setNarration(await r.json());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">나레이션</h3>
          <p className="mt-1 text-xs text-slate-500">현재 시나리오를 구어체 나레이션으로 변환하고, 가능하면 오디오 경로까지 생성해.</p>
        </div>
        <button
          onClick={runNarration}
          disabled={loading}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-40"
        >
          {loading ? "생성 중..." : narration ? "다시 생성" : "나레이션 생성"}
        </button>
      </div>

      <StatusModal open={Boolean(error)} title="작업을 진행할 수 없습니다" message={error} tone="error" onClose={() => setError(null)} />

      {narration && (
        <div className="mt-4 space-y-4">
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-center justify-between gap-2">
              <div className="text-xs font-semibold text-slate-500">생성 결과</div>
              <span className="text-[11px] text-slate-400">
                문장 {narration.sentences.length}개 · 타임라인 {narration.timeline.length}개
              </span>
            </div>
            {narration.audio_path ? (
              <p className="mt-2 break-all text-[11px] text-emerald-700">오디오: {narration.audio_path}</p>
            ) : (
              <p className="mt-2 text-[11px] text-amber-600">오디오는 아직 없고, 타임라인만 생성된 상태야.</p>
            )}
          </div>

          <div className="rounded-xl border border-slate-200 p-4">
            <div className="text-xs font-semibold text-slate-500">나레이션 본문</div>
            <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-slate-700">{narration.text_ko}</p>
          </div>

          <div className="rounded-xl border border-slate-200 p-4">
            <div className="text-xs font-semibold text-slate-500">문장별 타임라인</div>
            <div className="mt-3 space-y-2">
              {narration.timeline.slice(0, 8).map((item) => (
                <div key={`${item.idx}-${item.start_ms}`} className="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
                  <div className="font-medium text-slate-800">#{item.idx + 1}</div>
                  <div className="mt-1">{item.text}</div>
                  <div className="mt-1 text-[11px] text-slate-400">{item.start_ms}ms ~ {item.end_ms}ms</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
