"use client";

import { useState } from "react";

type ThumbnailOutput = {
  draft_images: string[];
  final_image: string;
  overlay_used: boolean;
  save_path: string;
};

export default function WorkspaceThumbnailAction({
  initialThumbnail,
}: {
  sessionId: string;
  initialThumbnail?: ThumbnailOutput | null;
}) {
  const [thumbnail] = useState<ThumbnailOutput | null>(initialThumbnail ?? null);
  const [showPreparing, setShowPreparing] = useState(false);

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">썸네일</h3>
          <p className="mt-1 text-xs text-slate-500">현재 주제와 썸네일 후보 문구를 기반으로 최종 썸네일 시안을 만든다.</p>
        </div>
        <button
          onClick={() => setShowPreparing(true)}
          className="rounded-lg bg-fuchsia-600 px-4 py-2 text-sm font-semibold text-white hover:opacity-90"
        >
          썸네일 생성
        </button>
      </div>

      {showPreparing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 px-4">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl">
            <div className="text-base font-semibold text-slate-900">준비중</div>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">썸네일 생성 기능은 현재 준비중입니다. 안정화 후 연결하겠습니다.</p>
            <button
              onClick={() => setShowPreparing(false)}
              className="mt-5 w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:opacity-90"
            >
              확인
            </button>
          </div>
        </div>
      )}

      {thumbnail && (
        <div className="mt-4 space-y-4">
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <div className="text-xs font-semibold text-slate-500">최종 결과</div>
            <p className="mt-2 break-all text-[11px] text-slate-700">최종 이미지: {thumbnail.final_image}</p>
            <p className="mt-1 break-all text-[11px] text-slate-500">저장 폴더: {thumbnail.save_path}</p>
            <p className="mt-1 text-[11px] text-slate-500">오버레이 사용: {thumbnail.overlay_used ? "예" : "아니오"}</p>
          </div>

          <div className="rounded-xl border border-slate-200 p-4">
            <div className="text-xs font-semibold text-slate-500">시안 파일</div>
            <ul className="mt-3 space-y-2 text-xs text-slate-600">
              {thumbnail.draft_images.map((path, index) => (
                <li key={`${path}-${index}`} className="rounded-lg bg-slate-50 px-3 py-2 break-all">{path}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </section>
  );
}
