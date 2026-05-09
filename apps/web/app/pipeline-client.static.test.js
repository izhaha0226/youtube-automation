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

console.log('static UI requirements satisfied');
