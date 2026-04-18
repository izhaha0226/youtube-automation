"use client";

import { useEffect, useState } from "react";

type Report = {
  window_days: number;
  videos: { video_id: string; title: string; views: number; likes: number; comments: number }[];
  insight: { summary?: string; patterns?: string[]; suggested_topics?: string[] };
};

export default function PerformancePage() {
  const [data, setData] = useState<Report | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    setBusy(true);
    try {
      const r = await fetch("/api/performance/report");
      setData(await r.json());
    } finally {
      setBusy(false);
    }
  }

  async function fetchLatest() {
    setBusy(true);
    try {
      await fetch("/api/performance/fetch", { method: "POST" });
      await load();
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="grid gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">성과</h2>
        <button
          onClick={fetchLatest}
          disabled={busy}
          className="rounded-lg bg-navy px-4 py-2 text-sm text-white disabled:opacity-40"
        >
          최신 데이터 수집
        </button>
      </div>

      {data?.insight?.summary && (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="font-semibold">주간 인사이트</h3>
          <p className="mt-2 whitespace-pre-wrap text-sm text-slate-700">{data.insight.summary}</p>
          {data.insight.suggested_topics && (
            <div className="mt-3">
              <div className="text-xs text-slate-500">다음 추천 주제</div>
              <ul className="list-disc pl-5 text-sm">
                {data.insight.suggested_topics.map((t, i) => (
                  <li key={i}>{t}</li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-500">
            <tr>
              <th className="p-3">제목</th>
              <th className="p-3">조회수</th>
              <th className="p-3">좋아요</th>
              <th className="p-3">댓글</th>
            </tr>
          </thead>
          <tbody>
            {(data?.videos ?? []).map((v) => (
              <tr key={v.video_id} className="border-t border-slate-100">
                <td className="p-3">{v.title}</td>
                <td className="p-3">{v.views.toLocaleString()}</td>
                <td className="p-3">{v.likes.toLocaleString()}</td>
                <td className="p-3">{v.comments.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
