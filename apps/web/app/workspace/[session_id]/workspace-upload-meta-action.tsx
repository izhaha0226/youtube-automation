"use client";

import { useState } from "react";

type UploadMeta = {
  title: string;
  description: string;
  tags: string[];
  hashtags: string[];
  pinned_comment: string;
};

const API = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8787";

export default function WorkspaceUploadMetaAction({
  sessionId,
  initialUploadMeta,
}: {
  sessionId: string;
  initialUploadMeta?: UploadMeta | null;
}) {
  const [loading, setLoading] = useState(false);
  const [uploadMeta, setUploadMeta] = useState<UploadMeta | null>(initialUploadMeta ?? null);
  const [error, setError] = useState<string | null>(null);

  async function runUploadMeta() {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`${API}/scenarios/workspace/${sessionId}/upload-meta`, { method: "POST" });
      if (!r.ok) throw new Error(`Upload Meta API: ${r.status}`);
      setUploadMeta(await r.json());
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
          <h3 className="text-sm font-semibold text-slate-900">업로드 메타</h3>
          <p className="mt-1 text-xs text-slate-500">현재 시나리오를 기준으로 제목, 설명, 태그, 해시태그, 고정댓글을 한 번에 만든다.</p>
        </div>
        <button
          onClick={runUploadMeta}
          disabled={loading}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-40"
        >
          {loading ? "생성 중..." : uploadMeta ? "다시 생성" : "메타 생성"}
        </button>
      </div>

      {error && <div className="mt-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-600">{error}</div>}

      {uploadMeta && (
        <div className="mt-4 space-y-4">
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <div className="text-xs font-semibold text-slate-500">추천 제목</div>
            <p className="mt-2 text-sm font-semibold leading-relaxed text-slate-800">{uploadMeta.title}</p>
          </div>

          <div className="rounded-xl border border-slate-200 p-4">
            <div className="text-xs font-semibold text-slate-500">설명</div>
            <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-slate-700">{uploadMeta.description}</p>
          </div>

          <div className="rounded-xl border border-slate-200 p-4">
            <div className="text-xs font-semibold text-slate-500">태그 / 해시태그</div>
            <div className="mt-2 flex flex-wrap gap-2">
              {uploadMeta.tags.map((tag) => <span key={tag} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600">{tag}</span>)}
              {uploadMeta.hashtags.map((tag) => <span key={tag} className="rounded-full bg-blue-50 px-3 py-1 text-xs text-blue-700">{tag}</span>)}
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 p-4">
            <div className="text-xs font-semibold text-slate-500">고정 댓글</div>
            <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-slate-700">{uploadMeta.pinned_comment}</p>
          </div>
        </div>
      )}
    </section>
  );
}
