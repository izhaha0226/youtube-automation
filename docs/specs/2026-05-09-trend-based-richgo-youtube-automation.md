# Trend-based Richgo YouTube Automation Spec

> Source of truth mirror: Obsidian `wiki/YouTube 자동화프로젝트/notes/2026-05-09_SPEC_트렌드기반_리치고_유튜브_자동화.md`

## Goal

Build a trend-first content strategy OS for Richgo YouTube: analyze channel performance, detect current trends/issues, validate issue demand via Naver/Google trends, collect news and YouTube benchmarks, recommend 3 Richgo-aligned topics with a 6-axis score, then generate an AI scenario for the selected topic.

## Core Flow

1. Richgo channel analytics
2. Trend/news issue scan
3. Naver/Google trend validation
4. News article evidence list
5. Related YouTube benchmark search
6. Benchmark analysis: hooks, views, thumbnails, comments, success factors
7. 3 topic recommendations based on Kim Ki-won/Richgo philosophy
8. 6-axis score comparison
9. User selects one topic
10. AI scenario generation
11. Save every step to Supabase

## Non-goals for MVP

- No auto-upload/publish/delete/update to YouTube without explicit approval
- No full video editing automation
- No source-less trend recommendations
- No pure news-summary scripts

## MVP Requirements

### Channel Analytics

- Import or fetch YouTube Analytics / channel video metrics
- Store demographics, topic performance, CTR, retention, view counts, high/low performer patterns
- Produce Richgo Channel DNA summary

### Trend Scan

- Scan Korean economy/real-estate/policy/rate/loan/tax/subscription issues
- Merge duplicate issues
- Store source links and summary

### Trend Validation

- Validate issue keywords with Naver DataLab and Google Trends
- Store search trend JSON and related keywords
- Compute search growth score and issue sustainability

### News Evidence

- Store article title, publisher, URL, stance, key claim, usable evidence
- Allow user selection/exclusion

### YouTube Benchmarks

- Search related YouTube videos
- Store title/channel/views/date/duration/thumbnail/url
- Analyze title hook, thumbnail hook, opening hook, success factor, audience pain point, differentiation opportunity

### Topic Recommendations

Recommend exactly 3 distinct angles:

1. Immediate hook angle
2. Trust/explainer angle
3. Long-term brand asset angle

Score each topic on 0-100 scale:

1. Trend fit
2. View prediction
3. Title hook strength
4. Target clarity
5. Richgo philosophy fit
6. Execution/filming fit

### Scenario Generation

Input selected topic + selected articles + selected benchmarks + channel DNA + Richgo philosophy.

Output:

- 5 title candidates
- 5 thumbnail copy candidates
- 30-second opening
- Main script
- Section emphasis points
- Evidence source list
- Shorts/clip points

## Supabase Tables

- `channel_snapshots`
- `channel_video_metrics`
- `trend_issues`
- `trend_validations`
- `news_articles`
- `youtube_benchmarks`
- `benchmark_analyses`
- `topic_recommendations`
- `topic_scores`
- `scenario_drafts`
- `user_selections`

## API Draft

- `GET /api/channel/summary`
- `POST /api/channel/import-youtube-analytics`
- `POST /api/trends/scan`
- `GET /api/trends/issues`
- `POST /api/trends/{issue_id}/validate`
- `GET /api/trends/{issue_id}/articles`
- `POST /api/trends/{issue_id}/youtube-search`
- `POST /api/benchmarks/{issue_id}/analyze`
- `POST /api/topics/recommend`
- `POST /api/topics/{topic_id}/select`
- `POST /api/scenarios/generate`
- `GET /api/scenarios/{scenario_id}`

## UI Screens

1. Today Radar
2. Channel DNA
3. Issue Validation
4. YouTube Benchmark
5. Topic Battle
6. Scenario Studio

## UX Principles

- Mobile 390px and PC 1440px are both first-class experiences
- Card-based decision flow
- One primary CTA per step
- Radar/hexagon score visualization
- Evidence collapsible but always traceable
- White premium research-room design with sharp accent color

### Mobile UX

- Fast “review → choose → next” flow
- Vertical step cards
- Bottom fixed CTA
- Swipeable issue/news/video cards
- Bottom-sheet evidence expansion

### PC UX

- Deep comparison/research workflow
- 2-column layout: left context/workflow layer + center main decision layer
- No right inspector panel
- Evidence/inspector content lives inside collapsible sections in the left context layer
- Command Center for today’s issues, channel DNA, and recommended action
- Issue Research Desk for trends, news, and keyword map
- Benchmark Lab for YouTube competitors and success factors
- Topic Battle Board for 3-topic comparison with hexagon scores
- Scenario Studio Pro with left evidence/context and center editor/revision workspace

## Implementation Order

1. Supabase schema
2. Backend DB adapter and models
3. Channel analytics import MVP
4. Trend scan MVP
5. Trend validation storage
6. News and YouTube search APIs
7. Benchmark analysis prompt/storage
8. 6-axis scoring engine
9. Topic recommendation API
10. Scenario generation API
11. Mobile-first UI redesign
12. Dry-run E2E verification
