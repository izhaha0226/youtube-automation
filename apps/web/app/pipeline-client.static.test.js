const fs = require('fs');
const source = fs.readFileSync('app/pipeline-client.tsx', 'utf8');

function assert(condition, message) {
  if (!condition) {
    console.error(message);
    process.exit(1);
  }
}

assert(source.includes('showAllKeywords'), '키워드 더보기 상태가 필요합니다.');
assert(source.includes('displayedTrendKeywordRows'), '키워드 순위 표시 행 분리가 필요합니다.');
assert(source.includes('분석 버튼을 누르기 전에는 주제 분석을 실행하지 않습니다.'), '분석 자동실행 방지 안내가 필요합니다.');
assert(!source.includes('onClick={runPrimaryAction}'), '상단 통합 실행 버튼은 분석 자동실행 위험 때문에 제거되어야 합니다.');
assert(source.includes('키워드 순위 Top 10'), '키워드 순위는 기본 Top 10으로 보여야 합니다.');
assert(source.includes('더보기'), '키워드 순위 더보기 버튼이 필요합니다.');
assert(source.includes('bg-blue-600') && source.includes('hover:bg-blue-700'), '트렌드 스캔 실행 버튼은 파란색이어야 합니다.');
assert(!source.includes('상관관계 강한 키워드 페어'), '어려운 상관관계 문구는 제거해야 합니다.');
assert(source.includes('함께 자주 언급된 키워드'), '키워드 페어는 쉬운 표현으로 설명해야 합니다.');
assert(source.includes('선택한 뉴스로 다음 단계 이동'), '선택 뉴스 다음 버튼은 뉴스 목록 하단 문맥에 있어야 합니다.');
assert(source.indexOf('트렌드 스캔 실행') < source.indexOf('선택한 뉴스로 다음 단계 이동'), '선택 뉴스 다음 버튼은 스캔 버튼 영역이 아니라 하단에 있어야 합니다.');
assert(source.includes('keywordChartHeight') && source.includes('height={keywordChartHeight}'), '키워드 차트 Top 10 전체 항목을 보여주도록 동적 높이가 필요합니다.');
assert(source.includes('width={150}') && source.includes('interval={0}') && source.includes('minTickGap={0}'), '키워드 차트 Top 10 y축 라벨을 생략하지 않도록 축 폭과 interval=0이 필요합니다.');
assert(source.includes('productionEdits'), '제작 리스트 수정 상태가 필요합니다.');
assert(source.includes('hiddenProductionKeys'), '제작 리스트 삭제/숨김 상태가 필요합니다.');
assert(source.includes('saveProductionEdit'), '제작 리스트 수정 저장 함수가 필요합니다.');
assert(source.includes('deleteSelectedProduction'), '제작 리스트 삭제 실행 함수가 필요합니다.');
assert(source.includes('resumeProduction') && source.includes('getProductionResumeHref'), '제작 리스트 클릭 시 마지막 진행 단계로 이동해야 합니다.');
assert(source.includes('if (item.key === "new-video")'), '제작 리스트의 마지막 진행 단계 이동은 신규 영상 항목에만 적용해야 합니다.');
assert(source.includes('return item.href;'), '트렌드/주제 제작 리스트는 각 항목의 고유 경로로 이동해야 합니다.');
assert(source.includes('if (scenario) return "/scenario";'), '시나리오가 있으면 우측 제작 리스트도 단일 시나리오 화면으로 이어져야 합니다.');
assert(!source.includes('if (scenario && research?.session_id) return `/workspace/${research.session_id}`;'), '우측 버튼이 별도 워크스페이스 시나리오로 이동하면 시나리오가 2개처럼 보입니다.');
assert(source.includes('hydratedDashboard') && source.includes('if (!hydratedDashboard) return;'), '저장된 대시보드가 복원되기 전 빈 상태로 덮어쓰면 안 됩니다.');
assert(source.includes('클릭하면 현재 시나리오로 이어가기'), '제작 리스트에는 현재 시나리오로 이어진다는 안내가 필요합니다.');
assert(source.includes('삭제 확인'), '삭제는 확인 단계를 거쳐야 합니다.');
assert(source.includes('복구'), '삭제된 제작 항목을 복구할 수 있어야 합니다.');
assert(source.includes('TrendSourceFilter = "all" | "naver" | "google" | "youtube"'), '트렌드 소스 필터는 전체/네이버/구글/유튜브만 허용해야 합니다.');
assert(source.includes('useState<TrendSourceFilter>("all")'), '트렌드 기본 화면은 전체여야 합니다.');
assert(source.includes('TREND_SOURCE_TABS') && source.includes('label: "전체"') && source.includes('label: "네이버"') && source.includes('label: "구글"') && source.includes('label: "유튜브"'), '소스 탭은 전체/네이버/구글/유튜브 고정이어야 합니다.');
assert(source.includes('compactUrl'), '긴 URL은 짧은 표시 URL로 변환해야 합니다.');
assert(source.includes('displayedTrendSourceItems') && source.includes('selectedIssues.length > 0'), '항목 체크 시 체크한 항목만 표시하는 필터가 필요합니다.');
assert(source.includes('benchmarkTopByChannel') && source.includes('채널당 최고 영상 1개만 표시'), '유튜브 벤치마크 차트는 채널별 1개 최고 영상으로 중복 채널을 막아야 합니다.');
assert(source.includes('xl:grid-cols-2'), '하단 트렌드 분석 섹션은 2열 구성이어야 합니다.');
assert(source.indexOf('카테고리별 이슈 분포') < source.indexOf('유튜브 벤치마크 채널별 최고 조회수'), '카테고리 분포와 유튜브 벤치마크는 분리된 섹션이어야 합니다.');
assert(source.includes('StatusModal') && source.includes('open={Boolean(error)}'), '오류/알림 메시지는 인라인 텍스트가 아니라 모달로 표시해야 합니다.');
assert(!source.includes('text-red-600">{error}</p>'), '인라인 오류 문구를 남기면 안 됩니다.');
assert(source.includes('영상별 분석 요약'), '4번에는 선택 영상별 개별 분석 요약이 보여야 합니다.');
assert(source.includes('우리 영상 도입 적용안'), '4번에는 분석 내용을 우리 영상 도입부에 어떻게 적용할지 보여야 합니다.');
assert(source.includes('most_watched_scene') && source.includes('most_watched_time'), '영상별 분석에는 가장 많이 본 시간대와 장면 필드가 필요합니다.');
assert(source.includes('/prompter') && source.includes('프롬프터 모드'), '시나리오 화면에는 프롬프터 모드 진입 버튼이 필요합니다.');

const layoutSource = fs.readFileSync('app/layout.tsx', 'utf8');
assert(layoutSource.includes('ActiveNavLinks'), '왼쪽/상단 메뉴는 현재 경로 active 표시 컴포넌트를 사용해야 합니다.');
assert(layoutSource.includes('aria-current="page"') || fs.existsSync('app/components/active-nav-links.tsx'), '현재 페이지 메뉴에는 aria-current page가 필요합니다.');

const prompterSource = fs.existsSync('app/prompter/page.tsx') ? fs.readFileSync('app/prompter/page.tsx', 'utf8') : '';
assert(prompterSource.includes('프롬프터 모드'), '별도 프롬프터 페이지가 필요합니다.');
assert(prompterSource.includes('requestAnimationFrame'), '프롬프터는 자동으로 글자가 위로 올라가야 합니다.');
assert(prompterSource.includes('scrollSpeed') && prompterSource.includes('fontSize'), '프롬프터는 올라가는 속도와 글자 크기를 조절해야 합니다.');
assert(prompterSource.includes('loadDashboard'), '프롬프터는 저장된 시나리오 본문을 불러와야 합니다.');
assert(prompterSource.includes('visibleSectionCount'), '프롬프터는 전체 대본을 한 번에 렌더링하지 않고 섹션 단위로 로드해야 합니다.');
assert(prompterSource.includes('ensureSectionsLoadedForViewport'), '프롬프터는 스크롤 위치에 따라 필요한 섹션만 추가 로드해야 합니다.');
assert(prompterSource.includes('더 읽는 중') || prompterSource.includes('섹션 단위'), '프롬프터에는 섹션 단위 로딩 상태 안내가 필요합니다.');

console.log('static UI requirements satisfied');
