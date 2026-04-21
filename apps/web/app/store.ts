type TrendItem = { title: string; channel?: string; link?: string; pub?: string; query?: string; views?: number; published?: string; source?: string; url?: string; likes?: number; video_id?: string; provider?: string };
type BenchmarkVideo = { video_id: string; title: string; channel: string; published: string; views: number; likes: number; comments: number };
type ChartData = {
  keyword_frequency: { keyword: string; count: number }[];
  category_distribution: { category: string; count: number }[];
  top3_timeline: Record<string, string | number>[];
  top3_keywords: string[];
  timeline_source: string;
};
type TrendSourceSection = {
  id: "naver" | "google" | "youtube";
  label: string;
  basis_label: string;
  basis_value: string;
  subtext: string;
  keywords: string[];
  items: TrendItem[];
};
type TrendKeyword = {
  keyword: string;
  count: number;
  sources: string[];
  naver: number;
  google: number;
  youtube: number;
  cluster: string;
  source_score: number;
};
type TrendCorrelation = { source: string; target: string; score: number; cluster: string };
type TrendCluster = { name: string; keywords: string[]; count: number };
type TrendKeywordMap = {
  keywords: TrendKeyword[];
  correlations: TrendCorrelation[];
  clusters: TrendCluster[];
};
type TrendData = {
  period: string;
  period_label: string;
  youtube: TrendItem[];
  news: TrendItem[];
  keywords: string[];
  benchmarks: BenchmarkVideo[];
  charts: ChartData;
  source_sections: TrendSourceSection[];
  keyword_map: TrendKeywordMap;
};

type TopicCandidate = {
  title: string; reason: string;
  score: { popularity: number; economy: number; realestate: number; virality: number; richgo_fit: number; discussion: number };
  keywords: string[];
};
type TopicResult = { recommended_topics: TopicCandidate[]; selected_topic: string; selected_reason: string };
type ScenarioSection = { heading: string; script: string };
type ScenarioOutput = {
  hook: string;
  hook_30s?: string;
  bridge_3min?: string;
  body: string[];
  body_sections?: ScenarioSection[];
  conclusion: string;
  action_takeaways?: string[];
  cta: string;
  title_candidates: string[];
  thumbnail_candidates: string[];
  opening: string;
  opening_title?: string;
  estimated_duration_min?: number;
};
type ResearchSource = { type: string; title: string; url?: string; summary?: string; keywords?: string[] };
type ResearchArticle = { id: string; title: string; source?: string; url?: string; published_at?: string; summary?: string; keywords?: string[]; related_score?: number; selected?: boolean };
type ResearchVideo = { id: string; youtube_video_id?: string; title: string; channel?: string; url?: string; views?: number; published_at?: string; relevance_score?: number; selected?: boolean };
type ResearchSession = { session_id: string; mode: string; category?: string; source: ResearchSource; articles: ResearchArticle[]; videos: ResearchVideo[] };

export type DashboardState = {
  trends: TrendData | null;
  selectedIssues: string[];
  intent: string;
  mustTags: string[];
  topics: TopicResult | null;
  selectedTopic: string | null;
  scenario: ScenarioOutput | null;
  period: string;
  researchMode?: "url" | "category";
  researchUrl?: string;
  researchCategory?: string;
  research?: ResearchSession | null;
  selectedArticleIds?: string[];
  selectedVideoIds?: string[];
};

const STORAGE_KEY = "yt-auto-dashboard";

export function saveDashboard(state: DashboardState) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {}
}

export function loadDashboard(): DashboardState | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export type { TrendData, TrendItem, BenchmarkVideo, ChartData, TopicCandidate, TopicResult, ScenarioOutput, ResearchSession, ResearchArticle, ResearchVideo };
