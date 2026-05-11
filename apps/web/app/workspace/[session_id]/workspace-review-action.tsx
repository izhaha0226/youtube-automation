"use client";

import { useState } from "react";
import StatusModal from "../../components/status-modal";

type ReviewOutput = {
  passed: boolean;
  issues: string[];
  fix_suggestions: string[];
  tone_structure_difference_percent?: number;
  tone_structure_comment?: string;
  structure_recommendation?: string;
  recommended_action?: "keep_content_adjust_structure" | "keep_structure_adjust_tone" | "pass";
};

export default function WorkspaceReviewAction({
  sessionId,
  initialReview,
}: {
  sessionId: string;
  initialReview?: ReviewOutput | null;
}) {
  const [loading, setLoading] = useState(false);
  const [review, setReview] = useState<ReviewOutput | null>(initialReview ?? null);
  const [error, setError] = useState<string | null>(null);

  async function runReview() {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`/api/scenarios/workspace/${sessionId}/review`, { method: "POST" });
      if (!r.ok) throw new Error(`Review API: ${r.status}`);
      setReview(await r.json());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function regenerateFromReview() {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`/api/scenarios/workspace/${sessionId}/regenerate`, { method: "POST" });
      if (!r.ok) throw new Error(`Regenerate API: ${r.status}`);
      window.location.reload();
    } catch (e) {
      setError((e as Error).message);
      setLoading(false);
    }
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">시나리오 검수</h3>
          <p className="mt-1 text-xs text-slate-500">현재 워크스페이스 대본을 그대로 리뷰해서 리치고 톤과 근거 밀도를 체크해.</p>
        </div>
        <div className="flex gap-2">
          {review && review.fix_suggestions.length > 0 && (
            <button
              onClick={regenerateFromReview}
              disabled={loading}
              className="rounded-lg border border-emerald-300 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-700 hover:bg-emerald-100 disabled:opacity-40"
            >
              {loading ? "재생성 중..." : "제안 반영 재생성"}
            </button>
          )}
          <button
            onClick={runReview}
            disabled={loading}
            className="rounded-lg bg-navy px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-40"
          >
            {loading ? "검수 중..." : review ? "다시 검수" : "검수 시작"}
          </button>
        </div>
      </div>

      <StatusModal open={Boolean(error)} title="작업을 진행할 수 없습니다" message={error} tone="error" onClose={() => setError(null)} />

      {review && (
        <div className={`mt-4 rounded-xl border p-4 ${review.passed ? "border-emerald-200 bg-emerald-50" : "border-amber-200 bg-amber-50"}`}>
          <div className={`text-sm font-semibold ${review.passed ? "text-emerald-700" : "text-amber-700"}`}>
            {review.passed ? "검수 통과" : "보완 필요"}
          </div>

          <div className="mt-3 rounded-lg border border-white/60 bg-white/70 p-3 text-xs text-slate-700">
            <div className="font-semibold text-slate-900">리치고 지난 영상 대비 톤·구조 차이: {review.tone_structure_difference_percent ?? 0}%</div>
            <p className="mt-1">{review.tone_structure_comment || "리치고 지난 영상 레퍼런스 대비 톤과 구조를 확인했습니다."}</p>
            <p className="mt-2 font-semibold text-slate-900">추천 구조</p>
            <p className="mt-1">{review.structure_recommendation || "오프닝 훅 → 리치고 데이터 확인 및 분석 → 실수요자 판단 기준 → 리스크/예외 → 결론 구조를 추천합니다."}</p>
          </div>

          <div className="mt-3 grid gap-4 lg:grid-cols-2">
            <div>
              <div className="text-xs font-semibold text-slate-500">이슈</div>
              <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-slate-700">
                {review.issues.length === 0 && <li>특별한 문제 없음</li>}
                {review.issues.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
              </ul>
            </div>
            <div>
              <div className="text-xs font-semibold text-slate-500">수정 제안</div>
              <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-slate-700">
                {review.fix_suggestions.length === 0 && <li>추가 수정 제안 없음</li>}
                {review.fix_suggestions.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
              </ul>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
