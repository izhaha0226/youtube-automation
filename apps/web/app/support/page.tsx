export default function SupportPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h2 className="text-xl font-semibold">고객지원</h2>
      <section className="rounded-2xl border border-slate-200 bg-white p-6">
        <h3 className="font-semibold">연락처</h3>
        <div className="mt-3 grid gap-2 text-sm text-slate-600">
          <div>이메일: bcs2013@bhub.co.kr</div>
          <div>Obsidian 공유: <a href="https://share.note.sx/qynhdluo" className="text-blue-600 underline" target="_blank" rel="noreferrer">share.note.sx/qynhdluo</a></div>
        </div>
      </section>
      <section className="rounded-2xl border border-slate-200 bg-white p-6">
        <h3 className="font-semibold">시스템 정보</h3>
        <div className="mt-3 grid gap-1 text-sm text-slate-500">
          <div>프로젝트: youtube-automation v0.1.0</div>
          <div>기본 모델: GPT-5.4</div>
          <div>백업 모델: Claude Opus 4.7</div>
          <div>채널: 리치고 (김기원 대표)</div>
          <div>백엔드: FastAPI (Railway)</div>
          <div>프론트엔드: Next.js 16 (Vercel)</div>
        </div>
      </section>
    </div>
  );
}
