"use client";

import { useState } from "react";

type SubtitleOutput = {
  lang: "ko" | "en" | "ja" | "zh";
  srt_path: string;
  json_path: string;
};

const LABELS: Record<string, string> = {
  ko: "한국어",
  en: "영어",
  ja: "일본어",
  zh: "중국어",
};

export default function WorkspaceSubtitleAction({
  sessionId,
  initialSubtitles,
}: {
  sessionId: string;
  initialSubtitles?: SubtitleOutput[] | null;
}) {
  const [loading, setLoading] = useState(false);
  const [subtitles, setSubtitles] = useState<SubtitleOutput[]>(initialSubtitles ?? []);
  const [error, setError] = useState<string | null>(null);

  async function runSubtitles() {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`/api/scenarios/workspace/${sessionId}/subtitles`, { method: "POST" });
      if (!r.ok) throw new Error(`Subtitle API: ${r.status}`);
      setSubtitles(await r.json());
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
          <h3 className="text-sm font-semibold text-slate-900">자막</h3>
          <p className="mt-1 text-xs text-slate-500">나레이션 결과를 기반으로 한국어/영어/일본어/중국어 자막 파일을 만든다.</p>
        </div>
        <button
          onClick={runSubtitles}
          disabled={loading}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-40"
        >
          {loading ? "생성 중..." : subtitles.length ? "다시 생성" : "자막 생성"}
        </button>
      </div>

      {error && <div className="mt-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-600">{error}</div>}

      {subtitles.length > 0 && (
        <div className="mt-4 rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-xs">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="p-3 text-left">언어</th>
                <th className="p-3 text-left">SRT</th>
                <th className="p-3 text-left">JSON</th>
              </tr>
            </thead>
            <tbody>
              {subtitles.map((item) => (
                <tr key={item.lang} className="border-t border-slate-100">
                  <td className="p-3 font-medium text-slate-700">{LABELS[item.lang] ?? item.lang}</td>
                  <td className="p-3 break-all text-slate-500">{item.srt_path}</td>
                  <td className="p-3 break-all text-slate-500">{item.json_path}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
