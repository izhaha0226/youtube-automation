type Run = { run_id: string; intent: string; status: string; created_at: string; meta: Record<string, unknown> };

async function getRuns(): Promise<Run[]> {
  const base = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8787";
  try {
    const r = await fetch(`${base}/pipeline/runs?limit=50`, { cache: "no-store" });
    if (!r.ok) return [];
    return r.json();
  } catch { return []; }
}

const STATUS = { done: "bg-emerald-100 text-emerald-700", pending: "bg-slate-100 text-slate-500", topic: "bg-yellow-100 text-yellow-700", failed: "bg-rose-100 text-rose-700" } as Record<string, string>;

export default async function ContentPage() {
  const runs = await getRuns();
  const done = runs.filter((r) => r.status === "done");
  const inProgress = runs.filter((r) => r.status !== "done" && r.status !== "failed");
  const failed = runs.filter((r) => r.status === "failed");

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">콘텐츠 관리</h2>

      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="text-3xl font-bold text-navy">{done.length}</div>
          <div className="mt-1 text-sm text-slate-500">완료된 콘텐츠</div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="text-3xl font-bold text-yellow-600">{inProgress.length}</div>
          <div className="mt-1 text-sm text-slate-500">진행 중</div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="text-3xl font-bold text-rose-600">{failed.length}</div>
          <div className="mt-1 text-sm text-slate-500">실패</div>
        </div>
      </div>

      {runs.length === 0 ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-sm text-slate-400">콘텐츠가 없습니다. 대시보드에서 파이프라인을 실행하세요.</div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs text-slate-500">
              <tr><th className="p-3">상태</th><th className="p-3">의도</th><th className="p-3">run_id</th><th className="p-3 whitespace-nowrap">생성일시</th></tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.run_id} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="p-3"><span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS[r.status] ?? "bg-slate-100 text-slate-500"}`}>{r.status}</span></td>
                  <td className="p-3 text-slate-700">{r.intent}</td>
                  <td className="p-3 font-mono text-xs text-slate-400">{r.run_id}</td>
                  <td className="p-3 whitespace-nowrap text-xs text-slate-400">{new Date(r.created_at).toLocaleString("ko-KR")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
