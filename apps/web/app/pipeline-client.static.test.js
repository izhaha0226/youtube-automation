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
assert(source.includes('width={140}') && source.includes('margin={{ left: 145'), '키워드 차트 라벨이 잘리지 않도록 왼쪽 여백과 축 폭을 확보해야 합니다.');
assert(source.includes('productionEdits'), '제작 리스트 수정 상태가 필요합니다.');
assert(source.includes('hiddenProductionKeys'), '제작 리스트 삭제/숨김 상태가 필요합니다.');
assert(source.includes('saveProductionEdit'), '제작 리스트 수정 저장 함수가 필요합니다.');
assert(source.includes('deleteSelectedProduction'), '제작 리스트 삭제 실행 함수가 필요합니다.');
assert(source.includes('삭제 확인'), '삭제는 확인 단계를 거쳐야 합니다.');
assert(source.includes('복구'), '삭제된 제작 항목을 복구할 수 있어야 합니다.');

console.log('static UI requirements satisfied');
