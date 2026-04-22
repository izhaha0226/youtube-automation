import WorkspaceNarrationAction from "./workspace-narration-action";
import WorkspaceReviewAction from "./workspace-review-action";
import WorkspaceSubtitleAction from "./workspace-subtitle-action";
import WorkspaceThumbnailAction from "./workspace-thumbnail-action";
import WorkspaceUploadMetaAction from "./workspace-upload-meta-action";

type WorkspaceResponse = {
  id: string;
  session_id: string;
  selected_topic: string;
  target_duration_min: number;
  target_duration_max: number;
  selected_article_ids: string[];
  selected_video_ids: string[];
  scenario: {
    hook?: string;
    hook_30s?: string;
    bridge_3min?: string;
    archetype?: "경고형" | "판단형" | "기회형" | "구조해설형" | "원칙형";
    body?: string[];
    body_sections?: { heading: string; script: string; summary?: string; viewer_takeaway?: string }[];
    conclusion?: string;
    action_takeaways?: string[];
    cta?: string;
    title_candidates?: string[];
    thumbnail_candidates?: string[];
    opening?: string;
    opening_title?: string;
    estimated_duration_min?: number;
  };
  review?: {
    passed: boolean;
    issues: string[];
    fix_suggestions: string[];
  } | null;
  narration?: {
    text_ko: string;
    sentences: string[];
    audio_path?: string | null;
    timeline: { idx: number; text: string; start_ms: number; end_ms: number }[];
  } | null;
  subtitles?: {
    lang: "ko" | "en" | "ja" | "zh";
    srt_path: string;
    json_path: string;
  }[] | null;
  thumbnail?: {
    draft_images: string[];
    final_image: string;
    overlay_used: boolean;
    save_path: string;
  } | null;
  upload_meta?: {
    title: string;
    description: string;
    tags: string[];
    hashtags: string[];
    pinned_comment: string;
  } | null;
  status: string;
  updated_at: string;
};

type ResearchResponse = {
  session_id: string;
  mode: string;
  category?: string;
  source?: { title?: string; summary?: string; url?: string };
  articles?: { id: string; title: string; source?: string; url?: string }[];
  videos?: { id: string; title: string; channel?: string; url?: string; views?: number }[];
};

const API = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8787";

async function fetchJson<T>(url: string): Promise<T | null> {
  try {
    const r = await fetch(url, { cache: "no-store" });
    if (!r.ok) return null;
    return r.json();
  } catch {
    return null;
  }
}

function pickSelected<T extends { id: string }>(items: T[] | undefined, selectedIds: string[]) {
  if (!items?.length || !selectedIds.length) return [] as T[];
  const idSet = new Set(selectedIds);
  return items.filter((item) => idSet.has(item.id));
}

function formatViews(n?: number) {
  if (!n) return "";
  if (n >= 10000) return `${(n / 10000).toFixed(1)}만회`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}천회`;
  return `${n}회`;
}

export default async function WorkspacePage({ params }: { params: Promise<{ session_id: string }> }) {
  const { session_id } = await params;
  const [workspace, research] = await Promise.all([
    fetchJson<WorkspaceResponse>(`${API}/scenarios/workspace/${session_id}`),
    fetchJson<ResearchResponse>(`${API}/research/sessions/${session_id}`),
  ]);

  if (!workspace) {
    return (
      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-slate-900">시나리오 워크스페이스</h2>
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
          해당 세션의 워크스페이스를 찾지 못했어. 먼저 홈에서 리서치 → 주제 선택 → 시나리오 생성까지 한 번 돌려줘.
        </div>
      </div>
    );
  }

  const scenario = workspace.scenario ?? {};
  const selectedArticles = pickSelected(research?.articles, workspace.selected_article_ids);
  const selectedVideos = pickSelected(research?.videos, workspace.selected_video_ids);
  const bodySections: { heading: string; script: string; summary?: string; viewer_takeaway?: string }[] = scenario.body_sections?.length
    ? scenario.body_sections
    : (scenario.body ?? []).map((script, index) => ({ heading: `섹션 ${index + 1}`, script }));

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="text-xs font-semibold text-slate-400">SESSION</div>
          <h1 className="mt-1 text-2xl font-bold text-slate-900">{workspace.selected_topic}</h1>
          <p className="mt-2 text-sm text-slate-500">
            {workspace.target_duration_min}~{workspace.target_duration_max}분 목표 · 마지막 갱신 {new Date(workspace.updated_at).toLocaleString("ko-KR")}
          </p>
        </div>
        <div className="flex gap-2">
          <a href="/" className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50">홈으로</a>
          <a href={research?.source?.url || "#"} className={`rounded-lg px-4 py-2 text-sm font-medium ${research?.source?.url ? "bg-navy text-white hover:opacity-90" : "bg-slate-100 text-slate-400 pointer-events-none"}`}>원문 소스</a>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.45fr_0.95fr]">
        <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">시나리오</h2>
            <div className="flex items-center gap-2">
              {scenario.archetype && <span className="rounded bg-amber-50 px-2.5 py-1 text-xs text-amber-700">{scenario.archetype}</span>}
              <span className="rounded bg-slate-100 px-2.5 py-1 text-xs text-slate-500">예상 {scenario.estimated_duration_min ?? workspace.target_duration_min}분</span>
            </div>
          </div>

          {scenario.opening_title && (
            <div className="rounded-xl border border-rose-200 bg-rose-50 p-4">
              <div className="text-xs font-semibold text-rose-500">오프닝 제목</div>
              <p className="mt-1 text-base font-semibold leading-relaxed text-rose-700">{scenario.opening_title}</p>
            </div>
          )}

          {scenario.opening && (
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <div className="text-xs font-semibold text-slate-500">오프닝</div>
              <p className="mt-1 text-sm leading-relaxed text-slate-700">{scenario.opening}</p>
            </div>
          )}

          {scenario.hook_30s && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
              <div className="text-xs font-semibold text-amber-600">0~30초 훅</div>
              <p className="mt-1 text-sm leading-relaxed text-amber-900">{scenario.hook_30s}</p>
            </div>
          )}

          {scenario.bridge_3min && (
            <div className="rounded-xl border border-blue-200 bg-blue-50 p-4">
              <div className="text-xs font-semibold text-blue-600">3분 유지 브릿지</div>
              <p className="mt-1 text-sm leading-relaxed text-blue-900">{scenario.bridge_3min}</p>
            </div>
          )}

          <div className="rounded-xl border border-slate-200 p-4">
            <div className="text-sm font-semibold text-slate-800">본문 섹션</div>
            <div className="mt-4 space-y-4">
              {bodySections.map((section, index) => (
                <div key={`${section.heading}-${index}`} className="border-l-2 border-slate-200 pl-4">
                  <div className="text-sm font-semibold text-slate-800">{section.heading}</div>
                  <p className="mt-1 whitespace-pre-wrap text-sm leading-relaxed text-slate-600">{section.script}</p>
                  {section.summary && <p className="mt-2 text-xs text-slate-500">요약: {section.summary}</p>}
                  {section.viewer_takeaway && <p className="mt-1 text-xs text-blue-600">시청자 포인트: {section.viewer_takeaway}</p>}
                </div>
              ))}
            </div>
          </div>

          {scenario.conclusion && (
            <div className="rounded-xl border border-slate-200 p-4">
              <div className="text-xs font-semibold text-slate-500">결론</div>
              <p className="mt-1 text-sm leading-relaxed text-slate-700">{scenario.conclusion}</p>
            </div>
          )}

          {scenario.cta && (
            <div className="rounded-xl border border-slate-200 p-4">
              <div className="text-xs font-semibold text-slate-500">CTA</div>
              <p className="mt-1 text-sm leading-relaxed text-slate-700">{scenario.cta}</p>
            </div>
          )}
        </section>

        <aside className="space-y-4">
          <WorkspaceReviewAction sessionId={session_id} initialReview={workspace.review ?? null} />
          <WorkspaceNarrationAction sessionId={session_id} initialNarration={workspace.narration ?? null} />
          <WorkspaceSubtitleAction sessionId={session_id} initialSubtitles={workspace.subtitles ?? []} />
          <WorkspaceThumbnailAction sessionId={session_id} initialThumbnail={workspace.thumbnail ?? null} />
          <WorkspaceUploadMetaAction sessionId={session_id} initialUploadMeta={workspace.upload_meta ?? null} />

          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-900">선택 근거</h3>
            <div className="mt-3 space-y-4">
              <div>
                <div className="text-xs font-semibold text-slate-400">리서치 소스</div>
                <div className="mt-1 text-sm font-medium text-slate-700">{research?.source?.title || "소스 정보 없음"}</div>
                {research?.source?.summary && <p className="mt-1 text-xs leading-relaxed text-slate-500">{research.source.summary}</p>}
              </div>
              <div>
                <div className="text-xs font-semibold text-slate-400">선택 기사 {selectedArticles.length}개</div>
                <ul className="mt-2 space-y-2">
                  {selectedArticles.length === 0 && <li className="text-xs text-slate-400">선택 기사 없음</li>}
                  {selectedArticles.map((article) => (
                    <li key={article.id} className="rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
                      <div className="font-medium text-slate-800">{article.title}</div>
                      {article.source && <div className="mt-1 text-slate-400">{article.source}</div>}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <div className="text-xs font-semibold text-slate-400">선택 영상 {selectedVideos.length}개</div>
                <ul className="mt-2 space-y-2">
                  {selectedVideos.length === 0 && <li className="text-xs text-slate-400">선택 영상 없음</li>}
                  {selectedVideos.map((video) => (
                    <li key={video.id} className="rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
                      <div className="font-medium text-slate-800">{video.title}</div>
                      <div className="mt-1 text-slate-400">{video.channel} {formatViews(video.views)}</div>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-900">후속 제작 포인트</h3>
            <div className="mt-3 space-y-4">
              <div>
                <div className="text-xs font-semibold text-slate-400">액션 포인트</div>
                <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-slate-600">
                  {(scenario.action_takeaways ?? []).map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
                </ul>
              </div>
              <div>
                <div className="text-xs font-semibold text-slate-400">제목 후보</div>
                <ul className="mt-2 space-y-1 text-xs text-slate-600">
                  {(scenario.title_candidates ?? []).map((item, index) => <li key={`${item}-${index}`}>• {item}</li>)}
                </ul>
              </div>
              <div>
                <div className="text-xs font-semibold text-slate-400">썸네일 문구</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {(scenario.thumbnail_candidates ?? []).map((item, index) => (
                    <span key={`${item}-${index}`} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">{item}</span>
                  ))}
                </div>
              </div>
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}
