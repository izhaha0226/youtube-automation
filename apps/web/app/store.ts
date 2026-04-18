type TrendItem = { title: string; channel?: string; link?: string; pub?: string; query?: string; views?: number; published?: string; source?: string; url?: string; likes?: number; video_id?: string };
type BenchmarkVideo = { video_id: string; title: string; channel: string; published: string; views: number; likes: number; comments: number };
type ChartData = {
  keyword_frequency: { keyword: string; count: number }[];
  category_distribution: { category: string; count: number }[];
  top3_timeline: Record<string, string | number>[];
  top3_keywords: string[];
  timeline_source: string;
};
type TrendData = { period: string; period_label: string; youtube: TrendItem[]; news: TrendItem[]; keywords: string[]; benchmarks: BenchmarkVideo[]; charts: ChartData };

type TopicCandidate = {
  title: string; reason: string;
  score: { popularity: number; economy: number; realestate: number; virality: number; richgo_fit: number; discussion: number };
  keywords: string[];
};
type TopicResult = { recommended_topics: TopicCandidate[]; selected_topic: string; selected_reason: string };
type ScenarioOutput = { hook: string; body: string[]; conclusion: string; cta: string; title_candidates: string[]; thumbnail_candidates: string[]; opening: string };

export type DashboardState = {
  trends: TrendData | null;
  selectedIssues: string[];
  intent: string;
  mustTags: string[];
  topics: TopicResult | null;
  selectedTopic: string | null;
  scenario: ScenarioOutput | null;
  period: string;
};

const STORAGE_KEY = "yt-auto-dashboard";

export function saveDashboard(state: DashboardState) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {}
}

export function loadDashboard(): DashboardState | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export type { TrendData, TrendItem, BenchmarkVideo, ChartData, TopicCandidate, TopicResult, ScenarioOutput };
