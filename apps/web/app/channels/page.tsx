"use client";

import { useState } from "react";

type Channel = {
  name: string;
  id: string;
  url: string;
  category: "운영" | "국내 벤치마크" | "해외 벤치마크";
  desc: string;
  subs: string;
  reason: string;
};

const INITIAL_CHANNELS: Channel[] = [
  // ─── 운영 채널 ───
  {
    name: "리치고TV",
    id: "UC3nsb3SxlRrJQ9egkKNnlfg",
    url: "https://www.youtube.com/@richgoTV",
    category: "운영",
    desc: "김기원 대표 — 부동산 데이터 기반 경제 해설",
    subs: "10만+",
    reason: "본 채널. 리치고 플랫폼 데이터를 활용한 부동산/경제 해설로, 전문성과 데이터 신뢰도가 핵심 차별점.",
  },

  // ─── 국내 벤치마크 (10개) ───
  {
    name: "삼프로TV",
    id: "UChlv4GSd7OQl3js-jkLOnFA",
    url: "https://www.youtube.com/@3PROTV",
    category: "국내 벤치마크",
    desc: "경제/시사 종합 — 전문가 패널 토론",
    subs: "300만+",
    reason: "국내 경제 유튜브 1위. 전문가 패널 형식과 시사 이슈 속보 대응력이 뛰어남. 포맷(패널 토론 + 속보 해설)과 제목/썸네일 전략을 벤치마킹.",
  },
  {
    name: "김작가TV",
    id: "UCvil4OAt-zShzkKHsg9EQAw",
    url: "https://www.youtube.com/@kimwriter",
    category: "국내 벤치마크",
    desc: "부동산/경제 투자 — 실전 투자 관점",
    subs: "90만+",
    reason: "부동산 투자자 시청자 비율이 높음. 실전 투자 사례 중심 콘텐츠와 '지금 사야 할 곳' 같은 직접적 제목 전략이 높은 CTR 기록.",
  },
  {
    name: "부동산김사부TV",
    id: "UC2rRsSOig2nHpGQhH8A8CcQ",
    url: "https://www.youtube.com/@kimmaster",
    category: "국내 벤치마크",
    desc: "부동산 전문 — 입지 분석/재개발",
    subs: "50만+",
    reason: "재개발/재건축 특화 채널. 현장 답사 영상과 지도 기반 입지 분석이 시청 지속시간 높음. 지역별 콘텐츠 기획 참고.",
  },
  {
    name: "슈카월드",
    id: "UCsJ6RuBiTVWRX156FVbeaGg",
    url: "https://www.youtube.com/@syuka_world",
    category: "국내 벤치마크",
    desc: "경제/금융 해설 — 스토리텔링형",
    subs: "250만+",
    reason: "복잡한 경제 이슈를 스토리텔링으로 풀어내는 대표 채널. 그래픽+나레이션 조합의 1인 제작 모델이 자동화 파이프라인과 유사한 구조.",
  },
  {
    name: "언더스탠딩",
    id: "UCIUni4ScRp4mqPXsxy62L5w",
    url: "https://www.youtube.com/@understanding",
    category: "국내 벤치마크",
    desc: "세상의 모든 지식 — 심층 경제 해설",
    subs: "100만+",
    reason: "삼프로TV에서 파생. 단일 주제 30분+ 심층 해설 포맷이 체류 시간 극대화. 시나리오 구성(훅→분석→결론) 패턴 참고.",
  },
  {
    name: "월급쟁이부자들TV",
    id: "UCx4coeYCiEoP3fCkuxnPOdQ",
    url: "https://www.youtube.com/@wealthyworkers",
    category: "국내 벤치마크",
    desc: "재테크/부동산 — 실전 재테크",
    subs: "80만+",
    reason: "2030 직장인 타겟. '월급으로 내 집 마련' 같은 공감형 제목과 단계별 가이드 구성이 높은 저장률 기록. 타겟 확장 시 참고.",
  },
  {
    name: "집코노미",
    id: "UC2QeHFtsGnB4LJr35TXq0oQ",
    url: "https://www.youtube.com/@zipconomy",
    category: "국내 벤치마크",
    desc: "한국경제TV — 부동산 데이터 분석",
    subs: "40만+",
    reason: "한국경제TV 산하 부동산 전문 채널. 실거래가/청약 데이터 기반 분석이 리치고와 유사. 데이터 시각화 방식과 차트 활용 벤치마킹.",
  },
  {
    name: "부읽남",
    id: "UCeYpS1JQ_FLUX6GjKhSMJpw",
    url: "https://www.youtube.com/@readman",
    category: "국내 벤치마크",
    desc: "부동산 읽어주는 남자 — 뉴스 해설",
    subs: "70만+",
    reason: "부동산 뉴스를 일반인 눈높이로 해설. 매일 업로드하는 높은 빈도와 뉴스 큐레이션 방식이 자동화 파이프라인의 일간 콘텐츠 모델 참고.",
  },
  {
    name: "전인구경제연구소",
    id: "UCM6C-JRJqk4HPwX-8CJZ1Gw",
    url: "https://www.youtube.com/@jeoningoo",
    category: "국내 벤치마크",
    desc: "거시경제/금리/환율 — 데이터 분석",
    subs: "60만+",
    reason: "거시경제 데이터(금리/환율/GDP) 전문. 차트와 데이터 중심 해설이 리치고 톤과 일치. 거시 경제 시나리오 구성 방식 참고.",
  },
  {
    name: "머니인사이드",
    id: "UC7bh5LaWvkJE_zj4xd5Ku0A",
    url: "https://www.youtube.com/@moneyinside",
    category: "국내 벤치마크",
    desc: "SBS — 경제 다큐멘터리형",
    subs: "30만+",
    reason: "방송국 제작 퀄리티의 경제 다큐멘터리. 스토리 아크(문제→원인→전망→대응) 구성이 검수 기준의 시나리오 구조와 동일. 편집 스타일 참고.",
  },

  // ─── 해외 벤치마크 (10개) ───
  {
    name: "Graham Stephan",
    id: "UCa-ckhlKL98F8YXKQ-BALiw",
    url: "https://www.youtube.com/@GrahamStephan",
    category: "해외 벤치마크",
    desc: "부동산/재테크 — 밀레니얼 투자",
    subs: "470만+",
    reason: "미국 부동산/재테크 1위. 'I bought a house for $X' 같은 개인 경험 기반 제목과 빠른 편집이 높은 CTR/체류시간. 제목 공식 참고.",
  },
  {
    name: "Meet Kevin",
    id: "UCUQo7YzCiqdAOwmHQY7iqCA",
    url: "https://www.youtube.com/@MeetKevin",
    category: "해외 벤치마크",
    desc: "부동산/주식/경제 속보",
    subs: "190만+",
    reason: "경제 속보 대응 속도가 업계 최고. Fed 금리 발표 직후 30분 내 영상 업로드. 속보 대응 자동화 파이프라인의 목표 모델.",
  },
  {
    name: "Economics Explained",
    id: "UCZ4AMrDcNrfy3X6nsU8-rPg",
    url: "https://www.youtube.com/@EconomicsExplained",
    category: "해외 벤치마크",
    desc: "거시경제 해설 — 애니메이션 그래픽",
    subs: "350만+",
    reason: "복잡한 거시경제를 모션 그래픽으로 해설. B-roll + 애니메이션 조합이 자동 영상 생성의 비주얼 참고. 글로벌 관점의 경제 해설 구성 참고.",
  },
  {
    name: "Patrick Boyle",
    id: "UCASM2CGGE4JsJjSbWOiWoTg",
    url: "https://www.youtube.com/@PBoyle",
    category: "해외 벤치마크",
    desc: "금융/헤지펀드 — 전문가 분석",
    subs: "100만+",
    reason: "전직 헤지펀드 매니저의 전문 분석. 데이터+논문 인용 기반 해설이 리치고의 '전문성+데이터' 포지셔닝과 일치. 톤&매너 참고.",
  },
  {
    name: "How Money Works",
    id: "UC3yA8nDwraeOfnYfBWun83g",
    url: "https://www.youtube.com/@HowMoneyWorks",
    category: "해외 벤치마크",
    desc: "금융 시스템 해설 — 스토리텔링",
    subs: "200만+",
    reason: "금융 시스템을 역사적 맥락으로 스토리텔링. '왜 은행은 망하지 않는가' 같은 호기심 갭 제목이 평균 조회수 200만+. 제목 전략 참고.",
  },
  {
    name: "Reventure Consulting",
    id: "UCFk8JV3oPMpmkSlYzQAikiA",
    url: "https://www.youtube.com/@Reventure",
    category: "해외 벤치마크",
    desc: "미국 부동산 데이터 분석",
    subs: "70만+",
    reason: "미국 부동산 시장을 Zillow/Redfin 데이터로 분석. 데이터 시각화 + 지역별 분석이 리치고의 데이터 기반 접근과 동일. 차트 UI 참고.",
  },
  {
    name: "ColdFusion",
    id: "UCnM5iMGiKsZg-iOlIO2ZkdQ",
    url: "https://www.youtube.com/@ColdFusion",
    category: "해외 벤치마크",
    desc: "테크/경제 다큐멘터리",
    subs: "500만+",
    reason: "다큐멘터리급 제작 퀄리티. 경제+테크 교차 주제(핀테크, AI 경제 영향)가 높은 바이럴. 크로스오버 주제 기획과 영상 톤 참고.",
  },
  {
    name: "Minority Mindset",
    id: "UCT3EznhW_CNFcfOlyDNTLLw",
    url: "https://www.youtube.com/@MinorityMindset",
    category: "해외 벤치마크",
    desc: "재테크/부동산 — 교육형",
    subs: "150만+",
    reason: "금융 문맹 해소를 타겟으로 쉬운 해설. 숏폼+롱폼 병행 전략과 시리즈 콘텐츠 구성이 채널 성장 전략 참고.",
  },
  {
    name: "Eurodollar University",
    id: "UCkMtTL6pjfmSwbCkt571-TA",
    url: "https://www.youtube.com/@EurodollarUniversity",
    category: "해외 벤치마크",
    desc: "글로벌 금융 시스템 — 심층 분석",
    subs: "30만+",
    reason: "유로달러/글로벌 유동성 등 심층 주제 전문. 니치한 주제에서 높은 체류시간(평균 15분+)을 기록. 전문 니치 포지셔닝 참고.",
  },
  {
    name: "The Plain Bagel",
    id: "UCFCEuCsyWP0YkP3CZ3Mr01Q",
    url: "https://www.youtube.com/@ThePlainBagel",
    category: "해외 벤치마크",
    desc: "투자/경제 — 깔끔한 해설",
    subs: "90만+",
    reason: "CFA 출신의 정제된 경제 해설. 클린한 그래픽+차분한 톤이 리치고의 '신뢰감 있는 전문가' 이미지와 일치. 톤&비주얼 참고.",
  },
];

const CATEGORY_STYLE = {
  "운영": "bg-emerald-100 text-emerald-700 border-emerald-200",
  "국내 벤치마크": "bg-blue-100 text-blue-700 border-blue-200",
  "해외 벤치마크": "bg-purple-100 text-purple-700 border-purple-200",
};

export default function ChannelsPage() {
  const [channels, setChannels] = useState<Channel[]>(INITIAL_CHANNELS);
  const [showAdd, setShowAdd] = useState(false);
  const [newCh, setNewCh] = useState({ name: "", url: "", category: "국내 벤치마크" as Channel["category"], desc: "", reason: "" });
  const [expandedReason, setExpandedReason] = useState<string | null>(null);

  function addChannel() {
    if (!newCh.name || !newCh.url) return;
    const id = newCh.url.match(/@[\w-]+/)?.[0] ?? "";
    setChannels([...channels, { ...newCh, id, subs: "-" }]);
    setNewCh({ name: "", url: "", category: "국내 벤치마크", desc: "", reason: "" });
    setShowAdd(false);
  }

  const ownChannel = channels.filter((c) => c.category === "운영");
  const domestic = channels.filter((c) => c.category === "국내 벤치마크");
  const global = channels.filter((c) => c.category === "해외 벤치마크");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">채널 관리</h2>
        <button onClick={() => setShowAdd(!showAdd)} className="rounded-lg bg-navy px-4 py-1.5 text-xs font-semibold text-white hover:bg-navy/90">
          + 채널 등록
        </button>
      </div>

      {/* 채널 등록 폼 */}
      {showAdd && (
        <div className="rounded-2xl border border-navy/20 bg-navy/5 p-5">
          <h3 className="text-sm font-semibold">새 채널 등록</h3>
          <div className="mt-3 grid grid-cols-2 gap-3">
            <input value={newCh.name} onChange={(e) => setNewCh({ ...newCh, name: e.target.value })} placeholder="채널명" className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-navy focus:outline-none" />
            <input value={newCh.url} onChange={(e) => setNewCh({ ...newCh, url: e.target.value })} placeholder="YouTube 채널 URL" className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-navy focus:outline-none" />
            <select value={newCh.category} onChange={(e) => setNewCh({ ...newCh, category: e.target.value as Channel["category"] })} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
              <option value="운영">운영 채널</option>
              <option value="국내 벤치마크">국내 벤치마크</option>
              <option value="해외 벤치마크">해외 벤치마크</option>
            </select>
            <input value={newCh.desc} onChange={(e) => setNewCh({ ...newCh, desc: e.target.value })} placeholder="채널 설명" className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-navy focus:outline-none" />
            <textarea value={newCh.reason} onChange={(e) => setNewCh({ ...newCh, reason: e.target.value })} placeholder="벤치마킹 근거 (왜 이 채널을 참고하는지)" rows={2} className="col-span-2 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-navy focus:outline-none" />
          </div>
          <div className="mt-3 flex gap-2">
            <button onClick={addChannel} disabled={!newCh.name || !newCh.url} className="rounded-lg bg-navy px-4 py-1.5 text-xs font-semibold text-white disabled:opacity-40">등록</button>
            <button onClick={() => setShowAdd(false)} className="rounded-lg border border-slate-300 px-4 py-1.5 text-xs text-slate-600">취소</button>
          </div>
        </div>
      )}

      {/* 운영 채널 */}
      <section>
        <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          운영 채널
        </h3>
        <div className="mt-2">
          {ownChannel.map((ch) => (
            <div key={ch.name} className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-5">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-navy text-lg font-bold text-white">{ch.name[0]}</div>
                <div className="flex-1">
                  <a href={ch.url} target="_blank" rel="noreferrer" className="text-lg font-bold text-navy hover:underline">{ch.name}</a>
                  <div className="text-sm text-slate-600">{ch.desc}</div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-navy">{ch.subs}</div>
                  <div className="text-xs text-slate-400">구독자</div>
                </div>
                <span className={`rounded-full border px-3 py-1 text-xs font-medium ${CATEGORY_STYLE[ch.category]}`}>{ch.category}</span>
              </div>
              <div className="mt-3 rounded-lg bg-white/80 px-3 py-2 text-xs leading-relaxed text-slate-600">{ch.reason}</div>
            </div>
          ))}
        </div>
      </section>

      {/* 국내 벤치마크 */}
      <section>
        <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
          <span className="h-2 w-2 rounded-full bg-blue-500" />
          국내 벤치마크 ({domestic.length}개)
        </h3>
        <div className="mt-2 grid grid-cols-2 gap-3">
          {domestic.map((ch) => (
            <div key={ch.name} className="rounded-xl border border-slate-200 bg-white p-4 hover:border-blue-200 transition-colors">
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">{ch.name[0]}</div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <a href={ch.url} target="_blank" rel="noreferrer" className="text-sm font-bold text-navy hover:underline truncate">{ch.name}</a>
                    <span className="shrink-0 text-xs font-medium text-blue-600">{ch.subs}</span>
                  </div>
                  <div className="text-xs text-slate-500">{ch.desc}</div>
                  <a href={ch.url} target="_blank" rel="noreferrer" className="mt-0.5 block truncate text-[10px] text-blue-400 hover:underline">{ch.url}</a>
                </div>
              </div>

              <button onClick={() => setExpandedReason(expandedReason === ch.name ? null : ch.name)} className="mt-2 flex w-full items-center gap-1 text-[10px] font-medium text-slate-400 hover:text-slate-600">
                <svg className={`h-3 w-3 transition-transform ${expandedReason === ch.name ? "rotate-90" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                벤치마킹 근거
              </button>
              {expandedReason === ch.name && (
                <div className="mt-1.5 rounded-lg bg-blue-50 px-3 py-2 text-[11px] leading-relaxed text-slate-600">{ch.reason}</div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* 해외 벤치마크 */}
      <section>
        <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
          <span className="h-2 w-2 rounded-full bg-purple-500" />
          해외 벤치마크 ({global.length}개)
        </h3>
        <div className="mt-2 grid grid-cols-2 gap-3">
          {global.map((ch) => (
            <div key={ch.name} className="rounded-xl border border-slate-200 bg-white p-4 hover:border-purple-200 transition-colors">
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-purple-600 text-sm font-bold text-white">{ch.name[0]}</div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <a href={ch.url} target="_blank" rel="noreferrer" className="text-sm font-bold text-navy hover:underline truncate">{ch.name}</a>
                    <span className="shrink-0 text-xs font-medium text-purple-600">{ch.subs}</span>
                  </div>
                  <div className="text-xs text-slate-500">{ch.desc}</div>
                  <a href={ch.url} target="_blank" rel="noreferrer" className="mt-0.5 block truncate text-[10px] text-purple-400 hover:underline">{ch.url}</a>
                </div>
              </div>

              <button onClick={() => setExpandedReason(expandedReason === ch.name ? null : ch.name)} className="mt-2 flex w-full items-center gap-1 text-[10px] font-medium text-slate-400 hover:text-slate-600">
                <svg className={`h-3 w-3 transition-transform ${expandedReason === ch.name ? "rotate-90" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                벤치마킹 근거
              </button>
              {expandedReason === ch.name && (
                <div className="mt-1.5 rounded-lg bg-purple-50 px-3 py-2 text-[11px] leading-relaxed text-slate-600">{ch.reason}</div>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
