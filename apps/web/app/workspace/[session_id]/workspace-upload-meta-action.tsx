"use client";

import { useState } from "react";

type UploadMeta = {
  title: string;
  description: string;
  tags: string[];
  hashtags: string[];
  pinned_comment: string;
};

export default function WorkspaceUploadMetaAction({
  initialUploadMeta,
}: {
  sessionId: string;
  initialUploadMeta?: UploadMeta | null;
}) {
  const [uploadMeta] = useState<UploadMeta | null>(initialUploadMeta ?? null);
  const [showPreparing, setShowPreparing] = useState(false);

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">업로드 메타</h3>
          <p className="mt-1 text-xs text-slate-500">현재 시나리오를 기준으로 제목, 설명, 태그, 해시태그, 고정댓글을 한 번에 만든다.</p>
        </div>
        <button
          onClick={() => setShowPreparing(true)}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:opacity-90"
        >
          메타 생성
        </button>
      </div>

      {showPreparing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 px-4">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl">
            <div className="text-base font-semibold text-slate-900">준비중</div>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">업로드 메타 생성 기능은 현재 준비중입니다. 안정화 후 연결하겠습니다.</p>
            <button
              onClick={() => setShowPreparing(false)}
              className="mt-5 w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:opacity-90"
            >
              확인
            </button>
          </div>
        </div>
      )}

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
