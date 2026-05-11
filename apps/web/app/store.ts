type CreativeAnalysis = { hook_type?: string; patterns?: string[]; score?: number; title_length?: number };
type TrendItem = { title: string; channel?: string; link?: string; pub?: string; query?: string; views?: number; published?: string; source?: string; url?: string; likes?: number; video_id?: string; provider?: string; thumbnail_url?: string; creative_analysis?: CreativeAnalysis };
type BenchmarkVideo = { video_id: string; title: string; channel: string; published: string; views: number; likes: number; comments: number; url?: string; thumbnail_url?: string; source?: string; creative_analysis?: CreativeAnalysis };
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
type TrendRecommendedIssue = {
  rank: number;
  title: string;
  keyword: string;
  cluster: string;
  score: number;
  shooting_priority: "오늘 찍기" | "3일 안에 찍기" | "데이터 확인 후" | string;
  content_angle: "경고형" | "판단형" | "기회형" | "구조해설형" | string;
  why_now: string;
  hook: string;
  representative_articles: TrendItem[];
  related_youtube: TrendItem[];
  keywords: string[];
  selection_titles: string[];
  richgo_data_signals: string[];
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
  recommended_issues?: TrendRecommendedIssue[];
  keyword_map: TrendKeywordMap;
};

type TopicCandidate = {
  title: string; reason: string;
  score: { popularity: number; economy: number; realestate: number; virality: number; richgo_fit: number; discussion: number };
  archetype?: "경고형" | "판단형" | "기회형" | "구조해설형" | "원칙형";
  keywords: string[];
  discovery_hypothesis?: string;
  strategy_hypothesis?: string;
  tactical_hypothesis?: string;
  verification_signals?: string[];
  failure_criteria?: string[];
  decision_label?: "scale" | "iterate" | "stop" | "data_missing";
  next_loop?: string;
  hypothesis_payload?: Record<string, unknown>;
};
type TopicVideoAnalysis = {
  title: string;
  channel?: string;
  content_summary?: string;
  duration?: string;
  production_intent?: string;
  most_watched_time?: string;
  most_watched_scene?: string;
  hook_takeaway?: string;
  views?: number;
  url?: string;
};
type TopicProductionApplication = {
  opening_strategy?: string;
  structure_strategy?: string;
  scene_strategy?: string;
  topic_generation_basis?: string;
};
type TopicResult = {
  recommended_topics: TopicCandidate[];
  selected_topic: string;
  selected_reason: string;
  selected_archetype?: TopicCandidate["archetype"];
  video_analyses?: TopicVideoAnalysis[];
  production_application?: TopicProductionApplication;
};
type ScenarioSection = { heading: string; script: string };
type ScenarioOutput = {
  hook: string;
  hook_30s?: string;
  bridge_3min?: string;
  archetype?: "경고형" | "판단형" | "기회형" | "구조해설형" | "원칙형";
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
type ResearchVideo = { id: string; youtube_video_id?: string; title: string; channel?: string; url?: string; views?: number; published_at?: string; relevance_score?: number; creative_analysis?: CreativeAnalysis; selected?: boolean };
type ResearchSession = { session_id: string; mode: string; category?: string; source: ResearchSource; articles: ResearchArticle[]; videos: ResearchVideo[] };

export type DashboardState = {
  trends: TrendData | null;
  selectedIssues: string[];
  intent: string;
  mustTags: string[];
  topics: TopicResult | null;
  selectedTopic: string | null;
  selectedTopicArchetype?: TopicCandidate["archetype"] | null;
  scenario: ScenarioOutput | null;
  period: string;
  researchMode?: "url" | "category";
  researchUrl?: string;
  researchCategory?: string;
  research?: ResearchSession | null;
  selectedArticleIds?: string[];
  selectedVideoIds?: string[];
  productionEdits?: Record<string, { title: string; meta: string; status: string }>;
  hiddenProductionKeys?: string[];
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

export function clearDashboard() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {}
}

export type { TrendData, TrendItem, BenchmarkVideo, ChartData, TrendRecommendedIssue, TopicCandidate, TopicResult, TopicVideoAnalysis, TopicProductionApplication, ScenarioOutput, ResearchSession, ResearchArticle, ResearchVideo };
