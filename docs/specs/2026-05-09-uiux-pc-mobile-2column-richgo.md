# UI/UX Spec: Richgo YouTube Automation PC/Mobile 2-Column Design

Source mirror: Obsidian `wiki/YouTube 자동화프로젝트/notes/2026-05-09_SPEC_UIUX_PC모바일_2열_리치고.md`

## Product UX Principle

This product is a Richgo content strategy research room, not a simple automation dashboard.

- PC: deep comparison and decision workflow
- Mobile: fast review and selection workflow
- PC uses exactly 2 layers: left + center
- No right inspector panel
- Evidence is always traceable but folded into the left context layer

## PC Layout

Target: 1440px+

```text
┌──────────────────────────────┬────────────────────────────────────────────────────┐
│ Left Context / Workflow      │ Center Main Decision                               │
│ 320~380px                    │ flexible                                           │
│                              │                                                    │
│ - Channel DNA                │ - Trend cards / charts / tables                    │
│ - Step rail                  │ - News and YouTube benchmark comparison            │
│ - Current selections         │ - Topic Battle Board                               │
│ - Filters                    │ - Scenario editor                                  │
│ - Collapsible evidence       │                                                    │
└──────────────────────────────┴────────────────────────────────────────────────────┘
```

### Left Context / Workflow Layer

Fixed responsibilities:

1. Channel DNA mini card
2. Workflow steps
3. Current selection summary
4. Filters
5. Evidence accordion
6. Next action

Evidence accordion includes:

- Search trend evidence
- News evidence
- YouTube benchmark evidence
- Richgo philosophy fit evidence
- Risk/caution notes

### Center Main Decision Layer

Changes by workflow step:

1. Command Center
2. Issue Research Desk
3. YouTube Benchmark Lab
4. Topic Battle Board
5. Scenario Studio Pro

## PC Screens

### Command Center

Purpose: show today’s content opportunities.

Center:

- Top recommended action
- Trend issue card grid
- Channel-performance-based recommendations/cautions

Issue card fields:

- Issue title
- Category
- Search growth badge
- News spread badge
- Richgo fit score
- Expected target
- CTA: `검증 보기`

### Issue Research Desk

Purpose: validate whether the selected issue is worth turning into content.

Center:

- Issue summary and keywords
- Naver/Google trend charts
- News article list
- Article select/exclude controls

Article fields:

- Title
- Publisher
- Published time
- Stance
- Key claim
- Usable evidence sentence
- Selection checkbox

### YouTube Benchmark Lab

Purpose: analyze why related YouTube videos performed well.

Center:

- Search keyword/filter row
- Video list
- Selected benchmark comparison

Video fields:

- Thumbnail
- Title
- Channel
- Published date
- View count
- Duration
- Title hook type
- Success factor
- Selection checkbox

Analysis fields:

- Title hook
- Thumbnail hook
- Opening hook
- Audience anxiety/desire point
- Comment response
- Richgo differentiation opportunity

### Topic Battle Board

Purpose: compare 3 Richgo-aligned topic angles and select one.

Topic types:

1. Immediate hook angle
2. Trust/explainer angle
3. Long-term brand asset angle

6-axis score:

1. Trend fit
2. View prediction
3. Title hook strength
4. Target clarity
5. Richgo philosophy fit
6. Execution/filming fit

Topic card fields:

- Topic title
- One-line angle
- Target audience
- Why now
- Richgo-specific interpretation
- Risk
- Hexagon score
- CTA: `이 주제로 시나리오 만들기`

### Scenario Studio Pro

Purpose: turn the selected topic into a filming-ready script.

Center:

- 5 title candidates
- 5 thumbnail copy candidates
- 30-second opening
- Main script editor
- Revision command box in the center workspace, not a right panel

Editor actions:

- Collapse/expand sections
- View evidence source
- Revision command
- Tone controls: sharper / simpler / more data-driven / more Kim Ki-won-like
- Extract Shorts clip points

## Mobile Layout

Target: 390px

Structure:

- Top: current step/progress
- Body: single-step card stack
- Bottom: fixed CTA
- Details/evidence: bottom sheet

Steps:

1. Today’s recommended issue
2. Issue validation
3. News article selection
4. YouTube benchmark selection
5. Topic selection among 3 recommendations
6. Scenario generation

Mobile rules:

- 3~5 options max per screen
- Cards instead of tables
- Mini chart + summary badges instead of full charts
- Evidence via `근거 보기` bottom sheet
- One emphasized CTA only

## Breakpoints

- Mobile: 0~767px
- Tablet: 768~1199px
- PC: 1200px+

Tablet:

- Left Context layer becomes collapsible drawer
- Center Main Decision layer remains the main workspace

PC:

- Left Context layer fixed
- Center Main Decision layer flexible
- No right panel

## Interaction Rules

All selections immediately update the left context layer or mobile top status.

Selection targets:

- Issue
- Article
- YouTube video
- Recommended topic
- Title/thumbnail candidate

Save to Supabase when:

- Trend scan completes
- Issue validation completes
- Article selected/excluded
- YouTube video selected/excluded
- Topic recommendations generated
- Topic selected
- Scenario generated/edited

CTA sequence:

- Command Center: `이슈 검증하기`
- Issue Research Desk: `이 기사로 유튜브 찾기`
- Benchmark Lab: `선택 영상으로 주제 추천`
- Topic Battle Board: `이 주제로 시나리오 만들기`
- Scenario Studio Pro: `수정 요청` / `촬영본으로 저장`

## Acceptance Criteria

PC:

- 1440px shows clear left/center 2-column structure
- No right panel exists
- Left layer shows current context and evidence
- Center layer supports comparison, selection, and writing
- 3 topic cards and hexagon scores fit in one view

Mobile:

- 390px has bottom fixed CTA
- Cards are readable
- Evidence opens in bottom sheet
- Selection flow is uninterrupted

Common:

- All selections and generated outputs are saved to Supabase
- No recommendation is shown without traceable evidence
- No YouTube publish/upload action runs without explicit approval
